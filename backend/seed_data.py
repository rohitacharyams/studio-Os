"""
Seed script to populate Studio OS with realistic demo data.
Run with: python seed_data.py
"""

import os
import sys
from datetime import datetime, timedelta
import random
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Studio, User, Contact, Conversation, Message,
    LeadStatusHistory, StudioKnowledge, MessageTemplate, AnalyticsDaily
)

app = create_app()

# Sample data
FIRST_NAMES = ["Emma", "Liam", "Olivia", "Noah", "Ava", "Isabella", "Sophia", "Mia", "Charlotte", "Amelia",
               "James", "Benjamin", "Lucas", "Henry", "Alexander", "Michael", "Daniel", "Matthew", "David", "Joseph"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris"]

LEAD_SOURCES = ["website", "instagram", "referral", "walk-in", "google", "facebook"]
CHANNELS = ["EMAIL", "WHATSAPP", "INSTAGRAM"]

# Realistic inquiry messages
INQUIRY_MESSAGES = [
    {
        "subject": "Dance classes for my daughter",
        "message": "Hi! My 7-year-old daughter has been begging to take dance classes. She loves watching dance videos and tries to copy the moves. What classes would you recommend for a complete beginner? Also, what's the schedule and pricing like?",
        "channel": "EMAIL"
    },
    {
        "subject": "Adult beginner classes?",
        "message": "Hello, I'm 32 and have always wanted to learn to dance but never had the chance. Do you offer classes for adult beginners? I'm interested in salsa or bachata. A bit nervous about starting!",
        "channel": "EMAIL"
    },
    {
        "subject": None,
        "message": "Hey! Saw your studio on Instagram. Do you have hip hop classes for teens? My son is 14 and obsessed with street dance 🔥",
        "channel": "INSTAGRAM"
    },
    {
        "subject": None,
        "message": "Hi, I'm looking for wedding dance lessons. Our wedding is in 3 months and we want to surprise our guests with a choreographed first dance. Is that enough time?",
        "channel": "WHATSAPP"
    },
    {
        "subject": "Ballet classes inquiry",
        "message": "Good morning! I'm interested in enrolling my twin girls (age 5) in ballet classes. Do you have any spots available? They're very energetic and I think dance would be great for them.",
        "channel": "EMAIL"
    },
    {
        "subject": None,
        "message": "yo do u guys do breakdancing? im tryna learn some power moves 💪",
        "channel": "INSTAGRAM"
    },
    {
        "subject": "Competition team information",
        "message": "Hello, my daughter has been dancing for 4 years and wants to join a competition team. What's the process for tryouts? What level of commitment is expected?",
        "channel": "EMAIL"
    },
    {
        "subject": None,
        "message": "Hi there! Quick question - do you offer drop-in classes? I travel a lot for work but would love to dance when I'm in town.",
        "channel": "WHATSAPP"
    },
    {
        "subject": "Group booking for bachelorette party",
        "message": "Hi! I'm planning a bachelorette party for my best friend and we'd love to do a dance class. There would be about 12 of us. Do you do private group sessions? Something fun and not too serious!",
        "channel": "EMAIL"
    },
    {
        "subject": None,
        "message": "Can my 3 year old join classes? She dances around the house all day!",
        "channel": "WHATSAPP"
    },
]

# Follow-up messages from leads
FOLLOW_UP_MESSAGES = [
    "Thanks for the info! When can I come for a trial class?",
    "That sounds perfect. What do I need to bring for the first class?",
    "Great, I'd like to sign up! How do I register?",
    "Can you tell me more about the pricing packages?",
    "Do you have any spots available this Saturday?",
]

# Studio responses
STUDIO_RESPONSES = [
    "Thank you for reaching out! We'd love to have you join our dance family. Let me answer your questions...",
    "Hi there! Thanks for your interest in our studio. We have the perfect class for you!",
    "Hello! Great to hear from you. We absolutely offer what you're looking for.",
    "Thanks for getting in touch! I'm excited to help you start your dance journey.",
]

# Knowledge base entries
KNOWLEDGE_BASE = [
    {
        "category": "classes",
        "title": "Class Schedule Overview",
        "content": """Our studio offers classes 7 days a week:
- Monday-Friday: 4pm-9pm
- Saturday: 9am-5pm  
- Sunday: 10am-3pm

Age groups:
- Tiny Dancers (3-5): Ballet, Creative Movement
- Kids (6-12): Ballet, Jazz, Hip Hop, Contemporary
- Teens (13-17): All styles including competition prep
- Adults (18+): Beginner to advanced in multiple styles

Drop-in classes available for $25/class. Monthly unlimited is $150."""
    },
    {
        "category": "pricing",
        "title": "Pricing & Packages",
        "content": """Pricing Structure:
- Drop-in class: $25
- 4-class pack: $80 (valid 1 month)
- 8-class pack: $140 (valid 2 months)
- Monthly unlimited: $150
- Annual membership: $1,400 (save 2 months!)

Private lessons: $75/hour
Semi-private (2 people): $100/hour
Wedding packages: Starting at $400 for 4 sessions

Registration fee: $35 (waived for annual members)
Costume fee for recitals: ~$75-100 per costume"""
    },
    {
        "category": "policies",
        "title": "Studio Policies",
        "content": """Key Policies:
- 24-hour cancellation policy for classes
- Proper dance attire required (we sell basics in studio)
- No outside food in dance rooms
- Parents may watch first and last class of each session
- Recital participation optional but encouraged
- Competition team by audition only (held in August)

Trial class: First class is FREE for new students!
We require signed waiver before first class."""
    },
    {
        "category": "faq",
        "title": "Frequently Asked Questions",
        "content": """Common Questions:

Q: What age can kids start?
A: We accept dancers as young as 3 in our Tiny Dancers program.

Q: Do I need dance experience?
A: Not at all! We have true beginner classes for all ages.

Q: What should I wear?
A: Comfortable clothing you can move in. Ballet requires specific attire.

Q: Can I watch my child's class?
A: Yes, during designated observation weeks (first and last of each session).

Q: Do you offer makeup classes?
A: Yes, within the same month for package holders."""
    },
    {
        "category": "about",
        "title": "About Dream Dance Studio",
        "content": """Dream Dance Studio was founded in 2015 by Sarah Mitchell, a former professional dancer with the NYC Ballet. 

Our mission: To inspire confidence and joy through dance, regardless of age or experience level.

What makes us special:
- Small class sizes (max 12 students)
- Professional-grade sprung floors
- Experienced, certified instructors
- Supportive, non-competitive environment
- Performance opportunities for all levels

We've trained over 2,000 students and counting! Several of our alumni have gone on to professional dance careers and college dance programs."""
    },
]

# Message templates
MESSAGE_TEMPLATES = [
    {
        "name": "Welcome - New Inquiry",
        "category": "inquiry",
        "subject": "Welcome to Dream Dance Studio!",
        "content": """Hi {name}!

Thank you so much for reaching out to Dream Dance Studio! We're thrilled you're considering us for your dance journey.

I'd love to help you find the perfect class. Based on what you've shared, I think {recommendation} would be a great fit!

Would you like to come in for a FREE trial class? Just let me know what days work best for you.

Looking forward to dancing with you!

Warm regards,
{sender_name}
Dream Dance Studio"""
    },
    {
        "name": "Follow-up - No Response",
        "category": "follow-up",
        "subject": "Still interested in dance classes?",
        "content": """Hi {name},

I wanted to follow up on your inquiry about dance classes. I know life gets busy!

Just a reminder that we'd love to offer you a FREE trial class so you can experience our studio firsthand.

Is there anything I can help answer to make your decision easier?

Best,
{sender_name}"""
    },
    {
        "name": "Class Confirmation",
        "category": "booking",
        "subject": "Your trial class is confirmed!",
        "content": """Hi {name}!

Great news - you're all set for your trial class!

📅 Date: {date}
⏰ Time: {time}
💃 Class: {class_name}
📍 Location: 123 Dance Street, Suite 100

What to bring:
- Comfortable clothing
- Water bottle
- Completed waiver (attached)

Can't wait to see you in the studio!

{sender_name}
Dream Dance Studio"""
    },
]


def generate_phone():
    return f"+1{random.randint(200,999)}{random.randint(100,999)}{random.randint(1000,9999)}"


def generate_email(first_name, last_name):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com"]
    return f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}@{random.choice(domains)}"


