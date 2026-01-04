# Studio OS - Unified Inbox & Onboarding Design

## 🎯 Overview

This document outlines the complete architecture for:
1. **Onboarding Journey** - First-time studio owner setup
2. **Channel Integration** - WhatsApp, Instagram, Gmail unified inbox
3. **Message Processing Pipeline** - Auto-tagging and categorization
4. **AI Admin Dashboard** - Insights and automation

---

## 📋 Part 1: Onboarding Journey

### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STUDIO OWNER ONBOARDING                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: Account Creation                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • Studio Name                                                │   │
│  │ • Owner Name & Email                                         │   │
│  │ • Password                                                   │   │
│  │ • Studio Type (Dance, Yoga, Fitness, Music, etc.)           │   │
│  │ • Business Phone Number                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  Step 2: Studio Profile Setup                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • Upload Logo                                                │   │
│  │ • Business Hours                                             │   │
│  │ • Location/Address                                           │   │
│  │ • Class Types Offered (Salsa, Hip-hop, Contemporary, etc.)  │   │
│  │ • Price Range (for AI to answer pricing questions)          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  Step 3: Connect Channels (The Magic!)                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                              │   │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐               │   │
│  │   │ WhatsApp │   │Instagram │   │  Gmail   │               │   │
│  │   │ Business │   │  DMs     │   │  Inbox   │               │   │
│  │   │    📱    │   │    📸    │   │    📧    │               │   │
│  │   └────┬─────┘   └────┬─────┘   └────┬─────┘               │   │
│  │        │              │              │                      │   │
│  │        └──────────────┼──────────────┘                      │   │
│  │                       ↓                                      │   │
│  │              [UNIFIED INBOX]                                 │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  Step 4: Knowledge Base Setup                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • FAQ Import (or guided Q&A builder)                        │   │
│  │ • Class Schedule Upload                                      │   │
│  │ • Pricing Information                                        │   │
│  │ • Instructor Profiles                                        │   │
│  │ • Studio Policies (cancellation, refunds, etc.)             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  Step 5: AI Configuration                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • Choose AI Provider (OpenAI, Anthropic, Gemini, Ollama)    │   │
│  │ • Set Auto-Reply Mode (Full Auto / Suggest / Manual)        │   │
│  │ • Define Business Tone (Friendly, Professional, Casual)     │   │
│  │ • Set Response Templates                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  Step 6: Test & Launch                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • Send test message to yourself                              │   │
│  │ • Verify AI responses                                        │   │
│  │ • Go Live! 🚀                                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Onboarding Database Models

```python
class OnboardingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    
    # Progress tracking
    step_account_created = db.Column(db.Boolean, default=False)
    step_profile_complete = db.Column(db.Boolean, default=False)
    step_channels_connected = db.Column(db.Boolean, default=False)
    step_knowledge_base_setup = db.Column(db.Boolean, default=False)
    step_ai_configured = db.Column(db.Boolean, default=False)
    step_test_completed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Which channels connected
    whatsapp_connected = db.Column(db.Boolean, default=False)
    instagram_connected = db.Column(db.Boolean, default=False)
    gmail_connected = db.Column(db.Boolean, default=False)
```

---

## 📨 Part 2: Message Queue Architecture

### Why Message Queues?

```
Without Queue:                      With Queue:
─────────────                       ───────────
                                    
WhatsApp ──┐                        WhatsApp ──┐
           │                                   │
Instagram ─┼──→ Direct to DB       Instagram ─┼──→ Redis Queue ──→ Workers ──→ DB
           │    (Slow, Blocking)               │    (Fast, Async)      │
Gmail ─────┘                        Gmail ─────┘                       │
                                                                       ↓
                                                              ┌────────────────┐
                                                              │ Pre-processing │
                                                              │ • Tag messages │
                                                              │ • Score leads  │
                                                              │ • Detect intent│
                                                              │ • Auto-reply   │
                                                              └────────────────┘
```

### Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MESSAGE PROCESSING PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   INGESTION LAYER                                                            │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│   │  WhatsApp   │  │  Instagram  │  │   Gmail     │                        │
│   │  Webhook    │  │  Webhook    │  │  Push/Poll  │                        │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                        │
│          │                │                │                                │
│          └────────────────┼────────────────┘                                │
│                           ↓                                                  │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                     REDIS MESSAGE QUEUE                          │      │
│   │  ┌──────────────────────────────────────────────────────────┐   │      │
│   │  │ Queue: incoming_messages                                  │   │      │
│   │  │ {                                                         │   │      │
│   │  │   "message_id": "uuid",                                   │   │      │
│   │  │   "channel": "whatsapp|instagram|gmail",                  │   │      │
│   │  │   "sender": "+1234567890",                                │   │      │
│   │  │   "content": "Hi, what are your dance class timings?",    │   │      │
│   │  │   "studio_id": 1,                                         │   │      │
│   │  │   "timestamp": "2024-12-24T10:30:00Z",                    │   │      │
│   │  │   "raw_payload": {...}                                    │   │      │
│   │  │ }                                                         │   │      │
│   │  └──────────────────────────────────────────────────────────┘   │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                           ↓                                                  │
│   PROCESSING LAYER (Celery Workers)                                          │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                                                                  │      │
│   │  Worker 1: Message Preprocessor                                  │      │
│   │  ├── Normalize message format                                    │      │
│   │  ├── Extract contact info                                        │      │
│   │  ├── Detect language                                             │      │
│   │  └── Store raw message                                           │      │
│   │                                                                  │      │
│   │  Worker 2: AI Tagger                                             │      │
│   │  ├── Classify intent (inquiry, booking, complaint, etc.)        │      │
│   │  ├── Extract entities (class type, date, time)                  │      │
│   │  ├── Assign priority (urgent, normal, low)                      │      │
│   │  └── Auto-tag message                                            │      │
│   │                                                                  │      │
│   │  Worker 3: Lead Scorer                                           │      │
│   │  ├── Calculate lead score (0-100)                               │      │
│   │  ├── Detect buying signals                                       │      │
│   │  └── Update contact status                                       │      │
│   │                                                                  │      │
│   │  Worker 4: Auto-Responder                                        │      │
│   │  ├── Check if auto-reply enabled                                 │      │
│   │  ├── Generate AI response                                        │      │
│   │  ├── Queue response for sending                                  │      │
│   │  └── Log response for review                                     │      │
│   │                                                                  │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                           ↓                                                  │
│   STORAGE & NOTIFICATION                                                     │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  • Store processed message in PostgreSQL/SQLite                  │      │
│   │  • Update conversation thread                                    │      │
│   │  • Send real-time notification via WebSocket                     │      │
│   │  • Update dashboard analytics                                    │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Celery Task Definitions

```python
# backend/app/tasks/message_tasks.py

from celery import shared_task
from app import db
from app.models import Message, Contact, Conversation
from app.services.ai_service import AIService

@shared_task(name='process_incoming_message')
def process_incoming_message(message_data: dict):
    """Main task that orchestrates message processing."""
    
    # Chain of tasks
    chain = (
        preprocess_message.s(message_data) |
        tag_message.s() |
        score_lead.s() |
        auto_respond.s()
    )
    return chain()

@shared_task(name='preprocess_message')
def preprocess_message(message_data: dict):
    """Normalize and store the raw message."""
    
    # Find or create contact
    contact = Contact.query.filter_by(
        phone=message_data.get('sender'),
        studio_id=message_data['studio_id']
    ).first()
    
    if not contact:
        contact = Contact(
            phone=message_data.get('sender'),
            email=message_data.get('email'),
            studio_id=message_data['studio_id'],
            source=message_data['channel'].upper(),
            lead_status='NEW'
        )
        db.session.add(contact)
        db.session.commit()
    
    # Find or create conversation
    conversation = Conversation.query.filter_by(
        contact_id=contact.id,
        channel=message_data['channel'].upper()
    ).first()
    
    if not conversation:
        conversation = Conversation(
            contact_id=contact.id,
            channel=message_data['channel'].upper(),
            studio_id=message_data['studio_id'],
            status='OPEN'
        )
        db.session.add(conversation)
        db.session.commit()
    
    # Store message
    message = Message(
        conversation_id=conversation.id,
        content=message_data['content'],
        direction='INBOUND',
        channel=message_data['channel'].upper(),
        external_id=message_data.get('message_id')
    )
    db.session.add(message)
    db.session.commit()
    
    return {
        'message_id': message.id,
        'contact_id': contact.id,
        'conversation_id': conversation.id,
        'content': message_data['content'],
        'studio_id': message_data['studio_id']
    }

@shared_task(name='tag_message')
def tag_message(processed_data: dict):
    """AI-powered message tagging."""
    
    ai_service = AIService()
    
    # Classify the message
    classification = ai_service.classify_message(processed_data['content'])
    
    # Update message with tags
    message = Message.query.get(processed_data['message_id'])
    message.tags = classification['tags']
    message.intent = classification['intent']
    message.priority = classification['priority']
    message.sentiment = classification['sentiment']
    db.session.commit()
    
    processed_data['classification'] = classification
    return processed_data

@shared_task(name='score_lead')
def score_lead(processed_data: dict):
    """Calculate and update lead score."""
    
    ai_service = AIService()
    contact = Contact.query.get(processed_data['contact_id'])
    
    # Calculate score based on message and history
    score = ai_service.calculate_lead_score(
        message=processed_data['content'],
        intent=processed_data['classification']['intent'],
        contact_history=contact.messages_count
    )
    
    contact.lead_score = score
    
    # Auto-update lead status based on score
    if score >= 80:
        contact.lead_status = 'HOT'
    elif score >= 50:
        contact.lead_status = 'WARM'
    else:
        contact.lead_status = 'COLD'
    
    db.session.commit()
    
    processed_data['lead_score'] = score
    return processed_data

@shared_task(name='auto_respond')
def auto_respond(processed_data: dict):
    """Generate and optionally send auto-response."""
    
    from app.models import Studio
    
    studio = Studio.query.get(processed_data['studio_id'])
    
    # Check if auto-reply is enabled
    if not studio.auto_reply_enabled:
        return processed_data
    
    ai_service = AIService()
    
    # Generate response
    response = ai_service.generate_smart_reply(
        message=processed_data['content'],
        intent=processed_data['classification']['intent'],
        studio_id=processed_data['studio_id']
    )
    
    # If full-auto mode, send immediately
    if studio.auto_reply_mode == 'FULL_AUTO':
        send_response.delay(
            conversation_id=processed_data['conversation_id'],
            response=response
        )
    else:
        # Store as draft for review
        message = Message(
            conversation_id=processed_data['conversation_id'],
            content=response,
            direction='OUTBOUND',
            status='DRAFT',
            ai_generated=True
        )
        db.session.add(message)
        db.session.commit()
    
    return processed_data
```

