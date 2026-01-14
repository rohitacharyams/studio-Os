"""
Add Razorpay payment ID columns to bookings table
"""
import sqlite3
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app, db

app = create_app()
app.app_context().push()

# Get the database URL to find the actual file
db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
print(f"Database URL: {db_url}")

# For SQLite, extract the file path
if db_url.startswith('sqlite:///'):
    db_path = db_url.replace('sqlite:///', '')
    if not os.path.isabs(db_path):
        # Relative path - could be in instance/ or backend/
        if os.path.exists(f'instance/{db_path}'):
            db_path = f'instance/{db_path}'
        elif os.path.exists(db_path):
            pass  # Already correct
        else:
            print(f"ERROR: Database file not found at {db_path}")
            sys.exit(1)
    
    print(f"Connecting to database: {db_path}")
    
    # Connect directly to SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(bookings)")
        existing_cols = [row[1] for row in cursor.fetchall()]
        
        if 'razorpay_payment_id' not in existing_cols:
            cursor.execute('ALTER TABLE bookings ADD COLUMN razorpay_payment_id VARCHAR(100)')
            print("✓ Added razorpay_payment_id column")
        else:
            print("✓ razorpay_payment_id column already exists")
            
        if 'razorpay_order_id' not in existing_cols:
            cursor.execute('ALTER TABLE bookings ADD COLUMN razorpay_order_id VARCHAR(100)')
            print("✓ Added razorpay_order_id column")
        else:
            print("✓ razorpay_order_id column already exists")
        
        conn.commit()
        print("\n✅ Successfully added Razorpay columns to bookings table!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()
else:
    # For PostgreSQL or other databases, use SQLAlchemy
    from sqlalchemy import text
    conn = db.engine.connect()
    try:
        conn.execute(text('ALTER TABLE bookings ADD COLUMN razorpay_payment_id VARCHAR(100)'))
        conn.execute(text('ALTER TABLE bookings ADD COLUMN razorpay_order_id VARCHAR(100)'))
        conn.commit()
        print("✅ Successfully added Razorpay columns to bookings table!")
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        conn.close()
