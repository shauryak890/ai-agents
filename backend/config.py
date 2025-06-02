import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Server settings
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# Ollama settings
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")

# Feature flags
ENABLE_AGENT_LOGS = os.getenv("ENABLE_AGENT_LOGS", "true").lower() == "true"
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

logger.info(f"Configured with OLLAMA_HOST={OLLAMA_HOST}, OLLAMA_MODEL={OLLAMA_MODEL}")
logger.info(f"Mock data mode: {USE_MOCK_DATA}")
