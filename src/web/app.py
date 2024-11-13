from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database.database import DatabaseHandler
from segmentation.core import SegmentationProcessor
import tempfile
import os

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database handler
db_handler = DatabaseHandler()
processor = SegmentationProcessor(db_handler)

@app.get("/")
async def root():
    return {"status": "ok", "message": "File Segmentation Service"}

@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    num_segments: int = 5
):
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_filepath = temp_file.name

        # Process file
        result = processor.process_file(temp_filepath, num_segments)
        
        # Clean up
        os.unlink(temp_filepath)
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/segments/{process_id}")
async def get_segments(process_id: str):
    try:
        return processor.get_segment_stats(process_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)