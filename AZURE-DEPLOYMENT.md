# Studio OS - Azure Deployment Documentation

> **Last Updated:** January 7, 2026  
> **Status:** ✅ LIVE at https://studioos-api.azurewebsites.net

---

## 🔐 CREDENTIALS & SECRETS (KEEP SECURE!)

### Azure Subscription
| Field | Value |
|-------|-------|
| Subscription Name | Visual Studio Enterprise Subscription |
| Subscription ID | `d8b4564f-81c5-4325-9c57-fcaef1a384fa` |
| Logged in as | rohitacharya |

### Azure SQL Database
| Field | Value |
|-------|-------|
| Server Name | `studioos-sql-server.database.windows.net` |
| Database Name | `studioos_db` |
| Admin Username | `studioos_admin` |
| Admin Password | `StormydusK123@` |
| SKU | Basic (5 DTU) |
| Estimated Cost | ~$5/month |
| Location | Central India |

**Connection String:**
```
Driver={ODBC Driver 18 for SQL Server};Server=tcp:studioos-sql-server.database.windows.net,1433;Database=studioos_db;Uid=studioos_admin;Pwd=StormydusK123@;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
```

### Azure Container Registry (ACR)
| Field | Value |
|-------|-------|
| Registry Name | `studiosoacr` |
| Login Server | `studiosoacr.azurecr.io` |
| Username | `studiosoacr` |
| Password | `<get-from-azure-portal>` |
| SKU | Basic |
| Estimated Cost | ~$5/month |

### Azure App Service (Web App)
| Field | Value |
|-------|-------|
| Web App Name | `studioos-api` |
| URL | https://studioos-api.azurewebsites.net |
| App Service Plan | `studioos-plan` |
| Plan SKU | B1 (Basic, Linux) |
| Estimated Cost | ~$13/month |
| Container Image | `studiosoacr.azurecr.io/studio-os-api:v13` |

### Demo Login Credentials
| Field | Value |
|-------|-------|
| Admin Email | `admin@rhythmdance.com` |
| Admin Password | `Admin@123` |
| Studio Name | Rhythm Dance Academy |

### Platform Super Admin (Whitelisted)
| Field | Value |
|-------|-------|
| Username | `rohitOwner` |
| Password | `StormyDusk@123` |
| Login URL | https://studio-os.netlify.app/admin/login |
| Dashboard URL | https://studio-os.netlify.app/admin/dashboard |

### LLM Provider (FREE)
| Field | Value |
|-------|-------|
| Provider | Groq (FREE Tier) |
| Model | `llama3-8b-8192` |
| API Key | Get from https://console.groq.com |
| Cost | **FREE** |

---

## 💰 MONTHLY COST SUMMARY

| Resource | Cost |
|----------|------|
| Azure SQL (Basic) | ~$5/month |
| Container Registry (Basic) | ~$5/month |
| App Service (B1 Linux) | ~$13/month |
| Groq LLM | FREE |
| **TOTAL** | **~$23/month** |

---

## 🏗️ AZURE RESOURCES CREATED

### Resource Group
```
Name: studio-os-rg
Location: Central India
```

### All Resources in Resource Group
1. **studioos-sql-server** - SQL Server
2. **studioos_db** - SQL Database  
3. **studioos-plan** - App Service Plan
4. **studioos-api** - Web App (Container)
5. **studiosoacr** - Container Registry

---

## 📁 PROJECT STRUCTURE

```
Studio OS/
├── backend/                    # Flask API (Python 3.11)
│   ├── app/
│   │   ├── __init__.py        # App factory with blueprints
│   │   ├── config.py          # Environment configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic
│   │   └── llm/               # LLM providers (OpenAI, Groq)
│   ├── Dockerfile             # Production Docker image
│   ├── requirements.txt       # Dev dependencies
│   ├── requirements-prod.txt  # Production dependencies
│   ├── wsgi.py               # Gunicorn entry point
│   └── gunicorn.conf.py      # Gunicorn configuration
│
├── frontend/                   # React + Vite + TypeScript
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/       # Reusable components
│   │   ├── api/              # API client
│   │   └── store/            # Zustand state
│   └── package.json
│
└── AZURE-DEPLOYMENT.md        # This file
```

