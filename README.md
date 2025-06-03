# CrewAI App Builder

A full-stack web application that uses CrewAI agents to convert natural language app ideas into production-ready code with real-time progress tracking and code validation.

## Features

- **Prompt Input**: Describe your app idea in natural language
- **Agent System**: Multiple AI agents collaborate to build your application
- **Real-time Status**: Track the progress of each agent in real-time with detailed task updates
- **Code Generation**: Frontend, backend, tests, and deployment code
- **Code Validation**: Automatic validation of generated code with error detection and fix suggestions
- **Preview & Deploy**: Download or deploy your generated application
- **Terminal Output**: Real-time logs of the generation process

## Tech Stack

- **Frontend**: React + Tailwind CSS + Framer Motion
- **Backend**: FastAPI + CrewAI
- **LLMs**: Open-source models via Ollama (Phi-3, Mistral, etc.)
- **Agent Orchestration**: CrewAI for agent definition and collaboration
- **Code Validation**: Integrated validation system for JavaScript, Python, HTML, and CSS
- **Real-time Communication**: WebSockets for live agent status updates

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
4. Monitor the progress in the Agent Status panel and terminal output
5. View the generated code in the Code Viewer after completion
6. Check the Validation tab for any code quality issues and suggested fixes
7. Download the complete project as a ZIP file

## Features in Detail

### Real-time Agent Status
- Track each agent's progress with detailed task information
- See which tasks are in progress, completed, or waiting
- Visual progress bar shows overall completion percentage

### Terminal Output
- View detailed logs from the CrewAI backend
- See real-time updates as agents work on tasks
- Terminal can be toggled on/off for better UI experience

### Code Viewer
- Browse generated code files organized by category (Frontend, Backend, etc.)
- Syntax highlighting for all supported languages
- Copy individual files or download the entire project

### Code Validation
- Automatic validation of all generated code files
- Detection of syntax errors, formatting issues, and potential bugs
- Suggested fixes for common coding problems
- Error count badge shows the number of issues found

## Agent System

The application uses the following CrewAI agents:

- **Planning Architect**: Analyzes the prompt and creates a project plan
- **Frontend Developer**: Generates React components and UI
- **Backend Engineer**: Creates FastAPI endpoints and business logic
- **Quality Assurance Engineer**: Writes tests for the application
- **DevOps Engineer**: Prepares deployment files and configuration
