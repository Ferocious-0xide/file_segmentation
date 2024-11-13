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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="File Segmentation Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory containing the static files
static_dir = Path(__file__).parent / "static"

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize database and processor
try:
    db_handler = DatabaseHandler()
    processor = SegmentationProcessor(db_handler)
    logger.info("Database and processor initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")
    raise

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serves the main page"""
    try:
        html_file = static_dir / "index.html"
        with open(html_file, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    num_segments: int = 5
):
    """Process uploaded file and segment it"""
    logger.info(f"Processing file: {file.filename} with {num_segments} segments")
    temp_filepath = None
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            temp_filepath = temp_file.name
            content = await file.read()
            temp_file.write(content)
            logger.info(f"Temporary file created at: {temp_filepath}")

        # Process the file
        logger.info("Starting file processing")
        result = processor.process_file(temp_filepath, num_segments)
        logger.info("File processing completed successfully")
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temporary file
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.unlink(temp_filepath)
                logger.info("Temporary file cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")

@app.get("/segments/{process_id}")
async def get_segments(process_id: str):
    """Get information about segments for a specific process"""
    try:
        logger.info(f"Retrieving segments for process: {process_id}")
        return processor.get_segment_stats(process_id)
    except Exception as e:
        logger.error(f"Error retrieving segments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with db_handler.session_scope() as session:
            session.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)