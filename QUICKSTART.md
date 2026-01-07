# Studio OS - Quick Start Commands

## Development (Local)

### Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

### Frontend  
```powershell
cd frontend
npm install
npm run dev
```

### Test Login
- Email: priya@rhythmdance.com
- Password: password123

---

## Production Deployment

### Prerequisites
- Azure CLI installed: `winget install Microsoft.AzureCLI`
- Vercel CLI installed: `npm i -g vercel`
- Docker installed (optional)

### Quick Deploy to Azure

```powershell
# 1. Login to Azure
az login

# 2. Create Resource Group
az group create --name studio-os-rg --location centralindia

# 3. Create PostgreSQL
az postgres flexible-server create `
  --resource-group studio-os-rg `
  --name studioos-db `
  --admin-user studioos_admin `
  --admin-password "YourSecurePassword123!" `
  --sku-name Standard_B1ms `
  --tier Burstable

# 4. Create Database
az postgres flexible-server db create `
  --resource-group studio-os-rg `
  --server-name studioos-db `
  --database-name studioos_prod

# 5. Deploy Backend
cd backend
az webapp up --resource-group studio-os-rg --name studioos-api --sku B1 --runtime "PYTHON:3.11"

# 6. Configure Environment Variables
az webapp config appsettings set --resource-group studio-os-rg --name studioos-api --settings `
  FLASK_ENV=production `
  SECRET_KEY=your-secret-key `
  DATABASE_URL="postgresql://studioos_admin:YourPassword@studioos-db.postgres.database.azure.com:5432/studioos_prod?sslmode=require"
```

### Deploy Frontend to Vercel

```powershell
cd frontend
vercel --prod
```

---

## Estimated Costs
- Azure PostgreSQL B1ms: ~$15/month
- Azure App Service B1: ~$13/month  
- Vercel: FREE
- **Total: ~$28/month**

See DEPLOYMENT.md for detailed instructions.
