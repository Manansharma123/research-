# 🚀 GitHub Setup Guide - Fresh Repository

## ✅ Pre-Push Checklist Completed

- ✅ Old `.git` folder removed
- ✅ Backup files cleaned up
- ✅ `.gitignore` configured properly
- ✅ Server tested and working
- ✅ All features functional

---

## 📋 Step-by-Step GitHub Push Instructions

### **Step 1: Create New GitHub Repository**

1. Go to [GitHub.com](https://github.com)
2. Click **"New Repository"** (green button)
3. Fill in details:
   - **Repository name:** `cafe-advisor` (or your preferred name)
   - **Description:** `AI-powered business feasibility analysis tool using Perplexity AI, OpenAI, and real-time web scraping`
   - **Visibility:** Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

---

### **Step 2: Install Git (if not already installed)**

Download and install Git from: https://git-scm.com/download/win

After installation, verify:
```bash
git --version
```

---

### **Step 3: Configure Git (First Time Only)**

Open PowerShell in your project folder and run:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

### **Step 4: Initialize Git Repository**

In your project folder (`cafe-advisor`), run:

```bash
# Initialize new git repository
git init

# Check status
git status
```

**Expected Output:**
```
Initialized empty Git repository in .../cafe-advisor/.git/
```

---

### **Step 5: Add All Files**

```bash
# Add all files (respecting .gitignore)
git add .

# Verify what will be committed
git status
```

**Files that SHOULD be added:**
- ✅ All `.py` files
- ✅ `requirements.txt`
- ✅ `.gitignore`
- ✅ `README.md`
- ✅ `static/` folder (HTML, CSS, JS)
- ✅ `data/` folder (CSV, DB files)
- ✅ `config/` folder
- ✅ `agents/` folder
- ✅ `utils/` folder

**Files that should NOT be added (auto-ignored):**
- ❌ `venv/` folder
- ❌ `.env` file
- ❌ `__pycache__/` folders
- ❌ `*.pyc` files
- ❌ Backup files

---

### **Step 6: Create First Commit**

```bash
git commit -m "Initial commit: AI-powered business feasibility analysis tool

Features:
- Perplexity AI for intelligent recommendations and brand classification
- OpenAI for chart generation
- Real-time web scraping (Booking.com, Swiggy.com, Edustoke.com)
- Professional source citations
- 3km radius for nearby businesses and amenities
- Property analysis from Proptek Database
- Demographics and sentiment analysis
- Interactive web interface"
```

---

### **Step 7: Add Remote Repository**

Replace `YOUR_USERNAME` and `REPO_NAME` with your actual GitHub username and repository name:

```bash
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Verify remote
git remote -v
```

**Example:**
```bash
git remote add origin https://github.com/manan/cafe-advisor.git
```

---

### **Step 8: Push to GitHub**

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

**If prompted for credentials:**
- Username: Your GitHub username
- Password: Use a **Personal Access Token** (not your GitHub password)

**To create a Personal Access Token:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "cafe-advisor-push")
4. Select scopes: `repo` (full control of private repositories)
5. Click "Generate token"
6. Copy the token and use it as password

---

### **Step 9: Verify on GitHub**

1. Go to your repository on GitHub
2. Refresh the page
3. You should see all your files uploaded

---

## 🔒 Security Checklist

Before pushing, verify these are NOT in your repository:

```bash
# Search for API keys in code
git log -p | grep -i "api_key"
git log -p | grep -i "sk-"
git log -p | grep -i "pplx-"

# Check .env is ignored
git status --ignored | grep ".env"
```

**Expected:** `.env` should appear in ignored files, NOT in tracked files.

---

## 📝 Environment Variables Setup (For Others)

After pushing, create a `.env.example` file for others to use:

```bash
# Create example env file
echo "SERPAPI_KEY=your_serpapi_key_here
OPENAI_API_KEY=your_openai_key_here
FOURSQUARE_API_KEY=your_foursquare_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
SERPER_API_KEY=your_serper_key_here" > .env.example

# Add and commit
git add .env.example
git commit -m "Add environment variables example file"
git push
```

---

## 🎯 Post-Push Tasks

### 1. **Update README.md**

Make sure your README includes:
- Project description
- Features list
- Installation instructions
- Environment variables setup
- Usage examples
- API requirements

### 2. **Add GitHub Topics**

On GitHub repository page:
- Click "⚙️ Settings"
- Add topics: `ai`, `perplexity`, `openai`, `web-scraping`, `business-analysis`, `python`, `flask`

### 3. **Create Releases (Optional)**

Tag your first version:
```bash
git tag -a v1.0.0 -m "Initial release with Perplexity AI integration"
git push origin v1.0.0
```

---

## 🔄 Future Updates

When you make changes:

```bash
# Check what changed
git status

# Add changed files
git add .

# Commit with descriptive message
git commit -m "feat: Add new feature description"

# Push to GitHub
git push
```

**Commit Message Conventions:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

---

## ⚠️ Common Issues & Solutions

### Issue 1: "Permission denied (publickey)"

**Solution:** Use HTTPS instead of SSH or set up SSH keys

```bash
# Check current remote
git remote -v

# If using SSH, switch to HTTPS
git remote set-url origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

### Issue 2: "Failed to push some refs"

**Solution:** Pull first, then push

```bash
git pull origin main --rebase
git push origin main
```

### Issue 3: Large files error

**Solution:** Check file sizes and add to .gitignore

```bash
# Find large files
Get-ChildItem -Recurse | Where-Object {$_.Length -gt 50MB} | Select-Object FullName, Length

# Add to .gitignore
echo "large_file.db" >> .gitignore
git add .gitignore
git commit -m "Update gitignore for large files"
```

---

## 📊 Repository Statistics

After pushing, your repository will contain:

**Languages:**
- Python (primary)
- HTML/CSS/JavaScript (frontend)
- SQL (database queries)

**Key Features:**
- ✅ Perplexity AI integration
- ✅ OpenAI integration
- ✅ Web scraping (Selenium)
- ✅ Real-time data analysis
- ✅ Interactive web interface
- ✅ Professional source citations

**File Structure:**
```
cafe-advisor/
├── agents/           # AI agents and workflow
├── config/           # Configuration files
├── data/             # Property and demographics data
├── static/           # Frontend files
├── utils/            # Utility functions and API clients
├── .gitignore        # Git ignore rules
├── requirements.txt  # Python dependencies
├── README.md         # Project documentation
└── asgi.py          # Server entry point
```

---

## ✅ Final Verification

After pushing, verify:

1. ✅ All files visible on GitHub
2. ✅ No `.env` file in repository
3. ✅ No API keys in code
4. ✅ README.md displays correctly
5. ✅ .gitignore working properly
6. ✅ Repository description set
7. ✅ Topics added

---

## 🎉 Success!

Your code is now on GitHub! 

**Repository URL:** `https://github.com/YOUR_USERNAME/REPO_NAME`

**Next Steps:**
1. Share the repository link
2. Add collaborators if needed
3. Set up GitHub Actions for CI/CD (optional)
4. Create project documentation
5. Add license file

---

## 📞 Need Help?

If you encounter any issues:
1. Check the error message carefully
2. Search on Google or Stack Overflow
3. Check GitHub documentation
4. Ask in GitHub Community forums

**Common Resources:**
- [GitHub Docs](https://docs.github.com)
- [Git Documentation](https://git-scm.com/doc)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

---

**Last Updated:** 2025-10-27
**Status:** Ready to push! 🚀
