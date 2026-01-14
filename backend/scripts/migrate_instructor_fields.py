"""
Data migration script to populate instructor_name, instructor_description, 
and instructor_instagram_handle from existing instructor_id.

This script:
1. For all DanceClass with instructor_id, copies User.name to instructor_name
2. Optionally copies from artist_details JSON if available
3. For all ClassSession with instructor_id, copies from parent class or User
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import DanceClass, ClassSession, User

def migrate_instructor_data():
    """Migrate instructor data from instructor_id to new fields."""
    app = create_app()
    
    with app.app_context():
        print("Starting instructor data migration...")
        
        # Migrate DanceClass records
        classes_updated = 0
        classes = DanceClass.query.filter(DanceClass.instructor_id.isnot(None)).all()
        
        for dance_class in classes:
            instructor = User.query.get(dance_class.instructor_id)
            if instructor:
                # Copy instructor name
                if not dance_class.instructor_name:
                    dance_class.instructor_name = instructor.name
                
                # Copy description from artist_details if available
                if not dance_class.instructor_description and dance_class.artist_details:
                    if isinstance(dance_class.artist_details, dict):
                        dance_class.instructor_description = dance_class.artist_details.get('bio', '')
                
                # Copy Instagram handle from artist_details if available
                if not dance_class.instructor_instagram_handle and dance_class.artist_details:
                    if isinstance(dance_class.artist_details, dict):
                        socials = dance_class.artist_details.get('socials', {})
                        if isinstance(socials, dict):
                            instagram = socials.get('instagram', '')
                            # Remove @ if present
                            if instagram.startswith('@'):
                                instagram = instagram[1:]
                            dance_class.instructor_instagram_handle = instagram
                
                classes_updated += 1
        
        # Migrate ClassSession records
        sessions_updated = 0
        sessions = ClassSession.query.all()
        
        for session in sessions:
            # First try to get from parent class
            if session.class_id:
                dance_class = DanceClass.query.get(session.class_id)
                if dance_class and dance_class.instructor_name:
                    if not session.instructor_name:
                        session.instructor_name = dance_class.instructor_name
            
            # If still no instructor_name, try to get from instructor_id
            if not session.instructor_name and session.instructor_id:
                instructor = User.query.get(session.instructor_id)
                if instructor:
                    session.instructor_name = instructor.name
            
            # Handle substitute instructor
            if session.substitute_instructor_id:
                substitute = User.query.get(session.substitute_instructor_id)
                if substitute and not session.substitute_instructor_name:
                    session.substitute_instructor_name = substitute.name
            
            if session.instructor_name or session.substitute_instructor_name:
                sessions_updated += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"✓ Successfully migrated {classes_updated} classes")
            print(f"✓ Successfully migrated {sessions_updated} sessions")
            print("Migration completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error during migration: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_instructor_data()
