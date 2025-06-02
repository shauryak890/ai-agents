"""
Mock data for simulating agent responses without using LLMs.
Used when USE_MOCK_DATA=true in environment variables.
"""

import json
import random
import time
from typing import Dict, Any, List

# Sample app templates for different types of applications
APP_TEMPLATES = {
    "movie": {
        "features": [
            "Movie browsing",
            "Search functionality",
            "Rating system",
            "User preferences",
            "Watchlist management"
        ],
        "architecture": {
            "frontend": "React with Tailwind CSS",
            "backend": "FastAPI with SQLite",
            "database": "SQLite for development",
            "deployment": "Vercel/Railway"
        },
        "tech_stack": ["React", "Tailwind CSS", "FastAPI", "SQLite", "TMDB API"],
        "timeline": "MVP in 2-3 days"
    },
    "todo": {
        "features": [
            "Task creation",
            "Task completion",
            "Categories",
            "Due dates",
            "Priority levels"
        ],
        "architecture": {
            "frontend": "React with Tailwind CSS",
            "backend": "FastAPI with SQLite",
            "database": "SQLite for development",
            "deployment": "Vercel/Railway"
        },
        "tech_stack": ["React", "Tailwind CSS", "FastAPI", "SQLite"],
        "timeline": "MVP in 1-2 days"
    },
    "chat": {
        "features": [
            "Real-time messaging",
            "User authentication",
            "Chat rooms",
            "Message history",
            "Typing indicators"
        ],
        "architecture": {
            "frontend": "React with Tailwind CSS",
            "backend": "FastAPI with WebSockets",
            "database": "SQLite for development",
            "deployment": "Vercel/Railway"
        },
        "tech_stack": ["React", "Tailwind CSS", "FastAPI", "WebSockets", "SQLite"],
        "timeline": "MVP in 3-4 days"
    },
    "ecommerce": {
        "features": [
            "Product catalog",
            "Shopping cart",
            "User accounts",
            "Order management",
            "Payment integration"
        ],
        "architecture": {
            "frontend": "React with Tailwind CSS",
            "backend": "FastAPI with SQLAlchemy",
            "database": "PostgreSQL",
            "deployment": "Vercel/Railway"
        },
        "tech_stack": ["React", "Tailwind CSS", "FastAPI", "SQLAlchemy", "PostgreSQL", "Stripe API"],
        "timeline": "MVP in 4-5 days"
    },
    "default": {
        "features": [
            "User interface",
            "Data management",
            "Core functionality",
            "Responsive design"
        ],
        "architecture": {
            "frontend": "React with Tailwind CSS",
            "backend": "FastAPI",
            "database": "SQLite for development",
            "deployment": "Vercel/Railway"
        },
        "tech_stack": ["React", "Tailwind CSS", "FastAPI", "SQLite"],
        "timeline": "MVP in 2-3 days"
    }
}

def get_plan_for_prompt(prompt: str) -> Dict[str, Any]:
    """Generate a mock planning result based on the user prompt"""
    prompt_lower = prompt.lower()
    
    if "movie" in prompt_lower or "film" in prompt_lower or "cinema" in prompt_lower:
        template = APP_TEMPLATES["movie"]
    elif "todo" in prompt_lower or "task" in prompt_lower or "list" in prompt_lower:
        template = APP_TEMPLATES["todo"]
    elif "chat" in prompt_lower or "message" in prompt_lower:
        template = APP_TEMPLATES["chat"]
    elif "ecommerce" in prompt_lower or "shop" in prompt_lower or "store" in prompt_lower:
        template = APP_TEMPLATES["ecommerce"]
    else:
        template = APP_TEMPLATES["default"]
    
    # Add some randomness to make it look more realistic
    return {
        "features": template["features"],
        "architecture": template["architecture"],
        "tech_stack": template["tech_stack"],
        "timeline": template["timeline"]
    }

