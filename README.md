# 🎭 Studio Operations OS

**A unified inbox and operations platform for dance studios**

Studio Operations OS helps dance studio owners manage customer communications, leads, and class scheduling from a single dashboard. Connect your WhatsApp, Instagram, and Email to receive all messages in one place, use AI to draft smart replies, score leads, and optimize your class schedule.

---

## 🌟 Features

### 📥 Unified Inbox
- **Multi-channel support**: WhatsApp Business, Instagram DM, Gmail
- **Single conversation view**: All messages from a contact in one thread
- **Real-time sync**: Webhooks for instant message delivery
- **Reply from anywhere**: Send messages back through original channel

### 👥 Lead Management
- **Lead status tracking**: NEW → CONTACTED → QUALIFIED → TRIAL_SCHEDULED → CONVERTED
- **Lead scoring**: AI-powered scoring based on conversation analysis
- **Contact enrichment**: Automatic contact creation from incoming messages
- **Status history**: Track lead progression over time

### 🤖 AI-Powered Features
- **Smart Reply**: AI drafts contextual responses using your knowledge base
- **Lead Scoring**: Automatic lead qualification based on conversation
- **Conversation Analysis**: Extract insights, interests, and action items
- **Multiple LLM Support**: OpenAI, Anthropic Claude, Google Gemini, Ollama (local)

### 📅 Class Scheduling
- **Constraint-based optimization**: Auto-schedule considering instructor availability and room capacity
- **Conflict detection**: Identify double-bookings and capacity issues
- **Suggestions**: AI suggests optimal times for new classes
- **Instructor management**: Track specialties and availability

### 📊 Analytics Dashboard
- **Message metrics**: Messages received/sent per day
- **Lead conversion**: Track conversion rates
- **Response times**: Monitor average response times
- **Channel breakdown**: See which channels drive most engagement

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Docker & Docker Compose

### Local Development Setup

#### 1. Clone and Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

Create `backend/.env`:

```env
# Database (SQLite for local dev)
DATABASE_URL=sqlite:///studio_os.db

# JWT Secret (generate a random string)
JWT_SECRET_KEY=your-super-secret-key-change-in-production

# OpenAI (for AI features)
OPENAI_API_KEY=sk-your-openai-key

# Optional: Other LLM providers
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-ai-key

# Optional: Channel integrations (see Integration Setup section)
WHATSAPP_APP_ID=your-meta-app-id
WHATSAPP_APP_SECRET=your-meta-app-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### 3. Initialize Database

```bash
cd backend

# Create tables
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# Seed demo data (optional but recommended)
python seed_data.py
```

#### 4. Start Backend

```bash
python run.py
# Backend runs on http://localhost:5001
```

#### 5. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:5001/api" > .env

# Start development server
npm run dev
# Frontend runs on http://localhost:5173
```

#### 6. Access the Application

Open **http://localhost:5173** in your browser.

---

## 🏗️ System Architecture

For a comprehensive understanding of the system design, including:
- **High-level architecture diagrams**
- **Data flow diagrams** (message ingestion, smart reply, lead scoring)
- **Database schema & entity relationships**
- **API design patterns**
- **Security architecture**
- **Scalability considerations**

