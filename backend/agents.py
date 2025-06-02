from typing import Dict, Any, List
import ollama
import logging

# Import config to check if we're using mock data
from config import USE_MOCK_DATA

# Import crewai only if not using mock data
if not USE_MOCK_DATA:
    try:
        from crewai import Agent, Task
    except ImportError:
        logging.warning("CrewAI not installed. Only mock mode will work.")
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentSystem:
    """Manages the AI agent system for app generation"""
    
    def __init__(self, llm_name="phi3"):
        """Initialize the agent system with specified LLM"""
        self.llm_name = llm_name
        self.agents = self._create_agents()
        
    def _create_agents(self) -> Dict[str, Agent]:
        """Create all required agents for the system"""
        return {
            "planner": self._create_planner_agent(),
            "frontend": self._create_frontend_agent(),
            "backend": self._create_backend_agent(),
            "tester": self._create_tester_agent(),
            "deployment": self._create_deployment_agent()
        }
    
    def _create_planner_agent(self) -> Agent:
        """Create the planner agent"""
        return Agent(
            role="Planning Architect",
            goal="Create a detailed plan for the application based on user requirements",
            backstory="You are an expert systems architect who breaks down app ideas into clear, achievable plans. You analyze requirements and create detailed specifications.",
            verbose=True,
            allow_delegation=False,
            llm=ollama.chat(model=self.llm_name)
        )
    
    def _create_frontend_agent(self) -> Agent:
        """Create the frontend agent"""
        return Agent(
            role="Frontend Developer",
            goal="Create modern, responsive React components with Tailwind CSS",
            backstory="You are a skilled frontend developer specializing in React and Tailwind CSS. You create beautiful, responsive UI components that follow best practices.",
            verbose=True,
            allow_delegation=False,
            llm=ollama.chat(model=self.llm_name)
        )
    
    def _create_backend_agent(self) -> Agent:
        """Create the backend agent"""
        return Agent(
            role="Backend Engineer",
            goal="Develop robust FastAPI endpoints and data models",
            backstory="You are an experienced backend developer who specializes in FastAPI. You create efficient, well-structured API endpoints and data models.",
            verbose=True,
            allow_delegation=False,
            llm=ollama.chat(model=self.llm_name)
        )
    
    def _create_tester_agent(self) -> Agent:
        """Create the tester agent"""
        return Agent(
            role="Quality Assurance Engineer",
            goal="Write comprehensive tests to ensure application quality",
            backstory="You are a meticulous QA engineer who writes thorough tests to catch bugs and ensure application reliability.",
            verbose=True,
            allow_delegation=False,
            llm=ollama.chat(model=self.llm_name)
        )
    
    def _create_deployment_agent(self) -> Agent:
        """Create the deployment agent"""
        return Agent(
            role="DevOps Engineer",
            goal="Prepare deployment configuration for the application",
            backstory="You are a DevOps specialist who creates deployment configurations and ensures applications are ready for production.",
            verbose=True,
            allow_delegation=False,
            llm=ollama.chat(model=self.llm_name)
        )
    
    def create_tasks(self, prompt: str) -> Dict[str, Task]:
        """Create tasks for all agents based on the user prompt"""
        tasks = {}
        
        # Planner task
        tasks["planner"] = Task(
            description=f"Analyze the following app idea and create a detailed plan: {prompt}",
            expected_output="A JSON object with 'features', 'architecture', 'tech_stack', and 'timeline' fields",
            agent=self.agents["planner"]
        )
        
        # Backend task
        tasks["backend"] = Task(
            description="Create FastAPI backend code based on the planning document",
            expected_output="A JSON object with 'endpoints', 'models', 'database', and 'requirements' fields",
            agent=self.agents["backend"],
            context=[tasks["planner"]]
        )
        
        # Frontend task
        tasks["frontend"] = Task(
            description="Create React components with Tailwind CSS based on the planning document and backend API",
            expected_output="A JSON object with 'components', 'styles', 'routing', and 'package_json' fields",
            agent=self.agents["frontend"],
            context=[tasks["planner"], tasks["backend"]]
        )
        
        # Testing task
        tasks["tester"] = Task(
            description="Write tests for the backend and frontend code",
            expected_output="A JSON object with 'backend_tests', 'frontend_tests', and 'integration_tests' fields",
            agent=self.agents["tester"],
            context=[tasks["backend"], tasks["frontend"]]
        )
        
        # Deployment task
        tasks["deployment"] = Task(
            description="Create deployment configuration for the application",
            expected_output="A JSON object with 'docker', 'deploy', 'env', and 'readme' fields",
            agent=self.agents["deployment"],
            context=[tasks["backend"], tasks["frontend"], tasks["tester"]]
        )
        
        return tasks