def generate_backend_code(app_type: str) -> Dict[str, Dict[str, str]]:
    """Generate mock backend code based on the app type"""
    # This would be much more extensive in a real implementation
    result = {
        "endpoints": {
            "main.py": get_backend_main_py(app_type),
        },
        "models": {
            "models.py": get_backend_models_py(app_type),
        },
        "database": {
            "database.py": get_backend_database_py(),
        },
        "requirements": get_backend_requirements(),
    }
    return result

def generate_frontend_code(app_type: str) -> Dict[str, Any]:
    """Generate mock frontend code based on the app type"""
    # This would be much more extensive in a real implementation
    result = {
        "components": {
            "App.jsx": get_frontend_app_jsx(),
            "HomePage.jsx": get_frontend_home_page_jsx(app_type),
            f"{app_type.capitalize()}List.jsx": get_frontend_list_component(app_type),
            f"{app_type.capitalize()}Item.jsx": get_frontend_item_component(app_type),
        },
        "styles": {
            "index.css": get_frontend_index_css(),
            "App.css": get_frontend_app_css(),
        },
        "routing": {
            "routes": [
                {"path": "/", "component": "HomePage"},
                {"path": "/list", "component": f"{app_type.capitalize()}List"},
                {"path": "/item/:id", "component": f"{app_type.capitalize()}Item"},
            ]
        },
        "package_json": get_frontend_package_json()
    }
    return result

def generate_tests(app_type: str) -> Dict[str, Dict[str, str]]:
    """Generate mock tests based on the app type"""
    # This would be much more extensive in a real implementation
    result = {
        "backend_tests": {
            "test_main.py": get_backend_test_main_py(app_type),
        },
        "frontend_tests": {
            "HomePage.test.jsx": get_frontend_home_page_test_jsx(app_type),
        },
        "integration_tests": {
            "test_integration.py": get_integration_test_py(app_type),
        }
    }
    return result

