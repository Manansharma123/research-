# 🚀 Production Deployment Guide - Vercel

## ✅ Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] All API keys are ready (OpenAI, Groq, SerpAPI)
- [ ] Code is tested locally
- [ ] `.env` file is in `.gitignore`
- [ ] No sensitive data in code
- [ ] Requirements.txt is complete
- [ ] Static files are in `static/` folder

---

## 📋 Files Prepared for Production

### 1. **vercel.json** ✅
- Configured for Python serverless functions
- Routes set up for API and static files
- Max Lambda size: 50MB
- Python version: 3.11
- Region: US East (iad1)

### 2. **api/index.py** ✅
- Vercel serverless function entry point
- Imports Flask app correctly

### 3. **app.py** ✅
- Production mode detection
- Debug disabled in production
- Dynamic port configuration

### 4. **requirements.txt** ✅
- All dependencies listed
- No duplicates
- Production-ready versions

### 5. **.gitignore** ✅
- Excludes `.env`, `venv/`, `__pycache__/`
- Protects sensitive data

---

## 🚀 Deployment Steps

### Step 1: Push to GitHub

```bash
cd "/Users/manansharma/Documents/Chatbot_proptek copy/cafe-advisor"

# Add all changes
git add .

# Commit
git commit -m "Production ready - Vercel deployment"

# Push to GitHub
git push origin main
```

### Step 2: Deploy to Vercel

#### Option A: Via Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Click "Add New..." → "Project"

2. **Import Repository**
   - Select your GitHub repository
   - Click "Import"

3. **Configure Project**
   - **Framework Preset:** Other
   - **Root Directory:** `./` (or `cafe-advisor` if deploying from parent)
   - **Build Command:** (leave empty)
   - **Output Directory:** (leave empty)
   - **Install Command:** `pip install -r requirements.txt`

4. **Add Environment Variables**
   
   Click "Environment Variables" and add:
   
   | Variable | Value | Environment |
   |----------|-------|-------------|
   | `OPENAI_API_KEY` | `sk-...` | Production, Preview, Development |
   | `GROQ_API_KEY` | `gsk_...` | Production, Preview, Development |
   | `SERPAPI_API_KEY` | `your-key` | Production, Preview, Development |
   | `VERCEL_ENV` | `production` | Production |

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your app will be live!

#### Option B: Via Vercel CLI

```bash
# Install Vercel CLI (if not installed)
npm install -g vercel

# Login
vercel login

# Deploy
cd "/Users/manansharma/Documents/Chatbot_proptek copy/cafe-advisor"
vercel --prod

# Add environment variables
vercel env add OPENAI_API_KEY production
vercel env add GROQ_API_KEY production
vercel env add SERPAPI_API_KEY production
```

---

## 🔧 Production Optimizations Applied

### 1. **Performance**
- ✅ Debug mode disabled in production
- ✅ Lambda size optimized (50MB limit)
- ✅ Static files served via CDN
- ✅ Gzip compression enabled

### 2. **Security**
- ✅ Environment variables for secrets
- ✅ CORS configured properly
- ✅ No sensitive data in code
- ✅ `.env` excluded from git

### 3. **Reliability**
- ✅ Health check endpoint (`/api/health`)
- ✅ Error handling in all routes
- ✅ Logging configured
- ✅ Graceful error responses

### 4. **Scalability**
- ✅ Serverless architecture
- ✅ Auto-scaling enabled
- ✅ CDN for static assets
- ✅ Regional deployment

---

## 🌐 After Deployment

### Your URLs

After deployment, you'll get:

- **Production:** `https://your-project.vercel.app`
- **API Endpoint:** `https://your-project.vercel.app/api/analyze`
- **Health Check:** `https://your-project.vercel.app/api/health`

### Testing Production

1. **Test Homepage:**
   ```bash
   curl https://your-project.vercel.app
   ```

2. **Test Health:**
   ```bash
   curl https://your-project.vercel.app/api/health
   ```

3. **Test Analysis:**
   ```bash
   curl -X POST https://your-project.vercel.app/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"query": "cafe in Emporio Mohali"}'
   ```

---

## ⚠️ Important Notes

### Vercel Limitations

**Free Tier:**
- ✅ 100 GB bandwidth/month
- ✅ 100 deployments/day
- ⚠️ **10-second function timeout** (may be tight for analysis)
- ⚠️ 512 MB function memory

**If Analysis Takes > 10 Seconds:**

You may need to:
1. **Upgrade to Pro Plan** ($20/month) - 60-second timeout
2. **Optimize analysis** - Cache results, reduce API calls
3. **Split into multiple functions** - Break analysis into steps

### Production Environment Variables

Make sure these are set in Vercel:

```env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
SERPAPI_API_KEY=...
VERCEL_ENV=production
```

### Monitoring

Monitor your deployment:
- **Vercel Dashboard:** https://vercel.com/dashboard
- **Function Logs:** Project → Deployments → Logs
- **Analytics:** Project → Analytics

---

## 🐛 Troubleshooting

### Issue: 404 Not Found

**Solution:**
- Check `vercel.json` routes
- Verify files are in correct directories
- Redeploy from Vercel dashboard

### Issue: Function Timeout

**Solution:**
- Optimize code to run faster
- Cache API responses
- Upgrade to Pro plan (60s timeout)
- Consider splitting analysis into steps

### Issue: Module Not Found

**Solution:**
- Check `requirements.txt` has all dependencies
- Verify Python version (3.11)
- Redeploy with clean build

### Issue: Environment Variables Not Working

**Solution:**
- Go to Project Settings → Environment Variables
- Add variables for all environments
- Redeploy after adding variables

---

## 📊 Performance Tips

### 1. **Caching**
- Cache SerpAPI results
- Cache geocoding results
- Use Vercel Edge Caching

### 2. **Optimization**
- Minimize API calls
- Compress responses
- Use async where possible

### 3. **Monitoring**
- Set up error tracking (Sentry)
- Monitor function duration
- Track API usage

---

## 🔄 Continuous Deployment

Vercel automatically deploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Vercel automatically deploys!
```

**Preview Deployments:**
- Every push creates a preview URL
- Test before merging to main
- Share preview links with team

---

## 📝 Quick Commands

```bash
# Deploy to production
vercel --prod

# View logs
vercel logs

# List deployments
vercel ls

# Open dashboard
vercel

# Add environment variable
vercel env add VARIABLE_NAME production

# Remove deployment
vercel rm deployment-url
```

---

## ✅ Production Checklist

Before going live:

- [ ] All environment variables added
- [ ] Tested in preview environment
- [ ] Health check endpoint works
- [ ] API endpoints respond correctly
- [ ] Static files load properly
- [ ] Charts display correctly
- [ ] Mobile responsive
- [ ] Error handling works
- [ ] Logs are clean
- [ ] Performance is acceptable

---

## 🎉 You're Ready to Deploy!

Your Research-Orra application is production-ready for Vercel deployment!

**Next Step:** Push to GitHub and deploy via Vercel Dashboard.

Good luck! 🚀
