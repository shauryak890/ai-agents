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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "wizardcoder")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "3600"))  # Default 60 minutes timeout

# Agent-specific model settings - using the same model for all agents by default
# but allowing for different models per agent role
AGENT_MODELS = {
    "planner": os.getenv("PLANNER_MODEL", OLLAMA_MODEL),
    "frontend": os.getenv("FRONTEND_MODEL", OLLAMA_MODEL),
    "backend": os.getenv("BACKEND_MODEL", OLLAMA_MODEL),
    "tester": os.getenv("TESTER_MODEL", OLLAMA_MODEL),
    "deployment": os.getenv("DEPLOYMENT_MODEL", OLLAMA_MODEL),
    "analyzer": os.getenv("ANALYZER_MODEL", OLLAMA_MODEL)
}

# Agent-specific timeout settings
AGENT_TIMEOUTS = {
    "planner": int(os.getenv("PLANNER_TIMEOUT", OLLAMA_TIMEOUT)),
    "frontend": int(os.getenv("FRONTEND_TIMEOUT", OLLAMA_TIMEOUT)),
    "backend": int(os.getenv("BACKEND_TIMEOUT", OLLAMA_TIMEOUT)),
    "tester": int(os.getenv("TESTER_TIMEOUT", OLLAMA_TIMEOUT)),
    "deployment": int(os.getenv("DEPLOYMENT_TIMEOUT", OLLAMA_TIMEOUT)),
    "analyzer": int(os.getenv("ANALYZER_TIMEOUT", 600))  # Default 10 minutes for analyzer
}

# Feature flags
ENABLE_AGENT_LOGS = os.getenv("ENABLE_AGENT_LOGS", "true").lower() == "true"
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

logger.info(f"Configured with OLLAMA_HOST={OLLAMA_HOST}, OLLAMA_MODEL={OLLAMA_MODEL}, OLLAMA_TIMEOUT={OLLAMA_TIMEOUT}")
logger.info(f"Agent models: {AGENT_MODELS}")
logger.info(f"Agent timeouts: {AGENT_TIMEOUTS}")
logger.info(f"Mock data mode: {USE_MOCK_DATA}")
