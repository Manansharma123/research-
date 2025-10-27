"""Vercel serverless function entry point."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from app import app

# Vercel expects the app to be named 'app' or exposed as a handler
# For Vercel, we need to expose the Flask app directly
handler = app
