from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PREVIEW_DIR = "preview_files"
os.makedirs(PREVIEW_DIR, exist_ok=True)

# Preview router
preview_router = APIRouter()

@preview_router.post("/prepare/{job_id}")
async def prepare_preview(job_id: str):
    """
    Prepare a preview for a specific job by extracting its files
    to a directory that can be served statically
    """
    # Get the job results file path
    job_results_path = f"job_results/{job_id}.json"
    
    if not os.path.exists(job_results_path):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    try:
        # Load the job results
        with open(job_results_path, "r") as f:
            job_results = json.load(f)
        
        # Create a job-specific preview directory
        job_preview_dir = os.path.join(PREVIEW_DIR, job_id)
        if os.path.exists(job_preview_dir):
            # Clean up any existing preview files
            shutil.rmtree(job_preview_dir)
        
        os.makedirs(job_preview_dir, exist_ok=True)
        
        # Extract all frontend files
        if "frontend_files" in job_results:
            for filename, content in job_results["frontend_files"].items():
                # Create subdirectories if needed
                file_path = os.path.join(job_preview_dir, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write the file
                with open(file_path, "w") as f:
                    f.write(content)
        
        # Create an index.html if it doesn't exist
        index_path = os.path.join(job_preview_dir, "index.html")
        if not os.path.exists(index_path):
            # Check if there are any HTML files
            html_files = [f for f in os.listdir(job_preview_dir) if f.endswith(".html")]
            
            if html_files:
                # Use the first HTML file as index
                shutil.copy(
                    os.path.join(job_preview_dir, html_files[0]),
                    index_path
                )
            else:
                # Create a minimal index file
                with open(index_path, "w") as f:
                    f.write("""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>App Preview</title>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    </head>
                    <body>
                        <h1>App Preview</h1>
                        <p>This is a preview of your generated app.</p>
                        <div id="app"></div>
                        
                        <!-- Load any JS files -->
                        <script src="index.js"></script>
                    </body>
                    </html>
                    """)
        
        return {"success": True, "preview_url": f"/preview/{job_id}/"}
        
    except Exception as e:
        logger.error(f"Error preparing preview for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to prepare preview: {str(e)}")

def setup_preview_server(app: FastAPI):
    """
    Configure the FastAPI app to serve preview files
    """
    # Add the preview router
    app.include_router(preview_router, prefix="/api/preview", tags=["preview"])
    
    # Mount the static file server
    app.mount("/preview", StaticFiles(directory=PREVIEW_DIR, html=True), name="preview")
    
    return app
