"""ASGI wrapper for Flask app to run with Uvicorn."""

from asgiref.wsgi import WsgiToAsgi
from app import app
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Convert Flask WSGI app to ASGI
asgi_app = WsgiToAsgi(app)

logger.info("ASGI wrapper initialized for Flask app")
