# Deploying HardRAG API

## Quick Deploy Options

### Option 1: Railway (Recommended - FREE tier)

**Steps:**
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `hardrag-api` repository
5. Add environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_KEY`
6. Deploy!

**Cost**: Free tier ($5 credit/month)
**Domain**: Automatic (e.g., hardrag-api-production.up.railway.app)

---

### Option 2: Render (FREE tier)

**Steps:**
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect GitHub repo
4. Settings:
   - **Name**: hardrag-api
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Create Web Service

**Cost**: Free tier (spins down after 15min inactivity)

---

### Option 3: Fly.io (FREE tier)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Launch app
flyctl launch

# Set secrets
flyctl secrets set SUPABASE_URL=your-url
flyctl secrets set SUPABASE_ANON_KEY=your-key
flyctl secrets set SUPABASE_SERVICE_KEY=your-service-key

# Deploy
flyctl deploy
```

**Cost**: Free tier (3 shared CPUs, 256MB RAM)

---

### Option 4: Vercel (Serverless)

Create `vercel.json`:
```json
{
  "build": {
    "env": {
      "PYTHON_VERSION": "3.11"
    }
  },
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

Deploy:
```bash
npm i -g vercel
vercel
```

---

## Environment Variables (Required)

All platforms need these:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...
```

## Post-Deployment

### 1. Test Deployment

```bash
curl https://your-api-url.com/health
```

### 2. Update API URL in Frontend

Update your frontend to use deployed API URL.

### 3. Setup Custom Domain (Optional)

Railway: Settings → Domains → Add Custom Domain
Render: Settings → Custom Domains

### 4. Monitor

- Check logs regularly
- Monitor error rates
- Track API usage

---

## CI/CD (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          service: hardrag-api
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
```

---

## Troubleshooting

### App won't start
- Check environment variables are set
- Check logs for errors
- Verify `requirements.txt` includes all dependencies

### 500 errors
- Check Supabase connection
- Verify API keys are correct
- Check logs

### Slow responses
- Check cold start time (serverless)
- Consider upgrading plan
- Add caching

---

## Cost Estimates

| Platform | Free Tier | Paid (Basic) |
|----------|-----------|--------------|
| Railway | $5/month credit | $5/month |
| Render | Free (sleep after 15min) | $7/month |
| Fly.io | 3 shared CPU, 256MB | $1.94/month (1 dedicated CPU) |
| Vercel | 100GB bandwidth | $20/month |

**Recommendation**: Start with Railway free tier
