from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import tempfile
import logging
from pathlib import Path
from src.database.database import DatabaseHandler
from src.segmentation.core import SegmentationProcessor
from src.database.models import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="File Segmentation Service")

# Initialize database and processor
try:
    db_handler = DatabaseHandler()
    # Initialize database tables
    init_db(db_handler.engine)
    logger.info("Database tables created successfully")
    
    processor = SegmentationProcessor(db_handler)
    logger.info("Database and processor initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")
    raise

# Rest of your web_app.py code remains the same...