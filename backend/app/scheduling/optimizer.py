# Schedule Optimizer - Constraint-based class scheduling optimization
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, date
from enum import Enum
import uuid
from collections import defaultdict


class DayOfWeek(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class TimeSlot:
    """Represents a time slot for scheduling."""
    day: DayOfWeek
    start_time: time
    end_time: time
    
    def overlaps(self, other: 'TimeSlot') -> bool:
        """Check if this slot overlaps with another."""
        if self.day != other.day:
            return False
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)
    
    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        start_mins = self.start_time.hour * 60 + self.start_time.minute
        end_mins = self.end_time.hour * 60 + self.end_time.minute
        return end_mins - start_mins
    
    def __str__(self) -> str:
        return f"{self.day.name} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"


@dataclass
class Instructor:
    """Instructor with availability and specialties."""
    id: str
    name: str
    specialties: List[str]  # Dance styles they can teach
    availability: List[TimeSlot]  # When they're available
    max_hours_per_week: int = 20
    min_break_between_classes: int = 15  # minutes
    
    def is_available(self, slot: TimeSlot) -> bool:
        """Check if instructor is available for a slot."""
        for avail in self.availability:
            if avail.day == slot.day:
                if avail.start_time <= slot.start_time and avail.end_time >= slot.end_time:
                    return True
        return False
    
    def can_teach(self, dance_style: str) -> bool:
        """Check if instructor can teach a style."""
        return dance_style.lower() in [s.lower() for s in self.specialties]


@dataclass
class Room:
    """Studio room with capacity and features."""
    id: str
    name: str
    capacity: int
    features: List[str]  # ['mirrors', 'sound_system', 'sprung_floor']
    
    def has_features(self, required: List[str]) -> bool:
        """Check if room has required features."""
        return all(f in self.features for f in required)


@dataclass
class ClassDefinition:
    """Definition of a class to be scheduled."""
    id: str
    name: str
    dance_style: str
    level: str  # Beginner, Intermediate, Advanced
    duration_minutes: int
    min_capacity: int
    max_capacity: int
    required_features: List[str] = field(default_factory=list)
    preferred_times: List[TimeSlot] = field(default_factory=list)  # Hints for optimization
    frequency_per_week: int = 1


@dataclass
class ScheduledClass:
    """A class that has been scheduled."""
    class_def: ClassDefinition
    instructor: Instructor
    room: Room
    time_slot: TimeSlot
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'class_id': self.class_def.id,
            'class_name': self.class_def.name,
            'dance_style': self.class_def.dance_style,
            'level': self.class_def.level,
            'instructor_id': self.instructor.id,
            'instructor_name': self.instructor.name,
            'room_id': self.room.id,
            'room_name': self.room.name,
            'day': self.time_slot.day.name,
            'start_time': self.time_slot.start_time.strftime('%H:%M'),
            'end_time': self.time_slot.end_time.strftime('%H:%M'),
        }


@dataclass
class ScheduleConstraints:
    """Constraints for schedule optimization."""
    # Operating hours
    opening_time: time = time(9, 0)
    closing_time: time = time(21, 0)
    
    # Business rules
    min_break_between_classes: int = 15  # minutes
    max_concurrent_classes: int = 3
    
    # Peak hour preferences (more beginner classes in evenings)
    peak_hours_start: time = time(17, 0)
    peak_hours_end: time = time(20, 0)
    prefer_beginners_in_peak: bool = True
    
    # Slot preferences
    preferred_slot_duration: int = 60  # minutes
    slot_increment: int = 30  # minutes between potential start times


@dataclass
class OptimizationResult:
    """Result of schedule optimization."""
    success: bool
    schedule: List[ScheduledClass]
    unscheduled: List[ClassDefinition]
    conflicts: List[Dict[str, Any]]
    utilization: Dict[str, float]  # Resource utilization metrics
    score: float  # Optimization score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'schedule': [s.to_dict() for s in self.schedule],
            'unscheduled': [{'id': c.id, 'name': c.name} for c in self.unscheduled],
            'conflicts': self.conflicts,
            'utilization': self.utilization,
            'score': self.score
        }


