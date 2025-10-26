# 🚀 Complete Vercel Deployment Guide for Research-Orra

## Prerequisites

- ✅ GitHub account
- ✅ Vercel account (free) - Sign up at https://vercel.com
- ✅ Git installed on your computer
- ✅ Node.js installed (for Vercel CLI)

---

## Method 1: Deploy via Vercel Dashboard (Easiest) ⭐

### Step 1: Push Code to GitHub

```bash
# Navigate to your project
cd "/Users/manansharma/Documents/Chatbot_proptek copy/cafe-advisor"

# Initialize Git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Research-Orra deployment"

# Create a new repository on GitHub:
# Go to https://github.com/new
# Name it: research-orra
# Don't initialize with README

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/research-orra.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Vercel

1. **Go to Vercel Dashboard:**
   - Visit: https://vercel.com/dashboard
   - Click "Add New..." → "Project"

2. **Import Repository:**
   - Click "Import Git Repository"
   - Select your GitHub account
   - Find and select "research-orra"
   - Click "Import"

3. **Configure Project:**
   - **Framework Preset:** Other
   - **Root Directory:** `./` (leave as is)
   - **Build Command:** (leave empty)
   - **Output Directory:** (leave empty)
   - **Install Command:** `pip install -r requirements.txt`

4. **Add Environment Variables:**
   Click "Environment Variables" and add:
   
   ```
   OPENAI_API_KEY=sk-your-key-here
   GROQ_API_KEY=gsk_your-key-here
   SERPAPI_API_KEY=your-key-here
   ```

5. **Deploy:**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your app will be live at: `https://research-orra.vercel.app`

---

## Method 2: Deploy via Vercel CLI (Advanced)

### Step 1: Install Vercel CLI

```bash
# Install Node.js first (if not installed)
# Download from: https://nodejs.org/

# Install Vercel CLI globally
npm install -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
# Follow the prompts to authenticate
```

### Step 3: Deploy

```bash
# Navigate to your project
cd "/Users/manansharma/Documents/Chatbot_proptek copy/cafe-advisor"

# Deploy
vercel

# Answer the prompts:
# ? Set up and deploy? [Y/n] Y
# ? Which scope? (Select your account)
# ? Link to existing project? [y/N] N
# ? What's your project's name? research-orra
# ? In which directory is your code located? ./
# ? Want to override the settings? [y/N] N
```

### Step 4: Add Environment Variables

```bash
# Add environment variables
vercel env add OPENAI_API_KEY
# Paste your key when prompted

vercel env add GROQ_API_KEY
# Paste your key when prompted

vercel env add SERPAPI_API_KEY
# Paste your key when prompted
```

### Step 5: Deploy to Production

```bash
# Deploy to production
vercel --prod
```

---

## Post-Deployment Steps

### 1. Test Your Deployment

Visit your Vercel URL (e.g., `https://research-orra.vercel.app`)

Test the application:
- ✅ Homepage loads
- ✅ Enter a query: "cafe in Emporio Mohali"
- ✅ Check if analysis runs
- ✅ Verify charts display
- ✅ Check browser console for errors (F12)

### 2. Custom Domain (Optional)

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions

### 3. Monitor Logs

```bash
# View real-time logs
vercel logs

# Or in dashboard:
# Project → Deployments → Click deployment → View Function Logs
```

---

## Troubleshooting

### Issue: Build Fails

**Solution:**
```bash
# Check if requirements.txt is correct
cat requirements.txt

# Ensure vercel.json exists
cat vercel.json
```

### Issue: API Calls Fail

**Solution:**
1. Check environment variables are set
2. Go to: Project Settings → Environment Variables
3. Verify all keys are present
4. Redeploy: `vercel --prod`

### Issue: "Module not found" Error

**Solution:**
```bash
# Ensure all imports are in requirements.txt
# Check app.py imports match installed packages
```

### Issue: Timeout Errors

**Solution:**
- Vercel free tier has 10-second timeout for serverless functions
- Consider upgrading to Pro plan for 60-second timeout
- Or optimize your analysis to run faster

### Issue: Static Files Not Loading

**Solution:**
1. Check `vercel.json` routes configuration
2. Ensure files are in `static/` folder
3. Check file paths in HTML

---

## Vercel Configuration Files

### vercel.json (Already Created)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/app.py"
    },
    {
      "src": "/(.*)",
      "dest": "/static/index.html"
    }
  ]
}
```

---

## Environment Variables Reference

Add these in Vercel Dashboard → Settings → Environment Variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | ✅ Yes |
| `GROQ_API_KEY` | Groq API key | ✅ Yes |
| `SERPAPI_API_KEY` | SerpAPI key | ✅ Yes |
| `LANGCHAIN_API_KEY` | LangChain key | ⚠️ Optional |
| `LANGCHAIN_TRACING_V2` | Enable tracing | ⚠️ Optional |

---

## Deployment Checklist

Before deploying:

- [ ] Code pushed to GitHub
- [ ] `.env` file in `.gitignore`
- [ ] `requirements.txt` complete
- [ ] `vercel.json` created
- [ ] All API keys ready
- [ ] Tested locally

After deploying:

- [ ] Visit deployment URL
- [ ] Test with sample query
- [ ] Check browser console
- [ ] Verify API calls work
- [ ] Test charts display
- [ ] Check mobile responsiveness

---

## Useful Commands

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# View logs
vercel logs

# List deployments
vercel ls

# Remove deployment
vercel rm <deployment-url>

# View project info
vercel inspect

# Pull environment variables
vercel env pull
```

---

## Free Tier Limits

Vercel Free Tier includes:
- ✅ 100 GB bandwidth/month
- ✅ 100 deployments/day
- ✅ Unlimited projects
- ✅ Automatic HTTPS
- ✅ Global CDN
- ⚠️ 10-second function timeout
- ⚠️ 512 MB function memory

---

## Next Steps After Deployment

1. **Monitor Performance:**
   - Check Vercel Analytics
   - Monitor function execution time
   - Track errors in logs

2. **Optimize:**
   - Cache API responses
   - Minimize function cold starts
   - Optimize images

3. **Scale:**
   - Consider Pro plan for production
   - Add custom domain
   - Set up monitoring alerts

---

## Support

- **Vercel Docs:** https://vercel.com/docs
- **Vercel Community:** https://github.com/vercel/vercel/discussions
- **Status Page:** https://www.vercel-status.com/

---

## Quick Reference

**Deploy:** `vercel --prod`
**Logs:** `vercel logs`
**Dashboard:** https://vercel.com/dashboard
**Docs:** https://vercel.com/docs

---

🎉 **Your Research-Orra app is now live on Vercel!**
