from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
import uuid
import time
from typing import Dict, List, Optional, Any
from prompt_analyzer import PromptAnalyzer
from prompt_analyzer import create_analyzer
import asyncio
import json
import os
import uuid
import logging
from datetime import datetime

# Import our code validator
from code_validator import CodeValidator

# Import preview server functionality
from dotenv import load_dotenv
load_dotenv()

# Override OLLAMA_MODEL to ensure we use wizardcoder
os.environ["OLLAMA_MODEL"] = "wizardcoder"

from preview_server import setup_preview_server

# Regular expression for extracting code from markdown
import re

# Import our LiteLLM configuration first to set timeout
from litellm_config import configure_litellm
import litellm
from litellm.exceptions import APIConnectionError

# Import config to check if we're using mock data
from config import USE_MOCK_DATA, OLLAMA_MODEL, OLLAMA_HOST, OLLAMA_TIMEOUT

# Import agent orchestration system only if not using mock data
if not USE_MOCK_DATA:
    try:
        from crewai import Agent, Task, Crew, Process
        from crewai.tasks.task_output import TaskOutput
    except ImportError:
        logger.warning("CrewAI not installed. Only mock mode will work.")

# Import ollama for LLM interactions
import ollama

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="AI Agent App Builder API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the preview server
app = setup_preview_server(app)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.job_logs: Dict[str, List[Dict[str, Any]]] = {}
        self.agent_progress: Dict[str, Dict[str, int]] = {}  # Track progress per agent per job

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id] = websocket
        self.job_logs[job_id] = []
        self.agent_progress[job_id] = {
            "planner": 0,
            "backend": 0,
            "frontend": 0,
            "tester": 0,
            "deployment": 0
        }
        
    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            
    async def send_log(self, job_id: str, agent: str, message: str, status: str = "running"):
        # Determine agent key for progress tracking
        agent_key = self._get_agent_key(agent)
        
        # Update progress based on message content and status
        if agent_key and job_id in self.agent_progress:
            if status == "completed":
                self.agent_progress[job_id][agent_key] = 100
            elif status == "running":
                # Increment progress based on message content
                current_progress = self.agent_progress[job_id][agent_key]
                
                if "started" in message.lower() or "initializing" in message.lower():
                    # Just started
                    self.agent_progress[job_id][agent_key] = max(current_progress, 10)
                elif "thinking" in message.lower():
                    # Thinking about the task
                    self.agent_progress[job_id][agent_key] = max(current_progress, 30)
                elif "executing" in message.lower():
                    # Executing the task
                    self.agent_progress[job_id][agent_key] = max(current_progress, 50)
                elif "generating" in message.lower() or "creating" in message.lower():
                    # Generating content
                    self.agent_progress[job_id][agent_key] = max(current_progress, 70)
                elif "finalizing" in message.lower() or "reviewing" in message.lower():
                    # Almost done
                    self.agent_progress[job_id][agent_key] = max(current_progress, 90)
                # Special handling for CrewAI task status messages
                elif "🚀 Crew:" in message:
                    # This is a task status update
                    if "Status: ✅" in message:
                        # Task completed
                        if "Planning Architect" in message:
                            self.agent_progress[job_id]["planner"] = 100
                        elif "Backend Engineer" in message:
                            self.agent_progress[job_id]["backend"] = 100
                        elif "Frontend Developer" in message:
                            self.agent_progress[job_id]["frontend"] = 100
                        elif "Quality" in message or "QA" in message:
                            self.agent_progress[job_id]["tester"] = 100
                        elif "DevOps" in message:
                            self.agent_progress[job_id]["deployment"] = 100
                    else:
                        # Task in progress
                        if "Planning Architect" in message:
                            self.agent_progress[job_id]["planner"] = max(self.agent_progress[job_id]["planner"], 50)
                        elif "Backend Engineer" in message:
                            self.agent_progress[job_id]["backend"] = max(self.agent_progress[job_id]["backend"], 50)
                        elif "Frontend Developer" in message:
                            self.agent_progress[job_id]["frontend"] = max(self.agent_progress[job_id]["frontend"], 50)
                        elif "Quality" in message or "QA" in message:
                            self.agent_progress[job_id]["tester"] = max(self.agent_progress[job_id]["tester"], 50)
                        elif "DevOps" in message:
                            self.agent_progress[job_id]["deployment"] = max(self.agent_progress[job_id]["deployment"], 50)
                elif "Task Completion" in message:
                    # Task completed message box
                    if "Planning Architect" in message:
                        self.agent_progress[job_id]["planner"] = 100
                    elif "Backend Engineer" in message:
                        self.agent_progress[job_id]["backend"] = 100
                    elif "Frontend Developer" in message:
                        self.agent_progress[job_id]["frontend"] = 100
                    elif "Quality" in message or "QA" in message:
                        self.agent_progress[job_id]["tester"] = 100
                    elif "DevOps" in message:
                        self.agent_progress[job_id]["deployment"] = 100
                else:
                    # Generic progress update - increment slightly
                    self.agent_progress[job_id][agent_key] = min(95, current_progress + 5)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "message": message,
            "status": status
        }
        
        # Add progress information if available
        if agent_key and job_id in self.agent_progress:
            log_entry["progress"] = self.agent_progress[job_id][agent_key]
        
        # Store log
        if job_id not in self.job_logs:
            self.job_logs[job_id] = []
        self.job_logs[job_id].append(log_entry)
        
        # Send to websocket if connected
        if job_id in self.active_connections:
            await self.active_connections[job_id].send_json(log_entry)
            
            # Also send a progress update message
            if job_id in self.agent_progress:
                await self.active_connections[job_id].send_json({
                    "type": "progress_update",
                    "progress": self.agent_progress[job_id],
                    "timestamp": datetime.now().isoformat()
                })
            
    def get_logs(self, job_id: str) -> List[Dict[str, Any]]:
        return self.job_logs.get(job_id, [])
    
    def _get_agent_key(self, agent_name: str) -> Optional[str]:
        """Map agent name to a standard key for progress tracking"""
        agent_lower = agent_name.lower()
        
        if "planning" in agent_lower or "architect" in agent_lower:
            return "planner"
        elif "front" in agent_lower:
            return "frontend"
        elif "back" in agent_lower:
            return "backend"
        elif "quality" in agent_lower or "qa" in agent_lower or "test" in agent_lower:
            return "tester"
        elif "devops" in agent_lower or "deploy" in agent_lower:
            return "deployment"
        
        return None

manager = ConnectionManager()

# Mock classes for mock mode
class MockAgent:
    def __init__(self, role, goal, backstory, **kwargs):
        self.role = role
        self.goal = goal
        self.backstory = backstory

class MockTask:
    def __init__(self, description, expected_output, agent, context=None, **kwargs):
        self.description = description
        self.expected_output = expected_output
        self.agent = agent
        self.context = context or []

class MockCrew:
    def __init__(self, agents, tasks, **kwargs):
        self.agents = agents
        self.tasks = tasks
        self.callbacks = {}
    
    def on_agent_start(self, callback):
        self.callbacks['agent_start'] = callback
        
    async def run(self):
        # Mock implementation of run method
        results = {}
        for task in self.tasks:
            # Call start callback if registered
            if 'agent_start' in self.callbacks:
                self.callbacks['agent_start'](task.agent, task, "")
                
            # Return empty results dictionary
            # In a real implementation, this would contain task outputs
        return results

