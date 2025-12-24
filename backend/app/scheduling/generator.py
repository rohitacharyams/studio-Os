# Schedule Generator - Generates schedules from database models
import uuid
from typing import List, Dict, Any, Optional
from datetime import time, date, datetime, timedelta

from app.models import db, DanceClass, ClassSchedule, User, Room as RoomModel, InstructorAvailability
from .optimizer import (
    ScheduleOptimizer, ScheduleConstraints, OptimizationResult,
    ClassDefinition, Instructor, Room, TimeSlot, DayOfWeek
)


class ScheduleGenerator:
    """
    Generates and manages class schedules using the optimizer.
    
    Bridges between database models and the optimization algorithm.
    """
    
    def __init__(self, studio_id: str):
        self.studio_id = studio_id
        
    def load_instructors(self) -> List[Instructor]:
        """Load instructors from database."""
        # Get users who are instructors
        users = User.query.filter_by(
            studio_id=self.studio_id,
            role='INSTRUCTOR'
        ).all()
        
        instructors = []
        for user in users:
            # Load availability
            availability_records = InstructorAvailability.query.filter_by(
                instructor_id=user.id,
                is_available=True
            ).all()
            
            availability = []
            for avail in availability_records:
                if avail.specific_date is None:  # Regular weekly availability
                    availability.append(TimeSlot(
                        day=DayOfWeek(avail.day_of_week),
                        start_time=avail.start_time,
                        end_time=avail.end_time
                    ))
            
            # Get specialties from user profile or default
            specialties = user.extra_data.get('specialties', []) if user.extra_data else []
            if not specialties:
                # Default to all styles
                specialties = ['salsa', 'bachata', 'hip-hop', 'ballet', 'contemporary', 'jazz']
            
            instructors.append(Instructor(
                id=user.id,
                name=f"{user.first_name} {user.last_name}",
                specialties=specialties,
                availability=availability,
                max_hours_per_week=user.extra_data.get('max_hours', 20) if user.extra_data else 20
            ))
        
        return instructors
    
    def load_rooms(self) -> List[Room]:
        """Load rooms from database."""
        room_records = RoomModel.query.filter_by(
            studio_id=self.studio_id,
            is_active=True
        ).all()
        
        rooms = []
        for room in room_records:
            rooms.append(Room(
                id=room.id,
                name=room.name,
                capacity=room.capacity,
                features=room.features or []
            ))
        
        return rooms
    
    def load_classes(self) -> List[ClassDefinition]:
        """Load class definitions from database."""
        class_records = DanceClass.query.filter_by(
            studio_id=self.studio_id,
            is_active=True
        ).all()
        
        classes = []
        for cls in class_records:
            classes.append(ClassDefinition(
                id=cls.id,
                name=cls.name,
                dance_style=cls.dance_style or 'general',
                level=cls.level or 'All Levels',
                duration_minutes=cls.duration_minutes or 60,
                min_capacity=cls.min_capacity or 3,
                max_capacity=cls.max_capacity or 20,
                required_features=[]
            ))
        
        return classes
    
    def generate_optimized_schedule(
        self,
        constraints: ScheduleConstraints = None
    ) -> OptimizationResult:
        """
        Generate an optimized schedule for all active classes.
        
        Returns:
            OptimizationResult with the generated schedule
        """
        instructors = self.load_instructors()
        rooms = self.load_rooms()
        classes = self.load_classes()
        
        if not instructors:
            return OptimizationResult(
                success=False,
                schedule=[],
                unscheduled=classes,
                conflicts=[{'reason': 'No instructors available'}],
                utilization={},
                score=0
            )
        
        if not rooms:
            return OptimizationResult(
                success=False,
                schedule=[],
                unscheduled=classes,
                conflicts=[{'reason': 'No rooms available'}],
                utilization={},
                score=0
            )
        
        optimizer = ScheduleOptimizer(constraints)
        return optimizer.optimize(classes, instructors, rooms)
    
    def save_schedule(self, result: OptimizationResult) -> List[str]:
        """
        Save optimization result to database.
        
        Returns:
            List of created schedule IDs
        """
        schedule_ids = []
        
        for scheduled in result.schedule:
            schedule = ClassSchedule(
                id=str(uuid.uuid4()),
                studio_id=self.studio_id,
                class_id=scheduled.class_def.id,
                day_of_week=scheduled.time_slot.day.value,
                start_time=scheduled.time_slot.start_time,
                end_time=scheduled.time_slot.end_time,
                room=scheduled.room.name,
                instructor_id=scheduled.instructor.id,
                is_recurring=True
            )
            db.session.add(schedule)
            schedule_ids.append(schedule.id)
        
        db.session.commit()
        return schedule_ids
    
    def get_current_schedule(self) -> List[Dict[str, Any]]:
        """Get current schedule from database."""
        schedules = ClassSchedule.query.filter_by(
            studio_id=self.studio_id,
            is_cancelled=False
        ).all()
        
        result = []
        for schedule in schedules:
            dance_class = DanceClass.query.get(schedule.class_id)
            instructor = User.query.get(schedule.instructor_id) if schedule.instructor_id else None
            
            result.append({
                'id': schedule.id,
                'class_name': dance_class.name if dance_class else 'Unknown',
                'dance_style': dance_class.dance_style if dance_class else None,
                'level': dance_class.level if dance_class else None,
                'day_of_week': schedule.day_of_week,
                'day_name': DayOfWeek(schedule.day_of_week).name if schedule.day_of_week is not None else None,
                'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else None,
                'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else None,
                'room': schedule.room,
                'instructor_name': f"{instructor.first_name} {instructor.last_name}" if instructor else None,
                'current_enrollment': schedule.current_enrollment
            })
        
        return result
    
    def suggest_new_class_time(
        self,
        class_def: ClassDefinition
    ) -> List[Dict[str, Any]]:
        """
        Suggest optimal times for a new class.
        
        Returns top 3 suggested time slots.
        """
        instructors = self.load_instructors()
        rooms = self.load_rooms()
        
        # Get current schedule to avoid conflicts
        current = self.get_current_schedule()
        
        # Find instructors who can teach this style
        qualified = [i for i in instructors if i.can_teach(class_def.dance_style)]
        
        suggestions = []
        optimizer = ScheduleOptimizer()
        all_slots = optimizer.generate_time_slots()
        
        for slot in all_slots:
            if slot.duration_minutes() != class_def.duration_minutes:
                continue
            
            for instructor in qualified:
                if not instructor.is_available(slot):
                    continue
                
                # Check for conflicts
                has_conflict = False
                for existing in current:
                    if existing['day_of_week'] == slot.day.value:
                        existing_start = datetime.strptime(existing['start_time'], '%H:%M').time()
                        existing_end = datetime.strptime(existing['end_time'], '%H:%M').time()
                        if not (slot.end_time <= existing_start or slot.start_time >= existing_end):
                            has_conflict = True
                            break
                
                if not has_conflict:
                    # Find suitable room
                    for room in rooms:
                        if room.capacity >= class_def.min_capacity:
                            suggestions.append({
                                'day': slot.day.name,
                                'start_time': slot.start_time.strftime('%H:%M'),
                                'end_time': slot.end_time.strftime('%H:%M'),
                                'instructor': instructor.name,
                                'instructor_id': instructor.id,
                                'room': room.name,
                                'room_id': room.id
                            })
                            break
        
        # Return top suggestions (limit to 5)
        return suggestions[:5]
