from fastapi import FastAPI, UploadFile, File, HTTPException, Form
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
    # Initialize database tables
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

@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    num_segments: int = Form(...)
):
    """
    Process uploaded file and segment it into specified number of segments.
    
    Args:
        file: Uploaded file
        num_segments: Number of segments to create
        
    Returns:
        JSON response with processing results
    """
    try:
        # Validate number of segments
        if num_segments < 1:
            raise HTTPException(
                status_code=400,
                detail="Number of segments must be at least 1"
            )
            
        # Create temporary file to store upload
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
            
        try:
            # Process the file
            result = processor.process_file(temp_path, num_segments)
            return JSONResponse(content=result)
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/segment/{process_uuid}")
async def get_segment_stats(process_uuid: str):
    """
    Get statistics for all segments in a file process.
    
    Args:
        process_uuid: UUID of the file process
        
    Returns:
        JSON response with segment statistics
    """
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
    """
    Get records for a specific segment with pagination.
    
    Args:
        segment_uuid: UUID of the segment
        page: Page number (default: 1)
        per_page: Records per page (default: 100)
        
    Returns:
        JSON response with paginated records
    """
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