---

## 🏷️ Part 3: AI Auto-Tagging System

### Message Categories (High-Level Tags)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MESSAGE CATEGORY TAXONOMY                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📋 INQUIRY                          💰 PRICING                      │
│  ├── Class Information               ├── Fee Inquiry                 │
│  ├── Schedule Query                  ├── Package Details             │
│  ├── Location/Directions             ├── Discount Request            │
│  ├── Instructor Details              └── Payment Options             │
│  └── Trial Class                                                     │
│                                                                      │
│  📅 BOOKING                          🔄 SCHEDULING                   │
│  ├── New Enrollment                  ├── Reschedule Request          │
│  ├── Class Reservation               ├── Cancellation                │
│  ├── Private Session                 ├── Makeup Class                │
│  └── Group Booking                   └── Time Change                 │
│                                                                      │
│  ⚠️ COMPLAINT                        🎉 FEEDBACK                     │
│  ├── Service Issue                   ├── Positive Review             │
│  ├── Billing Problem                 ├── Suggestion                  │
│  ├── Instructor Complaint            ├── Testimonial                 │
│  └── Facility Issue                  └── Referral                    │
│                                                                      │
│  ℹ️ GENERAL                          🆘 URGENT                       │
│  ├── Greeting                        ├── Emergency Contact           │
│  ├── Thank You                       ├── Immediate Response Needed   │
│  ├── Follow-up                       ├── Complaint Escalation        │
│  └── Other                           └── Time-Sensitive Booking      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### AI Classification Prompt

```python
CLASSIFICATION_PROMPT = """
You are an AI assistant for a dance studio. Classify the following customer message.

Message: "{message}"

Respond in JSON format:
{
    "primary_intent": "inquiry|pricing|booking|scheduling|complaint|feedback|general|urgent",
    "sub_category": "specific category from the taxonomy",
    "tags": ["tag1", "tag2"],
    "priority": "low|normal|high|urgent",
    "sentiment": "positive|neutral|negative",
    "entities": {
        "class_type": "extracted class name if mentioned",
        "date": "extracted date if mentioned",
        "time": "extracted time if mentioned",
        "instructor": "extracted instructor name if mentioned"
    },
    "suggested_action": "what the studio should do",
    "confidence": 0.95
}
"""
```

### Tag Database Model

