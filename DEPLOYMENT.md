# 🚀 STUDIO OS - PRODUCTION DEPLOYMENT GUIDE

## Quick Start (15-20 minutes)

This guide will help you deploy Studio OS to production with:
- **Backend**: Azure App Service ($13/month)
- **Database**: Azure PostgreSQL Flexible ($15-25/month)  
- **Frontend**: Vercel (FREE)
- **Total Cost**: ~$30-40/month

---

## 📋 Prerequisites

1. **Azure Account** - [Create free](https://azure.microsoft.com/free/)
2. **Vercel Account** - [Sign up free](https://vercel.com/signup)
3. **Domain Name** - GoDaddy/Namecheap (~$10-15/year)
4. **Razorpay Account** - [Sign up](https://dashboard.razorpay.com/signup)
5. **Git** - Code pushed to GitHub/GitLab

---

## 🗄️ Step 1: Create Azure PostgreSQL Database (5 min)

### Option A: Azure Portal (Easy)

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → Search "Azure Database for PostgreSQL Flexible Server"
3. Click **Create**
4. Fill in:
   - **Subscription**: Your subscription
   - **Resource Group**: `studio-os-rg` (create new)
   - **Server name**: `studioos-db` (must be unique)
   - **Region**: Central India (or closest to users)
   - **PostgreSQL version**: 15
   - **Workload type**: Development (cheapest)
   - **Compute + storage**: Burstable B1ms (~$15/month)
   - **Admin username**: `studioos_admin`
   - **Password**: Generate strong password, SAVE IT!
5. **Networking tab**:
   - Allow public access: Yes
   - Add your IP address
   - Check "Allow Azure services"
6. Click **Review + Create** → **Create**

### Option B: Azure CLI (Fast)

```bash
# Login to Azure
az login

# Create resource group
az group create --name studio-os-rg --location centralindia

# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group studio-os-rg \
  --name studioos-db \
  --location centralindia \
  --admin-user studioos_admin \
  --admin-password "YourStrongPassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0

# Create the database
az postgres flexible-server db create \
  --resource-group studio-os-rg \
  --server-name studioos-db \
  --database-name studioos_prod
```

### 📝 Save Your Connection String
```
postgresql://studioos_admin:YourPassword@studioos-db.postgres.database.azure.com:5432/studioos_prod?sslmode=require
```

---

## 🔧 Step 2: Deploy Backend to Azure App Service (10 min)

### Create App Service

1. In Azure Portal → **Create a resource** → **Web App**
2. Fill in:
   - **Resource Group**: `studio-os-rg`
   - **Name**: `studioos-api` (will be studioos-api.azurewebsites.net)
   - **Publish**: Docker Container
   - **OS**: Linux
   - **Region**: Same as database
   - **App Service Plan**: Create new, B1 Basic (~$13/month)
3. **Docker tab**:
   - Options: Single Container
   - Image Source: Docker Hub or Azure Container Registry
   - Image: `your-dockerhub/studio-os-api:latest` (or build from source)

### Deploy from Local (using Azure CLI)

```bash
# Navigate to backend folder
cd backend

# Build and push Docker image
docker build -t studio-os-api .
docker tag studio-os-api:latest yourregistry.azurecr.io/studio-os-api:latest
docker push yourregistry.azurecr.io/studio-os-api:latest

# Or deploy directly from source code
az webapp up --resource-group studio-os-rg --name studioos-api --sku B1 --runtime "PYTHON:3.11"
```

### Configure Environment Variables

In Azure Portal → Your App Service → **Configuration** → **Application settings**:

Add these settings:
```
FLASK_ENV=production
SECRET_KEY=your-super-secret-random-string
DATABASE_URL=postgresql://studioos_admin:password@studioos-db.postgres.database.azure.com:5432/studioos_prod?sslmode=require
JWT_SECRET_KEY=another-secret-key
RAZORPAY_KEY_ID=rzp_live_xxx
RAZORPAY_KEY_SECRET=xxx
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Run Database Migrations

```bash
# SSH into App Service or use Kudu console
az webapp ssh --resource-group studio-os-rg --name studioos-api

# Inside the container
flask db upgrade
```

---

## 🌐 Step 3: Deploy Frontend to Vercel (5 min)

### Option A: GitHub Integration (Recommended)

1. Push your code to GitHub
2. Go to [Vercel](https://vercel.com/new)
3. **Import Git Repository** → Select your repo
4. **Configure Project**:
   - Framework: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. **Environment Variables**:
   ```
   VITE_API_URL=https://studioos-api.azurewebsites.net
   VITE_RAZORPAY_KEY_ID=rzp_live_xxx
   ```
6. Click **Deploy**

### Option B: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend
cd frontend

# Deploy
vercel --prod
```

Your frontend will be live at: `your-project.vercel.app`

---

## 🌍 Step 4: Setup Custom Domain (5 min)

### Buy a Domain
- **GoDaddy**: godaddy.com
- **Namecheap**: namecheap.com  
- **Google Domains**: domains.google

Example: `rhythmdancestudio.com` (~₹800/year)

### Configure DNS

Add these DNS records:

| Type | Name | Value |
|------|------|-------|
| A | @ | Vercel IP (76.76.21.21) |
| CNAME | www | cname.vercel-dns.com |
| CNAME | api | studioos-api.azurewebsites.net |

### Add Domain to Vercel

1. Vercel Dashboard → Your Project → **Settings** → **Domains**
2. Add your domain
3. Vercel auto-configures SSL

### Add Domain to Azure App Service

1. Azure Portal → App Service → **Custom domains**
2. Add custom domain: `api.yourdomain.com`
3. Validate and add
4. Azure provides free SSL certificate

---

## 💳 Step 5: Setup Razorpay Production (5 min)

1. Login to [Razorpay Dashboard](https://dashboard.razorpay.com)
2. Complete KYC verification
3. Go to **Settings** → **API Keys**
4. Generate **Live Keys** (not Test)
5. Update environment variables:
   - Backend: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`
   - Frontend: `VITE_RAZORPAY_KEY_ID`

### Setup Webhook

1. Razorpay Dashboard → **Webhooks**
2. Add webhook URL: `https://api.yourdomain.com/api/payments/webhook`
3. Select events:
   - `payment.authorized`
   - `payment.captured`
   - `payment.failed`
   - `order.paid`
4. Copy webhook secret → Update `RAZORPAY_WEBHOOK_SECRET`

---

## 📱 Step 6: Setup WhatsApp Business (Optional)

### Option A: Twilio (Easier)

1. Sign up at [Twilio](https://twilio.com)
2. Get a WhatsApp-enabled number ($1/month + per message)
3. Configure in Twilio Console → Messaging → WhatsApp Senders
4. Set webhook URL: `https://api.yourdomain.com/api/whatsapp/webhook`

### Option B: Meta Business (Free, Complex)

1. Create [Meta Business Account](https://business.facebook.com)
2. Apply for WhatsApp Business API access
3. Takes 2-4 weeks for approval
4. More cost-effective for high volume

---

## ✅ Step 7: Verify Everything Works

### Test Checklist

- [ ] Frontend loads at `https://yourdomain.com`
- [ ] Login works with test credentials
- [ ] API calls succeed (check Network tab)
- [ ] Create a test booking
- [ ] Razorpay payment popup opens
- [ ] Complete a test payment
- [ ] Booking confirmation received

### Create First Admin User

```bash
# SSH into Azure App Service
az webapp ssh --resource-group studio-os-rg --name studioos-api

# Run Python shell
python
>>> from app import create_app, db
>>> from app.models import User, Studio
>>> app = create_app('production')
>>> with app.app_context():
...     studio = Studio(name="Your Studio", slug="your-studio")
...     db.session.add(studio)
...     user = User(
...         email="you@email.com",
...         name="Your Name",
...         role="owner",
...         studio=studio
...     )
...     user.set_password("your-password")
...     db.session.add(user)
...     db.session.commit()
```

---

## 🔒 Security Checklist

- [ ] All secrets in environment variables (not code)
- [ ] CORS only allows your domain
- [ ] SSL/HTTPS enabled everywhere
- [ ] Database not publicly accessible (firewall rules)
- [ ] Strong admin passwords
- [ ] Rate limiting enabled
- [ ] Regular backups configured

---

## 📊 Monitoring (Optional but Recommended)

### Sentry for Error Tracking (Free tier)

1. Sign up at [Sentry](https://sentry.io)
2. Create Flask project
3. Get DSN and add to environment: `SENTRY_DSN=xxx`

### Azure Monitor

1. Azure Portal → App Service → **Monitoring**
2. Enable Application Insights
3. View logs, metrics, and alerts

---

## 💰 Cost Summary

| Service | Monthly Cost |
|---------|-------------|
| Azure PostgreSQL (B1ms) | ~$15 |
| Azure App Service (B1) | ~$13 |
| Vercel (Hobby) | FREE |
| Domain | ~$1 (yearly) |
| **Total** | **~$28-30/month** |

---

## 🆘 Troubleshooting

### API returns 500 errors
- Check Azure App Service logs: **Log stream**
- Verify DATABASE_URL is correct
- Run migrations: `flask db upgrade`

### CORS errors
- Update `CORS_ORIGINS` in Azure settings
- Include `https://` in origins

### Payment fails
- Check Razorpay dashboard for errors
- Verify webhook secret matches
- Test with Razorpay test keys first

### WhatsApp not working
- Verify Twilio credentials
- Check webhook URL is accessible
- View Twilio console for errors

---

## 🎉 You're Live!

Congratulations! Your Studio OS is now live and ready for real bookings.

**Next Steps:**
1. Share booking link with students
2. Set up your class schedule
3. Configure pricing
4. Start accepting payments!

Need help? Check the docs or raise an issue on GitHub.
