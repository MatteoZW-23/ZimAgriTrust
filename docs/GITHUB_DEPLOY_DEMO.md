# Deploy Demo on GitHub (Step-by-Step)

## Option 1: Railway (Easiest - FREE)

### Step 1: Setup Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your ZimAgriTrust repository

### Step 2: Add Environment Variables
In Railway dashboard, add these:

```bash
# Database (Railway provides PostgreSQL automatically)
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Auto-generated

# Redis (Add Redis plugin)
REDIS_URL=${{Redis.REDIS_URL}}  # Auto-generated

# Secrets (Generate these)
SECRET_KEY=demo-secret-key-not-for-production-32-chars-long
REFRESH_SECRET_KEY=demo-refresh-key-not-for-production-32
PIN_PEPPER=demo-pepper-16-chars
ADMIN_BOOTSTRAP_TOKEN=demo-bootstrap-token-32-chars-long

# Demo settings
APP_ENV=development
MASTER_TEST_LOGIN_ENABLED=false
AUTO_CONFIRM_PAYMENTS=false
ADMIN_AUDIT_LOGGING=false
CORS_ORIGINS=*
ALLOWED_HOSTS=*
```

### Step 3: Deploy
Railway auto-deploys on every git push!

**Cost: FREE (up to $5 credit/month)**

---

## Option 2: Render.com (FREE Tier)

### Step 1: Create render.yaml
Create file `render.yaml` in your repo root:

```yaml
# Render.com Blueprint
services:
  # Backend API
  - type: web
    name: agritrust-api
    runtime: docker
    repo: https://github.com/YOUR_USERNAME/YOUR_REPO
    branch: main
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: agritrust-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: APP_ENV
        value: production
      - key: PORT
        value: 8000
    healthCheckPath: /health
    plan: free

  # Frontend
  - type: web
    name: agritrust-app
    runtime: static
    buildCommand: cd apps/app-portal && npm install && npm run build
    publishPath: ./apps/app-portal/dist
    envVars:
      - key: VITE_API_URL
        value: https://agritrust-api.onrender.com/api/v1
    plan: free

  # PostgreSQL Database
  - type: pserv
    name: agritrust-db
    runtime: docker
    repo: https://github.com/render-examples/postgres
    envVars:
      - key: POSTGRES_USER
        value: agritrust
      - key: POSTGRES_DB
        value: agritrust_demo
    plan: free

databases:
  - name: agritrust-db
    plan: free
```

### Step 2: Deploy on Render
1. Go to https://render.com
2. Click "Blueprint" → "New Blueprint Instance"
3. Connect your GitHub repo
4. Render reads `render.yaml` and creates all services

**Cost: FREE (Web: 750 hrs/month, DB: 90 days)**

---

## Option 3: GitHub Actions → Docker Hub → Any Server

### Step 1: Create GitHub Secrets
Go to GitHub → Settings → Secrets and variables → Actions

Add these secrets:
```
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password
RAILWAY_TOKEN=your_railway_token_if_using
```

### Step 2: Push to GitHub

```bash
# Add the workflow file I created
git add .github/workflows/deploy-demo.yml
git commit -m "Add GitHub Actions deployment"
git push origin main
```

### Step 3: Watch it Deploy
Go to GitHub → Actions tab → See deployment progress

---

## Quick Start (Recommended for You)

Since you want to launch NOW, here's the fastest way:

### 1. Push to GitHub First
```bash
cd /mnt/c/Users/MJ/desktop/agric
git add .
git commit -m "Ready for demo deployment"
git push origin main
```

### 2. Use Railway (Fastest)
1. Go to https://railway.app
2. Login with GitHub
3. New Project → Deploy from GitHub repo
4. Select your repo
5. Railway auto-detects Docker Compose!

### 3. Add These Environment Variables in Railway UI:
```bash
# Copy from .env.local and paste into Railway dashboard:
SECRET_KEY=demo-key-32-chars-not-for-production
REFRESH_SECRET_KEY=demo-refresh-32-chars-not-for-prod
PIN_PEPPER=demo-pepper-16
ADMIN_BOOTSTRAP_TOKEN=demo-bootstrap-token-32-chars

# Database (Railway auto-creates PostgreSQL)
# Just click "New" → "Database" → "Add PostgreSQL"

# Redis (Railway auto-creates Redis)
# Click "New" → "Database" → "Add Redis"
```

### 4. Deploy URL
Railway gives you a URL like:
- Backend: `https://agritrust-api.up.railway.app`
- Frontend: `https://agritrust-app.up.railway.app`

---

## Demo Limitations (FREE Tier)

| Feature | Limitation |
|---------|-----------|
| Sleep | App sleeps after 5 min inactivity (cold start ~10s) |
| Database | PostgreSQL free for 90 days on Render |
| Bandwidth | 100GB/month on Railway |
| Build time | 15 min max on free tier |
| Custom domain | Not available on free tier |

---

## Cost Summary

| Platform | Monthly Cost | Best For |
|----------|-------------|----------|
| Railway | FREE ($5 credit) | Quick demos, testing |
| Render | FREE | Longer demos, portfolio |
| Fly.io | FREE | Global edge deployment |
| Heroku | $0-7 | Simple apps |

---

## Next Steps

1. **Choose platform** (Railway recommended)
2. **Push code to GitHub**
3. **Connect platform to GitHub repo**
4. **Add environment variables**
5. **Deploy!**

**Timeline: 10-15 minutes to live demo**

Need help with any specific step?
