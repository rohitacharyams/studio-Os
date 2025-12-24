# Studio Operations OS - System Design Document

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Component Design](#component-design)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [API Design](#api-design)
7. [Integration Architecture](#integration-architecture)
8. [Security Architecture](#security-architecture)
9. [Scalability Considerations](#scalability-considerations)

---

## System Overview

### Purpose
Studio Operations OS is a unified communication and lead management platform designed specifically for dance studios. It consolidates messages from multiple channels (WhatsApp, Instagram, Gmail) into a single inbox, provides AI-powered smart replies, and includes class scheduling optimization.

### Key Capabilities
- **Unified Inbox**: Aggregate messages from WhatsApp Business, Instagram DMs, and Gmail
- **Lead Management**: Track and score leads through the sales funnel
- **AI-Powered Responses**: Generate contextual replies using multiple LLM providers
- **Class Scheduling**: Optimize dance class schedules with constraint satisfaction
- **Analytics Dashboard**: Real-time insights into lead conversion and engagement

---

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STUDIO OS PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FRONTEND (React + Vite)                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │  Inbox   │ │ Contacts │ │ Analytics│ │ Settings │ │Scheduling│  │   │
│  │  │   View   │ │   View   │ │Dashboard │ │   View   │ │   View   │  │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │   │
│  │       │            │            │            │            │         │   │
│  │  ┌────┴────────────┴────────────┴────────────┴────────────┴─────┐  │   │
│  │  │                    React Context + Hooks                      │  │   │
│  │  │              (AuthContext, InboxContext, etc.)                │  │   │
│  │  └──────────────────────────┬────────────────────────────────────┘  │   │
│  └─────────────────────────────┼────────────────────────────────────────┘   │
│                                │                                             │
│                                │ HTTP/REST API                               │
│                                ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        BACKEND (Flask + SQLAlchemy)                  │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                      API Layer (Blueprints)                  │   │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐│   │   │
│  │  │  │  Auth  │ │Contacts│ │Messages│ │Analytics│ │Integrations││   │   │
│  │  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘│   │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────────────────────────────┐  │   │   │
│  │  │  │  LLM   │ │Schedule│ │        Knowledge Base          │  │   │   │
│  │  │  └────────┘ └────────┘ └────────────────────────────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                     Service Layer                            │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │   │   │
│  │  │  │ Integration │ │    LLM      │ │     Scheduling      │   │   │   │
│  │  │  │   Manager   │ │  Registry   │ │     Optimizer       │   │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                      Data Layer                              │   │   │
│  │  │              SQLAlchemy ORM + SQLite/PostgreSQL              │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ External APIs
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   WhatsApp   │  │  Instagram   │  │    Gmail     │  │     LLM      │    │
│  │ Business API │  │  Graph API   │  │     API      │  │  Providers   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18.2 | UI Components |
| Build Tool | Vite 5.4 | Fast development server |
| Styling | Tailwind CSS | Utility-first CSS |
| Icons | Lucide React | Icon library |
| Backend | Flask 3.0 | Python web framework |
| ORM | SQLAlchemy | Database abstraction |
| Auth | Flask-JWT-Extended | JWT authentication |
| Database | SQLite/PostgreSQL | Data persistence |
| Migrations | Alembic | Database migrations |

---

## Component Design

### Frontend Components

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.jsx          # Main navigation
│   │   │   ├── Header.jsx           # Top bar with user info
│   │   │   └── Layout.jsx           # Page wrapper
│   │   ├── inbox/
│   │   │   ├── ConversationList.jsx # List of conversations
│   │   │   ├── MessageThread.jsx    # Message display
│   │   │   ├── MessageInput.jsx     # Compose message
│   │   │   └── ChannelFilter.jsx    # Filter by channel
│   │   ├── contacts/
│   │   │   ├── ContactList.jsx      # Contact directory
│   │   │   ├── ContactCard.jsx      # Individual contact
│   │   │   └── LeadStatusBadge.jsx  # Status indicator
│   │   └── analytics/
│   │       ├── MetricsCard.jsx      # KPI display
│   │       └── ChartContainer.jsx   # Graph wrapper
│   ├── contexts/
│   │   ├── AuthContext.jsx          # Authentication state
│   │   └── InboxContext.jsx         # Inbox state management
│   ├── pages/
│   │   ├── Dashboard.jsx            # Main dashboard
│   │   ├── Inbox.jsx                # Unified inbox
│   │   ├── Contacts.jsx             # Contact management
│   │   ├── Analytics.jsx            # Analytics view
│   │   └── Settings.jsx             # Configuration
│   └── services/
│       └── api.js                   # API client
```

### Backend Modules

```
backend/
├── app/
│   ├── routes/                      # API Endpoints
│   │   ├── auth.py                  # Authentication routes
│   │   ├── contacts.py              # Contact CRUD
│   │   ├── conversations.py         # Message handling
│   │   ├── analytics.py             # Analytics data
│   │   ├── integrations.py          # Channel connections
│   │   ├── llm.py                   # AI/LLM endpoints
│   │   └── scheduling.py            # Class scheduling
│   ├── models/                      # Database Models
│   │   └── __init__.py              # All SQLAlchemy models
│   ├── integrations/                # Channel Integrations
│   │   ├── base.py                  # Base integration class
│   │   ├── whatsapp.py              # WhatsApp Business API
│   │   ├── instagram.py             # Instagram Graph API
│   │   ├── gmail.py                 # Gmail API
│   │   └── manager.py               # Integration manager
│   ├── llm/                         # LLM Providers
│   │   ├── base.py                  # Base LLM provider
│   │   ├── openai_provider.py       # OpenAI GPT
│   │   ├── anthropic_provider.py    # Anthropic Claude
│   │   ├── gemini_provider.py       # Google Gemini
│   │   ├── ollama_provider.py       # Local Ollama
│   │   └── registry.py              # Provider registry
│   └── scheduling/                  # Scheduling Engine
│       ├── optimizer.py             # Schedule optimization
│       ├── generator.py             # Schedule generation
│       └── conflict_resolver.py     # Conflict resolution
```

---

## Data Flow

### Message Ingestion Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   WhatsApp   │     │  Instagram   │     │    Gmail     │
│   Webhook    │     │   Webhook    │     │   Push/Poll  │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Integration Manager │
                 │  - Normalize data   │
                 │  - Validate source  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Message Handler   │
                 │  - Create/Update    │
                 │    Conversation     │
                 │  - Store Message    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     Database        │
                 │  - Conversations    │
                 │  - Messages         │
                 │  - Contacts         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Real-time Push    │
                 │  (WebSocket/SSE)    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Frontend Inbox    │
                 │   (React Context)   │
                 └─────────────────────┘
```

### Smart Reply Generation Flow

```
┌─────────────────┐
│  User Request   │
│  "Generate      │
│   Reply"        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           Context Assembly               │
│  ┌─────────────────────────────────┐    │
│  │ 1. Conversation History         │    │
│  │ 2. Contact Information          │    │
│  │ 3. Knowledge Base Entries       │    │
│  │ 4. Studio Settings/Tone         │    │
│  └─────────────────────────────────┘    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│            LLM Registry                  │
│  ┌─────────────────────────────────┐    │
│  │ Select Provider:                │    │
│  │ - OpenAI (default)              │    │
│  │ - Anthropic                     │    │
│  │ - Gemini                        │    │
│  │ - Ollama (local)                │    │
│  └─────────────────────────────────┘    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         Agent Execution                  │
│  ┌─────────────────────────────────┐    │
│  │ SmartReplyAgent                 │    │
│  │ - System prompt with context    │    │
│  │ - Generate multiple options     │    │
│  │ - Format response               │    │
│  └─────────────────────────────────┘    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         Response to Frontend             │
│  {                                       │
│    "suggestions": [                      │
│      "Hi! Thanks for reaching out...",  │
│      "Hello! We'd love to help...",     │
│      "Great question! Our classes..."   │
│    ]                                     │
│  }                                       │
└─────────────────────────────────────────┘
```

### Lead Scoring Flow

```
┌─────────────────┐
│  New Message    │
│  or Interaction │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Lead Scoring Agent               │
│  ┌─────────────────────────────────┐    │
│  │ Analyze:                        │    │
│  │ - Message sentiment             │    │
│  │ - Engagement frequency          │    │
│  │ - Questions asked               │    │
│  │ - Intent signals                │    │
│  └─────────────────────────────────┘    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         Score Calculation                │
│  ┌─────────────────────────────────┐    │
│  │ Score: 0-100                    │    │
│  │ Factors:                        │    │
│  │ - Interest level (0-30)         │    │
│  │ - Urgency (0-25)                │    │
│  │ - Budget indicators (0-25)      │    │
│  │ - Fit score (0-20)              │    │
│  └─────────────────────────────────┘    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         Update Contact Status            │
│  ┌─────────────────────────────────┐    │
│  │ Score >= 80: HOT                │    │
│  │ Score >= 60: WARM               │    │
│  │ Score >= 40: ENGAGED            │    │
│  │ Score < 40:  NEW                │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Studio      │       │      User       │       │    Contact      │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──────│ studio_id (FK)  │       │ id (PK)         │
│ name            │       │ id (PK)         │       │ studio_id (FK)  │──┐
│ slug            │       │ email           │       │ name            │  │
│ settings (JSON) │       │ password_hash   │       │ phone           │  │
│ created_at      │       │ role            │       │ email           │  │
└─────────────────┘       │ created_at      │       │ lead_status     │  │
                          └─────────────────┘       │ lead_score      │  │
                                                    │ source          │  │
                                                    │ created_at      │  │
                                                    └─────────────────┘  │
                                                            │            │
                          ┌─────────────────────────────────┘            │
                          │                                              │
                          ▼                                              │
                 ┌─────────────────┐       ┌─────────────────┐          │
                 │  Conversation   │       │     Message     │          │
                 ├─────────────────┤       ├─────────────────┤          │
                 │ id (PK)         │◄──────│ conversation_id │          │
                 │ studio_id (FK)  │       │ id (PK)         │          │
                 │ contact_id (FK) │       │ content         │          │
                 │ channel         │       │ direction       │          │
                 │ status          │       │ channel         │          │
                 │ last_message_at │       │ status          │          │
                 │ unread_count    │       │ external_id     │          │
                 └─────────────────┘       │ created_at      │          │
                                           └─────────────────┘          │
                                                                        │
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐│
│ChannelIntegration│      │  StudioKnowledge │      │ LeadStatusHistory││
├─────────────────┤       ├─────────────────┤       ├─────────────────┤│
│ id (PK)         │       │ id (PK)         │       │ id (PK)         ││
│ studio_id (FK)  │       │ studio_id (FK)  │       │ contact_id (FK) │┘
│ channel_type    │       │ title           │       │ old_status      │
│ credentials     │       │ content         │       │ new_status      │
│ is_active       │       │ category        │       │ changed_at      │
│ webhook_secret  │       │ created_at      │       │ changed_by      │
└─────────────────┘       └─────────────────┘       └─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   DanceClass    │       │  ClassSchedule  │       │   Instructor    │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──────│ class_id (FK)   │       │ id (PK)         │
│ studio_id (FK)  │       │ id (PK)         │       │ studio_id (FK)  │
│ name            │       │ instructor_id   │──────►│ name            │
│ dance_style     │       │ day_of_week     │       │ email           │
│ level           │       │ start_time      │       │ specialties     │
│ duration_mins   │       │ end_time        │       │ availability    │
│ max_students    │       │ room            │       │ max_hours_week  │
│ instructor_id   │       │ is_recurring    │       │ is_active       │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

### Key Relationships

| Relationship | Type | Description |
|--------------|------|-------------|
| Studio → Users | One-to-Many | A studio has multiple staff users |
| Studio → Contacts | One-to-Many | A studio has multiple leads/customers |
| Contact → Conversations | One-to-Many | A contact can have conversations on multiple channels |
| Conversation → Messages | One-to-Many | A conversation contains multiple messages |
| Contact → LeadStatusHistory | One-to-Many | Track lead status changes over time |
| Studio → ChannelIntegration | One-to-Many | A studio can connect multiple channels |
| Instructor → ClassSchedule | One-to-Many | An instructor teaches multiple classes |

---

## API Design

### RESTful Endpoints

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new studio |
| POST | `/api/auth/login` | Login and get JWT |
| POST | `/api/auth/refresh` | Refresh JWT token |
| GET | `/api/auth/me` | Get current user |

#### Contacts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/contacts` | List contacts (paginated) |
| POST | `/api/contacts` | Create new contact |
| GET | `/api/contacts/{id}` | Get contact details |
| PUT | `/api/contacts/{id}` | Update contact |
| DELETE | `/api/contacts/{id}` | Delete contact |
| PUT | `/api/contacts/{id}/status` | Update lead status |

#### Conversations & Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{id}` | Get conversation with messages |
| POST | `/api/conversations/{id}/messages` | Send message |
| PUT | `/api/conversations/{id}/read` | Mark as read |

#### Integrations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/integrations/status` | Get all integration statuses |
| POST | `/api/integrations/connect/{provider}` | Start OAuth flow |
| GET | `/api/integrations/callback/{provider}` | OAuth callback |
| DELETE | `/api/integrations/disconnect/{provider}` | Disconnect channel |
| POST | `/api/integrations/webhook/{provider}` | Receive webhooks |

#### LLM & AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/llm/providers` | List available LLM providers |
| POST | `/api/llm/providers/{name}/configure` | Configure provider |
| POST | `/api/llm/smart-reply` | Generate smart reply |
| POST | `/api/llm/lead-score` | Score a lead |
| POST | `/api/llm/analyze` | Analyze conversation |

#### Scheduling
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scheduling/classes` | List classes |
| POST | `/api/scheduling/classes` | Create class |
| POST | `/api/scheduling/optimize` | Optimize schedule |
| GET | `/api/scheduling/conflicts` | Get scheduling conflicts |
| POST | `/api/scheduling/resolve-conflicts` | Auto-resolve conflicts |

### Response Format

```json
{
  "success": true,
  "data": { ... },
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  }
}
```

---

## Integration Architecture

### Channel Integration Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    BaseChannelIntegration                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Abstract Methods:                                          │  │
│  │ - connect(credentials) → OAuth URL                         │  │
│  │ - handle_callback(code) → tokens                           │  │
│  │ - send_message(to, content) → message_id                   │  │
│  │ - fetch_messages(since) → messages[]                       │  │
│  │ - handle_webhook(payload) → normalized_message             │  │
│  │ - disconnect() → void                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│WhatsAppIntegration│ │InstagramIntegration│ │GmailIntegration│
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ WhatsApp        │ │ Instagram       │ │ Gmail API       │
│ Business API    │ │ Graph API       │ │ with OAuth 2.0  │
│                 │ │                 │ │                 │
│ - Phone Number  │ │ - Instagram     │ │ - Email         │
│   ID            │ │   Business      │ │   Threading     │
│ - Message       │ │   Account       │ │ - Labels        │
│   Templates     │ │ - DM Access     │ │ - Attachments   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### LLM Provider Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                      BaseLLMProvider                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Abstract Methods:                                          │  │
│  │ - configure(api_key, **kwargs) → void                      │  │
│  │ - generate(messages, config) → LLMResponse                 │  │
│  │ - stream(messages, config) → AsyncGenerator                │  │
│  │ - get_capabilities() → LLMCapabilities                     │  │
│  │ - validate_config() → bool                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
      ┌───────────────┬───────┴───────┬───────────────┐
      │               │               │               │
      ▼               ▼               ▼               ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│  OpenAI   │  │ Anthropic │  │  Gemini   │  │  Ollama   │
│ Provider  │  │ Provider  │  │ Provider  │  │ Provider  │
├───────────┤  ├───────────┤  ├───────────┤  ├───────────┤
│ GPT-4     │  │ Claude 3  │  │ Gemini    │  │ Llama 2   │
│ GPT-3.5   │  │ Claude 2  │  │ Pro       │  │ Mistral   │
│ Embeddings│  │           │  │ Flash     │  │ CodeLlama │
└───────────┘  └───────────┘  └───────────┘  └───────────┘
```

---

## Security Architecture

### Authentication Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Client  │     │  API    │     │  JWT    │     │   DB    │
│(React)  │     │(Flask)  │     │ Service │     │         │
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │
     │ POST /login   │               │               │
     │──────────────►│               │               │
     │               │ Validate      │               │
     │               │──────────────────────────────►│
     │               │               │               │
     │               │◄──────────────────────────────│
     │               │ User data     │               │
     │               │               │               │
     │               │ Create JWT    │               │
     │               │──────────────►│               │
     │               │               │               │
     │               │◄──────────────│               │
     │               │ Signed token  │               │
     │               │               │               │
     │◄──────────────│               │               │
     │ JWT + Refresh │               │               │
     │               │               │               │
     │ GET /api/*    │               │               │
     │ (with JWT)    │               │               │
     │──────────────►│               │               │
     │               │ Verify JWT    │               │
     │               │──────────────►│               │
     │               │◄──────────────│               │
     │               │ User context  │               │
     │               │               │               │
```

### Security Measures

| Layer | Measure | Implementation |
|-------|---------|----------------|
| Transport | HTTPS | TLS 1.3 in production |
| Authentication | JWT | Short-lived access tokens (15 min) |
| Token Refresh | Refresh Token | Long-lived, rotated on use |
| Password | Bcrypt | Cost factor 12 |
| API Keys | Encryption | AES-256 for stored credentials |
| CORS | Whitelist | Strict origin validation |
| Rate Limiting | Per-user | 100 req/min default |
| Input Validation | Schema | Pydantic/Marshmallow validation |
| SQL Injection | ORM | SQLAlchemy parameterized queries |
| XSS | Sanitization | Output encoding, CSP headers |

---

## Scalability Considerations

### Current Architecture (MVP)

- **Database**: SQLite for development, PostgreSQL for production
- **Caching**: In-memory (can add Redis)
- **Background Jobs**: Synchronous (can add Celery)
- **Real-time**: Polling (can add WebSocket)

### Future Scaling Path

```
┌─────────────────────────────────────────────────────────────────┐
│                      Production Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐          │
│  │   Nginx    │     │   Nginx    │     │   Nginx    │          │
│  │   (LB)     │     │   (LB)     │     │   (LB)     │          │
│  └─────┬──────┘     └─────┬──────┘     └─────┬──────┘          │
│        │                  │                  │                  │
│        ▼                  ▼                  ▼                  │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐          │
│  │  Frontend  │     │  API Pod   │     │  Worker    │          │
│  │  (Static)  │     │  (Gunicorn)│     │  (Celery)  │          │
│  └────────────┘     └─────┬──────┘     └─────┬──────┘          │
│                           │                  │                  │
│                           ▼                  │                  │
│                    ┌────────────┐            │                  │
│                    │   Redis    │◄───────────┘                  │
│                    │  (Cache +  │                               │
│                    │   Queue)   │                               │
│                    └────────────┘                               │
│                           │                                     │
│                           ▼                                     │
│                    ┌────────────┐                               │
│                    │ PostgreSQL │                               │
│                    │  (Primary) │                               │
│                    └─────┬──────┘                               │
│                          │                                      │
│                          ▼                                      │
│                    ┌────────────┐                               │
│                    │ PostgreSQL │                               │
│                    │ (Replica)  │                               │
│                    └────────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Performance Targets

| Metric | MVP Target | Scale Target |
|--------|------------|--------------|
| API Response Time | < 200ms | < 100ms |
| Concurrent Users | 100 | 10,000 |
| Messages/day | 10,000 | 1,000,000 |
| Database Size | 1 GB | 100 GB |
| Uptime | 99% | 99.9% |

---

## Deployment

### Docker Compose (Development)

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5001:5001"
    environment:
      - DATABASE_URL=postgresql://...
      - JWT_SECRET_KEY=${JWT_SECRET}
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=studio_os
      - POSTGRES_USER=studio
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Database connection string | Yes |
| `JWT_SECRET_KEY` | Secret for JWT signing | Yes |
| `OPENAI_API_KEY` | OpenAI API key | For AI features |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Business token | For WhatsApp |
| `INSTAGRAM_CLIENT_ID` | Instagram app ID | For Instagram |
| `GMAIL_CLIENT_ID` | Google OAuth client ID | For Gmail |

---

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| Lead | A potential customer who has shown interest |
| Conversation | A thread of messages with a contact |
| Channel | A communication platform (WhatsApp, Instagram, Gmail) |
| Studio | A dance studio business entity |
| Agent | An AI-powered task handler (SmartReply, LeadScoring) |

### References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [Gmail API](https://developers.google.com/gmail/api)
- [OpenAI API](https://platform.openai.com/docs)