---

## 🚀 DEPLOYMENT STEPS (COMPLETE HISTORY)

### Step 1: Login to Azure CLI
```powershell
az login
# Selected: Visual Studio Enterprise Subscription
```

### Step 2: Create Resource Group
```powershell
az group create --name studio-os-rg --location centralindia
```

### Step 3: Create Azure SQL Server
```powershell
az sql server create \
  --name studioos-sql-server \
  --resource-group studio-os-rg \
  --location centralindia \
  --admin-user studioos_admin \
  --admin-password "StormydusK123@"
```

### Step 4: Create SQL Database
```powershell
az sql db create \
  --resource-group studio-os-rg \
  --server studioos-sql-server \
  --name studioos_db \
  --service-objective Basic
```

### Step 5: Configure Firewall for Azure Services
```powershell
az sql server firewall-rule create \
  --resource-group studio-os-rg \
  --server studioos-sql-server \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Step 6: Create App Service Plan
```powershell
az appservice plan create \
  --name studioos-plan \
  --resource-group studio-os-rg \
  --is-linux \
  --sku B1
```

### Step 7: Create Web App
```powershell
az webapp create \
  --resource-group studio-os-rg \
  --plan studioos-plan \
  --name studioos-api \
  --runtime "PYTHON:3.11"
```

### Step 8: Configure Environment Variables
```powershell
az webapp config appsettings set \
  --resource-group studio-os-rg \
  --name studioos-api \
  --settings \
    FLASK_ENV=production \
    SECRET_KEY="super-secret-key-change-in-production-xyz123" \
    SQL_SERVER="studioos-sql-server.database.windows.net" \
    SQL_DATABASE="studioos_db" \
    SQL_USER="studioos_admin" \
    SQL_PASSWORD="StormydusK123@" \
    REDIS_URL="redis://localhost:6379/0" \
    GROQ_API_KEY="your-groq-api-key" \
    DEFAULT_LLM_PROVIDER="groq" \
    DEFAULT_LLM_MODEL="llama3-8b-8192"
```

### Step 9: Create Container Registry
```powershell
az acr create \
  --resource-group studio-os-rg \
  --name studiosoacr \
  --sku Basic \
  --admin-enabled true
```

### Step 10: Build & Push Docker Image
```powershell
cd backend
az acr build --registry studiosoacr --image studio-os-api:v1 .
```

### Step 11: Configure Web App to Use Container
```powershell
az webapp config container set \
  --resource-group studio-os-rg \
  --name studioos-api \
  --docker-custom-image-name studiosoacr.azurecr.io/studio-os-api:v1 \
  --docker-registry-server-url https://studiosoacr.azurecr.io \
  --docker-registry-server-user studiosoacr \
  --docker-registry-server-password "<get-from-azure-portal>"
