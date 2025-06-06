import litellm
import logging
from config import OLLAMA_TIMEOUT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_litellm():
    """Configure LiteLLM with appropriate settings"""
    try:
        # Set timeout from config
        litellm.request_timeout = OLLAMA_TIMEOUT
        
        # Configure retry mechanism
        litellm.num_retries = 3  # Number of retries if request fails
        litellm.retry_after = 5  # Wait 5 seconds between retries
        
        # Configure other LiteLLM settings for better performance
        litellm.drop_params = True  # Drop unnecessary parameters
        litellm.success_callback = []  # No callbacks for faster processing
        
        # Set up model-specific parameters for WizardCoder
        litellm.model_aliases = {
            "wizardcoder": "ollama/wizardcoder"
        }
        
        logger.info(f"LiteLLM configured with timeout: {litellm.request_timeout} seconds")
        logger.info(f"LiteLLM retry settings: {litellm.num_retries} retries with {litellm.retry_after}s delay")
        logger.info(f"Optimized settings for WizardCoder model")
    except Exception as e:
        logger.error(f"Error configuring LiteLLM: {e}")

# Call this function when the module is imported
configure_litellm() 