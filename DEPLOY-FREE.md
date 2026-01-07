# 🚀 STUDIO OS - FREE DEPLOYMENT (Deploy Today!)

## Total Cost: $0/month 💰

This guide helps you deploy Studio OS completely FREE to share with potential customers.

---

## ⚡ Quick Deploy Steps (15 minutes)

### Step 1: Create FREE PostgreSQL Database (Neon.tech)

1. Go to [neon.tech](https://neon.tech) → Sign up free
2. Create new project: `studio-os`
3. Copy your connection string:
   ```
   postgresql://neondb_owner:xxx@ep-xxx.ap-south-1.aws.neon.tech/neondb?sslmode=require
   ```
4. **Save this!** You'll need it for backend.

**Free Tier Limits:**
- 0.5 GB storage (plenty for starting)
- 1 project
- Unlimited databases

---

### Step 2: Get FREE Groq API Key (AI)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up / Login with Google
3. Go to **API Keys** → Create new key
4. **Save the key!** Starts with `gsk_`

**Free Tier:**
- 30 requests/minute
- 6000 tokens/minute
- Uses Llama 3.3 70B (very good!)

---

### Step 3: Deploy Backend to Render.com (FREE)

1. Go to [render.com](https://render.com) → Sign up free
2. Connect your GitHub account
3. Click **New +** → **Web Service**
4. Connect your `studio-os` repository
5. Configure:
   - **Name:** `studio-os-api`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements-prod.txt`
   - **Start Command:** `gunicorn wsgi:app`
   - **Plan:** Free

6. Add Environment Variables:
   ```
   FLASK_ENV=production
   SECRET_KEY=generate-random-string-here
   JWT_SECRET_KEY=another-random-string
   DATABASE_URL=postgresql://... (from Neon)
   GROQ_API_KEY=gsk_... (from Groq)
   RAZORPAY_KEY_ID=rzp_test_xxx
   RAZORPAY_KEY_SECRET=test_xxx
   CORS_ORIGINS=https://your-app.netlify.app
   ```

7. Click **Create Web Service**
8. Wait 5-10 minutes for deployment
9. Your API URL: `https://studio-os-api.onrender.com`

**Free Tier Limits:**
- Sleeps after 15 min inactivity (wakes in ~30s)
- 750 hours/month (enough for demo)

---

### Step 4: Deploy Frontend to Netlify (FREE)

1. Go to [netlify.com](https://netlify.com) → Sign up free
2. Click **Add new site** → **Import from Git**
3. Connect GitHub → Select `studio-os` repo
4. Configure:
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `frontend/dist`

5. Add Environment Variables (Site Settings → Environment):
   ```
   VITE_API_URL=https://studio-os-api.onrender.com
   VITE_RAZORPAY_KEY_ID=rzp_test_xxx
   ```

6. Click **Deploy site**
7. Your frontend URL: `https://random-name.netlify.app`

**Free Tier Limits:**
- 100 GB bandwidth/month
- 300 build minutes/month
- Unlimited sites

---

### Step 5: Initialize Database

After backend is deployed, run migrations:

```bash
# Option 1: Via Render Shell
# Go to Render Dashboard → Your Service → Shell
python -c "from app import create_app, db; app = create_app('production'); ctx = app.app_context(); ctx.push(); db.create_all(); print('Done!')"

# Option 2: Run seed data
python scripts/seed_data.py
```

---

### Step 6: Test Everything! ✅

1. Open your Netlify URL
2. Login with: `priya@rhythmdance.com` / `password123`
3. Check:
   - [ ] Dashboard loads
   - [ ] Classes show up
   - [ ] AI reply suggestions work (uses Groq)
   - [ ] Booking flow works

---

## 🔗 Share with Customers

Your shareable URLs:
- **Dashboard:** `https://your-app.netlify.app`
- **Public Booking:** `https://your-app.netlify.app/book/rhythm-dance-studio`

---

## 📈 When to Upgrade?

Upgrade when you get paying customers:

| Trigger | Upgrade To | Cost |
|---------|------------|------|
| Database > 0.5GB | Neon Pro | $19/month |
| Need 24/7 uptime | Render Starter | $7/month |
| Custom domain | Buy domain | $10-15/year |
| More AI calls | Groq paid | Pay per use |

---

## 🛠 Troubleshooting

### Backend not starting?
- Check Render logs
- Verify DATABASE_URL is correct
- Make sure requirements-prod.txt exists

### CORS errors?
- Update `CORS_ORIGINS` in Render to include your Netlify URL
- Include both `https://` and no trailing slash

### AI not responding?
- Check GROQ_API_KEY is set
- Verify at console.groq.com you have API access

### Database connection fails?
- Neon requires `?sslmode=require` in connection string
- Check IP allowlist (Neon allows all by default)

---

## 🎉 You're Live!

Share your booking link with potential dance studio owners:

> "Hey! I built a studio management tool with AI. Check it out:
> https://your-app.netlify.app/book/rhythm-dance-studio
> 
> Want me to set it up for your studio?"

When they say yes, create their studio in the database and give them login access!