```

### Step 12: Restart Web App
```powershell
az webapp restart --resource-group studio-os-rg --name studioos-api
```

---

## ✅ LIVE ENDPOINTS

### Health Check
```
GET https://studioos-api.azurewebsites.net/health
Response: {"service":"studio-os-api","status":"healthy"}
```

### API Endpoints (All prefixed with /api/)
| Endpoint | Description |
|----------|-------------|
| `/api/auth/*` | Authentication (login, register, logout) |
| `/api/studio/*` | Studio settings & management |
| `/api/scheduling/*` | Class schedules |
| `/api/bookings/*` | Class bookings |
| `/api/payments/*` | Payment processing |
| `/api/contacts/*` | Contact/student management |
| `/api/whatsapp/*` | WhatsApp integration |
| `/api/conversations/*` | Chat conversations |
| `/api/messages/*` | Messages |
| `/api/ai/*` | AI assistant |
| `/api/llm/*` | LLM provider management |
| `/api/analytics/*` | Analytics & reports |

---

## 🔄 REDEPLOYMENT COMMANDS

### Update Code & Redeploy
```powershell
# 1. Navigate to backend
cd "C:\Users\rohitacharya\Practice\Studio OS\backend"

# 2. Build new image (increment version)
az acr build --registry studiosoacr --image studio-os-api:v2 .

# 3. Update web app to use new image
az webapp config container set \
  --resource-group studio-os-rg \
  --name studioos-api \
  --docker-custom-image-name studiosoacr.azurecr.io/studio-os-api:v2

# 4. Restart
az webapp restart --resource-group studio-os-rg --name studioos-api
```

### View Logs
```powershell
az webapp log tail --resource-group studio-os-rg --name studioos-api
```

### Check Container Status
```powershell
az webapp show --resource-group studio-os-rg --name studioos-api --query "state"
```

---

## 🗄️ DATABASE INITIALIZATION

### Option 1: Via API Endpoint (Recommended)
Create an init endpoint or use Flask shell via Azure console.

### Option 2: Connect Locally with Azure Data Studio
1. Download Azure Data Studio
2. Connect to `studioos-sql-server.database.windows.net`
3. Use credentials above
4. Run SQL scripts

### Option 3: Add Your IP to Firewall
```powershell
# Get your public IP
$myIP = (Invoke-WebRequest -Uri "https://api.ipify.org").Content

# Add firewall rule
az sql server firewall-rule create \
  --resource-group studio-os-rg \
  --server studioos-sql-server \
  --name MyIP \
  --start-ip-address $myIP \
  --end-ip-address $myIP
```

---

## 🎨 FRONTEND DEPLOYMENT (PENDING)

### Option 1: Netlify (Recommended - FREE)
1. Push code to GitHub
2. Connect repo to Netlify
3. Set build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
4. Set environment variable:
   - `VITE_API_URL=https://studioos-api.azurewebsites.net`

### Option 2: Vercel (FREE)
1. Push code to GitHub
2. Import to Vercel
3. Set environment variable:
   - `VITE_API_URL=https://studioos-api.azurewebsites.net`

### Option 3: Azure Static Web Apps (FREE Tier)
```powershell
az staticwebapp create \
  --name studioos-frontend \
  --resource-group studio-os-rg \
  --source https://github.com/YOUR_REPO \
  --location centralindia \
  --branch main \
  --app-location "/frontend" \
  --output-location "dist"
```

---

## 🔧 TROUBLESHOOTING

### Container Won't Start
```powershell
# Check container logs
az webapp log download --resource-group studio-os-rg --name studioos-api

# SSH into container
az webapp ssh --resource-group studio-os-rg --name studioos-api
```

### Database Connection Issues
1. Check firewall rules allow Azure services
2. Verify connection string format
3. Check SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD env vars

### CORS Issues
Update `CORS_ORIGINS` in config or environment:
```powershell
az webapp config appsettings set \
  --resource-group studio-os-rg \
  --name studioos-api \
  --settings CORS_ORIGINS="https://your-frontend-domain.com"
```

---

## 📊 MONITORING

### Azure Portal
- https://portal.azure.com
- Navigate to `studio-os-rg` resource group
- Check metrics, logs, and alerts

### Enable Application Insights (Optional)
```powershell
az monitor app-insights component create \
  --app studioos-insights \
  --location centralindia \
  --resource-group studio-os-rg
```

---

## 🧹 CLEANUP (Delete Everything)

⚠️ **WARNING: This will delete ALL resources and data!**

```powershell
az group delete --name studio-os-rg --yes --no-wait
```

---

## 📝 NOTES

1. **Why Docker Deployment?**
   - Standard GitHub deployment failed due to path issues (Oryx build system)
   - Docker gives full control over the environment and paths
   - ODBC driver for Azure SQL requires specific system packages

2. **Why Azure SQL instead of PostgreSQL?**
   - Azure SQL Basic tier is cheaper (~$5/month vs ~$15/month for PostgreSQL)
   - Better integration with Azure ecosystem
   - Enterprise-grade features included

3. **Why Groq for LLM?**
   - FREE tier available
   - Fast inference
   - Compatible with OpenAI API format
   - Good models (Llama 3, Mixtral)

---

## 🎯 NEXT STEPS

- [x] Initialize database tables ✅
- [x] Seed test data (studio, users, classes) ✅
- [ ] Deploy frontend to Netlify
- [ ] Configure custom domain (optional)
- [ ] Set up CI/CD pipeline (optional)
- [ ] Enable Application Insights monitoring (optional)

---

**Document Version:** 1.0  
**Created:** January 7, 2026  
**Author:** GitHub Copilot + Rohit Acharya