```python
class MessageTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    category = db.Column(db.String(50))  # inquiry, pricing, booking, etc.
    color = db.Column(db.String(7))  # hex color for UI
    icon = db.Column(db.String(50))  # icon name
    
class MessageTagAssociation(db.Model):
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('message_tag.id'), primary_key=True)
    confidence = db.Column(db.Float)  # AI confidence score
    
# Extended Message model
class Message(db.Model):
    # ... existing fields ...
    
    # AI Processing Fields
    intent = db.Column(db.String(50))  # Primary intent
    sub_category = db.Column(db.String(100))  # Sub-category
    priority = db.Column(db.Enum('LOW', 'NORMAL', 'HIGH', 'URGENT'))
    sentiment = db.Column(db.Enum('POSITIVE', 'NEUTRAL', 'NEGATIVE'))
    ai_confidence = db.Column(db.Float)
    
    # Extracted entities (JSON)
    entities = db.Column(db.JSON)
    
    # Tags relationship
    tags = db.relationship('MessageTag', secondary='message_tag_association')
```

---

## 📊 Part 4: Studio Dashboard Design

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STUDIO OS - Dashboard                                    [🔔] [👤 Owner]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    TODAY'S OVERVIEW                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │    42    │  │    12    │  │     5    │  │    89%   │            │   │
│  │  │ Messages │  │   New    │  │  Urgent  │  │ Response │            │   │
│  │  │  Today   │  │  Leads   │  │  Pending │  │   Rate   │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │   MESSAGE CATEGORIES        │  │   CHANNEL DISTRIBUTION               │  │
│  │   ────────────────────      │  │   ─────────────────────              │  │
│  │                             │  │                                      │  │
│  │   📋 Inquiries      35%    │  │      WhatsApp  ████████████  60%    │  │
│  │   💰 Pricing        25%    │  │      Instagram ██████       30%    │  │
│  │   📅 Bookings       20%    │  │      Gmail     ██           10%    │  │
│  │   🔄 Scheduling     10%    │  │                                      │  │
│  │   ⚠️ Complaints      5%    │  │                                      │  │
│  │   🎉 Feedback        5%    │  │                                      │  │
│  │                             │  │                                      │  │
│  └─────────────────────────────┘  └─────────────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │   AI INSIGHTS & RECOMMENDATIONS                                      │   │
│  │   ─────────────────────────────                                      │   │
│  │                                                                      │   │
│  │   💡 "Pricing inquiries increased 40% this week. Consider           │   │
│  │       creating a pricing FAQ or promotional offer."                  │   │
│  │                                                                      │   │
│  │   🔥 "3 HOT leads waiting for follow-up:                            │   │
│  │       • Priya S. - Interested in Salsa (Score: 92)                  │   │
│  │       • Raj M. - Asked about group booking (Score: 85)              │   │
│  │       • Anita K. - Ready to enroll (Score: 88)"                     │   │
│  │                                                                      │   │
│  │   📈 "Peak inquiry time: 6-8 PM. Ensure quick responses then."      │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │   RECENT CONVERSATIONS (Needs Attention)                             │   │
│  │   ──────────────────────────────────────                             │   │
│  │                                                                      │   │
│  │   ┌────┬─────────────────────────────────────────────┬────────────┐ │   │
│  │   │ 📱 │ Priya: "What's the fee for beginner salsa?" │ 🏷️ Pricing │ │   │
│  │   │    │ 2 min ago | Lead Score: 92 | 🔥 HOT        │ [Reply]    │ │   │
│  │   ├────┼─────────────────────────────────────────────┼────────────┤ │   │
│  │   │ 📸 │ Raj: "Can I book for a group of 10?"       │ 🏷️ Booking │ │   │
│  │   │    │ 15 min ago | Lead Score: 85 | 🔥 HOT       │ [Reply]    │ │   │
│  │   ├────┼─────────────────────────────────────────────┼────────────┤ │   │
│  │   │ 📧 │ Anita: "I'd like to enroll my daughter"    │ 🏷️ Booking │ │   │
│  │   │    │ 1 hour ago | Lead Score: 88 | 🔥 HOT       │ [Reply]    │ │   │
│  │   └────┴─────────────────────────────────────────────┴────────────┘ │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AI Admin Mode

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI ADMIN SETTINGS                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Auto-Response Mode:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ○ Full Auto    - AI responds to all messages automatically         │   │
│  │  ● Suggest      - AI drafts responses, you approve before sending   │   │
│  │  ○ Manual       - AI only tags/classifies, you write all responses  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Auto-Response Rules:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ☑️ Auto-reply to pricing inquiries                                 │   │
│  │  ☑️ Auto-reply to schedule questions                                │   │
│  │  ☑️ Auto-reply to location queries                                  │   │
│  │  ☐ Auto-reply to complaints (always notify human)                   │   │
│  │  ☑️ Auto-reply to greetings                                         │   │
│  │  ☐ Auto-reply to booking requests (requires confirmation)           │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Business Hours Auto-Reply:                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☑️ Send "We're currently closed" message outside business hours    │   │
│  │     Message: "Thanks for reaching out! We're currently closed.      │   │
│  │              Our team will respond when we open at 9 AM."           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Escalation Rules:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Escalate to owner if: Complaint detected                         │   │
│  │  • Escalate to owner if: Message contains "refund" or "cancel"      │   │
│  │  • Escalate to owner if: Lead score > 80 (hot lead!)                │   │
│  │  • Escalate to owner if: No response in 30 minutes                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Part 5: Channel Integration Details