📖 **See [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) for the complete system design document.**

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     STUDIO OS PLATFORM                          │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React + Vite)                                        │
│  ├── Inbox, Contacts, Analytics, Settings, Scheduling Views    │
│  └── React Context for state management                        │
├─────────────────────────────────────────────────────────────────┤
│  Backend (Flask + SQLAlchemy)                                   │
│  ├── REST API Layer (Blueprints)                               │
│  ├── Service Layer (Integration Manager, LLM Registry)         │
│  └── Data Layer (SQLite/PostgreSQL)                            │
├─────────────────────────────────────────────────────────────────┤
│  External Services                                              │
│  ├── WhatsApp Business API                                     │
│  ├── Instagram Graph API                                       │
│  ├── Gmail API                                                 │
│  └── LLM Providers (OpenAI, Anthropic, Gemini, Ollama)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
studio-os/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # App factory & blueprint registration
│   │   ├── config.py             # Configuration classes
│   │   ├── models/               # SQLAlchemy models
│   │   │   └── __init__.py       # All database models
│   │   ├── routes/               # API endpoints
│   │   │   ├── auth.py           # Authentication (register, login)
│   │   │   ├── conversations.py  # Conversation management
│   │   │   ├── contacts.py       # Contact & lead management
│   │   │   ├── ai.py             # AI endpoints (legacy)
│   │   │   ├── llm.py            # LLM provider management
│   │   │   ├── integrations.py   # Channel connections
│   │   │   └── scheduling.py     # Class scheduling
│   │   ├── services/             # Business logic services
│   │   ├── integrations/         # Channel integrations
│   │   │   ├── base.py           # Abstract base interface
│   │   │   ├── whatsapp.py       # WhatsApp Business API
│   │   │   ├── instagram.py      # Instagram Graph API
│   │   │   ├── gmail.py          # Gmail API
│   │   │   └── manager.py        # Integration orchestration
│   │   ├── llm/                  # LLM providers
│   │   │   ├── base.py           # Provider interface
│   │   │   ├── openai_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   ├── ollama_provider.py
│   │   │   └── registry.py       # Agent configuration
│   │   └── scheduling/           # Scheduling optimization
│   │       ├── optimizer.py      # Constraint solver
│   │       ├── generator.py      # Schedule generator
│   │       └── conflict_resolver.py
│   ├── run.py                    # Application entry point
│   ├── seed_data.py              # Demo data generator
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── pages/                # Page components
│   │   ├── services/             # API service layer
│   │   └── App.jsx               # Root component
│   └── package.json
│
├── docker-compose.yml            # Docker services
└── README.md                     # This file
```

---

## 🔌 API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user and studio |
| `/api/auth/login` | POST | Login and receive JWT token |
| `/api/auth/me` | GET | Get current user info |

**Register Example:**
```json
POST /api/auth/register
{
    "email": "owner@studio.com",
    "password": "securepassword",
    "first_name": "John",
    "last_name": "Doe",
    "studio_name": "Rhythm Dance Studio"
}
```

### Conversations & Messages

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/conversations` | GET | List all conversations |
| `/api/conversations/{id}` | GET | Get conversation with messages |
| `/api/messages` | POST | Send a new message |

### Contacts & Leads

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/contacts` | GET | List all contacts |
| `/api/contacts` | POST | Create new contact |
| `/api/contacts/{id}` | PUT | Update contact details |
| `/api/contacts/{id}/status` | PUT | Update lead status |

### AI & LLM Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/llm/providers` | GET | List available LLM providers |
| `/api/llm/agents` | GET | List configured AI agents |
| `/api/llm/agents/{name}/configure` | POST | Configure an agent |
| `/api/llm/smart-reply` | POST | Generate smart reply |
| `/api/llm/lead-score` | POST | Score a lead |
| `/api/llm/analyze` | POST | Analyze conversation |
| `/api/llm/invoke/{agent}` | POST | Invoke any agent directly |
| `/api/llm/test` | POST | Test LLM provider |

**Configure Agent Example:**
```json
POST /api/llm/agents/smart_reply/configure
{
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.7,
    "max_tokens": 500
}
```

**Smart Reply Example:**
```json
POST /api/llm/smart-reply
{
    "conversation_id": "uuid-here",
    "additional_context": "Customer is interested in evening classes"
}
```

### Channel Integrations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/integrations/status` | GET | Get all integration statuses |
| `/api/integrations/connect/{channel}` | POST | Start OAuth connection flow |
| `/api/integrations/disconnect/{channel}` | POST | Disconnect a channel |
| `/api/integrations/sync` | POST | Manually sync messages |
| `/api/integrations/send` | POST | Send message via channel |

### Class Scheduling

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scheduling/classes` | GET/POST | Manage class definitions |
| `/api/scheduling/rooms` | GET/POST | Manage studio rooms |
| `/api/scheduling/instructors` | GET | List instructors |
| `/api/scheduling/instructors/{id}/availability` | POST | Set availability |
| `/api/scheduling/schedule` | GET/POST | View/create schedule |
| `/api/scheduling/optimize` | POST | Run schedule optimization |
| `/api/scheduling/optimize/save` | POST | Save optimized schedule |
| `/api/scheduling/suggest` | POST | Get time suggestions |
| `/api/scheduling/conflicts` | GET | Check for conflicts |

**Optimization Example:**
```json
POST /api/scheduling/optimize
{
    "opening_time": "09:00",
    "closing_time": "21:00",
    "max_concurrent_classes": 3,
    "prefer_beginners_in_peak": true
}
```

---

## 🤖 LLM Configuration

### Supported Providers

| Provider | Models | Features |
|----------|--------|----------|
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo | Chat, Functions, Embeddings |
| **Anthropic** | claude-3-opus, claude-3-sonnet, claude-3-haiku | Chat, Tools |
| **Google Gemini** | gemini-1.5-pro, gemini-1.5-flash, gemini-pro | Chat, Functions, Embeddings |
| **Ollama** | llama3, mistral, codellama, etc. | Local models, Chat, Embeddings |

### AI Agents

| Agent | Purpose | Default |
|-------|---------|---------|
| `smart_reply` | Generate contextual conversation replies | gpt-4o-mini |
| `lead_scoring` | Score leads 0-100 based on conversation | gpt-4o-mini |
| `conversation_analysis` | Extract insights and action items | gpt-4o-mini |
| `scheduling` | Optimize class schedules | gpt-4o |

### Using Local Models (Ollama)

```bash
# 1. Install Ollama (https://ollama.com)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model
ollama pull llama3

