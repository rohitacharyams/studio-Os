"""
Seed script to populate the database with dummy data for testing
Run: python scripts/seed_data.py
"""

import sys
import os
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, time
import random
from app import create_app, db
from app.models import (
    User, Studio, Contact, DanceClass, ClassSchedule, ClassSession, 
    Booking, Payment, Conversation, Message
)

app = create_app()


def generate_id():
    return str(uuid.uuid4())


def generate_booking_number():
    return f"BK-{datetime.now().year}-{random.randint(1000, 9999)}"


def generate_payment_number():
    return f"PAY-{datetime.now().year}-{random.randint(1000, 9999)}"


def seed_data():
    """Seed the database with sample data"""
    
    with app.app_context():
        print("🌱 Starting to seed database...")
        
        # Check if data already exists
        if Studio.query.first():
            print("⚠️  Data already exists. Clearing existing data...")
            # Clear existing data in reverse dependency order
            Message.query.delete()
            Conversation.query.delete()
            Payment.query.delete()
            Booking.query.delete()
            ClassSession.query.delete()
            ClassSchedule.query.delete()
            DanceClass.query.delete()
            Contact.query.delete()
            User.query.delete()
            Studio.query.delete()
            db.session.commit()
        
        # Create Studio
        print("📍 Creating studio...")
        studio = Studio(
            id=generate_id(),
            name="Rhythm Dance Academy",
            email="hello@rhythmdance.com",
            phone="+919876543210",
            address="123 Dance Street, Bandra West, Mumbai, Maharashtra, India",
            timezone="Asia/Kolkata"
        )
        db.session.add(studio)
        db.session.flush()
        
        # Create Users (Studio Staff)
        print("👥 Creating users...")
        users = []
        user_data = [
            {"name": "Priya Sharma", "email": "priya@rhythmdance.com", "role": "owner"},
            {"name": "Rahul Menon", "email": "rahul@rhythmdance.com", "role": "instructor"},
            {"name": "Maya Patel", "email": "maya@rhythmdance.com", "role": "instructor"},
            {"name": "Arjun Singh", "email": "arjun@rhythmdance.com", "role": "staff"}
        ]
        
        for ud in user_data:
            user = User(
                id=generate_id(),
                studio_id=studio.id,
                email=ud["email"],
                name=ud["name"],
                role=ud["role"],
                is_active=True
            )
            user.set_password("password123")
            users.append(user)
            db.session.add(user)
        
        db.session.flush()
        
        # Create Dance Classes
        print("💃 Creating dance classes...")
        classes_data = [
            {
                "name": "Beginner Salsa",
                "description": "Learn the basics of Salsa dancing. Perfect for absolute beginners!",
                "dance_style": "Salsa",
                "level": "Beginner",
                "duration": 60,
                "max_capacity": 15,
                "price": 500,
                "instructor_idx": 1  # Rahul
            },
            {
                "name": "Intermediate Bachata",
                "description": "Take your Bachata skills to the next level with advanced patterns and styling.",
                "dance_style": "Bachata",
                "level": "Intermediate",
                "duration": 60,
                "max_capacity": 12,
                "price": 600,
                "instructor_idx": 2  # Maya
            },
            {
                "name": "Hip-Hop Basics",
                "description": "Learn foundational Hip-Hop moves and grooves.",
                "dance_style": "Hip-Hop",
                "level": "Beginner",
                "duration": 60,
                "max_capacity": 20,
                "price": 500,
                "instructor_idx": 1  # Rahul
            },
            {
                "name": "Contemporary Flow",
                "description": "Express yourself through fluid contemporary dance movements.",
                "dance_style": "Contemporary",
                "level": "All Levels",
                "duration": 75,
                "max_capacity": 15,
                "price": 700,
                "instructor_idx": 2  # Maya
            },
            {
                "name": "Advanced Salsa",
                "description": "Complex patterns, shines, and partner work for experienced dancers.",
                "dance_style": "Salsa",
                "level": "Advanced",
                "duration": 90,
                "max_capacity": 10,
                "price": 800,
                "instructor_idx": 1  # Rahul
            },
            {
                "name": "Bollywood Dance",
                "description": "Learn popular Bollywood choreography and express your inner star!",
                "dance_style": "Bollywood",
                "level": "All Levels",
                "duration": 60,
                "max_capacity": 20,
                "price": 500,
                "instructor_idx": 2  # Maya
            }
        ]
        
        dance_classes = []
        for cd in classes_data:
            dance_class = DanceClass(
                id=generate_id(),
                studio_id=studio.id,
                name=cd["name"],
                description=cd["description"],
                dance_style=cd["dance_style"],
                level=cd["level"],
                duration_minutes=cd["duration"],
                max_capacity=cd["max_capacity"],
                price=cd["price"],
                instructor_id=users[cd["instructor_idx"]].id,
                is_active=True
            )
            dance_classes.append(dance_class)
            db.session.add(dance_class)
        
        db.session.flush()
        
        # Create Class Sessions for the next 14 days
        print("📅 Creating class sessions...")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Weekly schedule template
        weekly_schedule = {
            0: [  # Monday
                {"class_idx": 0, "time": "10:00"},  # Beginner Salsa
                {"class_idx": 2, "time": "18:00"},  # Hip-Hop
                {"class_idx": 4, "time": "20:00"},  # Advanced Salsa
            ],
            1: [  # Tuesday
                {"class_idx": 1, "time": "11:00"},  # Intermediate Bachata
                {"class_idx": 3, "time": "19:00"},  # Contemporary
            ],
            2: [  # Wednesday
                {"class_idx": 0, "time": "10:00"},  # Beginner Salsa
                {"class_idx": 5, "time": "18:00"},  # Bollywood
                {"class_idx": 2, "time": "20:00"},  # Hip-Hop
            ],
            3: [  # Thursday
                {"class_idx": 1, "time": "11:00"},  # Intermediate Bachata
                {"class_idx": 4, "time": "19:30"},  # Advanced Salsa
            ],
            4: [  # Friday
                {"class_idx": 5, "time": "17:00"},  # Bollywood
                {"class_idx": 0, "time": "19:00"},  # Beginner Salsa
            ],
            5: [  # Saturday
                {"class_idx": 2, "time": "11:00"},  # Hip-Hop
                {"class_idx": 3, "time": "14:00"},  # Contemporary
                {"class_idx": 1, "time": "17:00"},  # Intermediate Bachata
            ],
            6: [  # Sunday
                {"class_idx": 3, "time": "10:00"},  # Contemporary
                {"class_idx": 5, "time": "12:00"},  # Bollywood
            ]
        }
        
        sessions = []
        for day_offset in range(14):
            date = today + timedelta(days=day_offset)
            day_of_week = date.weekday()
            
            for session_info in weekly_schedule.get(day_of_week, []):
                dance_class = dance_classes[session_info["class_idx"]]
                hour, minute = map(int, session_info["time"].split(":"))
                
                start_time = date.replace(hour=hour, minute=minute)
                end_time = start_time + timedelta(minutes=dance_class.duration_minutes)
                
                # Add some randomness to spots booked (only for past/current sessions)
                if date.date() <= datetime.now().date():
                    booked = random.randint(3, min(8, dance_class.max_capacity - 2))
                else:
                    booked = random.randint(0, min(5, dance_class.max_capacity - 5))
                
                session = ClassSession(
                    id=generate_id(),
                    studio_id=studio.id,
                    class_id=dance_class.id,
                    instructor_id=dance_class.instructor_id,
                    date=date.date(),
                    start_time=start_time,
                    end_time=end_time,
                    max_capacity=dance_class.max_capacity,
                    booked_count=booked,
                    status='SCHEDULED'
                )
                sessions.append(session)
                db.session.add(session)
        
        db.session.flush()
        
        # Create Contacts (Students/Leads)
        print("📱 Creating contacts...")
        contacts_data = [
            {"name": "Ananya Gupta", "phone": "+919876543211", "email": "ananya@email.com", "source": "whatsapp"},
            {"name": "Vikram Kumar", "phone": "+919876543212", "email": "vikram@email.com", "source": "instagram"},
            {"name": "Sneha Reddy", "phone": "+919876543213", "email": "sneha@email.com", "source": "website"},
            {"name": "Aditya Joshi", "phone": "+919876543214", "email": "aditya@email.com", "source": "whatsapp"},
            {"name": "Neha Kapoor", "phone": "+919876543215", "email": "neha@email.com", "source": "referral"},
            {"name": "Rohan Mehta", "phone": "+919876543216", "email": "rohan@email.com", "source": "instagram"},
            {"name": "Kavya Nair", "phone": "+919876543217", "email": "kavya@email.com", "source": "whatsapp"},
            {"name": "Aryan Shah", "phone": "+919876543218", "email": "aryan@email.com", "source": "website"},
            {"name": "Diya Sharma", "phone": "+919876543219", "email": "diya@email.com", "source": "whatsapp"},
            {"name": "Krish Patel", "phone": "+919876543220", "email": "krish@email.com", "source": "referral"}
        ]
        
        contacts = []
        for cd in contacts_data:
            contact = Contact(
                id=generate_id(),
                studio_id=studio.id,
                name=cd["name"],
                phone=cd["phone"],
                email=cd["email"],
                lead_source=cd["source"],
                lead_status='CONVERTED' if random.random() > 0.3 else 'NEW',
                tags=["student"] if random.random() > 0.3 else ["lead"]
            )
            contacts.append(contact)
            db.session.add(contact)
        
        db.session.flush()
        
        # Create some Bookings
        print("🎫 Creating bookings...")
        bookings = []
        
        # Get future sessions
        future_sessions = [s for s in sessions if s.start_time > datetime.now()]
        
        for i, contact in enumerate(contacts[:7]):  # First 7 contacts have bookings
            # Each contact books 1-3 classes
            num_bookings = random.randint(1, 3)
            contact_sessions = random.sample(future_sessions[:20], min(num_bookings, len(future_sessions[:20])))
            
            for session in contact_sessions:
                is_paid = random.random() > 0.3
                booking = Booking(
                    id=generate_id(),
                    booking_number=generate_booking_number(),
                    studio_id=studio.id,
                    contact_id=contact.id,
                    session_id=session.id,
                    status='CONFIRMED' if is_paid else 'PENDING',
                    payment_method='drop_in'
                )
                bookings.append(booking)
                db.session.add(booking)
        
        db.session.flush()
        
        # Create Payments for confirmed bookings
        print("💳 Creating payments...")
        for booking in bookings:
            if booking.status == 'CONFIRMED':
                # Get the session to determine price
                session = next((s for s in sessions if s.id == booking.session_id), None)
                if session:
                    dance_class = next((c for c in dance_classes if c.id == session.class_id), None)
                    if dance_class:
                        amount = dance_class.price
                        tax = amount * 0.18
                        total = amount + tax
                        
                        payment = Payment(
                            id=generate_id(),
                            payment_number=generate_payment_number(),
                            studio_id=studio.id,
                            contact_id=booking.contact_id,
                            amount=amount,
                            currency='INR',
                            tax_amount=tax,
                            tax_rate=18,
                            total_amount=total,
                            provider='RAZORPAY',
                            provider_payment_id=f"pay_demo_{random.randint(100000, 999999)}",
                            provider_order_id=f"order_demo_{random.randint(100000, 999999)}",
                            status='COMPLETED'
                        )
                        db.session.add(payment)
                        booking.payment_id = payment.id
        
        db.session.flush()
        
        # Create some Conversations
        print("💬 Creating conversations...")
        conversation_messages = [
            [
                {"dir": "inbound", "msg": "Hi! I want to join salsa classes"},
                {"dir": "outbound", "msg": "Hello! Welcome to Rhythm Dance Academy 💃 We have beginner Salsa classes on Mon/Wed at 10 AM. Would you like to book a trial?"},
                {"dir": "inbound", "msg": "Yes please! How much is it?"},
                {"dir": "outbound", "msg": "A drop-in class is ₹500. Your first class is free as a trial! When would you like to join?"}
            ],
            [
                {"dir": "inbound", "msg": "What time is the bachata class tomorrow?"},
                {"dir": "outbound", "msg": "Hi! The Intermediate Bachata class is at 11 AM tomorrow. There are 5 spots left. Want me to book you in?"},
                {"dir": "inbound", "msg": "Yes book me in 🙏"},
                {"dir": "outbound", "msg": "Done! You're booked for Intermediate Bachata tomorrow at 11 AM. See you there! 🎉"}
            ],
            [
                {"dir": "inbound", "msg": "Can I get a refund for Saturday's class? Something came up"},
                {"dir": "outbound", "msg": "No problem! I've cancelled your booking and initiated a refund. It should reflect in 3-5 business days. Hope to see you soon!"},
                {"dir": "inbound", "msg": "Thank you so much! Will definitely come next week"}
            ]
        ]
        
        for i, contact in enumerate(contacts[:3]):
            conv = Conversation(
                id=generate_id(),
                studio_id=studio.id,
                contact_id=contact.id,
                channel='WHATSAPP',
                is_unread=(i == 0),
                is_archived=False,
                last_message_at=datetime.utcnow() - timedelta(hours=i * 2)
            )
            db.session.add(conv)
            db.session.flush()
            
            messages = conversation_messages[i]
            for j, msg_data in enumerate(messages):
                msg = Message(
                    id=generate_id(),
                    conversation_id=conv.id,
                    direction=msg_data["dir"].upper(),
                    content=msg_data["msg"],
                    sender_id=users[0].id if msg_data["dir"] == "outbound" else None,
                    is_read=True,
                    created_at=datetime.utcnow() - timedelta(hours=i * 2, minutes=(len(messages) - j) * 5)
                )
                db.session.add(msg)
        
        db.session.commit()
        
        print("\n✅ Database seeded successfully!")
        print(f"""
📊 Summary:
   • 1 Studio: {studio.name}
   • {len(users)} Users (staff/instructors)
   • {len(dance_classes)} Dance Classes
   • {len(sessions)} Class Sessions (next 14 days)
   • {len(contacts)} Contacts
   • {len(bookings)} Bookings
   • 3 Conversations with messages

🔐 Login credentials:
   Email: priya@rhythmdance.com
   Password: password123

🌐 Public booking page:
   http://localhost:5173/book/rhythm-dance-academy
        """)


if __name__ == '__main__':
    seed_data()
