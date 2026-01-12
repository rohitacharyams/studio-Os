"""
Studio OS - Demo Data Seed Script via API
==========================================
Creates synthetic data for a demo studio by calling the live API.

Usage:
    python seed_demo_via_api.py

This will create:
- A demo studio "Groove Dance Academy"
- Multiple dance classes
- Class sessions for the next 30 days
"""

import requests
import random
from datetime import datetime, timedelta, date, time
import json

# API Configuration
BASE_URL = "https://studioos-api.azurewebsites.net/api"
# BASE_URL = "http://localhost:5001/api"  # For local testing

# Demo Studio Configuration
DEMO_STUDIO = {
    'name': 'Groove Dance Academy',
    'email': 'admin@groovedance.com',
    'password': 'Demo@123',
    'phone': '+91 98765 43210',
}

# Dance Classes to Create
DANCE_CLASSES = [
    {
        'name': 'Bollywood Beats',
        'description': 'High-energy Bollywood dance class featuring popular movie songs. Learn the signature moves from the latest hits while getting a fantastic workout.',
        'dance_style': 'Bollywood',
        'level': 'All Levels',
        'duration_minutes': 60,
        'max_capacity': 20,
        'price': 500,
    },
    {
        'name': 'Hip-Hop Fundamentals',
        'description': 'Master the basics of hip-hop dance including popping, locking, and breaking. Perfect for beginners who want to learn street dance.',
        'dance_style': 'Hip-Hop',
        'level': 'Beginner',
        'duration_minutes': 60,
        'max_capacity': 15,
        'price': 600,
    },
    {
        'name': 'Contemporary Flow',
        'description': 'Explore fluid movements and emotional expression through contemporary dance. Combines modern dance techniques with creative interpretation.',
        'dance_style': 'Contemporary',
        'level': 'Intermediate',
        'duration_minutes': 75,
        'max_capacity': 12,
        'price': 700,
    },
    {
        'name': 'Salsa Social',
        'description': 'Learn the passionate rhythms of salsa! This class covers both lead and follow techniques for social dancing.',
        'dance_style': 'Salsa',
        'level': 'Beginner',
        'duration_minutes': 60,
        'max_capacity': 24,
        'price': 550,
    },
    {
        'name': 'Classical Bharatanatyam',
        'description': 'Traditional South Indian classical dance form. Learn the graceful movements, expressions, and storytelling techniques.',
        'dance_style': 'Bharatanatyam',
        'level': 'All Levels',
        'duration_minutes': 90,
        'max_capacity': 10,
        'price': 800,
    },
    {
        'name': 'Zumba Fitness',
        'description': 'Dance your way to fitness! Fun, high-energy workout combining Latin rhythms with easy-to-follow moves.',
        'dance_style': 'Zumba',
        'level': 'All Levels',
        'duration_minutes': 45,
        'max_capacity': 30,
        'price': 400,
    },
    {
        'name': 'K-Pop Dance',
        'description': 'Learn choreography from your favorite K-Pop groups! Perfect for fans who want to dance like their idols.',
        'dance_style': 'K-Pop',
        'level': 'Intermediate',
        'duration_minutes': 60,
        'max_capacity': 18,
        'price': 600,
    },
    {
        'name': 'Ballet Basics',
        'description': 'Classical ballet fundamentals for adult beginners. Build grace, strength, and proper technique.',
        'dance_style': 'Ballet',
        'level': 'Beginner',
        'duration_minutes': 60,
        'max_capacity': 12,
        'price': 650,
    },
]

# Sample Contacts
FIRST_NAMES = ['Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Ananya', 'Diya', 'Myra', 'Aadhya', 'Pari',
               'Rohan', 'Kabir', 'Shaurya', 'Atharv', 'Sara', 'Kiara', 'Avni', 'Mira', 'Prisha', 'Anvi']
LAST_NAMES = ['Sharma', 'Verma', 'Patel', 'Singh', 'Kumar', 'Gupta', 'Reddy', 'Iyer', 'Nair', 'Das']


def register_studio():
    """Register the demo studio."""
    print("Registering demo studio...")
    
    # First try to login
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        'email': DEMO_STUDIO['email'],
        'password': DEMO_STUDIO['password']
    })
    
    if login_resp.status_code == 200:
        data = login_resp.json()
        print(f"Studio already exists, logged in as: {data.get('user', {}).get('email')}")
        return data.get('access_token')
    
    # Register new studio
    register_resp = requests.post(f"{BASE_URL}/auth/register", json={
        'email': DEMO_STUDIO['email'],
        'password': DEMO_STUDIO['password'],
        'name': 'Demo Admin',
        'studio_name': DEMO_STUDIO['name'],
        'phone': DEMO_STUDIO['phone'],
        'user_type': 'studio_owner'
    })
    
    if register_resp.status_code in [200, 201]:
        data = register_resp.json()
        print(f"Registered new studio: {DEMO_STUDIO['name']}")
        return data.get('access_token')
    else:
        print(f"Registration failed: {register_resp.status_code} - {register_resp.text}")
        return None


