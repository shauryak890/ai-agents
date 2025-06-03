import json
import os
from typing import Dict, List, Any, Optional
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptAnalyzer:
    """
    Analyzes user prompts and converts them into structured requirements 
    for code generation.
    """
    
    def __init__(self):
        """Initialize the prompt analyzer to use local Ollama LLM."""
        # No API key needed for Ollama as it runs locally
        # Check if Ollama is available
        try:
            # Just a simple test to see if Ollama is responding
            ollama.list()
            logger.info("Ollama is available and responding")
        except Exception as e:
            logger.warning(f"Ollama might not be running or accessible: {e}")
            # We don't raise here to allow fallback behavior
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
    def _call_ollama_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call Ollama API with retry logic for reliability."""
        try:
            # Format the prompt for Ollama
            combined_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
            
            # Call Ollama - using the model that best matches GPT-4 capabilities
            # Users can change this to any model they have pulled in Ollama
            response = ollama.generate(
                model="phi3",  # or another model like "mistral" or "llama2" that's available locally
                prompt=combined_prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 2000  # similar to max_tokens
                }
            )
            return response['response']
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            raise
    
    def analyze_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """
        Analyze the user prompt and extract structured requirements.
        
        Args:
            user_prompt: The raw user prompt
            
        Returns:
            A dictionary containing structured requirements
        """
        system_prompt = """
        You are an expert requirements analyzer for web and application development. 
        Your task is to analyze a user's prompt for an application and extract detailed technical requirements.
        
        For each prompt, provide a structured JSON response with the following fields:
        
        1. "app_name": A concise, descriptive name for the application
        2. "description": A detailed description of what the application does
        3. "features": A list of specific features to implement
        4. "framework": The recommended frontend framework (React, Vue, Angular, etc.)
        5. "backend": The recommended backend technology (Node.js, Python/FastAPI, etc.)
        6. "database": The recommended database (MongoDB, PostgreSQL, SQLite, etc.)
        7. "ui_components": A list of UI components needed (forms, tables, charts, etc.)
        8. "libraries": A list of specific libraries with their purposes
        9. "api_integrations": Any external APIs that should be integrated
        10. "deployment": Recommended deployment strategy
        11. "enhanced_prompt": A comprehensive, detailed prompt that would lead to better code generation
        
        Think step by step and be as specific as possible with your recommendations.
        Your output must be valid JSON that can be parsed programmatically.
        """
        
        try:
            response_text = self._call_ollama_api(system_prompt, user_prompt)
            
            # Extract JSON from response (handle cases where model might add extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                requirements = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                requirements = json.loads(response_text)
                
            # Add the original prompt
            requirements["original_prompt"] = user_prompt
            
            return requirements
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            logger.error(f"Response was: {response_text}")
            # Fallback with basic structure
            return {
                "app_name": "App from prompt",
                "description": user_prompt,
                "features": ["Basic functionality"],
                "framework": "React",
                "backend": "Node.js",
                "database": "None",
                "ui_components": ["Basic UI"],
                "libraries": [],
                "api_integrations": [],
                "deployment": "Local development",
                "enhanced_prompt": user_prompt,
                "original_prompt": user_prompt,
                "error": "Failed to parse requirements"
            }
        except Exception as e:
            logger.error(f"Error analyzing prompt: {e}")
            raise

    def format_requirements_for_display(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the requirements for display in the UI.
        
        Args:
            requirements: The requirements dictionary
            
        Returns:
            A formatted dictionary for UI display
        """
        return {
            "app_name": requirements.get("app_name", "Unnamed App"),
            "description": requirements.get("description", ""),
            "sections": [
                {
                    "title": "Features",
                    "items": requirements.get("features", []),
                    "type": "list"
                },
                {
                    "title": "Technical Stack",
                    "items": [
                        f"Frontend: {requirements.get('framework', 'Not specified')}",
                        f"Backend: {requirements.get('backend', 'Not specified')}",
                        f"Database: {requirements.get('database', 'Not specified')}"
                    ],
                    "type": "list"
                },
                {
                    "title": "UI Components",
                    "items": requirements.get("ui_components", []),
                    "type": "list"
                },
                {
                    "title": "Libraries",
                    "items": requirements.get("libraries", []),
                    "type": "list"
                },
                {
                    "title": "API Integrations",
                    "items": requirements.get("api_integrations", []),
                    "type": "list"
                }
            ],
            "enhanced_prompt": requirements.get("enhanced_prompt", requirements.get("original_prompt", ""))
        }

def create_analyzer() -> PromptAnalyzer:
    """Factory function to create a prompt analyzer instance."""
    return PromptAnalyzer()

# Example usage
if __name__ == "__main__":
    analyzer = create_analyzer()
    result = analyzer.analyze_prompt("Create a todo app with authentication")
    print(json.dumps(result, indent=2))
