# Research-Orra Deployment Guide

## Netlify Deployment

### Option 1: Deploy Static HTML (Recommended for Frontend Only)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Connect to Netlify:**
   - Go to [Netlify](https://app.netlify.com/)
   - Click "Add new site" → "Import an existing project"
   - Connect your GitHub repository
   - Configure build settings:
     - **Build command:** (leave empty)
     - **Publish directory:** `static`
   - Click "Deploy site"

3. **Configure Environment Variables:**
   - Go to Site settings → Environment variables
   - Add your API keys:
     - `OPENAI_API_KEY`
     - `GROQ_API_KEY`
     - `SERPAPI_API_KEY`

### Option 2: Deploy with Backend (Netlify Functions)

**Note:** The current Flask backend won't work on Netlify directly. You need to:

1. Convert Flask API to Netlify Functions
2. Or deploy backend separately (Heroku, Railway, Render)
3. Update API_URL in HTML to point to backend

### Backend Deployment Options

#### Option A: Railway.app
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### Option B: Render.com
1. Create account on Render.com
2. New → Web Service
3. Connect GitHub repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `python app.py`

#### Option C: Heroku
```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku

# Login and create app
heroku login
heroku create research-orra-api
git push heroku main
```

### Update Frontend API URL

After deploying backend, update `static/index.html`:

```javascript
// Change from:
const API_URL = 'http://localhost:8080/api';

// To:
const API_URL = 'https://your-backend-url.com/api';
```

## Environment Variables Required

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Groq
GROQ_API_KEY=gsk_...

# SerpAPI
SERPAPI_API_KEY=...

# Optional
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true
```

## Files for Deployment

- ✅ `.gitignore` - Ignore sensitive files
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version
- ✅ `netlify.toml` - Netlify configuration
- ✅ `static/` - Frontend files
- ✅ `.env.example` - Environment template

## Pre-Deployment Checklist

- [ ] All API keys added to environment variables
- [ ] `.env` file is in `.gitignore`
- [ ] Backend deployed and accessible
- [ ] Frontend API_URL updated
- [ ] Test deployment locally
- [ ] Check CORS settings
- [ ] Verify all dependencies in requirements.txt

## Testing Deployment

1. **Local test:**
   ```bash
   python app.py
   # Visit http://localhost:8080
   ```

2. **Production test:**
   - Visit your Netlify URL
   - Test a query
   - Check browser console for errors
   - Verify API calls work

## Troubleshooting

### Issue: API calls fail
- Check CORS settings
- Verify backend URL is correct
- Check environment variables

### Issue: Charts not displaying
- Verify Chart.js CDN is accessible
- Check browser console for errors

### Issue: Build fails
- Check Python version compatibility
- Verify all dependencies are in requirements.txt
- Check for syntax errors

## Support

For issues, check:
- Netlify build logs
- Browser console (F12)
- Backend logs
- Network tab in DevTools
