#!/usr/bin/env python3
"""
Run database migrations
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask_migrate import upgrade
from app import create_app

if __name__ == '__main__':
    app = create_app('production')
    with app.app_context():
        print("Running database migrations...")
        upgrade()
        print("Migrations completed successfully!")
