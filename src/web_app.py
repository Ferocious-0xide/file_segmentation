from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.database.database import DatabaseHandler
from src.segmentation.core import SegmentationProcessor
import tempfile
import os

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

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Initialize database and processor
db_handler = DatabaseHandler()
processor = SegmentationProcessor(db_handler)

@app.get("/")
async def root():
    """Root endpoint - serves the main page"""
    return FileResponse("src/static/index.html")

@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    num_segments: int = 5
):
    """Process uploaded file and segment it"""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_filepath = temp_file.name

        result = processor.process_file(temp_filepath, num_segments)
        
        os.unlink(temp_filepath)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/segments/{process_id}")
async def get_segments(process_id: str):
    """Get information about segments for a specific process"""
    try:
        return processor.get_segment_stats(process_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))