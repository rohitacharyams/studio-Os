"""
Studio OS - Demo Data Seed Script
=================================
Creates synthetic data for a demo studio to showcase the platform.

Usage:
    cd backend
    python seed_demo_data.py

This will create:
- A demo studio "Groove Dance Academy"
- Multiple dance classes
- Class sessions for the next 30 days
- Sample contacts/customers
- Sample bookings
- Sample conversations and messages
- Analytics data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta, time, date
import uuid
import random
from app import create_app, db
from app.models import (
    Studio, User, Contact, DanceClass, ClassSchedule, ClassSession,
    Booking, Conversation, Message, AnalyticsDaily, StudioKnowledge,
    MessageTemplate, LeadStatus, Channel, MessageDirection
)

# Demo Studio Configuration
DEMO_STUDIO = {
    'name': 'Groove Dance Academy',
    'email': 'admin@groovedance.com',
    'password': 'Demo@123',
    'phone': '+91 98765 43210',
    'address': '123 MG Road, Indiranagar',
    'city': 'Bangalore',
    'website': 'https://groovedance.com',
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
        'instructor_name': 'Priya Sharma',
    },
    {
        'name': 'Hip-Hop Fundamentals',
        'description': 'Master the basics of hip-hop dance including popping, locking, and breaking. Perfect for beginners who want to learn street dance.',
        'dance_style': 'Hip-Hop',
        'level': 'Beginner',
        'duration_minutes': 60,
        'max_capacity': 15,
        'price': 600,
        'instructor_name': 'Rahul Verma',
    },
    {
        'name': 'Contemporary Flow',
        'description': 'Explore fluid movements and emotional expression through contemporary dance. Combines modern dance techniques with creative interpretation.',
        'dance_style': 'Contemporary',
        'level': 'Intermediate',
        'duration_minutes': 75,
        'max_capacity': 12,
        'price': 700,
        'instructor_name': 'Ananya Iyer',
    },
    {
        'name': 'Salsa Social',
        'description': 'Learn the passionate rhythms of salsa! This class covers both lead and follow techniques for social dancing.',
        'dance_style': 'Salsa',
        'level': 'Beginner',
        'duration_minutes': 60,
        'max_capacity': 24,  # Pairs
        'price': 550,
        'instructor_name': 'Carlos Rodriguez',
    },
    {
        'name': 'Classical Bharatanatyam',
        'description': 'Traditional South Indian classical dance form. Learn the graceful movements, expressions, and storytelling techniques.',
        'dance_style': 'Bharatanatyam',
        'level': 'All Levels',
        'duration_minutes': 90,
        'max_capacity': 10,
        'price': 800,
        'instructor_name': 'Dr. Lakshmi Narayanan',
    },
    {
        'name': 'Zumba Fitness',
        'description': 'Dance your way to fitness! Fun, high-energy workout combining Latin rhythms with easy-to-follow moves.',
        'dance_style': 'Zumba',
        'level': 'All Levels',
        'duration_minutes': 45,
        'max_capacity': 30,
        'price': 400,
        'instructor_name': 'Sneha Patel',
    },
    {
        'name': 'K-Pop Dance',
        'description': 'Learn choreography from your favorite K-Pop groups! Perfect for fans who want to dance like their idols.',
        'dance_style': 'K-Pop',
        'level': 'Intermediate',
        'duration_minutes': 60,
        'max_capacity': 18,
        'price': 600,
        'instructor_name': 'Kim Soo-jin',
    },
    {
        'name': 'Ballet Basics',
        'description': 'Classical ballet fundamentals for adult beginners. Build grace, strength, and proper technique.',
        'dance_style': 'Ballet',
        'level': 'Beginner',
        'duration_minutes': 60,
        'max_capacity': 12,
        'price': 650,
        'instructor_name': 'Elena Petrova',
    },
]

# Sample Contact Names
FIRST_NAMES = [
    'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Reyansh', 'Ayaan',
    'Ananya', 'Diya', 'Myra', 'Aadhya', 'Pari', 'Anika', 'Navya', 'Ishani',
    'Rohan', 'Kabir', 'Shaurya', 'Atharv', 'Advait', 'Dhruv', 'Krish', 'Ritvik',
    'Sara', 'Kiara', 'Avni', 'Mira', 'Prisha', 'Anvi', 'Ahana', 'Shanaya',
    'Neha', 'Pooja', 'Riya', 'Sneha', 'Kavya', 'Tanvi', 'Simran', 'Nisha',
    'Vikram', 'Nikhil', 'Amit', 'Raj', 'Karan', 'Sanjay', 'Manish', 'Rahul'
]

LAST_NAMES = [
    'Sharma', 'Verma', 'Patel', 'Singh', 'Kumar', 'Gupta', 'Reddy', 'Iyer',
    'Nair', 'Menon', 'Das', 'Chatterjee', 'Banerjee', 'Mukherjee', 'Roy',
    'Joshi', 'Desai', 'Shah', 'Mehta', 'Kapoor', 'Malhotra', 'Sinha', 'Bose'
]

# Sample conversation messages
INQUIRY_MESSAGES = [
    "Hi! I'm interested in joining dance classes. What options do you have for beginners?",
    "Hello, I saw your Instagram and would love to know more about your Bollywood class!",
    "What are your class timings on weekends?",
    "Do you offer trial classes? I want to try before committing.",
    "Hi! My daughter is 8 years old. Do you have kids' classes?",
    "I'm looking for a couples' dance class. Do you teach salsa?",
    "What's the monthly fee for unlimited classes?",
    "Do you have any ongoing promotions or discounts?",
    "Can I book a private lesson for my wedding choreography?",
    "Is there parking available at your studio?",
]

RESPONSE_MESSAGES = [
    "Hi! Thank you for your interest! We have several beginner-friendly classes. I'd recommend our Bollywood Beats or Salsa Social class. Would you like me to share the schedule?",
    "Hello! Welcome! Our Bollywood class runs every Monday and Wednesday at 7 PM. It's perfect for all fitness levels. Would you like to book a trial?",
    "We have weekend batches on Saturday and Sunday! Saturday has Zumba at 10 AM and Hip-Hop at 4 PM. Sunday has Contemporary at 11 AM. Which interests you?",
    "Absolutely! We offer a trial class at just ₹299. You can try any class of your choice. Should I book one for you?",
    "Yes! We have kids' batches for ages 5-12. They run on Saturday mornings. I'll send you the details!",
    "Yes, we have Salsa Social class on Fridays at 8 PM! It's great for couples. Would you like to register?",
]

def generate_phone():
    """Generate a random Indian phone number."""
    return f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}"

def generate_email(first_name, last_name):
    """Generate a realistic email address."""
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
    patterns = [
        f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}",
        f"{first_name.lower()}{random.randint(1, 99)}@{random.choice(domains)}",
        f"{first_name.lower()}_{last_name.lower()}@{random.choice(domains)}",
    ]
    return random.choice(patterns)

def create_demo_studio():
    """Create the demo studio and admin user."""
    print("Creating demo studio...")
    
    # Check if studio already exists
    existing = Studio.query.filter_by(email=DEMO_STUDIO['email']).first()
    if existing:
        print(f"Studio already exists with ID: {existing.id}")
        return existing
    
    studio_id = str(uuid.uuid4())
    studio = Studio(
        id=studio_id,
        name=DEMO_STUDIO['name'],
        slug='groove-dance-academy',
        email=DEMO_STUDIO['email'],
        phone=DEMO_STUDIO['phone'],
        address=DEMO_STUDIO['address'],
        city=DEMO_STUDIO['city'],
        website=DEMO_STUDIO['website'],
        timezone='Asia/Kolkata',
        currency='INR',
        business_hours_open='09:00',
        business_hours_close='21:00',
        onboarding_completed=True,
        onboarding_step=5,
    )
    db.session.add(studio)
    
    # Create admin user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        studio_id=studio_id,
        email=DEMO_STUDIO['email'],
        name='Demo Admin',
        phone=DEMO_STUDIO['phone'],
        role='owner',
        user_type='studio_owner',
        is_active=True,
    )
    user.set_password(DEMO_STUDIO['password'])
    db.session.add(user)
    
    db.session.commit()
    print(f"Created studio: {studio.name} (ID: {studio.id})")
    return studio

def create_instructors(studio):
    """Create instructor users for the studio."""
    print("Creating instructors...")
    instructors = {}
    
    instructor_names = set(c['instructor_name'] for c in DANCE_CLASSES)
    for name in instructor_names:
        user_id = str(uuid.uuid4())
        first_name, last_name = name.rsplit(' ', 1) if ' ' in name else (name, '')
        email = f"{first_name.lower().replace(' ', '')}@groovedance.com"
        
        user = User(
            id=user_id,
            studio_id=studio.id,
            email=email,
            name=name,
            phone=generate_phone(),
            role='instructor',
            user_type='studio_owner',
            is_active=True,
        )
        user.set_password('Instructor@123')
        db.session.add(user)
        instructors[name] = user_id
    
    db.session.commit()
    print(f"Created {len(instructors)} instructors")
    return instructors

def create_dance_classes(studio, instructors):
    """Create dance classes for the studio."""
    print("Creating dance classes...")
    classes = []
    
    for class_data in DANCE_CLASSES:
        class_id = str(uuid.uuid4())
        dance_class = DanceClass(
            id=class_id,
            studio_id=studio.id,
            name=class_data['name'],
            description=class_data['description'],
            dance_style=class_data['dance_style'],
            level=class_data['level'],
            duration_minutes=class_data['duration_minutes'],
            max_capacity=class_data['max_capacity'],
            price=class_data['price'],
            instructor_id=instructors.get(class_data['instructor_name']),
            is_active=True,
            tags=[class_data['dance_style'], class_data['level']],
            artist_details={
                'name': class_data['instructor_name'],
                'bio': f"Professional {class_data['dance_style']} instructor with 5+ years of experience.",
                'specialties': [class_data['dance_style']],
            }
        )
        db.session.add(dance_class)
        classes.append(dance_class)
    
    db.session.commit()
    print(f"Created {len(classes)} dance classes")
    return classes

def create_class_sessions(studio, classes):
    """Create class sessions for the next 30 days."""
    print("Creating class sessions...")
    sessions = []
    today = date.today()
    
    # Define schedule: each class runs 2-3 times per week
    class_schedules = {
        'Bollywood Beats': [(0, '19:00'), (2, '19:00'), (5, '11:00')],  # Mon, Wed, Sat
        'Hip-Hop Fundamentals': [(1, '18:00'), (4, '18:00'), (5, '16:00')],  # Tue, Fri, Sat
        'Contemporary Flow': [(0, '17:00'), (3, '17:00'), (6, '11:00')],  # Mon, Thu, Sun
        'Salsa Social': [(4, '20:00'), (5, '20:00')],  # Fri, Sat
        'Classical Bharatanatyam': [(2, '16:00'), (5, '09:00'), (6, '09:00')],  # Wed, Sat, Sun
        'Zumba Fitness': [(0, '07:00'), (2, '07:00'), (4, '07:00'), (5, '10:00')],  # Mon, Wed, Fri, Sat
        'K-Pop Dance': [(1, '19:00'), (3, '19:00'), (5, '15:00')],  # Tue, Thu, Sat
        'Ballet Basics': [(1, '17:00'), (3, '10:00'), (6, '10:00')],  # Tue, Thu, Sun
    }
    
    for dance_class in classes:
        schedule = class_schedules.get(dance_class.name, [(0, '18:00'), (3, '18:00')])
        
        for day_offset in range(30):
            session_date = today + timedelta(days=day_offset)
            day_of_week = session_date.weekday()
            
            for sched_day, sched_time in schedule:
                if day_of_week == sched_day:
                    hour, minute = map(int, sched_time.split(':'))
                    start_dt = datetime.combine(session_date, time(hour, minute))
                    end_dt = start_dt + timedelta(minutes=dance_class.duration_minutes)
                    
                    # Random enrollment (more for past/today, less for future)
                    if session_date < today:
                        booked = random.randint(int(dance_class.max_capacity * 0.6), dance_class.max_capacity)
                        status = 'COMPLETED'
                    elif session_date == today:
                        booked = random.randint(int(dance_class.max_capacity * 0.4), int(dance_class.max_capacity * 0.8))
                        status = 'SCHEDULED'
                    else:
                        booked = random.randint(0, int(dance_class.max_capacity * 0.5))
                        status = 'SCHEDULED'
                    
                    session = ClassSession(
                        id=str(uuid.uuid4()),
                        studio_id=studio.id,
                        class_id=dance_class.id,
                        date=session_date,
                        start_time=start_dt,
                        end_time=end_dt,
                        max_capacity=dance_class.max_capacity,
                        booked_count=booked,
                        instructor_id=dance_class.instructor_id,
                        status=status,
                    )
                    db.session.add(session)
                    sessions.append(session)
    
    db.session.commit()
    print(f"Created {len(sessions)} class sessions")
    return sessions

def create_contacts(studio, count=80):
    """Create sample contacts/customers."""
    print(f"Creating {count} contacts...")
    contacts = []
    
    lead_statuses = [
        (LeadStatus.CONVERTED.value, 40),  # 40% converted
        (LeadStatus.NEW.value, 20),
        (LeadStatus.CONTACTED.value, 15),
        (LeadStatus.TRIAL_SCHEDULED.value, 15),
        (LeadStatus.LOST.value, 10),
    ]
    
    lead_sources = ['website', 'instagram', 'referral', 'walk-in', 'google', 'facebook']
    
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Weighted random status selection
        status_pool = []
        for status, weight in lead_statuses:
            status_pool.extend([status] * weight)
        
        contact = Contact(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            name=f"{first_name} {last_name}",
            email=generate_email(first_name, last_name),
            phone=generate_phone(),
            lead_status=random.choice(status_pool),
            lead_source=random.choice(lead_sources),
            tags=random.sample(['regular', 'vip', 'student', 'corporate', 'trial'], k=random.randint(0, 2)),
            created_at=datetime.now() - timedelta(days=random.randint(1, 180)),
        )
        db.session.add(contact)
        contacts.append(contact)
    
    db.session.commit()
    print(f"Created {len(contacts)} contacts")
    return contacts

def create_bookings(studio, sessions, contacts):
    """Create sample bookings."""
    print("Creating bookings...")
    bookings = []
    booking_counter = 1
    
    # Only converted contacts can have bookings
    converted_contacts = [c for c in contacts if c.lead_status == LeadStatus.CONVERTED.value]
    
    for session in sessions:
        # Create bookings up to the booked_count
        num_bookings = min(session.booked_count, len(converted_contacts))
        selected_contacts = random.sample(converted_contacts, num_bookings)
        
        for contact in selected_contacts:
            booking_status = 'ATTENDED' if session.status == 'COMPLETED' else 'CONFIRMED'
            
            booking = Booking(
                id=str(uuid.uuid4()),
                booking_number=f"BK-2026-{booking_counter:05d}",
                studio_id=studio.id,
                contact_id=contact.id,
                session_id=session.id,
                status=booking_status,
                payment_method=random.choice(['drop_in', 'class_pack']),
                booked_at=session.start_time - timedelta(days=random.randint(1, 7)),
                confirmed_at=session.start_time - timedelta(days=random.randint(0, 3)),
            )
            if booking_status == 'ATTENDED':
                booking.checked_in_at = session.start_time + timedelta(minutes=random.randint(-10, 5))
            
            db.session.add(booking)
            bookings.append(booking)
            booking_counter += 1
    
    db.session.commit()
    print(f"Created {len(bookings)} bookings")
    return bookings

def create_conversations(studio, contacts):
    """Create sample conversations with messages."""
    print("Creating conversations...")
    conversations = []
    
    # Select ~30% of contacts to have conversations
    chatty_contacts = random.sample(contacts, int(len(contacts) * 0.3))
    
    for contact in chatty_contacts:
        channel = random.choice([Channel.WHATSAPP.value, Channel.EMAIL.value])
        
        conv = Conversation(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            contact_id=contact.id,
            channel=channel,
            subject=f"Inquiry from {contact.name}" if channel == Channel.EMAIL.value else None,
            is_unread=random.choice([True, False, False]),  # 33% unread
            last_message_at=datetime.now() - timedelta(hours=random.randint(1, 72)),
            created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
        )
        db.session.add(conv)
        db.session.flush()  # Get the ID
        
        # Add 2-6 messages per conversation
        num_messages = random.randint(2, 6)
        for i in range(num_messages):
            is_inbound = i % 2 == 0  # Alternate between customer and studio
            
            if is_inbound:
                content = random.choice(INQUIRY_MESSAGES)
            else:
                content = random.choice(RESPONSE_MESSAGES)
            
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conv.id,
                direction=MessageDirection.INBOUND.value if is_inbound else MessageDirection.OUTBOUND.value,
                content=content,
                is_read=not conv.is_unread or i < num_messages - 1,
                created_at=conv.created_at + timedelta(hours=i * random.randint(1, 12)),
            )
            db.session.add(message)
        
        conversations.append(conv)
    
    db.session.commit()
    print(f"Created {len(conversations)} conversations")
    return conversations

def create_analytics(studio):
    """Create sample analytics data for the past 30 days."""
    print("Creating analytics data...")
    analytics = []
    today = date.today()
    
    for day_offset in range(30, 0, -1):
        analytics_date = today - timedelta(days=day_offset)
        
        # Weekends have more activity
        is_weekend = analytics_date.weekday() >= 5
        multiplier = 1.5 if is_weekend else 1.0
        
        analytic = AnalyticsDaily(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            date=analytics_date,
            messages_received=int(random.randint(5, 20) * multiplier),
            messages_sent=int(random.randint(8, 25) * multiplier),
            new_leads=int(random.randint(2, 8) * multiplier),
            leads_converted=int(random.randint(0, 3) * multiplier),
            channel_breakdown={
                'WHATSAPP': random.randint(40, 60),
                'EMAIL': random.randint(20, 40),
                'INSTAGRAM': random.randint(10, 20),
            },
            avg_response_time_minutes=random.uniform(5, 30),
        )
        db.session.add(analytic)
        analytics.append(analytic)
    
    db.session.commit()
    print(f"Created {len(analytics)} daily analytics records")
    return analytics

def create_knowledge_base(studio):
    """Create knowledge base entries for AI."""
    print("Creating knowledge base...")
    
    knowledge_entries = [
        {
            'category': 'pricing',
            'title': 'Class Pricing',
            'content': '''Our class pricing:
- Drop-in (single class): ₹400-800 depending on class
- 5-class pack: 10% discount
- 10-class pack: 15% discount
- Monthly unlimited: ₹4,999
- Trial class: ₹299 (first-time visitors only)
All prices include GST.''',
        },
        {
            'category': 'schedule',
            'title': 'Class Schedule Overview',
            'content': '''We offer classes 7 days a week:
- Morning batches: 7 AM - 9 AM
- Afternoon batches: 4 PM - 6 PM
- Evening batches: 6 PM - 9 PM
- Weekend special batches: 9 AM - 12 PM
Check our website for the full schedule.''',
        },
        {
            'category': 'policies',
            'title': 'Cancellation Policy',
            'content': '''Cancellation Policy:
- Free cancellation up to 12 hours before class
- 50% credit for cancellations 6-12 hours before
- No refund for cancellations less than 6 hours before
- Class packs valid for 60 days from purchase
- Monthly passes are non-refundable''',
        },
        {
            'category': 'faq',
            'title': 'What to Bring',
            'content': '''What to bring to class:
- Comfortable clothing that allows movement
- Dance shoes or clean sneakers (no outdoor shoes)
- Water bottle
- Small towel
- Positive attitude!
We have changing rooms and lockers available.''',
        },
        {
            'category': 'faq',
            'title': 'First Time Visitors',
            'content': '''First time at Groove Dance Academy?
- Arrive 15 minutes early to register
- Trial class is just ₹299
- No experience needed for beginner classes
- We provide a welcoming, judgment-free environment
- You can observe a class before joining if you prefer''',
        },
    ]
    
    for entry in knowledge_entries:
        knowledge = StudioKnowledge(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            category=entry['category'],
            title=entry['title'],
            content=entry['content'],
            is_active=True,
        )
        db.session.add(knowledge)
    
    db.session.commit()
    print(f"Created {len(knowledge_entries)} knowledge base entries")

def create_message_templates(studio):
    """Create message templates."""
    print("Creating message templates...")
    
    templates = [
        {
            'name': 'Welcome Message',
            'category': 'welcome',
            'content': '''Hi {{name}}! 👋

Welcome to Groove Dance Academy! We're thrilled to have you join our dance family.

Your trial class is confirmed for {{class_name}} on {{date}} at {{time}}.

Please arrive 15 minutes early. Looking forward to dancing with you!

Groove Dance Academy 💃🕺''',
            'channels': ['WHATSAPP', 'EMAIL'],
        },
        {
            'name': 'Class Reminder',
            'category': 'reminder',
            'content': '''Hi {{name}}!

This is a reminder for your {{class_name}} class tomorrow at {{time}}.

See you on the dance floor! 🎵

Groove Dance Academy''',
            'channels': ['WHATSAPP'],
        },
        {
            'name': 'Follow Up - No Show',
            'category': 'follow-up',
            'content': '''Hi {{name}},

We missed you at {{class_name}} yesterday! We hope everything is okay.

Would you like to reschedule? We have spots available this week.

Let us know how we can help!

Groove Dance Academy''',
            'channels': ['WHATSAPP', 'EMAIL'],
        },
    ]
    
    for template in templates:
        msg_template = MessageTemplate(
            id=str(uuid.uuid4()),
            studio_id=studio.id,
            name=template['name'],
            category=template['category'],
            content=template['content'],
            channels=template['channels'],
            variables=['name', 'class_name', 'date', 'time'],
            is_active=True,
        )
        db.session.add(msg_template)
    
    db.session.commit()
    print(f"Created {len(templates)} message templates")

def main():
    """Main function to seed demo data."""
    print("\n" + "=" * 60)
    print("🎭 STUDIO OS - DEMO DATA SEEDER")
    print("=" * 60 + "\n")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Create demo studio
            studio = create_demo_studio()
            
            # Create instructors
            instructors = create_instructors(studio)
            
            # Create dance classes
            classes = create_dance_classes(studio, instructors)
            
            # Create class sessions
            sessions = create_class_sessions(studio, classes)
            
            # Create contacts
            contacts = create_contacts(studio, count=80)
            
            # Create bookings
            bookings = create_bookings(studio, sessions, contacts)
            
            # Create conversations
            conversations = create_conversations(studio, contacts)
            
            # Create analytics
            analytics = create_analytics(studio)
            
            # Create knowledge base
            create_knowledge_base(studio)
            
            # Create message templates
            create_message_templates(studio)
            
            print("\n" + "=" * 60)
            print("✅ DEMO DATA CREATED SUCCESSFULLY!")
            print("=" * 60)
            print(f"""
📍 Demo Studio: {DEMO_STUDIO['name']}
📧 Login Email: {DEMO_STUDIO['email']}
🔑 Password: {DEMO_STUDIO['password']}

🌐 Access URLs:
   - Frontend: https://studio-os.netlify.app
   - Public Booking: https://studio-os.netlify.app/book/groove-dance-academy

📊 Data Created:
   - Dance Classes: {len(classes)}
   - Class Sessions: {len(sessions)}
   - Contacts: {len(contacts)}
   - Bookings: {len(bookings)}
   - Conversations: {len(conversations)}
   - Analytics Days: {len(analytics)}
""")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    main()
