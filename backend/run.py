"""
Script to run the FastAPI server with proper configuration options
"""
import uvicorn
import os
from dotenv import load_dotenv
from config import PORT, HOST, logger

def main():
    """Run the FastAPI server"""
    logger.info("Starting the AI Agents App Builder backend server")
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info",
    )

if __name__ == "__main__":
    main()
