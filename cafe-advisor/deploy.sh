#!/bin/bash

# Research-Orra Vercel Deployment Script
# This script automates the deployment process

echo "🚀 Research-Orra Deployment Script"
echo "===================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo ""
    echo "❌ Vercel CLI not found!"
    echo "📥 Installing Vercel CLI..."
    npm install -g vercel
    echo "✅ Vercel CLI installed"
fi

echo ""
echo "📋 Pre-deployment checklist:"
echo "  1. Have you added your API keys to .env?"
echo "  2. Have you tested the app locally?"
echo "  3. Are you ready to deploy?"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Add all files
echo ""
echo "📦 Adding files to Git..."
git add .

# Commit
echo "💾 Committing changes..."
git commit -m "Deploy to Vercel - $(date '+%Y-%m-%d %H:%M:%S')"

# Check if remote exists
if git remote | grep -q origin; then
    echo "✅ Git remote exists"
    echo "📤 Pushing to GitHub..."
    git push origin main
else
    echo ""
    echo "⚠️  No Git remote found!"
    echo "Please create a GitHub repository and add it as remote:"
    echo ""
    echo "  git remote add origin https://github.com/YOUR_USERNAME/research-orra.git"
    echo "  git push -u origin main"
    echo ""
fi

# Deploy to Vercel
echo ""
echo "🚀 Deploying to Vercel..."
echo ""

vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Visit your Vercel dashboard to see the deployment"
echo "  2. Add environment variables if not already added"
echo "  3. Test your live application"
echo ""
echo "🎉 Your app is live!"