def generate_deployment_files(app_type: str, plan: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Generate mock deployment files based on the app type and plan"""
    # This would be much more extensive in a real implementation
    result = {
        "docker": {
            "Dockerfile.backend": get_dockerfile_backend(),
            "Dockerfile.frontend": get_dockerfile_frontend(),
            "docker-compose.yml": get_docker_compose_yml(),
        },
        "deploy": {
            "deploy.sh": get_deploy_script(),
        },
        "env": {
            ".env.example": get_env_example(),
        },
        "readme": get_readme(app_type, plan),
    }
    return result

# These functions would return actual code templates in a real implementation
# For brevity, I'm just returning placeholders
def get_backend_main_py(app_type: str) -> str:
    return f"""from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="{app_type.capitalize()} API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class {app_type.capitalize()}Item(BaseModel):
    id: Optional[int] = None
    title: str
    description: str

# Sample data
items = [
    {{"id": 1, "title": "Sample {app_type} 1", "description": "This is a sample {app_type}"}},
    {{"id": 2, "title": "Sample {app_type} 2", "description": "Another sample {app_type}"}},
]

@app.get("/")
async def root():
    return {{"message": "Welcome to your {app_type} API"}}

@app.get("/api/items")
async def get_items():
    return items

@app.post("/api/items")
async def create_item(item: {app_type.capitalize()}Item):
    item.id = len(items) + 1
    items.append(item.dict())
    return item

@app.get("/api/items/{{item_id}}")
async def get_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

def get_backend_models_py(app_type: str) -> str:
    return f"""from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class {app_type.capitalize()}Item(Base):
    __tablename__ = "{app_type}_items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
"""

def get_backend_database_py() -> str:
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

def get_backend_requirements() -> str:
    return """fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-multipart==0.0.6
crewai==0.28.2
langchain==0.0.344
requests==2.31.0
python-dotenv==1.0.0
websockets==11.0.3
aiofiles==23.2.1
numpy==1.26.1
Jinja2==3.1.2
ollama==0.1.5
huggingface-hub==0.19.4"""

def get_frontend_app_jsx() -> str:
    return """import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;"""

def get_frontend_home_page_jsx(app_type: str) -> str:
    return f"""import React, {{ useState, useEffect }} from 'react';
import {{ motion }} from 'framer-motion';

const HomePage = () => {{
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    fetchData();
  }}, []);

  const fetchData = async () => {{
    try {{
      const response = await fetch('/api/items');
      const result = await response.json();
      setData(result);
    }} catch (error) {{
      console.error('Error fetching data:', error);
    }} finally {{
      setLoading(false);
    }}
  }};

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-5xl font-bold text-white mb-4">
          {app_type.capitalize()} App
        </h1>
        <p className="text-xl text-gray-300">
          Your awesome {app_type} application
        </p>
      </motion.div>

      {{loading ? (
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {{data.map((item, index) => (
            <motion.div 
              key={{index}}
              whileHover={{ scale: 1.05 }}
              className="bg-white bg-opacity-10 p-6 rounded-lg shadow-md"
            >
              <h3 className="text-xl font-semibold mb-2 text-white">{{item.title}}</h3>
              <p className="text-gray-300">{{item.description}}</p>
            </motion.div>
          ))}}
        </div>
      )}}
    </div>
  );
}};

export default HomePage;"""

def get_frontend_list_component(app_type: str) -> str:
    return f"""import React, {{ useState, useEffect }} from 'react';
import {{ motion }} from 'framer-motion';
import {{ Link }} from 'react-router-dom';

const {app_type.capitalize()}List = () => {{
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    fetchItems();
  }}, []);

  const fetchItems = async () => {{
    try {{
      const response = await fetch('/api/items');
      const data = await response.json();
      setItems(data);
    }} catch (error) {{
      console.error('Error fetching items:', error);
    }} finally {{
      setLoading(false);
    }}
  }};

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-6">All {app_type.capitalize()} Items</h1>
      
      {{loading ? (
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {{items.map((item) => (
            <motion.div
              key={{item.id}}
              whileHover={{ scale: 1.05 }}
              className="bg-white bg-opacity-10 p-6 rounded-lg shadow-md"
            >
              <h3 className="text-xl font-semibold mb-2 text-white">{{item.title}}</h3>
              <p className="text-gray-300 mb-4">{{item.description}}</p>
              <Link 
                to={{`/item/${{item.id}}`}}
                className="text-blue-400 hover:text-blue-300"
              >
                View Details
              </Link>
            </motion.div>
          ))}}
        </div>
      )}}
    </div>
  );
}};

export default {app_type.capitalize()}List;"""

def get_frontend_item_component(app_type: str) -> str:
    return f"""import React, {{ useState, useEffect }} from 'react';
import {{ useParams, useNavigate }} from 'react-router-dom';
import {{ motion }} from 'framer-motion';

const {app_type.capitalize()}Item = () => {{
  const {{ id }} = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    fetchItem();
  }}, [id]);

  const fetchItem = async () => {{
    try {{
      const response = await fetch(`/api/items/${{id}}`);
      if (!response.ok) {{
        throw new Error('Item not found');
      }}
      const data = await response.json();
      setItem(data);
    }} catch (error) {{
      console.error('Error fetching item:', error);
      navigate('/list');
    }} finally {{
      setLoading(false);
    }}
  }};

  if (loading) {{
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }}

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div
        initial={{{{ opacity: 0, y: 20 }}}}
        animate={{{{ opacity: 1, y: 0 }}}}
        className="bg-white bg-opacity-10 p-8 rounded-lg shadow-lg max-w-2xl mx-auto"
      >
        <h1 className="text-3xl font-bold text-white mb-4">{{{{item.title}}}}</h1>
        <p className="text-gray-300 mb-6">{{{{item.description}}}}</p>
        
        <div className="flex justify-between">
          <button
            onClick={{{{() => navigate('/list')}}}}
            className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded"
          >
            Back to List
          </button>
          
          <button
            className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded"
          >
            Edit {app_type.capitalize()}
          </button>
        </div>
      </motion.div>
    </div>
  );
}};

export default {app_type.capitalize()}Item;"""

def get_frontend_index_css() -> str:
    return """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}"""

def get_frontend_app_css() -> str:
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
  @apply bg-white bg-opacity-10 shadow-md rounded-lg p-6;
}"""

def get_frontend_package_json() -> Dict[str, Any]:
    return {
        "name": "generated-app",
        "version": "1.0.0",
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.16.0",
            "framer-motion": "^10.16.4"
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^4.1.0",
            "tailwindcss": "^3.3.3",
            "vite": "^4.4.11"
        }
    }

def get_backend_test_main_py(app_type: str) -> str:
    return f"""import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {{"message": "Welcome to your {app_type} API"}}