class ScheduleOptimizer:
    """
    Constraint-based class schedule optimizer.
    
    Uses a greedy algorithm with backtracking to find optimal schedules
    that satisfy all hard constraints and maximize soft constraint scores.
    
    Hard Constraints:
    - Instructor availability
    - Room capacity
    - No double-booking (instructor, room)
    - Operating hours
    
    Soft Constraints (scored):
    - Preferred time slots
    - Beginner classes in peak hours
    - Minimize instructor transitions
    - Balance room utilization
    """
    
    def __init__(self, constraints: ScheduleConstraints = None):
        self.constraints = constraints or ScheduleConstraints()
        
    def generate_time_slots(self) -> List[TimeSlot]:
        """Generate all possible time slots based on constraints."""
        slots = []
        increment = timedelta(minutes=self.constraints.slot_increment)
        
        for day in DayOfWeek:
            current = datetime.combine(date.today(), self.constraints.opening_time)
            closing = datetime.combine(date.today(), self.constraints.closing_time)
            
            while current < closing:
                for duration in [60, 75, 90]:  # Common class durations
                    end = current + timedelta(minutes=duration)
                    if end.time() <= self.constraints.closing_time:
                        slots.append(TimeSlot(
                            day=day,
                            start_time=current.time(),
                            end_time=end.time()
                        ))
                current += increment
        
        return slots
    
    def optimize(
        self,
        classes: List[ClassDefinition],
        instructors: List[Instructor],
        rooms: List[Room]
    ) -> OptimizationResult:
        """
        Run schedule optimization.
        
        Args:
            classes: Classes to schedule
            instructors: Available instructors
            rooms: Available rooms
            
        Returns:
            OptimizationResult with optimized schedule
        """
        all_slots = self.generate_time_slots()
        scheduled: List[ScheduledClass] = []
        unscheduled: List[ClassDefinition] = []
        conflicts: List[Dict[str, Any]] = []
        
        # Track assignments
        instructor_schedule: Dict[str, List[TimeSlot]] = defaultdict(list)
        room_schedule: Dict[str, List[TimeSlot]] = defaultdict(list)
        
        # Sort classes by priority (more constrained first)
        sorted_classes = self._prioritize_classes(classes, instructors)
        
        for class_def in sorted_classes:
            best_assignment = None
            best_score = -1
            
            # Find all valid assignments
            for instructor in instructors:
                if not instructor.can_teach(class_def.dance_style):
                    continue
                
                for room in rooms:
                    if room.capacity < class_def.min_capacity:
                        continue
                    if not room.has_features(class_def.required_features):
                        continue
                    
                    for slot in all_slots:
                        if slot.duration_minutes() != class_def.duration_minutes:
                            continue
                        
                        # Check hard constraints
                        if not self._is_valid_assignment(
                            class_def, instructor, room, slot,
                            instructor_schedule, room_schedule
                        ):
                            continue
                        
                        # Score this assignment
                        score = self._score_assignment(
                            class_def, instructor, room, slot,
                            instructor_schedule
                        )
                        
                        if score > best_score:
                            best_score = score
                            best_assignment = (instructor, room, slot)
            
            if best_assignment:
                instructor, room, slot = best_assignment
                scheduled_class = ScheduledClass(
                    class_def=class_def,
                    instructor=instructor,
                    room=room,
                    time_slot=slot
                )
                scheduled.append(scheduled_class)
                instructor_schedule[instructor.id].append(slot)
                room_schedule[room.id].append(slot)
            else:
                unscheduled.append(class_def)
                conflicts.append({
                    'class': class_def.name,
                    'reason': self._get_failure_reason(class_def, instructors, rooms)
                })
        
        # Calculate utilization metrics
        utilization = self._calculate_utilization(
            scheduled, instructors, rooms
        )
        
        # Calculate overall score
        total_score = sum(
            self._score_assignment(
                s.class_def, s.instructor, s.room, s.time_slot,
                instructor_schedule
            )
            for s in scheduled
        )
        
        return OptimizationResult(
            success=len(unscheduled) == 0,
            schedule=scheduled,
            unscheduled=unscheduled,
            conflicts=conflicts,
            utilization=utilization,
            score=total_score / max(len(scheduled), 1)
        )
    
    def _prioritize_classes(
        self,
        classes: List[ClassDefinition],
        instructors: List[Instructor]
    ) -> List[ClassDefinition]:
        """Sort classes by how constrained they are (most constrained first)."""
        def constraint_score(c: ClassDefinition) -> int:
            # Count available instructors
            available_instructors = sum(
                1 for i in instructors if i.can_teach(c.dance_style)
            )
            # More constrained = higher priority
            return -available_instructors + len(c.required_features) * 10
        
        return sorted(classes, key=constraint_score, reverse=True)
    
    def _is_valid_assignment(
        self,
        class_def: ClassDefinition,
        instructor: Instructor,
        room: Room,
        slot: TimeSlot,
        instructor_schedule: Dict[str, List[TimeSlot]],
        room_schedule: Dict[str, List[TimeSlot]]
    ) -> bool:
        """Check if assignment satisfies all hard constraints."""
        # Instructor availability
        if not instructor.is_available(slot):
            return False
        
        # Instructor not double-booked
        for existing in instructor_schedule[instructor.id]:
            if slot.overlaps(existing):
                return False
            # Check break time
            if slot.day == existing.day:
                gap = self._time_gap(existing, slot)
                if 0 < gap < self.constraints.min_break_between_classes:
                    return False
        
        # Room not double-booked
        for existing in room_schedule[room.id]:
            if slot.overlaps(existing):
                return False
        
        # Check max concurrent classes
        concurrent = sum(
            1 for r_slots in room_schedule.values()
            for r_slot in r_slots
            if slot.overlaps(r_slot)
        )
        if concurrent >= self.constraints.max_concurrent_classes:
            return False
        
        return True
    
    def _score_assignment(
        self,
        class_def: ClassDefinition,
        instructor: Instructor,
        room: Room,
        slot: TimeSlot,
        instructor_schedule: Dict[str, List[TimeSlot]]
    ) -> float:
        """Score an assignment based on soft constraints."""
        score = 0.0
        
        # Preferred time slots
        for pref in class_def.preferred_times:
            if slot.day == pref.day:
                if pref.start_time <= slot.start_time <= pref.end_time:
                    score += 20
        
        # Beginner classes in peak hours
        is_peak = self.constraints.peak_hours_start <= slot.start_time <= self.constraints.peak_hours_end
        is_beginner = 'beginner' in class_def.level.lower()
        
        if self.constraints.prefer_beginners_in_peak:
            if is_peak and is_beginner:
                score += 15
            elif is_peak and not is_beginner:
                score -= 5
        
        # Room size fit (not too big, not too small)
        size_ratio = class_def.max_capacity / room.capacity
        if 0.5 <= size_ratio <= 1.0:
            score += 10
        elif size_ratio > 1.0:
            score -= 20  # Room too small
        
        # Instructor continuity (keep same instructor on same day)
        same_day_classes = [
            s for s in instructor_schedule[instructor.id]
            if s.day == slot.day
        ]
        if same_day_classes:
            score += 5 * len(same_day_classes)
        
        return score
    
    def _time_gap(self, slot1: TimeSlot, slot2: TimeSlot) -> int:
        """Calculate gap in minutes between two slots."""
        if slot1.day != slot2.day:
            return float('inf')
        
        end1 = slot1.end_time.hour * 60 + slot1.end_time.minute
        start1 = slot1.start_time.hour * 60 + slot1.start_time.minute
        end2 = slot2.end_time.hour * 60 + slot2.end_time.minute
        start2 = slot2.start_time.hour * 60 + slot2.start_time.minute
        
        if end1 <= start2:
            return start2 - end1
        elif end2 <= start1:
            return start1 - end2
        else:
            return 0  # Overlapping
    
    def _get_failure_reason(
        self,
        class_def: ClassDefinition,
        instructors: List[Instructor],
        rooms: List[Room]
    ) -> str:
        """Get reason why a class couldn't be scheduled."""
        # Check instructor availability
        qualified = [i for i in instructors if i.can_teach(class_def.dance_style)]
        if not qualified:
            return f"No instructor qualified to teach {class_def.dance_style}"
        
        # Check room availability
        suitable = [r for r in rooms if r.capacity >= class_def.min_capacity]
        if not suitable:
            return f"No room with capacity >= {class_def.min_capacity}"
        
        if class_def.required_features:
            with_features = [r for r in suitable if r.has_features(class_def.required_features)]
            if not with_features:
                return f"No room with required features: {class_def.required_features}"
        
        return "No available time slot that satisfies all constraints"
    
    def _calculate_utilization(
        self,
        scheduled: List[ScheduledClass],
        instructors: List[Instructor],
        rooms: List[Room]
    ) -> Dict[str, float]:
        """Calculate resource utilization metrics."""
        # Instructor utilization
        instructor_hours = defaultdict(int)
        for s in scheduled:
            instructor_hours[s.instructor.id] += s.time_slot.duration_minutes()
        
        instructor_util = {
            i.id: (instructor_hours[i.id] / 60) / i.max_hours_per_week * 100
            for i in instructors
        }
        
        # Room utilization (based on operating hours per week)
        operating_hours = (
            (self.constraints.closing_time.hour - self.constraints.opening_time.hour) * 7
        )
        room_hours = defaultdict(int)
        for s in scheduled:
            room_hours[s.room.id] += s.time_slot.duration_minutes()
        
        room_util = {
            r.id: (room_hours[r.id] / 60) / operating_hours * 100
            for r in rooms
        }
        
        return {
            'instructor_utilization': instructor_util,
            'room_utilization': room_util,
            'avg_instructor_util': sum(instructor_util.values()) / max(len(instructor_util), 1),
            'avg_room_util': sum(room_util.values()) / max(len(room_util), 1),
            'total_classes': len(scheduled),
            'total_hours': sum(s.time_slot.duration_minutes() for s in scheduled) / 60
        }
