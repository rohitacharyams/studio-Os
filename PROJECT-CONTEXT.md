# Studio OS - Complete Project Context & Documentation

> **Last Updated:** January 11, 2026  
> **Project Status:** ✅ LIVE IN PRODUCTION

---

## 📋 PROJECT OVERVIEW

**Studio OS** is a comprehensive SaaS platform for dance and fitness studios to manage their business operations including:
- Class scheduling and calendar management
- Customer bookings and payments
- WhatsApp and email communications
- AI-powered customer support chatbot
- Analytics and reporting
- Multi-tenant architecture (each studio is isolated)

---

## 🌐 LIVE URLs

| Environment | URL |
|-------------|-----|
| **Frontend (Netlify)** | https://studio-os.netlify.app |
| **Backend API (Azure)** | https://studioos-api.azurewebsites.net |
| **Health Check** | https://studioos-api.azurewebsites.net/health |

---

## 🔐 CREDENTIALS & ACCESS

### Platform Super Admin (Owner)
| Field | Value |
|-------|-------|
| Username | `rohitOwner` |
| Password | `StormyDusk@123` |
| Login URL | https://studio-os.netlify.app/admin/login |
| Dashboard | https://studio-os.netlify.app/admin/dashboard |

### Demo Studio Account
| Field | Value |
|-------|-------|
| Email | `admin@rhythmdance.com` |
| Password | `Admin@123` |
| Studio Name | Rhythm Dance Academy |

### Azure SQL Database
| Field | Value |
|-------|-------|
| Server | `studioos-sql-server.database.windows.net` |
| Database | `studioos_db` |
| Username | `studioos_admin` |
| Password | `StormydusK123@` |
| SKU | Basic (5 DTU) |

### Azure Container Registry (ACR)
| Field | Value |
|-------|-------|
| Registry | `studiosoacr.azurecr.io` |
| Current Image | `studio-os-api:v13` |
| SKU | Basic |

### Azure App Service
| Field | Value |
|-------|-------|
| Name | `studioos-api` |
| Resource Group | `studio-os-rg` |
| Plan | B1 (Basic, Linux) |
| Region | Central India |

### Azure Subscription
| Field | Value |
|-------|-------|
| Name | Visual Studio Enterprise Subscription |
| ID | `d8b4564f-81c5-4325-9c57-fcaef1a384fa` |

---

## 💰 MONTHLY COSTS

| Resource | Cost |
|----------|------|
| Azure SQL (Basic) | ~$5/month |
| Container Registry (Basic) | ~$5/month |
| App Service (B1 Linux) | ~$13/month |
| Groq LLM | FREE |
| Netlify Frontend | FREE |
| **TOTAL** | **~$23/month** |

---

## 🏗️ TECH STACK

### Backend
- **Framework:** Flask (Python 3.11)
- **Database:** Azure SQL Server with SQLAlchemy ORM
- **Authentication:** JWT (Flask-JWT-Extended)
- **Migrations:** Alembic (Flask-Migrate)
- **CORS:** Flask-CORS
- **Deployment:** Docker container on Azure App Service

### Frontend
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **State Management:** Zustand
- **Data Fetching:** TanStack Query (React Query)
- **Routing:** React Router v6
- **Icons:** Lucide React
- **Deployment:** Netlify (auto-deploy from GitHub)

### Third-Party Integrations
- **LLM Provider:** Groq (FREE tier) - llama3-8b-8192
- **Payments:** Razorpay
- **WhatsApp:** Twilio
- **Email:** SendGrid

---

## 📁 PROJECT STRUCTURE

