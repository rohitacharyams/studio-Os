"""
Add media fields to studios table in SQLite database
Similar to how theme_settings was added
"""
import sqlite3
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Get database path
db_path = Path(__file__).resolve().parent.parent / 'instance' / 'studio_os.db'

# If instance directory doesn't exist, try root
if not db_path.exists():
    db_path = Path(__file__).resolve().parent.parent.parent / 'instance' / 'studio_os.db'

# If still not found, try current directory
if not db_path.exists():
    db_path = Path('instance/studio_os.db')

print(f"Connecting to database: {db_path}")

if not db_path.exists():
    print(f"ERROR: Database file not found at {db_path}")
    print("Please make sure the database exists and the path is correct.")
    sys.exit(1)

# Connect to SQLite database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(studios)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"Existing columns: {columns}")
    
    # Add columns if they don't exist
    columns_to_add = [
        ('photos', 'TEXT', '[]'),
        ('videos', 'TEXT', '[]'),
        ('testimonials', 'TEXT', '[]'),
        ('amenities', 'TEXT', '[]'),
        ('social_links', 'TEXT', '{}'),
        ('about', 'TEXT', 'NULL'),
    ]
    
    for col_name, col_type, default_value in columns_to_add:
        if col_name not in columns:
            if default_value == 'NULL':
                sql = f"ALTER TABLE studios ADD COLUMN {col_name} {col_type}"
            else:
                sql = f"ALTER TABLE studios ADD COLUMN {col_name} {col_type} DEFAULT '{default_value}'"
            
            print(f"Adding column: {col_name}")
            cursor.execute(sql)
            print(f"✓ Added column: {col_name}")
        else:
            print(f"⊘ Column {col_name} already exists, skipping")
    
    # Commit changes
    conn.commit()
    print("\n✓ Successfully added all media fields to studios table!")
    
    # Verify
    cursor.execute("PRAGMA table_info(studios)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"\nUpdated columns: {columns}")
    
except sqlite3.Error as e:
    print(f"ERROR: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    conn.close()