# Template responses for code generation (used when LLM isn't available)
class CodeTemplates:
    """Provides template code for different parts of the application"""
    
    @staticmethod
    def backend_main(app_name: str) -> str:
        """Generate main FastAPI file"""
        return f"""from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="{app_name} API", version="1.0.0")

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
    {{"id": 1, "title": "Sample Item 1", "description": "This is a sample item"}},
    {{"id": 2, "title": "Sample Item 2", "description": "Another sample item"}},
]

@app.get("/")
async def root():
    return {{"message": "Welcome to {app_name} API"}}

@app.get("/api/data")
async def get_data():
    return items

@app.post("/api/data")
async def create_item(item: Item):
    item.id = len(items) + 1
    items.append(item.dict())
    return item

@app.get("/api/data/{{item_id}}")
async def get_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

    @staticmethod
    def react_app_component() -> str:
        """Generate React App component"""
        return """import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-blue-900">
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;"""

    @staticmethod
    def react_home_component() -> str:
        """Generate React Home component"""
        return """import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const HomePage = () => {
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState(null);
  const [activeTab, setActiveTab] = useState('frontend');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    
    setIsProcessing(true);
    setLogs([]);
    setResults(null);
    
    try {
      // Start the job
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      
      const data = await response.json();
      const jobId = data.job_id;
      
      // Connect to WebSocket for real-time logs
      const ws = new WebSocket(`ws://localhost:8000/ws/${jobId}`);
      
      ws.onmessage = (event) => {
        const logData = JSON.parse(event.data);
        setLogs(prevLogs => [...prevLogs, logData]);
      };
      
      // Poll for job completion
      const checkInterval = setInterval(async () => {
        const statusRes = await fetch(`/api/jobs/${jobId}`);
        const statusData = await statusRes.json();
        
        if (statusData.status === 'completed') {
          clearInterval(checkInterval);
          setResults(statusData.results);
          setIsProcessing(false);
          ws.close();
        } else if (statusData.status === 'failed') {
          clearInterval(checkInterval);
          setIsProcessing(false);
          ws.close();
          alert('Job failed: ' + statusData.error);
        }
      }, 2000);
      
    } catch (error) {
      console.error('Error:', error);
      setIsProcessing(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-5xl font-bold text-white mb-4">
          🤖 AI Agent App Builder
        </h1>
        <p className="text-xl text-gray-300">
          Transform your ideas into production-ready apps with AI agents
        </p>
      </motion.div>
      
      {/* Form section */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white bg-opacity-10 backdrop-filter backdrop-blur-lg rounded-2xl p-6 mb-8 border border-white border-opacity-20"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-white text-lg font-semibold mb-2">
              Describe your app idea:
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., I want a movie recommendation app using TMDB API with user ratings and favorites..."
              className="w-full h-32 p-4 bg-white bg-opacity-10 border border-white border-opacity-20 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
              disabled={isProcessing}
            />
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={isProcessing || !prompt.trim()}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold py-4 px-8 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-all duration-300"
          >
            {isProcessing ? (
              <span className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                Agents Working...
              </span>
            ) : (
              '🚀 Launch AI Agents'
            )}
          </motion.button>
        </form>
      </motion.div>
      
      {/* Results section - only shown when results are available */}
      {(isProcessing || results) && (
        <div className="grid lg:grid-cols-3 gap-8 mt-8">
          {/* Agent Status Panel */}
          <div className="bg-white bg-opacity-10 backdrop-filter backdrop-blur-lg rounded-2xl p-6 border border-white border-opacity-20">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
              <span className="mr-3">🔄</span>
              Agent Pipeline
            </h2>
            {/* Agent status items would go here */}
          </div>
          
          {/* Agent Logs */}
          <div className="bg-white bg-opacity-10 backdrop-filter backdrop-blur-lg rounded-2xl p-6 border border-white border-opacity-20">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
              <span className="mr-3">📊</span>
              Agent Console
            </h2>
            <div className="bg-black bg-opacity-50 rounded-lg p-4 h-80 overflow-y-auto font-mono">
              {logs.length === 0 ? (
                <div className="text-gray-400 text-center py-8">
                  Agent logs will appear here...
                </div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="mb-2 text-sm">
                    <span className="text-gray-500">[{log.timestamp}]</span>
                    <span className={`${log.status === 'completed' ? 'text-green-400' : 'text-blue-400'}`}> {log.message}</span>
                  </div>
                ))
              )}
            </div>
          </div>
          
          {/* Code Preview Panel */}
          <div className="bg-white bg-opacity-10 backdrop-filter backdrop-blur-lg rounded-2xl p-6 border border-white border-opacity-20">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
              <span className="mr-3">💻</span>
              Code Preview
            </h2>
            {/* Code preview tabs and content would go here */}
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;"""