def seed_database():
    with app.app_context():
        print("🌱 Starting database seed...")
        
        # Clear existing data (optional - comment out to append)
        print("   Clearing existing data...")
        Message.query.delete()
        LeadStatusHistory.query.delete()
        Conversation.query.delete()
        Contact.query.delete()
        StudioKnowledge.query.delete()
        MessageTemplate.query.delete()
        AnalyticsDaily.query.delete()
        # Keep users and studios
        
        # Get or create studio
        studio = Studio.query.first()
        if not studio:
            studio = Studio(
                id=str(uuid.uuid4()),
                name="Dream Dance Studio",
                email="hello@dreamdance.studio",
                phone="+1 (555) 123-4567",
                address="123 Dance Street, Suite 100, New York, NY 10001",
                timezone="America/New_York"
            )
            db.session.add(studio)
            db.session.commit()
            print(f"   ✅ Created studio: {studio.name}")
        else:
            print(f"   ✅ Using existing studio: {studio.name}")
        
        # Get the user
        user = User.query.filter_by(studio_id=studio.id).first()
        if not user:
            print("   ⚠️ No user found. Please register first!")
            return
        print(f"   ✅ Using user: {user.email}")
        
        # Add knowledge base
        print("   📚 Adding knowledge base...")
        for kb_entry in KNOWLEDGE_BASE:
            knowledge = StudioKnowledge(
                id=str(uuid.uuid4()),
                studio_id=studio.id,
                category=kb_entry["category"],
                title=kb_entry["title"],
                content=kb_entry["content"],
                is_active=True
            )
            db.session.add(knowledge)
        
        # Add message templates
        print("   📝 Adding message templates...")
        for template in MESSAGE_TEMPLATES:
            msg_template = MessageTemplate(
                id=str(uuid.uuid4()),
                studio_id=studio.id,
                name=template["name"],
                category=template["category"],
                subject=template.get("subject"),
                content=template["content"],
                channels=["EMAIL", "WHATSAPP"],
                is_active=True
            )
            db.session.add(msg_template)
        
        # Create contacts and conversations
        print("   👥 Creating contacts and conversations...")
        
        lead_statuses = ["NEW", "CONTACTED", "ENGAGED", "QUALIFIED", "CONVERTED", "LOST"]
        
        for i, inquiry in enumerate(INQUIRY_MESSAGES):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            
            # Create contact
            contact = Contact(
                id=str(uuid.uuid4()),
                studio_id=studio.id,
                name=f"{first_name} {last_name}",
                email=generate_email(first_name, last_name),
                phone=generate_phone() if inquiry["channel"] == "WHATSAPP" else None,
                instagram_handle=f"@{first_name.lower()}_{last_name.lower()}" if inquiry["channel"] == "INSTAGRAM" else None,
                lead_status=random.choice(lead_statuses[:4]),  # Most are in early stages
                lead_source=random.choice(LEAD_SOURCES),
                notes=f"Inquiry about dance classes via {inquiry['channel']}",
                tags=random.sample(["parent", "adult", "teen", "wedding", "beginner", "competition"], k=random.randint(1, 3))
            )
            db.session.add(contact)
            
            # Create conversation
            days_ago = random.randint(0, 14)
            created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 12))
            
            conversation = Conversation(
                id=str(uuid.uuid4()),
                studio_id=studio.id,
                contact_id=contact.id,
                channel=inquiry["channel"],
                subject=inquiry["subject"],
                is_unread=random.choice([True, False, False]),  # 1/3 unread
                is_archived=False,
                is_starred=random.choice([True, False, False, False]),  # 1/4 starred
                last_message_at=created_at + timedelta(hours=random.randint(1, 48)),
                created_at=created_at
            )
            db.session.add(conversation)
            
            # Add initial inquiry message
            msg1 = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                direction="INBOUND",
                content=inquiry["message"],
                is_read=not conversation.is_unread,
                created_at=created_at
            )
            db.session.add(msg1)
            
            # Randomly add a response and follow-up for some conversations
            if random.random() > 0.3:  # 70% have responses
                response_time = created_at + timedelta(hours=random.randint(1, 6))
                msg2 = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation.id,
                    sender_id=user.id,
                    direction="OUTBOUND",
                    content=random.choice(STUDIO_RESPONSES) + "\n\nBest regards,\n" + (user.name or "Studio Team"),
                    is_read=True,
                    created_at=response_time
                )
                db.session.add(msg2)
                
                # Some have follow-ups from the lead
                if random.random() > 0.5:  # 50% have follow-ups
                    followup_time = response_time + timedelta(hours=random.randint(2, 24))
                    msg3 = Message(
                        id=str(uuid.uuid4()),
                        conversation_id=conversation.id,
                        direction="INBOUND",
                        content=random.choice(FOLLOW_UP_MESSAGES),
                        is_read=random.choice([True, False]),
                        created_at=followup_time
                    )
                    db.session.add(msg3)
                    conversation.last_message_at = followup_time
            
            # Add lead status history
            history = LeadStatusHistory(
                id=str(uuid.uuid4()),
                contact_id=contact.id,
                from_status=None,
                to_status="NEW",
                changed_by_id=None,
                notes="Lead created from inquiry",
                created_at=created_at
            )
            db.session.add(history)
            
            if contact.lead_status != "NEW":
                history2 = LeadStatusHistory(
                    id=str(uuid.uuid4()),
                    contact_id=contact.id,
                    from_status="NEW",
                    to_status=contact.lead_status,
                    changed_by_id=user.id,
                    notes="Updated based on engagement",
                    created_at=created_at + timedelta(days=random.randint(1, 3))
                )
                db.session.add(history2)
        
        # Add analytics data
        print("   📊 Adding analytics data...")
        for days_ago in range(14):
            date = (datetime.utcnow() - timedelta(days=days_ago)).date()
            analytics = AnalyticsDaily(
                id=str(uuid.uuid4()),
                studio_id=studio.id,
                date=date,
                messages_received=random.randint(3, 15),
                messages_sent=random.randint(2, 12),
                new_leads=random.randint(1, 5),
                leads_converted=random.randint(0, 2),
                avg_response_time_minutes=random.randint(30, 180),  # minutes
                channel_breakdown={
                    "EMAIL": random.randint(2, 8),
                    "WHATSAPP": random.randint(1, 5),
                    "INSTAGRAM": random.randint(1, 4)
                }
            )
            db.session.add(analytics)
        
        db.session.commit()
        print("\n✅ Database seeded successfully!")
        print(f"   - {len(KNOWLEDGE_BASE)} knowledge base entries")
        print(f"   - {len(MESSAGE_TEMPLATES)} message templates")
        print(f"   - {len(INQUIRY_MESSAGES)} contacts with conversations")
        print(f"   - 14 days of analytics data")
        print("\n🎉 You can now explore the app at http://localhost:5173")


if __name__ == "__main__":
    seed_database()
