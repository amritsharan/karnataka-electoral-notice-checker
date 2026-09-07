#!/usr/bin/env python
"""
Celery worker startup script.

Usage:
  python worker.py
  
Or with specific options:
  celery -A app.celery_app worker --loglevel=info --concurrency=4
  celery -A app.celery_app worker --loglevel=info --pool=solo  (for Windows)
"""
import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.celery_app import celery_app
from app.config import settings

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting Celery worker")
    logger.info(f"Broker: {settings.CELERY_BROKER_URL}")
    logger.info(f"Result Backend: {settings.CELERY_RESULT_BACKEND_URL}")
    
    # Start the worker with default settings
    # Note: On Windows, use pool=solo
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--pool=solo",  # Use solo pool for Windows compatibility
    ])