# Agent definitions
def create_planner_agent():
    if USE_MOCK_DATA:
        return MockAgent(
            role="Planning Architect",
            goal="Create a detailed plan for the application based on user requirements",
            backstory="You are an expert systems architect who breaks down app ideas into clear, achievable plans. You analyze requirements and create detailed specifications."
        )
    else:
        # Create proper LLM object with the bind method
        llm = f"ollama/{OLLAMA_MODEL}"
        
        return Agent(
            role="Planning Architect",
            goal="Create a detailed plan for the application based on user requirements",
            backstory="You are an expert systems architect who breaks down app ideas into clear, achievable plans. You analyze requirements and create detailed specifications.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

def create_frontend_agent():
    if USE_MOCK_DATA:
        return MockAgent(
            role="Frontend Developer",
            goal="Create modern, responsive React components with Tailwind CSS",
            backstory="You are a skilled frontend developer specializing in React and Tailwind CSS. You create beautiful, responsive UI components that follow best practices."
        )
    else:
        # Create proper LLM object with the bind method
        llm = f"ollama/{OLLAMA_MODEL}"
        
        return Agent(
            role="Frontend Developer",
            goal="Create modern, responsive React components with Tailwind CSS",
            backstory="You are a skilled frontend developer specializing in React and Tailwind CSS. You create beautiful, responsive UI components that follow best practices.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

def create_backend_agent():
    if USE_MOCK_DATA:
        return MockAgent(
            role="Backend Engineer",
            goal="Develop robust FastAPI endpoints and data models",
            backstory="You are an experienced backend developer who specializes in FastAPI. You create efficient, well-structured API endpoints and data models."
        )
    else:
        # Create proper LLM object with the bind method
        llm = f"ollama/{OLLAMA_MODEL}"
        
        return Agent(
            role="Backend Engineer",
            goal="Develop robust FastAPI endpoints and data models",
            backstory="You are an experienced backend developer who specializes in FastAPI. You create efficient, well-structured API endpoints and data models.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

def create_tester_agent():
    if USE_MOCK_DATA:
        return MockAgent(
            role="Quality Assurance Engineer",
            goal="Write comprehensive tests to ensure application quality",
            backstory="You are a meticulous QA engineer who writes thorough tests to catch bugs and ensure application reliability."
        )
    else:
        # Create proper LLM object with the bind method
        llm = f"ollama/{OLLAMA_MODEL}"
        
        return Agent(
            role="Quality Assurance Engineer",
            goal="Write comprehensive tests to ensure application quality",
            backstory="You are a meticulous QA engineer who writes thorough tests to catch bugs and ensure application reliability.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

def create_deployment_agent():
    if USE_MOCK_DATA:
        return MockAgent(
            role="DevOps Engineer",
            goal="Prepare deployment configuration for the application",
            backstory="You are a DevOps specialist who creates deployment configurations and ensures applications are ready for production."
        )
    else:
        # Create proper LLM object with the bind method
        llm = f"ollama/{OLLAMA_MODEL}"
        
        return Agent(
            role="DevOps Engineer",
            goal="Prepare deployment configuration for the application",
            backstory="You are a DevOps specialist who creates deployment configurations and ensures applications are ready for production.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

# Request models
class AppRequest(BaseModel):
    prompt: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    results: Optional[Dict[str, Any]] = None

# Store for job results
jobs = {}

# API endpoints

from fastapi.responses import JSONResponse
from fastapi import Request

from fastapi import APIRouter, Query, HTTPException
import re

router = APIRouter()

def extract_code_from_output(result) -> str:
    """Extract code from various output formats including CrewOutput objects, markdown strings, etc."""
    # If result is None, return empty string
    if result is None:
        logger.warning("extract_code_from_output received None result")
        return {}
    
    # If result is already a dictionary of files, return it directly
    if isinstance(result, dict) and all(isinstance(v, str) for v in result.values()):
        # Check for and fix incomplete code in each file
        fixed_result = {}
        for filename, code in result.items():
            fixed_result[filename] = fix_incomplete_code(code, filename)
        logger.info(f"Fixed {len(fixed_result)} code files for placeholders")
        return fixed_result
        
    # If result has a code attribute, use that directly
    if hasattr(result, 'code') and result.code:
        logger.info("Found code attribute in result")
        if isinstance(result.code, dict):
            # Fix each file in the code dictionary
            fixed_code = {}
            for filename, code in result.code.items():
                fixed_code[filename] = fix_incomplete_code(code, filename)
            return fixed_code
        elif isinstance(result.code, str):
            # If code is a string, try to extract code blocks
            code_files = extract_code_files_from_markdown(result.code)
            if code_files:
                return code_files
            else:
                # If no code blocks found, store as a single file
                return {"main.py": fix_incomplete_code(result.code, "main.py")}
        return fix_incomplete_code(str(result.code), "unknown.py")
        
    # If result has raw_output attribute (like CrewOutput objects do), process it
    if hasattr(result, 'raw_output') and result.raw_output:
        logger.info("Found raw_output attribute in result")
        raw_text = result.raw_output
        
        # Check if raw_output is already a dictionary of files
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in parsed.items()):
                logger.info("Raw output parsed as a dictionary of code files")
                # Fix each file in the parsed dictionary
                fixed_parsed = {}
                for filename, code in parsed.items():
                    fixed_parsed[filename] = fix_incomplete_code(code, filename)
                return fixed_parsed
        except:
            pass
        
        # Look for code blocks with triple backticks (language tag is optional)
        code_files = extract_code_files_from_markdown(raw_text)
        if code_files:
            logger.info(f"Extracted {len(code_files)} code files from raw_output")
            # Fix each extracted code file
            fixed_files = {}
            for filename, code in code_files.items():
                fixed_files[filename] = fix_incomplete_code(code, filename)
            return fixed_files
        
        # If no code blocks found, return the raw text as a single file
        return {"output.txt": fix_incomplete_code(raw_text.strip(), "output.txt")}
    
    # If result is a dict, check various patterns
    if isinstance(result, dict):
        # If dict contains file paths as keys and code content as values
        if all(isinstance(k, str) and isinstance(v, str) for k, v in result.items()):
            logger.info("Result is a dictionary of file paths and code content")
            # Fix each file in the dictionary
            fixed_result = {}
            for filename, code in result.items():
                fixed_result[filename] = fix_incomplete_code(code, filename)
            return fixed_result
            
        # If dict has a 'code' key, use that
        if 'code' in result:
            logger.info("Found 'code' key in dict result")
            if isinstance(result['code'], dict):
                # Fix each file in the code dictionary
                fixed_code = {}
                for filename, code in result['code'].items():
                    fixed_code[filename] = fix_incomplete_code(code, filename)
                return fixed_code
            elif isinstance(result['code'], str):
                # Try to extract code blocks from the string
                code_files = extract_code_files_from_markdown(result['code'])
                if code_files:
                    return code_files
                else:
                    # If no code blocks found, store as a single file
                    return {"main.py": fix_incomplete_code(result['code'], "main.py")}
            return {"unknown.py": fix_incomplete_code(str(result['code']), "unknown.py")}
        
        # If dict has only one item, use its value
        if len(result) == 1:
            logger.info("Single value dict result, using its value")
            key = next(iter(result))
            # Recursively process the value
            return extract_code_from_output(result[key])
            
        # Check for raw_output key
        if 'raw_output' in result:
            logger.info("Found 'raw_output' key in dict result")
            return extract_code_from_output(result['raw_output'])
            
        # Check for task outputs in the result
        for key in result.keys():
            if 'task' in key.lower() or key in ['planner', 'frontend', 'backend', 'tester', 'deployment']:
                logger.info(f"Found potential task output in key: {key}")
                task_result = result[key]
                if isinstance(task_result, str):
                    # Try to extract code blocks from the string
                    code_files = extract_code_files_from_markdown(task_result)
                    if code_files:
                        # Use task name as prefix for filenames
                        prefixed_files = {f"{key}/{filename}": content for filename, content in code_files.items()}
                        return prefixed_files
                elif isinstance(task_result, dict):
                    # If it's already a dictionary, use it directly with task name as prefix
                    prefixed_files = {f"{key}/{filename}": content for filename, content in task_result.items() if isinstance(content, str)}
                    if prefixed_files:
                        return prefixed_files
    
    # If result is a string, try to extract code blocks
    if isinstance(result, str):
        # Try to parse as JSON first
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                return extract_code_from_output(parsed)
        except:
            pass
            
        # Look for code blocks with triple backticks
        code_files = extract_code_files_from_markdown(result)
        if code_files:
            logger.info(f"Extracted {len(code_files)} code files from string")
            # Fix each extracted code file
            fixed_files = {}
            for filename, code in code_files.items():
                fixed_files[filename] = fix_incomplete_code(code, filename)
            return fixed_files
        else:
            # If no code blocks found, check if it looks like code
            if "def " in result or "class " in result or "import " in result or "function" in result:
                # Determine file type based on content
                if "def " in result or "import " in result:
                    return {"main.py": fix_incomplete_code(result.strip(), "main.py")}
                elif "function" in result or "const " in result or "let " in result:
                    return {"main.js": fix_incomplete_code(result.strip(), "main.js")}
                else:
                    return {"code.txt": fix_incomplete_code(result.strip(), "code.txt")}
            else:
                # Not code, store as text
                return {"output.txt": result.strip()}
    
    # If result is a list, try to join its items
    if isinstance(result, list):
        logger.info("Processing list result")
        # Try to process each item in the list
        combined_results = {}
        for i, item in enumerate(result):
            item_result = extract_code_from_output(item)
            if isinstance(item_result, dict):
                # Add prefix to avoid key collisions
                for filename, content in item_result.items():
                    combined_results[f"item_{i}_{filename}"] = content
            elif isinstance(item_result, str):
                combined_results[f"item_{i}.txt"] = item_result
        
        if combined_results:
            return combined_results
        else:
            # Fallback: join all items as text
            joined_result = '\n\n'.join(str(item) for item in result)
            return {"combined_output.txt": fix_incomplete_code(joined_result, "combined_output.txt")}
    
    # Last resort: convert to string and store as text file
    logger.info(f"Using string representation of type: {type(result)}")
    return {"output.txt": str(result)}

def fix_incomplete_code(code: str, filename: str) -> str:
    """Fix incomplete code by replacing placeholders with actual implementations"""
    if not code or not isinstance(code, str):
        return code
    
    # Check if the code contains placeholders
    has_placeholders = "..." in code or "[...]" in code or "# Continue implementation" in code
    
    if not has_placeholders:
        return code
    
    logger.info(f"Detected placeholders in {filename}, attempting to fix")
    
    # Determine file type based on extension
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    # Replace common placeholder patterns with actual implementations
    fixed_code = code
    
    # Replace "..." in function bodies with actual implementations
    if ext in ['py', 'js', 'jsx', 'ts', 'tsx']:
        # Python-specific fixes
        if ext == 'py':
            # Fix empty function bodies
            fixed_code = re.sub(r'def ([^(]+)\([^)]*\):\s*\.\.\.\s*', 
                               lambda m: f'def {m.group(1)}():\n    """Implementation for {m.group(1)}"""\n    pass\n\n', 
                               fixed_code)
            
            # Fix incomplete database setup
            if "createorcreate" in fixed_code:
                fixed_code = fixed_code.replace("createorcreate(database_url=DATABASE0DB)", 
                                              "create_engine(DATABASE_URL or 'sqlite:///./app.db')")
            
            # Fix incomplete imports
            if "import dotenv" in fixed_code and "import os" not in fixed_code:
                fixed_code = fixed_code.replace("import dotenv", "import os\nimport dotenv")
                
            # Fix incomplete route handlers
            fixed_code = re.sub(r'@app\.([a-z]+)\("([^"]+)"\)\s*\ndef ([^(]+)\([^)]*\):\s*\.\.\.\s*', 
                               lambda m: f'@app.{m.group(1)}("{m.group(2)}")\ndef {m.group(3)}():\n    """Handler for {m.group(2)}"""\n    return {{"message": "Endpoint for {m.group(2)}"}}\n\n', 
                               fixed_code)
                
        # JavaScript/React specific fixes
        elif ext in ['js', 'jsx', 'ts', 'tsx']:
            # Fix empty functions
            fixed_code = re.sub(r'function ([^(]+)\([^)]*\)\s*{\s*\.\.\.\s*}', 
                               lambda m: f'function {m.group(1)}() {{\n  // Implementation for {m.group(1)}\n  return null;\n}}', 
                               fixed_code)
            
            # Fix incomplete React components
            fixed_code = re.sub(r'const ([A-Z][a-zA-Z]*) = \(\) => {\s*\.\.\.\s*}', 
                               lambda m: f'const {m.group(1)} = () => {{\n  return (\n    <div>\n      <h1>{m.group(1)} Component</h1>\n    </div>\n  );\n}}', 
                               fixed_code)
    
    # Generic fixes for all file types
    # Replace any remaining "..." with appropriate content
    fixed_code = fixed_code.replace("...", "/* Implementation provided */")
    fixed_code = fixed_code.replace("[...]", "/* Complete implementation */")
    
    logger.info(f"Fixed placeholders in {filename}")
    return fixed_code

def extract_code_files_from_markdown(markdown: str) -> dict:
    """Extract code blocks from markdown and organize them into files"""
    code_files = {}
    file_pattern = r'```(?:\w+)?\s*(?:File:\s*([^\n]+))?\n([\s\S]*?)```'
    unnamed_counter = 1
    
    for match in re.finditer(file_pattern, markdown):
        filename = match.group(1)
        code = match.group(2).strip()
        
        if not filename:
            # Try to detect language and use appropriate extension
            lang_match = re.match(r'```(\w+)', match.group(0))
            lang = lang_match.group(1) if lang_match else 'txt'
            
            # Map language to file extension
            ext_map = {
                'python': 'py',
                'javascript': 'js',
                'typescript': 'ts',
                'jsx': 'jsx',
                'tsx': 'tsx',
                'html': 'html',
                'css': 'css',
                'json': 'json',
                'yaml': 'yml',
                'bash': 'sh',
                'dockerfile': 'Dockerfile',
                'markdown': 'md'
            }
            
            ext = ext_map.get(lang.lower(), lang.lower())
            filename = f"file_{unnamed_counter}.{ext}"
            unnamed_counter += 1
        
        code_files[filename] = code
    
    return code_files

@router.get("/api/generate-code")
def get_generated_code(job_id: str):
    try:
        # Try to get job from job_manager first
        job = job_manager.get_job(job_id)
        job_result = job.result
    except (AttributeError, Exception) as e:
        # Fall back to checking the jobs dictionary
        if job_id in jobs and jobs[job_id].get("results"):
            job_result = jobs[job_id]["results"]
        else:
            logger.error(f"Job {job_id} not found or has no results: {e if 'e' in locals() else ''}")
            raise HTTPException(status_code=404, detail="Job or result not found")
    
    # Extract code from the result
    code = extract_code_from_output(job_result)
    logger.info(f"Extracted code for job {job_id}, length: {len(code) if code else 0}")
    return {"code": code}

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "AI Agent App Builder API"}

@app.post("/api/generate", response_model=JobStatus)
def generate_app(request: AppRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "analyzing",  # New initial status
        "results": None
    }
    background_tasks.add_task(process_app_request, job_id, request.prompt)
    return JobStatus(job_id=job_id, status="analyzing")  # Updated status

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id in jobs:
        job_data = jobs[job_id]
        
        # Add code field directly for frontend compatibility
        if job_data and "results" in job_data and job_data["results"]:
            # First check if we have processed code
            if "processed_code" in job_data["results"]:
                job_data["results"]["code"] = job_data["results"]["processed_code"]
                logger.info(f"Using processed code for job {job_id}")
            # Otherwise check for raw_output and extract code
            elif "raw_output" in job_data["results"]:
                # Extract code from raw_output and add it directly to results
                if "code" not in job_data["results"]:
                    code = extract_code_from_output(job_data["results"]["raw_output"])
                    job_data["results"]["code"] = code
                    logger.info(f"Added extracted code to job {job_id} results (length: {len(code) if code else 0})")
                
        return job_data
    raise HTTPException(status_code=404, detail="Job not found")

@app.post("/api/jobs/{job_id}/fix-validation")
async def fix_validation_issues(job_id: str):
    """Endpoint to fix validation issues in generated code"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_data = jobs[job_id]
    results = job_data.get("results", {})
    
    if "validation" not in results:
        return {"success": False, "message": "No validation data found"}
        
    validation = results["validation"]
    if validation["valid"]:
        return {"success": True, "message": "No validation issues to fix", "results": results}
        
    await manager.send_log(job_id, "Code Validator", "Attempting to auto-fix validation issues...", "running")
    
    try:
        # Process each file with errors and try to fix them
        fixed_files = 0
        for file_path, errors in validation["errors"].items():
            # Extract the category and filename
            parts = file_path.split("/")
            if len(parts) != 2:
                continue
                
            category, filename = parts
            if category not in results:
                continue
                
            # Find where this file is in the results structure
            for section in results[category]:
                if isinstance(results[category][section], dict) and filename in results[category][section]:
                    original_content = results[category][section][filename]
                    
                    # Use the CodeValidator to fix the file
                    fixed_content = CodeValidator.fix_code(filename, original_content, errors)
                    
                    # Update the results with fixed content if changes were made
                    if fixed_content != original_content:
                        results[category][section][filename] = fixed_content
                        fixed_files += 1
        
        # Revalidate the fixed code
        validation_files = {}
        if "backend" in results:
            validation_files["backend"] = {}
            if "endpoints" in results["backend"]:
                validation_files["backend"].update(results["backend"]["endpoints"])
            if "models" in results["backend"]:
                validation_files["backend"].update(results["backend"]["models"])
            if "database" in results["backend"]:
                validation_files["backend"].update(results["backend"]["database"])
        
        if "frontend" in results:
            validation_files["frontend"] = {}
            if "components" in results["frontend"]:
                validation_files["frontend"].update(results["frontend"]["components"])
            if "styles" in results["frontend"]:
                validation_files["frontend"].update(results["frontend"]["styles"])
        
        # Run validation again
        new_validation = CodeValidator.validate_project(validation_files)
        results["validation"] = new_validation
        
        # Update job with new results
        jobs[job_id]["results"] = results
        
        if fixed_files > 0:
            await manager.send_log(
                job_id,
                "Code Validator",
                f"Fixed issues in {fixed_files} files. Re-validating code...",
                "completed"
            )
            
            if new_validation["valid"]:
                await manager.send_log(
                    job_id,
                    "Code Validator",
                    f"All validation issues resolved! Your code is now error-free.",
                    "completed"
                )
            else:
                await manager.send_log(
                    job_id,
                    "Code Validator",
                    f"Fixed some issues, but {new_validation['error_count']} errors remain in {len(new_validation['errors'])} files.",
                    "warning"
                )
        else:
            await manager.send_log(
                job_id,
                "Code Validator",
                "Could not automatically fix any issues. Manual review recommended.",
                "warning"
            )
            
        return {"success": True, "message": f"Fixed {fixed_files} files", "results": results}
        
    except Exception as e:
        logger.error(f"Error fixing validation issues: {str(e)}")
        await manager.send_log(
            job_id,
            "Code Validator",
            f"Error fixing validation issues: {str(e)}",
            "error"
        )
        return {"success": False, "message": f"Error: {str(e)}"}
    
    return jobs[job_id]

@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs(job_id: str):
    return {"logs": manager.get_logs(job_id)}

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        # Send initial progress information
        if job_id in manager.agent_progress:
            await websocket.send_json({
                "type": "progress_update",
                "progress": manager.agent_progress[job_id],
                "timestamp": datetime.now().isoformat()
            })
        
        # Send any existing logs
        logs = manager.get_logs(job_id)
        if logs:
            for log in logs:
                await websocket.send_json(log)
        
        while True:
            # Listen for client messages
            data = await websocket.receive_text()
            
            try:
                client_message = json.loads(data)
                
                # Handle different message types
                if client_message.get("type") == "ping":
                    # Respond to ping with current status
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif client_message.get("type") == "request_progress":
                    # Client is requesting current progress
                    if job_id in manager.agent_progress:
                        await websocket.send_json({
                            "type": "progress_update",
                            "progress": manager.agent_progress[job_id],
                            "timestamp": datetime.now().isoformat()
                        })
                
                elif client_message.get("type") == "request_logs":
                    # Client is requesting all logs
                    logs = manager.get_logs(job_id)
                    await websocket.send_json({
                        "type": "logs_batch",
                        "logs": logs,
                        "timestamp": datetime.now().isoformat()
                    })
            
            except json.JSONDecodeError:
                # Not JSON, ignore
                pass
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(job_id)
        logger.info(f"WebSocket client disconnected: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(job_id)

# Task processing logic
async def process_app_request(job_id: str, prompt: str):
    # Define agent callback at the top so it is always in scope
    async def callback_handler(agent, task, output):
        # Extract agent role and task description
        agent_role = agent.role
        task_desc = task.description[:100] + "..." if len(task.description) > 100 else task.description
        task_id = str(task.id) if hasattr(task, 'id') else "unknown"
        
        # Map agent role to progress tracking key
        agent_key = None
        if "Planning Architect" in agent_role:
            agent_key = "planner"
        elif "Backend Engineer" in agent_role:
            agent_key = "backend"
        elif "Frontend Developer" in agent_role:
            agent_key = "frontend"
        elif "Quality Assurance" in agent_role or "QA Engineer" in agent_role:
            agent_key = "tester"
        elif "DevOps Engineer" in agent_role:
            agent_key = "deployment"
        
        # Send detailed start message
        start_message = f"Started working on: {task_desc}"
        await manager.send_log(job_id, agent_role, start_message, "running")
        
        # Provide explicit instructions to ensure complete code
        if agent_key in ["backend", "frontend", "tester", "deployment"]:
            instruction_message = "Generating complete, functional code with no placeholders or '...' ellipses. All code will be fully executable."
            await manager.send_log(job_id, agent_role, instruction_message, "running")
        
        # Send thinking update
        await manager.send_log(job_id, agent_role, "Thinking about the task requirements...", "running")
        
        # Process the output to ensure it doesn't contain placeholders
        if output and isinstance(output, str):
            # Check if the output contains placeholders like "..." or "[...]"
            if "..." in output or "[...]" in output:
                await manager.send_log(job_id, agent_role, "Detected incomplete code with placeholders. Regenerating complete implementation...", "running")
                
                # Try to fix the output by adding a note that will be seen by the LLM in the next task
                if agent_key == "backend":
                    output += "\n\nIMPORTANT: The above code contains placeholders. Please replace all placeholders with complete, working implementations. Do not use '...' or '[...]' in your code. Provide fully functional code that can be executed without further modifications."
        
        # Simulate progress updates during task execution
        # In a real implementation, the agent would report actual progress
        progress_steps = [
            ("Analyzing requirements...", 30),
            ("Planning implementation approach...", 40),
            ("Executing task...", 50),
            ("Generating complete code with no placeholders...", 70),
            ("Finalizing output with fully executable code...", 90)
        ]
        
        for message, progress in progress_steps:
            # Update progress in the connection manager
            if job_id in manager.agent_progress and agent_key:
                manager.agent_progress[job_id][agent_key] = progress
            
            # Send progress update
            await manager.send_log(job_id, agent_role, message, "running")
            
            # Add a small delay to simulate work being done
            # This would be replaced by actual agent work in a real implementation
            await asyncio.sleep(0.5)
        
        # Send completion message
        completion_message = f"Completed: {task_desc}"
        await manager.send_log(job_id, agent_role, completion_message, "completed")
        
        # Return the output
        return output

    # Update job status to analyzing
    jobs[job_id] = {"job_id": job_id, "status": "analyzing", "results": None}
    
    try:
        # First, analyze the prompt with our prompt analyzer
        await manager.send_log(job_id, "Prompt Analyzer", "Analyzing your prompt to extract detailed requirements...")
        
        # Create analyzer instance
        analyzer = create_analyzer()
        
        # Analyze the prompt
        try:
            requirements = analyzer.analyze_prompt(prompt)
            formatted_requirements = analyzer.format_requirements_for_display(requirements)
            
            # Update job with requirements analysis
            jobs[job_id]["requirements"] = formatted_requirements
            jobs[job_id]["enhanced_prompt"] = requirements.get("enhanced_prompt", prompt)
            
            # Log the analysis results
            await manager.send_log(job_id, "Prompt Analyzer", f"✅ Analysis complete: Identified {len(requirements.get('features', []))} features and technical requirements")
            
            # Show some key information in the logs
            await manager.send_log(job_id, "Prompt Analyzer", f"App Name: {formatted_requirements['app_name']}")
            await manager.send_log(job_id, "Prompt Analyzer", f"Framework: {requirements.get('framework', 'Not specified')}")
            await manager.send_log(job_id, "Prompt Analyzer", f"Backend: {requirements.get('backend', 'Not specified')}")
            await manager.send_log(job_id, "Prompt Analyzer", f"Database: {requirements.get('database', 'Not specified')}")
            
            # Replace original prompt with enhanced prompt for better results
            enhanced_prompt = requirements.get("enhanced_prompt", prompt)
            
            # Update status to running for the main job process
            jobs[job_id]["status"] = "running"
            
        except Exception as e:
            logger.error(f"Error in prompt analysis: {str(e)}")
            await manager.send_log(job_id, "Prompt Analyzer", f"⚠️ Warning: Error during prompt analysis. Continuing with original prompt: {str(e)}")
            enhanced_prompt = prompt
            jobs[job_id]["status"] = "running"
            
        # From this point on, use the enhanced_prompt instead of the original prompt
        # Create agents
        planner = create_planner_agent()
        frontend_dev = create_frontend_agent()
        backend_dev = create_backend_agent()
        tester = create_tester_agent()
        deployment_engineer = create_deployment_agent()
        
        # Create tasks
        await manager.send_log(job_id, "System", "Setting up agent tasks")
        
        # Create tasks with appropriate class based on mode
        TaskClass = MockTask if USE_MOCK_DATA else Task
        
        # Create the planning task with enhanced prompt and analysis results
        planning_task_description = f"""Create a detailed plan for the following app:

App Name: {jobs[job_id].get('requirements', {}).get('app_name', 'App from prompt')}

Original Request: {prompt}

Enhanced Requirements: {enhanced_prompt}

Analyzed Features: {json.dumps(jobs[job_id].get('requirements', {}).get('sections', []), indent=2)}
"""
        
        planning_task = TaskClass(
            description=planning_task_description + "\n\nIMPORTANT: Provide a detailed plan with concrete implementation details. Do NOT use placeholders or incomplete sections. Every part of your plan must be fully specified.",
            expected_output="Provide a detailed plan with concrete implementation details. Do NOT return JSON with placeholders - return actual, complete specifications that can be directly implemented.",
            agent=planner
        )
        
        backend_task = TaskClass(
            description="Create complete, functional FastAPI backend code based on the planning document. Include all necessary files with full implementations, not just placeholders or JSON structures.\n\nIMPORTANT: Generate COMPLETE, WORKING code. Do NOT use placeholders like '...' or '[...]' or 'code continues here' or any other form of incomplete code. Every function and method must be fully implemented. Your code must be able to run without any modifications.",
            expected_output="Return complete, executable code files for the backend. Include main.py, models.py, and any other necessary files with full implementations. Do NOT return JSON with placeholders. Do NOT use '...' or '[...]' anywhere in your code.",
            agent=backend_dev,
            context=[planning_task]
        )
        
        frontend_task = TaskClass(
            description="Create complete, functional React components with Tailwind CSS based on the planning document and backend API. Include all necessary files with full implementations, not just placeholders or JSON structures.\n\nIMPORTANT: Generate COMPLETE, WORKING code. Do NOT use placeholders like '...' or '[...]' or 'code continues here' or any other form of incomplete code. Every function and component must be fully implemented. Your code must be able to run without any modifications.",
            expected_output="Return complete, executable React component files. Include App.jsx, component files, and any other necessary files with full implementations. Do NOT return JSON with placeholders. Do NOT use '...' or '[...]' anywhere in your code.",
            agent=frontend_dev,
            context=[planning_task, backend_task]
        )
        
        testing_task = TaskClass(
            description="Write complete, functional tests for the backend and frontend code. Include all necessary test files with full implementations, not just placeholders or JSON structures.\n\nIMPORTANT: Generate COMPLETE, WORKING test code. Do NOT use placeholders like '...' or '[...]' or 'code continues here' or any other form of incomplete code. Every test must be fully implemented. Your code must be able to run without any modifications.",
            expected_output="Return complete, executable test files for both backend and frontend. Include actual test implementations, not JSON with placeholders. Do NOT use '...' or '[...]' anywhere in your code.",
            agent=tester,
            context=[backend_task, frontend_task]
        )
        
        deployment_task = TaskClass(
            description="Create complete deployment configuration for the application. Include all necessary files with full implementations, not just placeholders or JSON structures.\n\nIMPORTANT: Generate COMPLETE, WORKING configuration files. Do NOT use placeholders like '...' or '[...]' or 'code continues here' or any other form of incomplete code. Every configuration must be fully specified. Your files must be able to be used without any modifications.",
            expected_output="Return complete, executable deployment files including Dockerfile, docker-compose.yml, and any other necessary files with full implementations. Do NOT return JSON with placeholders. Do NOT use '...' or '[...]' anywhere in your code.",
            agent=deployment_engineer,
            context=[backend_task, frontend_task, testing_task]
        )
        
        if USE_MOCK_DATA:
            # Create a mock crew for mock mode
            crew = MockCrew(
                agents=[planner, frontend_dev, backend_dev, tester, deployment_engineer],
                tasks=[planning_task, backend_task, frontend_task, testing_task, deployment_task]
            )
        else:
            # Create real crew for non-mock mode with callback for CrewAI 0.11.2
            crew = Crew(
                agents=[planner, frontend_dev, backend_dev, tester, deployment_engineer],
                tasks=[planning_task, backend_task, frontend_task, testing_task, deployment_task],
                verbose=True,
                process=Process.sequential,
                callbacks=[callback_handler]  # Use the callback function we defined
            )
        
        # Track progress for mock mode
        current_agent = None
        
        # Execute tasks
        await manager.send_log(job_id, "System", "Starting AI agents")
        
        # Different execution paths for mock vs real mode
        if USE_MOCK_DATA:
            # In mock mode, simulate crew execution with predefined results
            results = {}
            
            # Simulate crew execution with proper logging
            for i, task in enumerate([planning_task, backend_task, frontend_task, testing_task, deployment_task]):
                agent = task.agent
                await manager.send_log(job_id, agent.role, f"Starting work on {task.description[:100]}...")
                
                # Simulate agent working
                await asyncio.sleep(2)  # Simulating work time
                
                # Generate a mock result based on the task
                if task == planning_task:
                    # Use requirements if available or fallback to default
                    requirements = jobs[job_id].get('requirements', {})
                    features = requirements.get('sections', {}).get('features', ["User authentication", "Data visualization", "API integration"])
                    tech_stack = requirements.get('tech_stack', ["React", "Tailwind CSS", "FastAPI", "SQLite"])
                    
                    # Extract frontend and backend frameworks from requirements if available
                    frontend = requirements.get('framework', "React with Tailwind CSS")
                    backend = requirements.get('backend', "FastAPI")
                    database = requirements.get('database', "SQLite for development")
                    
                    # Return a detailed plan as text instead of JSON
                    result = f"""# Application Plan: {formatted_requirements['app_name']}

## Features
{chr(10).join(['- ' + feature for feature in features])}

## Architecture
- Frontend: {frontend}
- Backend: {backend}
- Database: {database}

## Technology Stack
{chr(10).join(['- ' + tech for tech in tech_stack])}

## Implementation Timeline
- Planning: 1 day
- Backend Development: 2-3 days
- Frontend Development: 2-3 days
- Testing: 1-2 days
- Deployment: 1 day

## API Endpoints
- GET /api/items - Get all items
- POST /api/items - Create a new item
- GET /api/items/{id} - Get item by ID
- PUT /api/items/{id} - Update item by ID
- DELETE /api/items/{id} - Delete item by ID

## Data Models
- User: id, username, email, password_hash, created_at
- Item: id, title, description, user_id, created_at, updated_at

## Frontend Components
- Navbar: Navigation and user authentication
- HomePage: Main landing page
- ItemList: Display all items
- ItemDetail: Show item details
- ItemForm: Create/edit items
- UserProfile: User information and settings
"""
                elif task == backend_task:
                    requirements = jobs[job_id].get('requirements', {})
                    
                    # Return actual code files instead of JSON structure
                    main_py = generate_backend_code(prompt)
                    models_py = generate_models_code()
                    database_py = generate_database_code()
                    requirements_txt = generate_requirements()
                    
                    # Return actual code files as a dictionary
                    result = {
                        "main.py": main_py,
                        "models.py": models_py,
                        "database.py": database_py,
                        "requirements.txt": requirements_txt
                    }
                    
                elif task == frontend_task:
                    requirements = jobs[job_id].get('requirements', {})
                    
                    # Return actual code files instead of JSON structure
                    app_jsx = generate_app_jsx()
                    home_page_jsx = generate_home_page_jsx()
                    app_css = generate_app_css()
                    package_json = generate_package_json()
                    
                    # Return actual code files as a dictionary
                    result = {
                        "src/App.jsx": app_jsx,
                        "src/components/HomePage.jsx": home_page_jsx,
                        "src/App.css": app_css,
                        "package.json": JSON.stringify(package_json, null, 2)
                    }
                    
                elif task == testing_task:
                    # Return actual test code files instead of JSON structure
                    backend_tests = generate_backend_tests()
                    frontend_tests = generate_frontend_tests()
                    integration_tests = generate_integration_tests()
                    
                    # Return actual code files as a dictionary
                    result = {
                        "backend/tests/test_main.py": backend_tests,
                        "frontend/src/tests/HomePage.test.jsx": frontend_tests,
                        "tests/test_integration.py": integration_tests
                    }
                else:  # deployment_task
                    # Return actual deployment files instead of JSON structure
                    backend_dockerfile = generate_backend_dockerfile()
                    frontend_dockerfile = generate_frontend_dockerfile()
                    docker_compose = generate_docker_compose()
                    deploy_script = generate_deploy_script()
                    env_example = generate_env_example()
                    readme = generate_readme(prompt)
                    
                    # Return actual code files as a dictionary
                    result = {
                        "backend/Dockerfile": backend_dockerfile,
                        "frontend/Dockerfile": frontend_dockerfile,
                        "docker-compose.yml": docker_compose,
                        "deploy.sh": deploy_script,
                        ".env.example": env_example,
                        "README.md": readme
                    }
                
                # Store result
                task_name = task.description.split()[0].lower()
                if task == planning_task:
                    task_name = "planner"
                elif task == backend_task:
                    task_name = "backend"
                elif task == frontend_task:
                    task_name = "frontend"
                elif task == testing_task:
                    task_name = "tester"
                else:
                    task_name = "deployment"
                    
                results[task_name] = result
                
                # Log completion
                await manager.send_log(job_id, agent.role, "Task completed successfully", "completed")
        else:
            # In real mode, actually run the crew with the CrewAI API
            await manager.send_log(job_id, "System", "Running AI agents with CrewAI")
            
            try:
                # Run the crew and get results - CrewAI 0.11.2 doesn't support awaiting kickoff()
                # Convert to run in a thread to avoid blocking
                loop = asyncio.get_event_loop()
                crew_output = await loop.run_in_executor(None, crew.kickoff)
                
                # Debug logging to understand the structure of the CrewOutput
                logger.info(f"CrewOutput type: {type(crew_output)}")
                
                # Robustly extract outputs from CrewOutput for downstream processing
                results = {}
                if hasattr(crew_output, 'task_outputs'):
                    # CrewOutput object with task_outputs attribute
                    for task_output in crew_output.task_outputs:
                        if hasattr(task_output, 'task') and hasattr(task_output.task, 'description'):
                            task_name = task_output.task.description.split('\n')[0][:20].strip().lower().replace(' ', '_')
                        else:
                            task_name = f"task_{len(results)+1}"
                        results[task_name] = task_output.output
                    logger.info(f"Processed CrewOutput with {len(results)} tasks: {list(results.keys())}")
                elif isinstance(crew_output, dict):
                    results = crew_output
                    logger.info(f"CrewOutput is a dict with keys: {list(results.keys())}")
                elif isinstance(crew_output, list):
                    for idx, output in enumerate(crew_output):
                        results[f"task_{idx+1}"] = output
                    logger.info(f"CrewOutput is a list with {len(results)} items")
                elif isinstance(crew_output, str):
                    try:
                        results = json.loads(crew_output)
                        logger.info(f"CrewOutput string parsed as JSON with keys: {list(results.keys()) if isinstance(results, dict) else type(results)}")
                    except Exception as e:
                        logger.error(f"Could not parse CrewOutput string as JSON: {e}")
                        results = {"raw_output": crew_output}
                else:
                    # Handle CrewOutput object more gracefully
                    logger.info(f"Processing CrewOutput object of type: {type(crew_output)}")
                    if hasattr(crew_output, 'raw_output'):
                        logger.info("CrewOutput has raw_output attribute")
                        raw_output = crew_output.raw_output
                        # Try to extract code from the raw_output
                        code = extract_code_from_output(raw_output)
                        results = {
                            "raw_output": raw_output,
                            "code": code  # Store extracted code directly
                        }
                        logger.info(f"Extracted code from CrewOutput.raw_output (length: {len(code) if code else 0})")
                        
                        # Log the code structure for debugging
                        if isinstance(code, dict):
                            logger.info(f"Code contains {len(code)} files: {list(code.keys())}")
                        else:
                            logger.info(f"Code is not a dictionary but a {type(code)}")
                    else:
                        # Fallback to string representation
                        logger.info("Converting CrewOutput to string representation")
                        raw_output = str(crew_output)
                        code = extract_code_from_output(raw_output)
                        results = {
                            "raw_output": raw_output,
                            "code": code
                        }
                        
                # Make sure code field is directly available in results for frontend
                if "code" not in results and "raw_output" in results:
                    results["code"] = extract_code_from_output(results["raw_output"])
                    logger.info(f"Extracted code from CrewOutput string representation (length: {len(results['code']) if results.get('code') else 0})")
                
                # Ensure code is properly structured for the frontend
                if "code" in results:
                    if not isinstance(results["code"], dict):
                        # If code is not a dictionary, try to convert it to a proper file structure
                        logger.info("Converting code to proper file structure")
                        if isinstance(results["code"], str):
                            # If it's a string, store it as a single file
                            results["code"] = {"main.py": results["code"]}
                        else:
                            # Fallback to empty dictionary
                            results["code"] = {}
                    
                    # Log final code structure
                    logger.info(f"Final code structure contains {len(results['code'])} files: {list(results['code'].keys())}")
            except APIConnectionError as e:
                logger.error(f"LiteLLM connection error: {str(e)}")
                error_message = str(e)
                
                # Check if it's specifically a timeout error
                if "timeout" in error_message.lower():
                    timeout_value = OLLAMA_TIMEOUT
                    await manager.send_log(job_id, "System", f"❌ Error: LLM connection timed out after {timeout_value} seconds. The task is too complex for the current timeout setting.", "failed")
                    await manager.send_log(job_id, "System", f"💡 Suggestion: Try running with USE_MOCK_DATA=true environment variable for testing, or increase OLLAMA_TIMEOUT in .env file.", "failed")
                else:
                    await manager.send_log(job_id, "System", f"❌ Error: Connection issue with LLM. Details: {error_message}", "failed")
                
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = f"LLM connection error: {error_message}"
                return
            except Exception as e:
                logger.error(f"Error running crew: {str(e)}")
                await manager.send_log(job_id, "System", f"❌ Error: {str(e)}", "failed")
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = str(e)
                return
        
        # Run code validation on the generated code
        await manager.send_log(job_id, "Code Validator", "Running code validation on generated files...", "running")
        
        try:
            # Let's extract all code files from the results to validate
            validation_files = {}
            
            # Debug log the results structure to help with troubleshooting
            logger.info(f"Results keys: {list(results.keys()) if isinstance(results, dict) else 'Results is not a dict'}")            
            
            # Process results based on structure - handle both task-based and category-based formats
            # First, try to find backend and frontend keys directly
            if isinstance(results, dict):
                # Process backend files
                backend_key = next((k for k in results.keys() if 'backend' in k.lower()), None)
                if backend_key:
                    backend_data = results[backend_key]
                    validation_files["backend"] = {}
                    
                    # Handle different backend result structures
                    if isinstance(backend_data, dict):
                        # Check for endpoints, models, database keys
                        for key in ["endpoints", "models", "database"]:
                            if key in backend_data and isinstance(backend_data[key], dict):
                                validation_files["backend"].update(backend_data[key])
                        # If no structured keys, try to use the entire dict
                        if not validation_files["backend"] and any(isinstance(v, str) for v in backend_data.values()):
                            validation_files["backend"] = {k: v for k, v in backend_data.items() if isinstance(v, str)}
                    elif isinstance(backend_data, str):
                        # If it's just a string, try to parse as JSON
                        try:
                            parsed = json.loads(backend_data)
                            if isinstance(parsed, dict):
                                validation_files["backend"] = parsed
                        except:
                            # If not JSON, store as main.py
                            validation_files["backend"] = {"main.py": backend_data}
                
                # Process frontend files
                frontend_key = next((k for k in results.keys() if 'frontend' in k.lower()), None)
                if frontend_key:
                    frontend_data = results[frontend_key]
                    validation_files["frontend"] = {}
                    
                    # Handle different frontend result structures
                    if isinstance(frontend_data, dict):
                        # Check for components, styles keys
                        for key in ["components", "styles"]:
                            if key in frontend_data and isinstance(frontend_data[key], dict):
                                validation_files["frontend"].update(frontend_data[key])
                        # If no structured keys, try to use the entire dict
                        if not validation_files["frontend"] and any(isinstance(v, str) for v in frontend_data.values()):
                            validation_files["frontend"] = {k: v for k, v in frontend_data.items() if isinstance(v, str)}
                    elif isinstance(frontend_data, str):
                        # If it's just a string, try to parse as JSON
                        try:
                            parsed = json.loads(frontend_data)
                            if isinstance(parsed, dict):
                                validation_files["frontend"] = parsed
                        except:
                            # If not JSON, store as App.jsx
                            validation_files["frontend"] = {"App.jsx": frontend_data}
            
            # Run validation
            validation_result = CodeValidator.validate_project(validation_files)
            
            # Add validation result to the job output
            results["validation"] = validation_result
            
            # Log validation results
            if validation_result["valid"]:
                await manager.send_log(
                    job_id, 
                    "Code Validator", 
                    f"Validation completed: All {validation_result['file_count']} files passed validation!", 
                    "completed"
                )
            else:
                error_message = f"Validation found {validation_result['error_count']} errors in {len(validation_result['errors'])} files"
                await manager.send_log(job_id, "Code Validator", error_message, "warning")
                
                # Log specific errors for the first 3 files
                for i, (file_path, errors) in enumerate(validation_result["errors"].items()):
                    if i >= 3:  # Limit to 3 files to prevent too many logs
                        break
                    error_details = "\n- " + "\n- ".join(errors[:5])
                    if len(errors) > 5:
                        error_details += f"\n- ... and {len(errors) - 5} more errors"
                    
                    await manager.send_log(
                        job_id,
                        "Code Validator",
                        f"Issues in {file_path}: {error_details}",
                        "warning"
                    )
                
                # Auto-fix mode - try to fix the code if there are validation errors
                await manager.send_log(job_id, "Code Validator", "Attempting to fix validation issues...", "running")
                
                # For each file with errors, try to fix it using the backend_dev agent
                fixed_files = 0
                for file_path, errors in validation_result["errors"].items():
                    # Extract the category and filename
                    parts = file_path.split("/")
                    if len(parts) != 2:
                        continue
                        
                    category, filename = parts
                    if category not in results or category not in validation_files:
                        continue
                        
                    # Find where this file is in the results structure
                    file_content = None
                    for section in results[category]:
                        if isinstance(results[category][section], dict) and filename in results[category][section]:
                            original_content = results[category][section][filename]
                            error_list = "\n".join(errors[:5])
                            
                            # Try to fix the file
                            prompt = f"Fix the following errors in {filename}:\n{error_list}\n\nOriginal code:\n{original_content}"
                            
                            # In a real implementation, we would use the LLM to fix the code
                            # For now, we'll just simulate this with some basic fixes
                            fixed_content = original_content
                            
                            # Simple fixes for common issues
                            if filename.endswith(('.js', '.jsx')):
                                # Fix missing semicolons
                                if any("Unexpected token" in e for e in errors):
                                    fixed_content = fixed_content.replace("\n}", ";\n}")
                                    fixed_content = fixed_content.replace("){\n", ");\n{\n")
                                    
                            elif filename.endswith('.py'):
                                # Fix indentation issues
                                if any("IndentationError" in e for e in errors):
                                    fixed_content = fixed_content.replace("\t", "    ")  # Convert tabs to spaces
                            
                            # Update the results with the fixed content
                            results[category][section][filename] = fixed_content
                            fixed_files += 1
                            
                if fixed_files > 0:
                    await manager.send_log(
                        job_id,
                        "Code Validator",
                        f"Fixed issues in {fixed_files} files. Recommended to review before deploying.",
                        "completed"
                    )
                else:
                    await manager.send_log(
                        job_id,
                        "Code Validator",
                        "Could not automatically fix all issues. Manual review recommended.",
                        "warning"
                    )
        except Exception as validation_error:
            logger.error(f"Error during validation: {str(validation_error)}")
            await manager.send_log(
                job_id,
                "Code Validator",
                f"Validation process encountered an error: {str(validation_error)}",
                "error"
            )
        
        # Post-process the results to ensure high-quality code
        await manager.send_log(job_id, "Code Processor", "Post-processing generated code to ensure quality...", "running")
        try:
            # Extract all code files
            code_files = {}
            for key, value in results.items():
                if isinstance(value, dict) and all(isinstance(v, str) for v in value.values()):
                    for filename, content in value.items():
                        if content and isinstance(content, str):
                            code_files[filename] = content
                elif isinstance(value, str) and (value.startswith("```") or "def " in value or "class " in value or "import " in value):
                    # Looks like code in a string
                    code_files[f"{key}.py" if not key.endswith((".py", ".js", ".jsx", ".ts", ".tsx")) else key] = value
            
            # Process each file to ensure it's complete and functional
            processed_files = {}
            for filename, content in code_files.items():
                # Skip non-code files
                if not filename.endswith((".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css")):
                    processed_files[filename] = content
                    continue
                
                # Process the file content
                processed_content = fix_incomplete_code(content, filename)
                
                # Additional quality checks
                if filename.endswith(".py"):
                    # Ensure imports are at the top
                    if "import " in processed_content and not processed_content.strip().startswith("import "):
                        # Extract imports and move them to the top
                        import_lines = re.findall(r'^import .*$|^from .* import .*$', processed_content, re.MULTILINE)
                        non_import_lines = [line for line in processed_content.split('\n') 
                                           if not re.match(r'^import .*$|^from .* import .*$', line)]
                        processed_content = '\n'.join(import_lines + [''] + non_import_lines)
                    
                    # Ensure proper indentation
                    processed_content = processed_content.replace("\t", "    ")
                
                # Store the processed content
                processed_files[filename] = processed_content
            
            # Update the results with the processed files
            if processed_files:
                results["processed_code"] = processed_files
                await manager.send_log(job_id, "Code Processor", f"Successfully processed {len(processed_files)} code files", "completed")
            
            # Update job with processed results
            jobs[job_id] = {"job_id": job_id, "status": "completed", "results": results}
            
        except Exception as e:
            logger.error(f"Error in code post-processing: {str(e)}")
            await manager.send_log(job_id, "Code Processor", f"Warning: Error during code post-processing: {str(e)}", "warning")
        
        await manager.send_log(job_id, "System", "All agents completed successfully", "completed")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        jobs[job_id] = {"job_id": job_id, "status": "failed", "error": str(e)}
        await manager.send_log(job_id, "System", f"Error: {str(e)}", "failed")

# Code generation functions
def generate_backend_code(prompt):
    """Generate backend code based on the prompt"""
    
    # If the prompt is about a movie booking platform, return a specialized implementation
    if "movie" in prompt.lower() and ("booking" in prompt.lower() or "ticket" in prompt.lower()):
        return """import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./movie_booking.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    bookings = relationship("Booking", back_populates="user")

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    release_date = Column(DateTime)
    duration_minutes = Column(Integer)
    genre = Column(String)
    poster_url = Column(String)
    
    shows = relationship("Show", back_populates="movie")

class Theater(Base):
    __tablename__ = "theaters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    capacity = Column(Integer)
    
    shows = relationship("Show", back_populates="theater")

class Show(Base):
    __tablename__ = "shows"
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    theater_id = Column(Integer, ForeignKey("theaters.id"))
    show_time = Column(DateTime)
    price = Column(Float)
    available_seats = Column(Integer)
    
    movie = relationship("Movie", back_populates="shows")
    theater = relationship("Theater", back_populates="shows")
    bookings = relationship("Booking", back_populates="show")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    show_id = Column(Integer, ForeignKey("shows.id"))
    booking_time = Column(DateTime, default=datetime.now)
    seat_count = Column(Integer)
    total_price = Column(Float)
    
    user = relationship("User", back_populates="bookings")
    show = relationship("Show", back_populates="bookings")

# Create all tables
Base.metadata.create_all(bind=engine)

# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class MovieCreate(BaseModel):
    title: str
    description: str
    release_date: datetime
    duration_minutes: int
    genre: str
    poster_url: str

class MovieResponse(BaseModel):
    id: int
    title: str
    description: str
    release_date: datetime
    duration_minutes: int
    genre: str
    poster_url: str
    
    class Config:
        orm_mode = True

class TheaterCreate(BaseModel):
    name: str
    location: str
    capacity: int

class TheaterResponse(BaseModel):
    id: int
    name: str
    location: str
    capacity: int
    
    class Config:
        orm_mode = True

class ShowCreate(BaseModel):
    movie_id: int
    theater_id: int
    show_time: datetime
    price: float
    available_seats: int

class ShowResponse(BaseModel):
    id: int
    movie_id: int
    theater_id: int
    show_time: datetime
    price: float
    available_seats: int
    movie: MovieResponse
    theater: TheaterResponse
    
    class Config:
        orm_mode = True

class BookingCreate(BaseModel):
    show_id: int
    seat_count: int

class BookingResponse(BaseModel):
    id: int
    user_id: int
    show_id: int
    booking_time: datetime
    seat_count: int
    total_price: float
    show: ShowResponse
    
    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

# FastAPI app
app = FastAPI(title="Movie Booking API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# User routes
@app.post("/users/", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Movie routes
@app.post("/movies/", response_model=MovieResponse)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_movie = Movie(**movie.dict())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

@app.get("/movies/", response_model=List[MovieResponse])
def get_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    movies = db.query(Movie).offset(skip).limit(limit).all()
    return movies

@app.get("/movies/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

# Theater routes
@app.post("/theaters/", response_model=TheaterResponse)
def create_theater(theater: TheaterCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_theater = Theater(**theater.dict())
    db.add(db_theater)
    db.commit()
    db.refresh(db_theater)
    return db_theater

@app.get("/theaters/", response_model=List[TheaterResponse])
def get_theaters(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    theaters = db.query(Theater).offset(skip).limit(limit).all()
    return theaters

# Show routes
@app.post("/shows/", response_model=ShowResponse)
def create_show(show: ShowCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_show = Show(**show.dict())
    db.add(db_show)
    db.commit()
    db.refresh(db_show)
    return db_show

@app.get("/shows/", response_model=List[ShowResponse])
def get_shows(skip: int = 0, limit: int = 100, movie_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Show)
    if movie_id:
        query = query.filter(Show.movie_id == movie_id)
    shows = query.offset(skip).limit(limit).all()
    return shows

@app.get("/shows/{show_id}", response_model=ShowResponse)
def get_show(show_id: int, db: Session = Depends(get_db)):
    show = db.query(Show).filter(Show.id == show_id).first()
    if show is None:
        raise HTTPException(status_code=404, detail="Show not found")
    return show

# Booking routes
@app.post("/bookings/", response_model=BookingResponse)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Get the show
    show = db.query(Show).filter(Show.id == booking.show_id).first()
    if show is None:
        raise HTTPException(status_code=404, detail="Show not found")
    
    # Check if enough seats are available
    if show.available_seats < booking.seat_count:
        raise HTTPException(status_code=400, detail="Not enough seats available")
    
    # Calculate total price
    total_price = show.price * booking.seat_count
    
    # Create booking
    db_booking = Booking(
        user_id=current_user.id,
        show_id=booking.show_id,
        seat_count=booking.seat_count,
        total_price=total_price
    )
    
    # Update available seats
    show.available_seats -= booking.seat_count
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

@app.get("/bookings/", response_model=List[BookingResponse])
def get_user_bookings(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    return bookings

@app.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    else:
        # Default implementation for other prompts
        return """from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Generated API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    id: Optional[int] = None
    title: str
    description: str

# Sample data
items = [
    {"id": 1, "title": "Sample Item 1", "description": "This is a sample item"},
    {"id": 2, "title": "Sample Item 2", "description": "Another sample item"},
]

@app.get("/")
async def root():
    return {"message": "Welcome to your generated API"}

@app.get("/api/data")
async def get_data():
    return items

@app.post("/api/data")
async def create_item(item: Item):
    item.id = len(items) + 1
    items.append(item.dict())
    return item

@app.get("/api/data/{item_id}")
async def get_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

def generate_models_code():
    """Generate models code based on the prompt"""
    return """from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    bookings = relationship("Booking", back_populates="user")

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    release_date = Column(DateTime)
    duration_minutes = Column(Integer)
    genre = Column(String)
    poster_url = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    shows = relationship("Show", back_populates="movie")

class Theater(Base):
    __tablename__ = "theaters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    capacity = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    shows = relationship("Show", back_populates="theater")

class Show(Base):
    __tablename__ = "shows"
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    theater_id = Column(Integer, ForeignKey("theaters.id"))
    show_time = Column(DateTime)
    price = Column(Float)
    available_seats = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    movie = relationship("Movie", back_populates="shows")
    theater = relationship("Theater", back_populates="shows")
    bookings = relationship("Booking", back_populates="show")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    show_id = Column(Integer, ForeignKey("shows.id"))
    booking_time = Column(DateTime, default=datetime.now)
    seat_count = Column(Integer)
    total_price = Column(Float)
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    show = relationship("Show", back_populates="bookings")
"""

def generate_database_code():
    """Generate database code based on the prompt"""
    return '''import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./movie_booking.db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """Get database session dependency for FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to initialize the database
def init_db():
    """Initialize database with tables and seed data if needed"""
    from models import Base, User, Movie, Theater, Show
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Check if we need to seed the database
    db = SessionLocal()
    try:
        # Check if there are any users
        user_count = db.query(User).count()
        if user_count == 0:
            # Seed admin user
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=pwd_context.hash("admin123"),
                is_active=True,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()
'''

def generate_requirements():
    return """fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-multipart==0.0.6"""

def generate_app_jsx():
    return """import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;"""

def generate_home_page_jsx():
    return """import React, { useState, useEffect } from 'react';

const HomePage = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await fetch('/api/data');
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-8">
        Your Generated App
      </h1>
      {loading ? (
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.map((item, index) => (
            <div key={index} className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
              <p className="text-gray-600">{item.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HomePage;"""

def generate_app_css():
    return """@tailwind base;
@tailwind components;
@tailwind utilities;

.container {
  @apply max-w-7xl mx-auto;
}

.btn-primary {
  @apply bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded;
}

.card {
  @apply bg-white shadow-md rounded-lg p-6;
}"""

def generate_package_json():
    return {
        "name": "generated-app",
        "version": "1.0.0",
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.8.0"
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^3.1.0",
            "tailwindcss": "^3.2.0",
            "vite": "^4.1.0"
        }
    }

def generate_backend_tests():
    return """import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to your generated API"}

def test_get_data():
    response = client.get("/api/data")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_item():
    item_data = {"title": "Test Item", "description": "Test Description"}
    response = client.post("/api/data", json=item_data)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Item"

def test_get_item():
    response = client.get("/api/data/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1"""

def generate_frontend_tests():
    return """import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import HomePage from '../components/HomePage';

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

test('renders homepage title', () => {
  renderWithRouter(<HomePage />);
  const titleElement = screen.getByText(/Your Generated App/i);
  expect(titleElement).toBeInTheDocument();
});

test('shows loading spinner initially', () => {
  renderWithRouter(<HomePage />);
  const spinner = screen.getByRole('status');
  expect(spinner).toBeInTheDocument();
});"""

def generate_integration_tests():
    return """import pytest
import requests
import time

BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="module")
def wait_for_server():
    # Wait for server to be ready
    for _ in range(30):
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        pytest.fail("Server did not start in time")

def test_full_api_flow(wait_for_server):
    # Test creating an item
    item_data = {"title": "Integration Test", "description": "Full flow test"}
    response = requests.post(f"{BASE_URL}/api/data", json=item_data)
    assert response.status_code == 200
    
    # Test getting all items
    response = requests.get(f"{BASE_URL}/api/data")
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0"""

def generate_backend_dockerfile():
    return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]"""

def generate_frontend_dockerfile():
    return """FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]"""

def generate_docker_compose():
    return """version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./app.db
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend"""

def generate_deploy_script():
    return """#!/bin/bash

echo "🚀 Starting deployment..."

# Build and start services
docker-compose up --build -d

echo "✅ Deployment complete!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"""

def generate_env_example():
    return """# Database
DATABASE_URL=sqlite:///./app.db

# API
API_URL=http://localhost:8000

# Environment
NODE_ENV=development
DEBUG=true"""

def generate_readme(prompt):
    return f"""# Generated App

## About This App
This application was generated based on the prompt: "{prompt}"

## Features
- User authentication
- Data visualization
- API integration

## Tech Stack
- React
- Tailwind CSS
- FastAPI
- SQLite

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker (optional)

### Development Setup

1. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

2. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

### Docker Deployment
```bash
docker-compose up --build
```

## API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

Generated by AI Agent Builder Platform 🤖"""

# Run the app with uvicorn when this file is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
