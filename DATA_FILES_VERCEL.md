# 📊 Data Files for Vercel Deployment

## ✅ Changes Made for Your Data Files

Your application uses CSV files and SQLite databases in the `data/` folder. Here's what was configured:

### 📁 Your Data Files

```
data/
├── property_project_lat_long.csv      ✅ Will deploy
├── dummy_property_variables.csv       ✅ Will deploy
├── aligned_dummy_property_variables.csv ✅ Will deploy
├── city_businesses.csv                ✅ Will deploy
├── establishments.csv                 ✅ Will deploy
├── nearby_places.db                   ✅ Will deploy (READ-ONLY)
├── serp_api_data.db                   ✅ Will deploy (READ-ONLY)
└── test_rate_limit_cache.json         ✅ Will deploy
```

---

## 🔧 Configuration Changes

### 1. `.gitignore` Updated ✅

**Added exceptions for data files:**
```gitignore
# Database
*.db
*.sqlite
*.sqlite3

# But allow data folder databases (needed for deployment)
!data/*.db
!data/*.sqlite
!data/*.sqlite3
```

This ensures:
- ✅ Data folder databases ARE committed to Git
- ✅ Other random .db files are still ignored
- ✅ Your data will be deployed to Vercel

### 2. `.vercelignore` Updated ✅

**Added explicit includes:**
```
# Keep data files - they're needed for deployment
!data/*.csv
!data/*.db
```

This ensures:
- ✅ CSV files are included in deployment
- ✅ Database files are included in deployment

---

## ⚠️ Important: Database Limitations on Vercel

### SQLite Databases are READ-ONLY

**What this means:**
- ✅ You CAN read from `.db` files
- ❌ You CANNOT write to `.db` files
- ❌ You CANNOT update/insert/delete data

**Why?**
- Vercel serverless functions run in a read-only filesystem
- Each function invocation gets a fresh copy
- Changes don't persist between requests

### Your Current Databases

**1. `nearby_places.db` (483 KB)**
- ✅ Can be used for lookups
- ⚠️ Cannot cache new places during runtime

**2. `serp_api_data.db` (1.05 MB)**
- ✅ Can be used for cached API responses
- ⚠️ Cannot save new API responses during runtime

---

## 🔄 Recommended Solutions

### Option 1: Keep Databases Read-Only (Simplest)

**For cached data that doesn't change often:**

```python
# This will work - reading from database
def get_cached_data(place_id):
    conn = sqlite3.connect('data/nearby_places.db')
    result = conn.execute("SELECT * FROM places WHERE id=?", (place_id,))
    return result.fetchone()
```

**Pre-populate databases before deployment:**
1. Run your app locally
2. Let it cache data in the databases
3. Commit the updated `.db` files
4. Deploy to Vercel

### Option 2: Use External Database (Recommended for Production)

**For data that needs to be updated:**

Use a cloud database service:
- **Vercel Postgres** (Free tier available)
- **Supabase** (Free tier available)
- **PlanetScale** (Free tier available)
- **MongoDB Atlas** (Free tier available)

**Benefits:**
- ✅ Read AND write operations
- ✅ Persistent across deployments
- ✅ Shared across all function invocations
- ✅ Better for production

### Option 3: Use Vercel KV (Key-Value Store)

**For simple caching:**

```bash
# Install Vercel KV
pip install vercel-kv
```

```python
from vercel_kv import kv

# Store data
await kv.set('key', 'value')

# Retrieve data
value = await kv.get('key')
```

**Benefits:**
- ✅ Fast caching
- ✅ Persistent storage
- ✅ Free tier: 256 MB storage

---

## 📝 What You Need to Do

### Before Deployment

**1. Check Database Usage**

Review your code to see if databases are used for:
- ✅ **Reading only** → No changes needed
- ⚠️ **Writing/caching** → Consider external database

**2. Commit Data Files**

```bash
# Check if data files are tracked
git status

# If not tracked, add them
git add data/*.csv
git add data/*.db

# Commit
git commit -m "Add data files for deployment"
```

**3. Verify File Sizes**

Vercel has a 50MB limit per serverless function:

```bash
# Check sizes
ls -lh data/

# Your current sizes:
# nearby_places.db: 483 KB ✅ OK
# serp_api_data.db: 1.05 MB ✅ OK
# Total: ~1.5 MB ✅ Well under limit
```

---

## 🧪 Testing Database Access

### Local Test

```python
import sqlite3
import os

# Test database access
db_path = os.path.join('data', 'nearby_places.db')
print(f"Database exists: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Try reading
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables: {tables}")

conn.close()
```

### Production Test (After Deployment)

Add a test endpoint to `app.py`:

```python
@app.route('/api/test-db', methods=['GET'])
def test_db():
    """Test database access."""
    import sqlite3
    import os
    
    try:
        db_path = os.path.join('data', 'nearby_places.db')
        exists = os.path.exists(db_path)
        
        if exists:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()
            
            return jsonify({
                'success': True,
                'database_exists': True,
                'table_count': table_count,
                'path': db_path
            })
        else:
            return jsonify({
                'success': False,
                'database_exists': False,
                'path': db_path
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
```

Then test: `https://your-app.vercel.app/api/test-db`

---

## ✅ Summary

### What Works on Vercel

✅ **CSV Files** - Full read/write (in memory only)
✅ **SQLite Databases** - Read-only access
✅ **JSON Files** - Read-only access
✅ **Small data files** - Under 50MB total

### What Doesn't Work

❌ **Database writes** - Filesystem is read-only
❌ **File uploads** - No persistent storage
❌ **Large files** - Over 50MB limit

### Your Setup

✅ **All your data files are under 2MB** - Perfect!
✅ **CSV files work perfectly** - No issues
✅ **Databases can be used for lookups** - Read-only is fine
⚠️ **If you need to cache new data** - Consider external DB

---

## 🚀 Ready to Deploy!

Your data files are now properly configured for Vercel deployment. Just:

1. ✅ Commit the changes
2. ✅ Push to GitHub
3. ✅ Deploy to Vercel
4. ✅ Test database access

Your CSV and database files will be included in the deployment and accessible to your application! 🎉