# 3. Configure agent via API
curl -X POST http://localhost:5001/api/llm/agents/smart_reply/configure \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"provider": "ollama", "model": "llama3"}'
```

---

## 📱 Channel Integration Setup

### WhatsApp Business API

1. Create a [Meta Business Account](https://business.facebook.com/)
2. Go to [Meta Developers](https://developers.facebook.com/) and create an App
3. Add the WhatsApp product to your app
4. Get your Phone Number ID and generate an access token
5. Configure webhook URL: `https://your-domain.com/api/integrations/webhook/whatsapp`
6. Add to `.env`:
   ```
   WHATSAPP_APP_ID=your-app-id
   WHATSAPP_APP_SECRET=your-app-secret
   WHATSAPP_VERIFY_TOKEN=your-custom-verify-token
   ```

### Instagram Messaging

1. Connect Instagram Professional Account to a Facebook Page
2. Add Instagram permissions to your Meta App:
   - `instagram_basic`
   - `instagram_manage_messages`
   - `pages_messaging`
3. Configure webhook: `https://your-domain.com/api/integrations/webhook/instagram`

### Gmail Integration

1. Create a [Google Cloud Project](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Create OAuth 2.0 credentials (Web Application type)
4. Add authorized redirect URI: `https://your-domain.com/api/integrations/callback/email`
5. Add to `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

---

## 📅 Class Scheduling System

### How Optimization Works

The scheduling optimizer uses **constraint satisfaction** with **greedy assignment**:

**Hard Constraints (Must Satisfy):**
- Instructors can only teach their specialties
- Instructors must be available at the scheduled time
- Rooms must have sufficient capacity
- No double-booking of instructors or rooms
- Classes must fit within operating hours

**Soft Constraints (Scoring):**
- Preferred time slots (+20 points)
- Beginner classes in peak hours (+15 points)
- Good room size fit (+10 points)
- Instructor continuity on same day (+5 per class)

### Setup Steps

```bash
# 1. Create class definitions
POST /api/scheduling/classes
{
    "name": "Salsa Basics",
    "dance_style": "salsa",
    "level": "Beginner",
    "duration_minutes": 60,
    "max_capacity": 20,
    "min_capacity": 3
}

# 2. Add studio rooms
POST /api/scheduling/rooms
{
    "name": "Main Studio",
    "capacity": 30,
    "features": ["mirrors", "sound_system", "sprung_floor"]
}

# 3. Set instructor availability
POST /api/scheduling/instructors/{instructor_id}/availability
{
    "availability": [
        {"day_of_week": 0, "start_time": "17:00", "end_time": "21:00"},
        {"day_of_week": 1, "start_time": "17:00", "end_time": "21:00"},
        {"day_of_week": 2, "start_time": "17:00", "end_time": "21:00"}
    ]
}

# 4. Run optimization
POST /api/scheduling/optimize

# 5. Review and save
POST /api/scheduling/optimize/save
```

---

## 🐳 Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5001:5001"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/studio_os
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=studio_os
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop
docker-compose down
```

---

## 🧪 Testing the API

```bash
# Test backend health
curl http://localhost:5001/health

# Register a user
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","first_name":"Test","last_name":"User","studio_name":"Test Studio"}'

# Login
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'

# Use the returned token for authenticated requests
curl http://localhost:5001/api/conversations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🛠️ Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Activate virtual environment: `.\venv\Scripts\Activate.ps1`
- Install dependencies: `pip install -r requirements.txt`
- Check `.env` file exists and has required values

### Database errors
- Create tables: `python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"`
- For SQLite, ensure the path is writable

### AI features not working
- Check `OPENAI_API_KEY` is set in `.env`
- Verify API key is valid: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

### Port conflicts
- Default ports: Backend 5001, Frontend 5173
- Change backend port: Edit `PORT` in `.env` or `run.py`
- Change frontend port: `npm run dev -- --port 3000`

---

## 📈 Roadmap

- [ ] Payment integration (Stripe for class bookings)
- [ ] Student portal (view schedule, book classes)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics & reporting
- [ ] Multi-language support
- [ ] SMS channel integration (Twilio)
- [ ] Calendar sync (Google Calendar, Outlook)
- [ ] Automated follow-up sequences

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 💬 Support

For questions or issues, please open a GitHub issue.

---

Built with ❤️ for dance studios everywhere