```
Studio OS/
├── backend/                    # Flask API
│   ├── app/
│   │   ├── __init__.py        # App factory, blueprint registration
│   │   ├── config.py          # Environment configuration
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── user.py        # User, Studio models
│   │   │   ├── booking.py     # Booking, ClassSchedule models
│   │   │   ├── contact.py     # Contact/Customer models
│   │   │   └── ...
│   │   ├── routes/            # API endpoints
│   │   │   ├── auth.py        # Authentication
│   │   │   ├── studio.py      # Studio management
│   │   │   ├── scheduling.py  # Class schedules
│   │   │   ├── bookings.py    # Booking management
│   │   │   ├── admin.py       # Platform admin (super admin)
│   │   │   └── ...
│   │   ├── services/          # Business logic
│   │   └── llm/               # LLM providers (OpenAI, Groq, Anthropic)
│   ├── Dockerfile             # Production Docker image
│   ├── requirements.txt       # Dev dependencies
│   ├── requirements-prod.txt  # Production dependencies
│   ├── wsgi.py               # Gunicorn entry point
│   └── gunicorn.conf.py      # Gunicorn configuration
│
├── frontend/                   # React + Vite + TypeScript
│   ├── src/
│   │   ├── pages/            # Page components
│   │   │   ├── LoginPage.tsx
│   │   │   ├── CalendarPage.tsx
│   │   │   ├── BookingPage.tsx
│   │   │   ├── AdminLoginPage.tsx
│   │   │   ├── AdminDashboardPage.tsx
│   │   │   └── ...
│   │   ├── components/       # Reusable components
│   │   ├── api/              # API client (axios)
│   │   ├── store/            # Zustand state stores
│   │   └── App.tsx           # Router configuration
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml         # Local development
├── netlify.toml              # Netlify deployment config
├── AZURE-DEPLOYMENT.md       # Azure deployment docs
└── PROJECT-CONTEXT.md        # This file
```

---

## 🔌 API ENDPOINTS

### Authentication (`/api/auth`)
- `POST /api/auth/register` - Register new user/studio
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### Studio (`/api/studio`)
- `GET /api/studio` - Get studio details
- `PUT /api/studio` - Update studio settings (including media fields: photos, videos, testimonials, amenities, social_links, about)
- `POST /api/studio/onboarding` - Complete onboarding
- `GET /api/studio/public/<slug>` - Get public studio info (for booking page, includes theme_settings)
- `GET /api/studio/settings/theme` - Get theme settings
- `PUT /api/studio/settings/theme` - Update theme settings

### Scheduling (`/api/scheduling`)
- `GET /api/scheduling/classes` - List classes
- `POST /api/scheduling/classes` - Create class
- `PUT /api/scheduling/classes/<id>` - Update class
- `DELETE /api/scheduling/classes/<id>` - Delete class
- `GET /api/scheduling/sessions` - List sessions (calendar events)
- `POST /api/scheduling/sessions` - Create session
- `PUT /api/scheduling/sessions/<id>` - Update session
- `DELETE /api/scheduling/sessions/<id>` - Delete/cancel session

### Bookings (`/api/bookings`)
- `GET /api/bookings` - List bookings
- `POST /api/bookings` - Create booking
- `PUT /api/bookings/<id>` - Update booking
- `DELETE /api/bookings/<id>` - Cancel booking
- `GET /api/bookings/public/<studio_slug>` - Public booking page data

### Contacts (`/api/contacts`)
- `GET /api/contacts` - List contacts/customers
- `POST /api/contacts` - Add contact
- `PUT /api/contacts/<id>` - Update contact
- `DELETE /api/contacts/<id>` - Delete contact

### Platform Admin (`/api/admin`)
- `POST /api/admin/login` - Admin login (whitelisted users)
- `GET /api/admin/dashboard` - Platform statistics
- `GET /api/admin/studios` - List all studios
- `GET /api/admin/studios/<id>` - Studio details
- `GET /api/admin/activity` - Recent activity

### Other Endpoints
- `GET /health` - Health check
- `/api/ai/*` - AI chatbot
- `/api/analytics/*` - Analytics
- `/api/payments/*` - Payment processing
- `/api/whatsapp/*` - WhatsApp integration
- `/api/conversations/*` - Chat conversations

---

## 🚀 DEPLOYMENT COMMANDS

### Build & Deploy Backend to Azure
```powershell
# Navigate to backend
cd "C:\Users\rohitacharya\Practice\Studio OS\backend"

# Build and push Docker image (increment version)
az acr build --registry studiosoacr --image studio-os-api:v14 .

# Update web app to use new image
az webapp config container set `
  --resource-group studio-os-rg `
  --name studioos-api `
  --docker-custom-image-name studiosoacr.azurecr.io/studio-os-api:v14

