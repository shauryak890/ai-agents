from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import os
import uuid
import logging
from datetime import datetime

# Import config to check if we're using mock data
from config import USE_MOCK_DATA

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

# Agent definitions
def create_planner_agent():
    return Agent(
        role="Planning Architect",
        goal="Create a detailed plan for the application based on user requirements",
        backstory="You are an expert systems architect who breaks down app ideas into clear, achievable plans. You analyze requirements and create detailed specifications.",
        verbose=True,
        allow_delegation=False,
        llm=ollama.chat(model="phi3")
    )

def create_frontend_agent():
    return Agent(
        role="Frontend Developer",
        goal="Create modern, responsive React components with Tailwind CSS",
        backstory="You are a skilled frontend developer specializing in React and Tailwind CSS. You create beautiful, responsive UI components that follow best practices.",
        verbose=True,
        allow_delegation=False,
        llm=ollama.chat(model="phi3")
    )

def create_backend_agent():
    return Agent(
        role="Backend Engineer",
        goal="Develop robust FastAPI endpoints and data models",
        backstory="You are an experienced backend developer who specializes in FastAPI. You create efficient, well-structured API endpoints and data models.",
        verbose=True,
        allow_delegation=False,
        llm=ollama.chat(model="phi3")
    )

def create_tester_agent():
    return Agent(
        role="Quality Assurance Engineer",
        goal="Write comprehensive tests to ensure application quality",
        backstory="You are a meticulous QA engineer who writes thorough tests to catch bugs and ensure application reliability.",
        verbose=True,
        allow_delegation=False,
        llm=ollama.chat(model="phi3")
    )

def create_deployment_agent():
    return Agent(
        role="DevOps Engineer",
        goal="Prepare deployment configuration for the application",
        backstory="You are a DevOps specialist who creates deployment configurations and ensures applications are ready for production.",
        verbose=True,
        allow_delegation=False,
        llm=ollama.chat(model="phi3")
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
@app.get("/")
async def root():
    return {"message": "AI Agent App Builder API"}

@app.post("/api/generate")
async def generate_app(request: AppRequest):
    job_id = str(uuid.uuid4())
    
    # Start job in background
    asyncio.create_task(process_app_request(job_id, request.prompt))
    
    return {"job_id": job_id, "message": "Job started"}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
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
    jobs[job_id] = {"job_id": job_id, "status": "running", "results": None}
    
    try:
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
        
        planning_task = Task(
            description=f"Analyze the following app idea and create a detailed plan: {prompt}",
            expected_output="A JSON object with 'features', 'architecture', 'tech_stack', and 'timeline' fields",
            agent=planner
        )
        
        backend_task = Task(
            description="Create FastAPI backend code based on the planning document",
            expected_output="A JSON object with 'endpoints', 'models', 'database', and 'requirements' fields",
            agent=backend_dev,
            context=[planning_task]
        )
        
        frontend_task = Task(
            description="Create React components with Tailwind CSS based on the planning document and backend API",
            expected_output="A JSON object with 'components', 'styles', 'routing', and 'package_json' fields",
            agent=frontend_dev,
            context=[planning_task, backend_task]
        )
        
        testing_task = Task(
            description="Write tests for the backend and frontend code",
            expected_output="A JSON object with 'backend_tests', 'frontend_tests', and 'integration_tests' fields",
            agent=tester,
            context=[backend_task, frontend_task]
        )
        
        deployment_task = Task(
            description="Create deployment configuration for the application",
            expected_output="A JSON object with 'docker', 'deploy', 'env', and 'readme' fields",
            agent=deployment_engineer,
            context=[backend_task, frontend_task, testing_task]
        )
        
        # Create crew
        crew = Crew(
            agents=[planner, frontend_dev, backend_dev, tester, deployment_engineer],
            tasks=[planning_task, backend_task, frontend_task, testing_task, deployment_task],
            verbose=2,
            process=Process.sequential
        )
        
        # Track progress
        current_agent = None
        
        # Define custom callback
        def agent_callback(agent, task, output):
            nonlocal current_agent
            current_agent = agent.role
            asyncio.run(manager.send_log(job_id, agent.role, f"Working on: {task.description[:100]}..."))
            return output
        
        # Execute tasks
        await manager.send_log(job_id, "System", "Starting AI agents")
        
        # Run crew
        results = {}
        
        # Simulate crew execution with proper logging
        for i, task in enumerate([planning_task, backend_task, frontend_task, testing_task, deployment_task]):
            agent = task.agent
            await manager.send_log(job_id, agent.role, f"Starting work on {task.description[:100]}...")
            
            # Simulate agent working
            await asyncio.sleep(2)  # Simulating work time
            
            # Generate a result based on the task
            if task == planning_task:
                result = {
                    "features": ["User authentication", "Data visualization", "API integration"],
                    "architecture": {
                        "frontend": "React with Tailwind CSS",
                        "backend": "FastAPI",
                        "database": "SQLite for development"
                    },
                    "tech_stack": ["React", "Tailwind CSS", "FastAPI", "SQLite"],
                    "timeline": "MVP in 2-3 days"
                }
            elif task == backend_task:
                result = {
                    "endpoints": {
                        "main.py": generate_backend_code(prompt)
                    },
                    "models": {
                        "models.py": generate_models_code()
                    },
                    "database": {
                        "database.py": generate_database_code()
                    },
                    "requirements": generate_requirements()
                }
            elif task == frontend_task:
                result = {
                    "components": {
                        "App.jsx": generate_app_jsx(),
                        "HomePage.jsx": generate_home_page_jsx()
                    },
                    "styles": {
                        "App.css": generate_app_css()
                    },
                    "routing": {
                        "routes": [
                            {"path": "/", "component": "HomePage"},
                            {"path": "/preview", "component": "PreviewPage"}
                        ]
                    },
                    "package_json": generate_package_json()
                }
            elif task == testing_task:
                result = {
                    "backend_tests": {
                        "test_main.py": generate_backend_tests()
                    },
                    "frontend_tests": {
                        "HomePage.test.jsx": generate_frontend_tests()
                    },
                    "integration_tests": {
                        "test_integration.py": generate_integration_tests()
                    }
                }
            else:  # deployment_task
                result = {
                    "docker": {
                        "Dockerfile.backend": generate_backend_dockerfile(),
                        "Dockerfile.frontend": generate_frontend_dockerfile(),
                        "docker-compose.yml": generate_docker_compose()
                    },
                    "deploy": {
                        "deploy.sh": generate_deploy_script()
                    },
                    "env": {
                        ".env.example": generate_env_example()
                    },
                    "readme": generate_readme(prompt)
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