### WhatsApp Business API Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WHATSAPP INTEGRATION FLOW                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Setup Requirements:                                                 │
│  • Meta Business Account                                             │
│  • WhatsApp Business API access                                      │
│  • Verified business phone number                                    │
│  • Webhook URL for receiving messages                                │
│                                                                      │
│  Flow:                                                               │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐     │
│  │  Customer   │───────▶│  WhatsApp   │───────▶│  Webhook    │     │
│  │  sends msg  │        │  Cloud API  │        │  /webhook/  │     │
│  └─────────────┘        └─────────────┘        │  whatsapp   │     │
│                                                └──────┬──────┘     │
│                                                       │             │
│                                                       ▼             │
│                                          ┌─────────────────────┐   │
│                                          │  Redis Queue        │   │
│                                          │  Process Message    │   │
│                                          └─────────────────────┘   │
│                                                       │             │
│  ┌─────────────┐        ┌─────────────┐              │             │
│  │  Customer   │◀───────│  WhatsApp   │◀─────────────┘             │
│  │  receives   │        │  Cloud API  │   (AI Response)            │
│  └─────────────┘        └─────────────┘                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Instagram DM Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INSTAGRAM INTEGRATION FLOW                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Setup Requirements:                                                 │
│  • Instagram Business/Creator Account                                │
│  • Facebook Page linked to Instagram                                 │
│  • Meta App with Instagram Messaging permission                      │
│  • Webhook subscription for messages                                 │
│                                                                      │
│  Supported Message Types:                                            │
│  • Text messages                                                     │
│  • Image/Video shares                                                │
│  • Story replies                                                     │
│  • Story mentions                                                    │
│  • Post comments (optional)                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Gmail Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                      GMAIL INTEGRATION FLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Setup Requirements:                                                 │
│  • Google Cloud Project                                              │
│  • Gmail API enabled                                                 │
│  • OAuth 2.0 credentials                                             │
│  • Pub/Sub for real-time notifications (optional)                    │
│                                                                      │
│  Methods:                                                            │
│  1. Push Notifications (Recommended)                                 │
│     • Google Pub/Sub sends notification when new email arrives       │
│     • Our server fetches and processes the email                     │
│                                                                      │
│  2. Polling (Fallback)                                               │
│     • Check for new emails every X minutes                           │
│     • Less real-time but simpler setup                               │
│                                                                      │
│  Email Threading:                                                    │
│  • Group emails by thread ID                                         │
│  • Show as conversation in unified inbox                             │
│  • Track reply chains                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Onboarding UI components
- [ ] Channel connection wizards
- [ ] Basic message queue setup (Redis + Celery)
- [ ] Database models for tags and processing

### Phase 2: AI Integration (Week 3-4)
- [ ] Message classification pipeline
- [ ] Auto-tagging system
- [ ] Lead scoring algorithm
- [ ] Smart reply generation

### Phase 3: Dashboard & Analytics (Week 5-6)
- [ ] Studio dashboard with insights
- [ ] Message category analytics
- [ ] Lead funnel visualization
- [ ] AI recommendations engine

### Phase 4: Advanced Features (Week 7-8)
- [ ] Full auto-reply mode
- [ ] Custom automation rules
- [ ] Multi-language support
- [ ] Advanced reporting

---

## 📝 Summary

This design enables:

1. **Easy Onboarding** - Studio owners can connect all channels in minutes
2. **Unified Inbox** - All messages from WhatsApp, Instagram, Gmail in one place
3. **AI-Powered Tagging** - Automatic categorization saves hours of manual work
4. **Smart Prioritization** - Hot leads surface automatically
5. **AI Admin** - The AI handles routine queries while owners focus on high-value interactions

The message queue architecture ensures:
- **Reliability** - No messages lost even during high traffic
- **Scalability** - Can handle thousands of messages per second
- **Intelligence** - Every message is processed, tagged, and scored
- **Speed** - Real-time updates via WebSockets
