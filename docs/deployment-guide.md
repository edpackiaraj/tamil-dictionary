# Free Deployment Guide — Tamil Dictionary

Deploy the Tamil Dictionary for free using:
- **Railway** — Backend (FastAPI) + PostgreSQL database
- **Vercel** — Frontend (React widget)

Then embed the widget in your Blogger page.

---

## Step 1 — Deploy Backend on Railway (Free)

Railway gives you a free PostgreSQL + Python hosting tier.

### 1.1 — Create Railway account
Go to https://railway.app and sign up (free tier available).

### 1.2 — Create a new project

```
1. Click "New Project"
2. Choose "Deploy from GitHub repo"
3. Connect your GitHub and select your Tamil Dictionary repo
4. Select the /backend folder as root
```

Or use Railway CLI:
```bash
npm install -g @railway/cli
railway login
cd "Tamil Dictionary/backend"
railway init
railway up
```

### 1.3 — Add PostgreSQL

In Railway dashboard:
```
1. Click "New" → "Database" → "PostgreSQL"
2. Railway auto-sets DATABASE_URL in your environment
```

### 1.4 — Set environment variables

In Railway → Your service → Variables:
```
SECRET_KEY=your_long_random_secret_key_here
CORS_ORIGINS=["https://your-blog.blogspot.com","https://yourdomain.com"]
```

### 1.5 — Run the database schema

Connect to Railway PostgreSQL and run:
```bash
railway run psql $DATABASE_URL -f database/schema.sql
railway run psql $DATABASE_URL -f database/seed.sql
```

Or use the Railway web console to paste and run the SQL directly.

### 1.6 — Note your API URL

Railway gives you a URL like:
```
https://your-app-name.railway.app
```

This is your `API_BASE` for the frontend.

---

## Step 2 — Deploy Frontend on Vercel (Free)

### 2.1 — Prepare for Vercel

Create `Tamil Dictionary/frontend/vercel.json`:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### 2.2 — Deploy

```bash
npm install -g vercel
cd "Tamil Dictionary/frontend"
vercel
```

Follow the prompts:
```
? Set up and deploy? Yes
? Which scope? (your account)
? Link to existing project? No
? Project name: tamil-dictionary
? Directory: ./
```

### 2.3 — Set environment variable

In Vercel dashboard → Settings → Environment Variables:
```
VITE_API_BASE = https://your-app-name.railway.app
```

Then redeploy:
```bash
vercel --prod
```

Your widget URL will be:
```
https://tamil-dictionary.vercel.app
```

---

## Step 3 — Embed in Blogger

### 3.1 — Go to your Blogger post/page editor

Switch to **HTML view** and paste:

```html
<!-- Tamil Dictionary Widget -->
<link
  href="https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap"
  rel="stylesheet"
/>

<div style="max-width:900px; margin:0 auto;">
  <iframe
    src="https://tamil-dictionary.vercel.app"
    style="width:100%; min-height:700px; border:none; border-radius:12px;"
    title="Tamil Dictionary — தமிழ் அகராதி"
    loading="lazy"
  ></iframe>
</div>
```

### 3.2 — Publish

That's it! The dictionary is now embedded in your blog.

---

## Alternative: 100% Free Stack (No Railway paid tier)

| Service | What it hosts | Free limit |
|---------|--------------|------------|
| **Supabase** | PostgreSQL | 500MB, unlimited rows |
| **Render** | FastAPI backend | 750 hrs/month, sleeps after 15min |
| **Vercel** | React frontend | Unlimited |

### Using Supabase (PostgreSQL)

```
1. Go to https://supabase.com → New Project
2. Copy the connection string: postgresql://...
3. Run your schema in Supabase SQL editor
4. Use that DATABASE_URL in Render
```

### Using Render (Backend)

```
1. Go to https://render.com → New Web Service
2. Connect GitHub, select /backend folder
3. Build: pip install -r requirements.txt
4. Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
5. Add DATABASE_URL from Supabase
```

> ⚠️ Render free tier sleeps after 15 min of inactivity.
> First request after sleep takes ~30s. Acceptable for a blog dictionary.

---

## Admin Dashboard Access

After deployment, go to:
```
https://tamil-dictionary.vercel.app/#/admin
```

Login with the editor account you created via:
```bash
curl -X POST https://your-app.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Editor","email":"you@email.com","password":"secure_password"}'
```

Then update the user role to 'editor' in the database:
```sql
UPDATE users SET role = 'editor' WHERE email = 'you@email.com';
```

---

## Custom Domain (Optional)

Both Railway and Vercel support custom domains:
- Vercel: Project → Settings → Domains → Add `dict.yourdomain.com`
- Railway: Service → Settings → Domains

---

## Morphology Pre-generation (Post-deploy)

After deployment, generate all inflected forms:
```bash
railway run python scripts/generate_morphology.py
```

This makes inflected form search (வீட்டில் → வீடு) work instantly.

---

## Cost Summary

| Component | Service | Cost |
|-----------|---------|------|
| PostgreSQL | Railway / Supabase | **Free** |
| FastAPI backend | Railway / Render | **Free** |
| React frontend | Vercel | **Free** |
| Fonts | Google Fonts CDN | **Free** |
| **Total** | | **₹0 / $0** |
