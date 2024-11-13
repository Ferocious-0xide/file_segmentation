from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path
from src.database.database import DatabaseHandler
from src.segmentation.core import SegmentationProcessor

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
db_handler = DatabaseHandler()
processor = SegmentationProcessor(db_handler)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serves the main page"""
    html_file = static_dir / "index.html"
    with open(html_file, "r") as f:
        return f.read()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))