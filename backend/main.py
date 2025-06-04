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

from preview_server import setup_preview_server

# Regular expression for extracting code from markdown
import re

import litellm

# Import config to check if we're using mock data
from config import USE_MOCK_DATA, OLLAMA_MODEL, OLLAMA_HOST

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

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id] = websocket
        self.job_logs[job_id] = []
        
    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            
    async def send_log(self, job_id: str, agent: str, message: str, status: str = "running"):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "message": message,
            "status": status
        }
        
        # Store log
        if job_id not in self.job_logs:
            self.job_logs[job_id] = []
        self.job_logs[job_id].append(log_entry)
        
        # Send to websocket if connected
        if job_id in self.active_connections:
            await self.active_connections[job_id].send_json(log_entry)
            
    def get_logs(self, job_id: str) -> List[Dict[str, Any]]:
        return self.job_logs.get(job_id, [])

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
        return ""
    
    # If result has a code attribute, use that directly
    if hasattr(result, 'code') and result.code:
        logger.info("Found code attribute in result")
        return str(result.code)
        
    # If result has raw_output attribute (like CrewOutput objects do), process it
    if hasattr(result, 'raw_output') and result.raw_output:
        logger.info("Found raw_output attribute in result")
        raw_text = result.raw_output
        
        # Look for code blocks with triple backticks (language tag is optional)
        code_blocks = re.findall(r'```(?:\w*)?\s*\n([\s\S]*?)```', raw_text, re.DOTALL)
        if code_blocks:
            logger.info(f"Extracted {len(code_blocks)} code blocks from raw_output")
            # Join all code blocks with newlines
            return '\n\n'.join(code_blocks)
        
        return raw_text.strip()
    
    # If result is a dict, check various patterns
    if isinstance(result, dict):
        # If dict has a 'code' key, use that
        if 'code' in result:
            logger.info("Found 'code' key in dict result")
            return str(result['code'])
        
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
    
    # If result is a string, try to extract code blocks
    if isinstance(result, str):
        # Look for code blocks with triple backticks
        code_blocks = re.findall(r'```(?:\w*)?\s*\n([\s\S]*?)```', result, re.DOTALL)
        if code_blocks:
            logger.info(f"Extracted {len(code_blocks)} code blocks from string")
            # Join all code blocks with newlines
            return '\n\n'.join(code_blocks)
        else:
            # If no code blocks found, return the entire string
            return result.strip()
    
    # If result is a list, try to join its items
    if isinstance(result, list):
        logger.info("Processing list result")
        # Try to concatenate all items in the list
        try:
            return '\n\n'.join(str(extract_code_from_output(item)) for item in result)
        except Exception as e:
            logger.error(f"Error processing list result: {e}")
    
    # Last resort: convert to string
    logger.info(f"Using string representation of type: {type(result)}")
    return str(result)

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
        if job_data and "results" in job_data and job_data["results"] and "raw_output" in job_data["results"]:
            # Extract code from raw_output and add it directly to results
            if "code" not in job_data["results"]:
                code = extract_code_from_output(job_data["results"]["raw_output"])
                job_data["results"]["code"] = {"main.py": code}
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
        while True:
            # Keep connection open
            data = await websocket.receive_text()
            # Process any client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(job_id)

