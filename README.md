# AI Agent App Builder

A full-stack web application that uses AI agents to convert natural language app ideas into production-ready code.

## Features

- **Prompt Input**: Describe your app idea in natural language
- **Agent System**: Multiple AI agents collaborate to build your application
- **Real-time Status**: Track the progress of each agent in real-time
- **Code Generation**: Frontend, backend, tests, and deployment code
- **Preview & Deploy**: Download or deploy your generated application

## Tech Stack

- **Frontend**: React + Tailwind CSS + Framer Motion
- **Backend**: FastAPI + CrewAI
- **LLMs**: Open-source models via Ollama (Phi-3, Mistral, etc.)
- **Agent Orchestration**: CrewAI for agent definition and collaboration

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- Ollama (for running local LLMs)

### Backend Setup

1. Install dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```

2. Start the backend server:
   ```
   python main.py
   ```

### Frontend Setup

1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

## Using the Application

1. Ensure Ollama is running with the required models (phi, mistral)
2. Enter your app idea in the prompt input
3. Click "Launch AI Agents" to start the generation process
4. Monitor the progress in the Agent Status panel
5. View the generated code in the Code Viewer
6. Download the complete project as a ZIP file

## Agent System

The application uses the following agents:

- **Planner Agent**: Analyzes the prompt and creates a project plan
- **Frontend Agent**: Generates React components and UI
- **Backend Agent**: Creates FastAPI endpoints and business logic
- **Tester Agent**: Writes tests for the application
- **Deployment Agent**: Prepares deployment files and configuration
