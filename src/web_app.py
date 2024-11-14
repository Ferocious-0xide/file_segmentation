from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
import tempfile
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List
from src.database.database import DatabaseHandler
from src.segmentation.core import SegmentationProcessor
from src.database.models import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="File Segmentation Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Initialize database and processor
try:
    db_handler = DatabaseHandler()
    init_db(db_handler.engine)
    logger.info("Database tables created successfully")
    
    processor = SegmentationProcessor(db_handler)
    logger.info("Database and processor initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")
    raise

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    try:
        with open(static_path / "index.html") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="HTML template not found")

@app.post("/preview-columns")
async def preview_columns(file: UploadFile = File(...)):
    """
    Preview columns from the uploaded CSV file.
    """
    try:
        # Read first chunk of file to get columns
        chunk = await file.read(1024)  # Read first 1KB
        # Reset file pointer for future reading
        await file.seek(0)
        
        # Decode and get first line
        first_line = chunk.decode().split('\n')[0]
        columns = [col.strip() for col in first_line.split(',')]
        
        return JSONResponse(content={"columns": columns})
    except Exception as e:
        logger.error(f"Error previewing columns: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    segmentation_method: str = Form(...),
    selected_columns: str = Form(...),
    num_segments: Optional[int] = Form(None),
    segment_column: Optional[str] = Form(None)
):
    """
    Process uploaded file with enhanced segmentation options.
    
    Args:
        file: Uploaded CSV file
        segmentation_method: Either 'equal' or 'column'
        selected_columns: JSON string of selected column names
        num_segments: Number of segments for equal distribution
        segment_column: Column name for column-based segmentation
    """
    try:
        # Parse selected columns
        selected_columns = json.loads(selected_columns)
        
        # Validate inputs
        if segmentation_method not in ['equal', 'column']:
            raise HTTPException(
                status_code=400,
                detail="Invalid segmentation method"
            )
            
        if segmentation_method == 'equal' and (not num_segments or num_segments < 1):
            raise HTTPException(
                status_code=400,
                detail="Number of segments must be at least 1 for equal distribution"
            )
            
        if segmentation_method == 'column' and not segment_column:
            raise HTTPException(
                status_code=400,
                detail="Must specify segment column for column-based segmentation"
            )
            
        # Create temporary file to store upload
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
            
        try:
            # Process the file based on segmentation method
            if segmentation_method == 'equal':
                result = processor.process_file(
                    temp_path,
                    num_segments,
                    selected_columns=selected_columns
                )
            else:  # column-based
                result = processor.process_file_by_column(
                    temp_path,
                    segment_column,
                    selected_columns=selected_columns
                )
                
            return JSONResponse(content=result)
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/segment/{process_uuid}")
async def get_segment_stats(process_uuid: str):
    """Get statistics for all segments in a file process."""
    try:
        stats = processor.get_segment_stats(process_uuid)
        return JSONResponse(content=stats)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting segment stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/segment/{segment_uuid}/records")
async def get_segment_records(
    segment_uuid: str,
    page: int = 1,
    per_page: int = 100
):
    """Get records for a specific segment with pagination."""
    try:
        records = processor.get_segment_records(segment_uuid, page, per_page)
        return JSONResponse(content=records)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting segment records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)