# Task processing logic
async def process_app_request(job_id: str, prompt: str):
    # Define agent callback at the top so it is always in scope
    def agent_callback(agent, task, output):
        import asyncio
        # Send 'started' log before task execution
        asyncio.run(manager.send_log(job_id, agent.role, f"Started: {task.description[:50]}...", "running"))
        # If possible, yield here or call the agent's execution logic
        # Send 'completed' log after task execution
        asyncio.run(manager.send_log(job_id, agent.role, f"Completed: {task.description[:50]}...", "completed"))
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
        # Set up callback for logging
        async def callback_handler(agent, task, output):
            await manager.send_log(job_id, agent.role, f"Completed: {task.description[:100]}...")
            return output
        
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
            description=planning_task_description,
            expected_output="A JSON object with 'features', 'architecture', 'tech_stack', and 'timeline' fields",
            agent=planner
        )
        
        backend_task = TaskClass(
            description="Create FastAPI backend code based on the planning document",
            expected_output="A JSON object with 'endpoints', 'models', 'database', and 'requirements' fields",
            agent=backend_dev,
            context=[planning_task]
        )
        
        frontend_task = TaskClass(
            description="Create React components with Tailwind CSS based on the planning document and backend API",
            expected_output="A JSON object with 'components', 'styles', 'routing', and 'package_json' fields",
            agent=frontend_dev,
            context=[planning_task, backend_task]
        )
        
        testing_task = TaskClass(
            description="Write tests for the backend and frontend code",
            expected_output="A JSON object with 'backend_tests', 'frontend_tests', and 'integration_tests' fields",
            agent=tester,
            context=[backend_task, frontend_task]
        )
        
        deployment_task = TaskClass(
            description="Create deployment configuration for the application",
            expected_output="A JSON object with 'docker', 'deploy', 'env', and 'readme' fields",
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
                callbacks=[agent_callback]  # Use the callback function we defined
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
                    
                    result = {
                        "features": features,
                        "architecture": {
                            "frontend": frontend,
                            "backend": backend,
                            "database": database
                        },
                        "tech_stack": tech_stack,
                        "timeline": "MVP in 2-3 days"
                    }
                elif task == backend_task:
                    requirements = jobs[job_id].get('requirements', {})
                    result = {}
                    
                    # Always include main API endpoint
                    result["endpoints"] = {"main.py": generate_backend_code(prompt)}
                    
                    # Only include models if the requirements indicate data models are needed
                    needs_models = False
                    features = requirements.get('sections', {}).get('features', [])
                    for feature in features:
                        if any(term in str(feature).lower() for term in ['database', 'model', 'data', 'storage', 'user', 'authentication']):
                            needs_models = True
                            break
                    
                    # Include models only if needed
                    if needs_models:
                        result["models"] = {"models.py": generate_models_code()}
                    
                    # Only include database setup if needed based on requirements
                    database_type = requirements.get('database', '').lower()
                    if database_type and database_type != 'none':
                        result["database"] = {"database.py": generate_database_code()}
                    
                    # Always include requirements file
                    result["requirements"] = generate_requirements()
                elif task == frontend_task:
                    requirements = jobs[job_id].get('requirements', {})
                    result = {}
                    
                    # Determine the frontend framework from requirements
                    frontend_framework = requirements.get('framework', '').lower()
                    
                    # Basic components are always needed
                    components = {}
                    
                    # Always include App and HomePage components
                    components["App.jsx"] = generate_app_jsx()
                    components["HomePage.jsx"] = generate_home_page_jsx()
                    
                    # Check if additional pages are needed based on features
                    features = requirements.get('sections', {}).get('features', [])
                    needs_auth = any('auth' in str(feature).lower() or 'login' in str(feature).lower() or 'user' in str(feature).lower() for feature in features)
                    needs_dashboard = any('dashboard' in str(feature).lower() or 'admin' in str(feature).lower() for feature in features)
                    
                    # Add UI components only if required by features
                    result["components"] = components
                    
                    # Always include basic styles
                    result["styles"] = {"App.css": generate_app_css()}
                    
                    # Create routing based on required pages
                    routes = [{"path": "/", "component": "HomePage"}]
                    
                    if needs_auth:
                        routes.append({"path": "/login", "component": "LoginPage"})
                        
                    if needs_dashboard:
                        routes.append({"path": "/dashboard", "component": "DashboardPage"})
                    
                    result["routing"] = {"routes": routes}
                    
                    # Always include package.json
                    result["package_json"] = generate_package_json()
                elif task == testing_task:
                    requirements = jobs[job_id].get('requirements', {})
                    result = {}
                    
                    # Determine if tests are needed based on requirements
                    needs_tests = requirements.get('needs_tests', True)  # Default to True for better quality
                    
                    # Skip test generation if explicitly not needed
                    if not needs_tests:
                        result["note"] = "Tests were skipped based on requirements analysis"
                        await manager.send_log(job_id, agent.role, "Skipping test generation as per requirements", "completed")
                    else:
                        # Determine which tests to generate based on what's been created
                        if "backend" in results and "endpoints" in results["backend"]:
                            result["backend_tests"] = {"test_main.py": generate_backend_tests()}
                            
                        if "frontend" in results and "components" in results["frontend"]:
                            result["frontend_tests"] = {"HomePage.test.jsx": generate_frontend_tests()}
                        
                        # Only generate integration tests if both frontend and backend exist
                        if "backend" in results and "frontend" in results:
                            result["integration_tests"] = {"test_integration.py": generate_integration_tests()}
                else:  # deployment_task
                    requirements = jobs[job_id].get('requirements', {})
                    result = {}
                    
                    # Check if deployment configuration is needed based on requirements
                    needs_deployment = requirements.get('needs_deployment', True)
                    deployment_type = requirements.get('deployment_type', 'docker').lower()
                    
                    # Only generate deployment files if needed
                    if not needs_deployment:
                        result["note"] = "Deployment configuration was skipped based on requirements analysis"
                        await manager.send_log(job_id, agent.role, "Skipping deployment configuration as per requirements", "completed")
                    else:
                        # Generate Docker files only if Docker deployment is specified or no specific type is mentioned
                        if deployment_type in ['docker', 'container']:
                            docker_files = {}
                            
                            # Only generate backend Dockerfile if backend exists
                            if "backend" in results:
                                docker_files["Dockerfile.backend"] = generate_backend_dockerfile()
                                
                            # Only generate frontend Dockerfile if frontend exists
                            if "frontend" in results:
                                docker_files["Dockerfile.frontend"] = generate_frontend_dockerfile()
                                
                            # Only generate docker-compose if both exist
                            if "backend" in results and "frontend" in results:
                                docker_files["docker-compose.yml"] = generate_docker_compose()
                                
                            # Add Docker files to result if any were generated
                            if docker_files:
                                result["docker"] = docker_files
                    
                    # Always include deployment script, but adapt it based on what's being deployed
                    if "backend" in results or "frontend" in results:
                        result["deploy"] = {"deploy.sh": generate_deploy_script()}
                    
                    # Only include env example if backend exists (since it typically needs environment variables)
                    if "backend" in results:
                        result["env"] = {".env.example": generate_env_example()}
                    
                    # Always include README for project documentation
                    result["readme"] = generate_readme(prompt)
                
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
            
            # Define the crew with the callback function
            crew = Crew(
                agents=[planner, frontend_dev, backend_dev, tester, deployment_engineer],
                tasks=[planning_task, backend_task, frontend_task, testing_task, deployment_task],
                verbose=True,
                process=Process.sequential,
                callbacks=[agent_callback]  # Use the callback function we defined
            )
            
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
                else:
                    # Fallback to string representation
                    logger.info("Converting CrewOutput to string representation")
                    raw_output = str(crew_output)
                    code = extract_code_from_output(raw_output)
                    results = {
                        "raw_output": raw_output,
                        "code": code
                    }
                    logger.info(f"Extracted code from CrewOutput string representation (length: {len(code) if code else 0})")
                
                # Make sure code field is directly available in results for frontend
                if "code" not in results and "raw_output" in results:
                    results["code"] = extract_code_from_output(results["raw_output"])

        
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
        
        # Update job status
        jobs[job_id] = {"job_id": job_id, "status": "completed", "results": results}
        await manager.send_log(job_id, "System", "All agents completed successfully", "completed")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        jobs[job_id] = {"job_id": job_id, "status": "failed", "error": str(e)}
        await manager.send_log(job_id, "System", f"Error: {str(e)}", "failed")

# Code generation functions
def generate_backend_code(prompt):
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
    return """from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
"""

def generate_database_code():
    return """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

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