def complete_onboarding(token):
    """Complete studio onboarding."""
    print("Completing onboarding...")
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    resp = requests.post(f"{BASE_URL}/studio/onboarding", headers=headers, json={
        'studio_name': DEMO_STUDIO['name'],
        'phone': DEMO_STUDIO['phone'],
        'address': '123 MG Road, Indiranagar',
        'city': 'Bangalore',
        'business_hours_open': '09:00',
        'business_hours_close': '21:00',
    })
    
    if resp.status_code == 200:
        print("Onboarding completed!")
    else:
        print(f"Onboarding response: {resp.status_code}")


def create_classes(token):
    """Create dance classes."""
    print("Creating dance classes...")
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    created_classes = []
    
    for class_data in DANCE_CLASSES:
        resp = requests.post(f"{BASE_URL}/scheduling/classes", headers=headers, json=class_data)
        if resp.status_code in [200, 201]:
            created_class = resp.json()
            created_classes.append(created_class)
            print(f"  ✓ Created: {class_data['name']}")
        elif resp.status_code == 409:
            print(f"  - Already exists: {class_data['name']}")
            # Get existing classes
            list_resp = requests.get(f"{BASE_URL}/scheduling/classes", headers=headers)
            if list_resp.status_code == 200:
                existing = [c for c in list_resp.json() if c['name'] == class_data['name']]
                if existing:
                    created_classes.append(existing[0])
        else:
            print(f"  ✗ Failed: {class_data['name']} - {resp.status_code}")
    
    return created_classes


def create_sessions(token, classes):
    """Create class sessions for the next 30 days."""
    print("Creating class sessions...")
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    today = date.today()
    sessions_created = 0
    
    # Schedule: each class runs at specific times
    class_times = {
        'Bollywood Beats': [('19:00', '20:00')],
        'Hip-Hop Fundamentals': [('18:00', '19:00')],
        'Contemporary Flow': [('17:00', '18:15')],
        'Salsa Social': [('20:00', '21:00')],
        'Classical Bharatanatyam': [('16:00', '17:30')],
        'Zumba Fitness': [('07:00', '07:45'), ('10:00', '10:45')],
        'K-Pop Dance': [('19:00', '20:00')],
        'Ballet Basics': [('17:00', '18:00')],
    }
    
    for dance_class in classes:
        class_name = dance_class.get('name')
        class_id = dance_class.get('id')
        
        times = class_times.get(class_name, [('18:00', '19:00')])
        
        # Create sessions for next 14 days (to keep it manageable)
        for day_offset in range(14):
            session_date = today + timedelta(days=day_offset)
            
            # Skip some days randomly to make it realistic
            if random.random() < 0.3:
                continue
            
            for start_str, end_str in times:
                start_dt = datetime.combine(session_date, datetime.strptime(start_str, '%H:%M').time())
                end_dt = datetime.combine(session_date, datetime.strptime(end_str, '%H:%M').time())
                
                session_data = {
                    'class_id': class_id,
                    'date': session_date.isoformat(),
                    'start_time': start_dt.isoformat(),
                    'end_time': end_dt.isoformat(),
                    'max_capacity': dance_class.get('max_capacity', 15),
                }
                
                resp = requests.post(f"{BASE_URL}/scheduling/sessions", headers=headers, json=session_data)
                if resp.status_code in [200, 201]:
                    sessions_created += 1
    
    print(f"  Created {sessions_created} sessions")
    return sessions_created


def create_contacts(token, count=30):
    """Create sample contacts."""
    print(f"Creating {count} contacts...")
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    created = 0
    
    lead_sources = ['website', 'instagram', 'referral', 'walk-in', 'google']
    
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        contact_data = {
            'name': f"{first_name} {last_name}",
            'email': f"{first_name.lower()}{random.randint(1,99)}@gmail.com",
            'phone': f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}",
            'lead_source': random.choice(lead_sources),
            'lead_status': random.choice(['NEW', 'CONTACTED', 'CONVERTED']),
        }
        
        resp = requests.post(f"{BASE_URL}/contacts", headers=headers, json=contact_data)
        if resp.status_code in [200, 201]:
            created += 1
    
    print(f"  Created {created} contacts")
    return created


def main():
    print("\n" + "=" * 60)
    print("🎭 STUDIO OS - DEMO DATA SEEDER (API)")
    print("=" * 60 + "\n")
    
    # Step 1: Register/Login
    token = register_studio()
    if not token:
        print("Failed to get access token!")
        return
    
    # Step 2: Complete onboarding
    complete_onboarding(token)
    
    # Step 3: Create classes
    classes = create_classes(token)
    print(f"\nTotal classes: {len(classes)}")
    
    # Step 4: Create sessions
    if classes:
        sessions = create_sessions(token, classes)
    
    # Step 5: Create contacts
    create_contacts(token, count=30)
    
    print("\n" + "=" * 60)
    print("✅ DEMO DATA CREATED!")
    print("=" * 60)
    print(f"""
📍 Demo Studio: {DEMO_STUDIO['name']}
📧 Login Email: {DEMO_STUDIO['email']}
🔑 Password: {DEMO_STUDIO['password']}

🌐 Access URLs:
   - Frontend: https://studio-os.netlify.app
   - Login: https://studio-os.netlify.app/login
   - Public Booking: https://studio-os.netlify.app/book/groove-dance-academy
""")


if __name__ == '__main__':
    main()