# Restart app
az webapp restart --resource-group studio-os-rg --name studioos-api
```

### View Azure Logs
```powershell
az webapp log tail --resource-group studio-os-rg --name studioos-api
```

### Frontend Deployment
Frontend auto-deploys to Netlify when you push to `main` branch.

```powershell
git add -A
git commit -m "Your commit message"
git push origin main
```

---

## 🐛 RECENT BUG FIXES (January 2026)

1. **Date/Time Issues** - Fixed timezone handling for class schedules
2. **415 Error on Bookings** - Added Content-Type header to API calls
3. **Backend Session CRUD** - Implemented full create/update/delete for sessions
4. **Delete Class UI** - Added cancel class button with confirmation modal
5. **Edit Class UI** - Added edit functionality for sessions
6. **Mobile Responsive** - Made CalendarPage, PublicBookingPage, MyBookingsPage responsive

## ✨ NEW FEATURES (January 2026)

### Theme Customization & Media Management
1. **Theme Settings** - Studios can customize colors, gradients, and branding for their public booking page
   - Primary/secondary colors
   - Background gradients
   - Text colors
   - Live preview in settings
   - Applied dynamically to `/book/<slug>` page

2. **Media Gallery** - Upload and manage studio content
   - Photo gallery (image URLs)
   - Video gallery (YouTube/Vimeo URLs)
   - Testimonials with ratings
   - Studio amenities list
   - Social media links (Instagram, YouTube, Facebook)

3. **Database Migrations**
   - `003_add_theme_settings.py` - Adds `theme_settings` JSON column
   - `004_add_media_fields.py` - Adds photos, videos, testimonials, amenities, social_links, about fields

4. **Settings Page Enhancements**
   - New "Media" tab for managing photos, videos, testimonials, amenities
   - New "Theme" tab for customizing booking page colors
   - Improved UI with preview functionality

---

## ✨ FEATURES IMPLEMENTED

### For Studio Owners
- ✅ User registration and authentication
- ✅ Studio onboarding wizard
- ✅ Class management (create, edit, delete)
- ✅ Calendar view (week/month)
- ✅ Session scheduling
- ✅ Customer/contact management
- ✅ Booking management
- ✅ Payment processing (Razorpay)
- ✅ AI chatbot for customer queries
- ✅ Analytics dashboard
- ✅ WhatsApp integration
- ✅ Email templates
- ✅ Knowledge base for AI
- ✅ **Theme customization** - Customize colors for public booking page
- ✅ **Media management** - Photos, videos, testimonials, amenities
- ✅ **Social media links** - Instagram, YouTube, Facebook integration
- ✅ **About section** - Studio description and branding

### For Customers
- ✅ Public booking page (shareable link)
- ✅ Class discovery and booking
- ✅ My bookings view
- ✅ Explore studios

### For Platform Owner
- ✅ Super admin dashboard
- ✅ Platform-wide analytics
- ✅ View all studios
- ✅ Whitelisted admin authentication

---

## 📱 MOBILE RESPONSIVENESS

All main pages are mobile-responsive using Tailwind breakpoints:
- `sm:` - Small screens (640px+)
- `md:` - Medium screens (768px+)
- `lg:` - Large screens (1024px+)

---

## 🔮 FUTURE ENHANCEMENTS (Ideas)

1. **PWA Support** - Add service worker for offline access
2. **React Native App** - Native mobile app
3. **Multi-language** - i18n support
4. **Waitlist Feature** - For full classes
5. **Recurring Bookings** - Package deals
6. **Instructor Management** - Multiple instructors per studio
7. **Video Integration** - Online classes
8. **Advanced Analytics** - Revenue forecasting

---

## 🧪 LOCAL DEVELOPMENT

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop (optional)

### Backend Setup
```powershell
cd "C:\Users\rohitacharya\Practice\Studio OS"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend Setup
```powershell
cd "C:\Users\rohitacharya\Practice\Studio OS\frontend"
npm install
npm run dev
```

### Environment Variables
Backend `.env` file required with:
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `SQL_SERVER`, `SQL_DATABASE`, `SQL_USER`, `SQL_PASSWORD`
- `GROQ_API_KEY`
- `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`
- `SENDGRID_API_KEY`

---

## 📞 SUPPORT & CONTACTS

- **GitHub Repo:** https://github.com/rohitacharyams/studio-Os
- **Owner:** Rohit Acharya

---

*This document serves as the complete context for the Studio OS project. Update it when making significant changes.*
