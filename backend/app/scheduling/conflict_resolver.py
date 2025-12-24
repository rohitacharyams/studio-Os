# Conflict Resolver - Handles schedule conflicts and adjustments
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, time, date, timedelta
from dataclasses import dataclass

from .optimizer import TimeSlot, DayOfWeek, ScheduledClass


@dataclass
class Conflict:
    """Represents a scheduling conflict."""
    type: str  # 'instructor', 'room', 'time'
    severity: str  # 'hard', 'soft'
    description: str
    affected_classes: List[str]
    suggested_resolution: Optional[str] = None


class ConflictResolver:
    """
    Detects and resolves scheduling conflicts.
    
    Handles:
    - Double-booked instructors
    - Double-booked rooms
    - Overlapping classes
    - Instructor availability violations
    - Capacity issues
    """
    
    def __init__(self):
        self.conflicts: List[Conflict] = []
    
    def detect_conflicts(
        self,
        schedule: List[ScheduledClass]
    ) -> List[Conflict]:
        """
        Detect all conflicts in a schedule.
        
        Args:
            schedule: List of scheduled classes
            
        Returns:
            List of detected conflicts
        """
        self.conflicts = []
        
        # Check instructor double-booking
        self._check_instructor_conflicts(schedule)
        
        # Check room double-booking
        self._check_room_conflicts(schedule)
        
        # Check capacity issues
        self._check_capacity_issues(schedule)
        
        return self.conflicts
    
    def _check_instructor_conflicts(self, schedule: List[ScheduledClass]):
        """Check for instructor double-booking."""
        instructor_classes: Dict[str, List[ScheduledClass]] = {}
        
        for cls in schedule:
            instructor_id = cls.instructor.id
            if instructor_id not in instructor_classes:
                instructor_classes[instructor_id] = []
            instructor_classes[instructor_id].append(cls)
        
        for instructor_id, classes in instructor_classes.items():
            # Sort by day and time
            classes.sort(key=lambda c: (c.time_slot.day.value, c.time_slot.start_time))
            
            for i, cls1 in enumerate(classes):
                for cls2 in classes[i+1:]:
                    if cls1.time_slot.overlaps(cls2.time_slot):
                        self.conflicts.append(Conflict(
                            type='instructor',
                            severity='hard',
                            description=f"Instructor {cls1.instructor.name} double-booked",
                            affected_classes=[cls1.class_def.id, cls2.class_def.id],
                            suggested_resolution=f"Move {cls2.class_def.name} to different time or assign different instructor"
                        ))
    
    def _check_room_conflicts(self, schedule: List[ScheduledClass]):
        """Check for room double-booking."""
        room_classes: Dict[str, List[ScheduledClass]] = {}
        
        for cls in schedule:
            room_id = cls.room.id
            if room_id not in room_classes:
                room_classes[room_id] = []
            room_classes[room_id].append(cls)
        
        for room_id, classes in room_classes.items():
            classes.sort(key=lambda c: (c.time_slot.day.value, c.time_slot.start_time))
            
            for i, cls1 in enumerate(classes):
                for cls2 in classes[i+1:]:
                    if cls1.time_slot.overlaps(cls2.time_slot):
                        self.conflicts.append(Conflict(
                            type='room',
                            severity='hard',
                            description=f"Room {cls1.room.name} double-booked",
                            affected_classes=[cls1.class_def.id, cls2.class_def.id],
                            suggested_resolution=f"Move {cls2.class_def.name} to different room"
                        ))
    
    def _check_capacity_issues(self, schedule: List[ScheduledClass]):
        """Check for capacity issues."""
        for cls in schedule:
            if cls.room.capacity < cls.class_def.min_capacity:
                self.conflicts.append(Conflict(
                    type='capacity',
                    severity='soft',
                    description=f"Room {cls.room.name} may be too small for {cls.class_def.name}",
                    affected_classes=[cls.class_def.id],
                    suggested_resolution=f"Consider larger room (current: {cls.room.capacity}, needed: {cls.class_def.min_capacity})"
                ))
    
    def resolve_instructor_conflict(
        self,
        conflict: Conflict,
        schedule: List[ScheduledClass],
        available_instructors: List[Any]
    ) -> Optional[ScheduledClass]:
        """
        Attempt to resolve an instructor conflict by reassignment.
        
        Returns the modified class or None if unresolvable.
        """
        if conflict.type != 'instructor':
            return None
        
        # Find the conflicting classes
        affected = [c for c in schedule if c.class_def.id in conflict.affected_classes]
        if len(affected) < 2:
            return None
        
        # Try to reassign the second class
        cls_to_move = affected[1]
        
        for instructor in available_instructors:
            if instructor.id == cls_to_move.instructor.id:
                continue
            
            if not instructor.can_teach(cls_to_move.class_def.dance_style):
                continue
            
            if instructor.is_available(cls_to_move.time_slot):
                # Check if this instructor is free at this time
                is_free = True
                for other in schedule:
                    if other.instructor.id == instructor.id:
                        if other.time_slot.overlaps(cls_to_move.time_slot):
                            is_free = False
                            break
                
                if is_free:
                    # Create new scheduled class with different instructor
                    return ScheduledClass(
                        class_def=cls_to_move.class_def,
                        instructor=instructor,
                        room=cls_to_move.room,
                        time_slot=cls_to_move.time_slot
                    )
        
        return None
    
    def resolve_room_conflict(
        self,
        conflict: Conflict,
        schedule: List[ScheduledClass],
        available_rooms: List[Any]
    ) -> Optional[ScheduledClass]:
        """
        Attempt to resolve a room conflict by reassignment.
        """
        if conflict.type != 'room':
            return None
        
        affected = [c for c in schedule if c.class_def.id in conflict.affected_classes]
        if len(affected) < 2:
            return None
        
        cls_to_move = affected[1]
        
        for room in available_rooms:
            if room.id == cls_to_move.room.id:
                continue
            
            if room.capacity < cls_to_move.class_def.min_capacity:
                continue
            
            # Check if room is free
            is_free = True
            for other in schedule:
                if other.room.id == room.id:
                    if other.time_slot.overlaps(cls_to_move.time_slot):
                        is_free = False
                        break
            
            if is_free:
                return ScheduledClass(
                    class_def=cls_to_move.class_def,
                    instructor=cls_to_move.instructor,
                    room=room,
                    time_slot=cls_to_move.time_slot
                )
        
        return None
    
    def get_conflict_summary(self) -> Dict[str, Any]:
        """Get summary of detected conflicts."""
        hard_conflicts = [c for c in self.conflicts if c.severity == 'hard']
        soft_conflicts = [c for c in self.conflicts if c.severity == 'soft']
        
        by_type = {}
        for c in self.conflicts:
            if c.type not in by_type:
                by_type[c.type] = 0
            by_type[c.type] += 1
        
        return {
            'total': len(self.conflicts),
            'hard': len(hard_conflicts),
            'soft': len(soft_conflicts),
            'by_type': by_type,
            'conflicts': [
                {
                    'type': c.type,
                    'severity': c.severity,
                    'description': c.description,
                    'resolution': c.suggested_resolution
                }
                for c in self.conflicts
            ]
        }