def test_get_items():
    response = client.get("/api/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_item():
    item_data = {{"title": "Test {app_type}", "description": "Test Description"}}
    response = client.post("/api/items", json=item_data)
    assert response.status_code == 200
    assert response.json()["title"] == "Test {app_type}"

def test_get_item():
    response = client.get("/api/items/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1"""

def get_frontend_home_page_test_jsx(app_type: str) -> str:
    return f"""import {{ render, screen }} from '@testing-library/react';
import {{ BrowserRouter }} from 'react-router-dom';
import HomePage from '../components/HomePage';

const renderWithRouter = (component) => {{
  return render(
    <BrowserRouter>
      {{component}}
    </BrowserRouter>
  );
}};

test('renders homepage title', () => {{
  renderWithRouter(<HomePage />);
  const titleElement = screen.getByText(/{app_type} app/i);
  expect(titleElement).toBeInTheDocument();
}});

test('shows loading spinner initially', () => {{
  renderWithRouter(<HomePage />);
  const spinner = screen.getByRole('status');
  expect(spinner).toBeInTheDocument();
}});"""

def get_integration_test_py(app_type: str) -> str:
    return f"""import pytest
import requests
import time

BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="module")
def wait_for_server():
    # Wait for server to be ready
    for _ in range(30):
        try:
            response = requests.get(f"{{BASE_URL}}/")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        pytest.fail("Server did not start in time")

def test_full_api_flow(wait_for_server):
    # Test creating an item
    item_data = {{"title": "Integration Test {app_type}", "description": "Full flow test"}}
    response = requests.post(f"{{BASE_URL}}/api/items", json=item_data)
    assert response.status_code == 200
    
    # Test getting all items
    response = requests.get(f"{{BASE_URL}}/api/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0"""

def get_dockerfile_backend() -> str:
    return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]"""

def get_dockerfile_frontend() -> str:
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

def get_docker_compose_yml() -> str:
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

def get_deploy_script() -> str:
    return """#!/bin/bash

echo "🚀 Starting deployment..."

# Build and start services
docker-compose up --build -d

echo "✅ Deployment complete!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"""

def get_env_example() -> str:
    return """# Database
DATABASE_URL=sqlite:///./app.db

# API
API_URL=http://localhost:8000

# Environment
NODE_ENV=development
DEBUG=true"""

def get_readme(app_type: str, plan: Dict[str, Any]) -> str:
    features = "\n".join([f"- {feature}" for feature in plan["features"]])
    tech_stack = "\n".join([f"- {tech}" for tech in plan["tech_stack"]])
    
    return f"""# {app_type.capitalize()} Application

## Features
{features}

## Tech Stack
{tech_stack}

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

def simulate_agent_execution(prompt: str) -> Dict[str, Any]:
    """Simulate the execution of the agent system with mock data"""
    app_type = "app"
    if "movie" in prompt.lower():
        app_type = "movie"
    elif "todo" in prompt.lower():
        app_type = "todo"
    elif "chat" in prompt.lower():
        app_type = "chat"
    elif "ecommerce" in prompt.lower() or "shop" in prompt.lower():
        app_type = "ecommerce"
    
    # Generate mock results
    plan_result = get_plan_for_prompt(prompt)
    backend_result = generate_backend_code(app_type)
    frontend_result = generate_frontend_code(app_type)
    test_result = generate_tests(app_type)
    deployment_result = generate_deployment_files(app_type, plan_result)
    
    return {
        "planner": plan_result,
        "backend": backend_result,
        "frontend": frontend_result,
        "tester": test_result,
        "deployment": deployment_result
    }
