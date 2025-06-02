"""
Templates for code generation used by agents
"""

def generate_frontend_template(app_name, features):
    """Generate React frontend template code"""
    return f"""
import React, {{ useState, useEffect }} from 'react';
import {{ BrowserRouter as Router, Routes, Route }} from 'react-router-dom';
import {{ motion }} from 'framer-motion';
import axios from 'axios';
import './App.css';

function App() {{
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    // Fetch data from API
    const fetchData = async () => {{
      try {{
        const response = await axios.get('/api/data');
        setData(response.data);
        setLoading(false);
      }} catch (error) {{
        console.error('Error fetching data:', error);
        setLoading(false);
      }}
    }};

    fetchData();
  }}, []);

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
        <header className="p-4 bg-black bg-opacity-30">
          <div className="container mx-auto">
            <h1 className="text-2xl font-bold text-white">{app_name}</h1>
          </div>
        </header>
        
        <main className="container mx-auto p-4">
          {{loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
            </div>
          ) : (
            <div>
              {/* App content goes here */}
              <h2 className="text-xl text-white mb-4">Features:</h2>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {features_list}
              </ul>
            </div>
          )}}
        </main>
      </div>
    </Router>
  );
}}

export default App;
"""

def generate_backend_template(app_name):
    """Generate FastAPI backend template code"""
    return f"""
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import uuid
from datetime import datetime

app = FastAPI(title="{app_name} API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data models
class Item(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    created_at: Optional[datetime] = None

# Sample in-memory database
items_db = []

@app.get("/")
async def root():
    return {{"message": "Welcome to {app_name} API"}}

@app.get("/api/data")
async def get_data():
    return items_db

@app.post("/api/items")
async def create_item(item: Item):
    item_dict = item.dict()
    item_dict["id"] = str(uuid.uuid4())
    item_dict["created_at"] = datetime.now()
    items_db.append(item_dict)
    return item_dict

@app.get("/api/items/{{item_id}}")
async def get_item(item_id: str):
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
"""

def generate_test_template(app_name):
    """Generate test template code"""
    return f"""
# Backend Tests (pytest)
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {{"message": "Welcome to {app_name} API"}}

def test_get_data():
    response = client.get("/api/data")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_item():
    item = {{"name": "Test Item", "description": "Test Description"}}
    response = client.post("/api/items", json=item)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == "Test Item"

# Frontend Tests (React Testing Library)
import React from 'react';
import {{ render, screen }} from '@testing-library/react';
import App from './App';

test('renders the app name', () => {{
  render(<App />);
  const appNameElement = screen.getByText(/{app_name}/i);
  expect(appNameElement).toBeInTheDocument();
}});

test('shows loading state initially', () => {{
  render(<App />);
  const loadingElement = screen.getByRole('status');
  expect(loadingElement).toBeInTheDocument();
}});
"""

def generate_deployment_template(app_name):
    """Generate deployment template code"""
    return f"""
# Dockerfile for Backend
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dockerfile for Frontend
FROM node:16-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always

# Environment Variables
ENVIRONMENT=development
DEBUG=True
API_URL=http://localhost:8000
"""

def generate_readme_template(app_name, description, features, tech_stack):
    """Generate README template"""
    feature_list = "\n".join([f"- {feature}" for feature in features])
    tech_list = "\n".join([f"- {tech}" for tech in tech_stack])
    
    return f"""# {app_name}

{description}

## Features

{feature_list}

## Tech Stack

{tech_list}

## Installation

### Prerequisites
- Node.js 16 or higher
- Python 3.10 or higher
- Docker (optional, for containerized deployment)

### Backend Setup
1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the server:
   ```
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

## Deployment

### Using Docker
1. Build and run with Docker Compose:
   ```
   docker-compose up --build
   ```

## API Documentation
- API documentation is available at `/docs` endpoint when the backend is running.

## Generated by AI Agent App Builder
This application was automatically generated using AI Agent App Builder.
"""

def generate_tailwind_config():
    """Generate Tailwind CSS configuration"""
    return """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
        secondary: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
          950: '#2e1065',
        },
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(79, 70, 229, 0.6)' },
          '100%': { boxShadow: '0 0 20px rgba(79, 70, 229, 0.8)' },
        }
      },
    },
  },
  plugins: [],
}
"""
