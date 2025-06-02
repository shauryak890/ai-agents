import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { saveAs } from 'file-saver';
import JSZip from 'jszip';
import axios from 'axios';

// Import components
import PromptInput from './PromptInput';
import AgentStatusVisualizer from './AgentStatusVisualizer';
import LogViewer from './LogViewer';
import CodeViewer from './CodeViewer';
import DeploymentPanel from './DeploymentPanel';
import SubscriptionPanel from './SubscriptionPanel';

const HomePage = () => {
  // State
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState(null);
  const [activeTab, setActiveTab] = useState('frontend');
  const [activeFile, setActiveFile] = useState(null);
  const [agentStatuses, setAgentStatuses] = useState({
    planner: 'pending',
    frontend: 'pending',
    backend: 'pending',
    tester: 'pending',
    deployment: 'pending'
  });
  
  // WebSocket reference
  const wsRef = useRef(null);
  
  // Effect for establishing WebSocket connection
  useEffect(() => {
    if (jobId) {
      const wsUrl = `ws://${window.location.hostname}:8000/ws/${jobId}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLogs(prevLogs => [...prevLogs, data]);
        
        // Update agent status based on log
        if (data.agent) {
          const agentKey = data.agent.toLowerCase().includes('plan') ? 'planner' : 
                          data.agent.toLowerCase().includes('front') ? 'frontend' :
                          data.agent.toLowerCase().includes('back') ? 'backend' :
                          data.agent.toLowerCase().includes('test') ? 'tester' :
                          data.agent.toLowerCase().includes('dev') ? 'deployment' : null;
          
          if (agentKey && data.status) {
            setAgentStatuses(prev => ({
              ...prev,
              [agentKey]: data.status === 'completed' ? 'completed' : 'running'
            }));
          }
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      wsRef.current = ws;
      
      return () => {
        ws.close();
      };
    }
  }, [jobId]);
  
  // Effect for polling job status
  useEffect(() => {
    let interval;
    
    if (jobId && isProcessing) {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`/api/jobs/${jobId}`);
          if (response.data.status === 'completed') {
            setResults(response.data.results);
            setIsProcessing(false);
            clearInterval(interval);
            
            // Set all agents to completed
            setAgentStatuses({
              planner: 'completed',
              frontend: 'completed',
              backend: 'completed',
              tester: 'completed',
              deployment: 'completed'
            });
            
            // Set initial active file
            if (response.data.results && response.data.results.frontend && 
                response.data.results.frontend.components) {
              const firstComponentKey = Object.keys(response.data.results.frontend.components)[0];
              setActiveFile({
                type: 'frontend',
                category: 'components',
                name: firstComponentKey,
                content: response.data.results.frontend.components[firstComponentKey]
              });
            }
          } else if (response.data.status === 'failed') {
            setIsProcessing(false);
            clearInterval(interval);
            alert('Job failed: ' + response.data.error);
          }
        } catch (error) {
          console.error('Error polling job status:', error);
        }
      }, 2000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [jobId, isProcessing]);
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    
    setIsProcessing(true);
    setResults(null);
    setLogs([]);
    setJobId(null);
    setAgentStatuses({
      planner: 'pending',
      frontend: 'pending',
      backend: 'pending',
      tester: 'pending',
      deployment: 'pending'
    });
    
    try {
      const response = await axios.post('/api/generate', { prompt });
      setJobId(response.data.job_id);
      
      // Mark planner as running initially
      setAgentStatuses(prev => ({
        ...prev,
        planner: 'running'
      }));
      
    } catch (error) {
      console.error('Error starting job:', error);
      setIsProcessing(false);
      alert('Failed to start job: ' + error.message);
    }
  };
  
  // Download project as ZIP
  const downloadProject = async () => {
    if (!results) return;
    
    const zip = new JSZip();
    
    // Add README
    if (results.deployment && results.deployment.readme) {
      zip.file('README.md', results.deployment.readme);
    }
    
    // Backend files
    const backend = zip.folder('backend');
    if (results.backend) {
      if (results.backend.endpoints) {
        Object.entries(results.backend.endpoints).forEach(([fileName, content]) => {
          backend.file(fileName, content);
        });
      }
      
      if (results.backend.models) {
        Object.entries(results.backend.models).forEach(([fileName, content]) => {
          backend.file(fileName, content);
        });
      }
      
      if (results.backend.database) {
        Object.entries(results.backend.database).forEach(([fileName, content]) => {
          backend.file(fileName, content);
        });
      }
      
      if (results.backend.requirements) {
        backend.file('requirements.txt', results.backend.requirements);
      }
    }
    
    // Frontend files
    const frontend = zip.folder('frontend');
    if (results.frontend) {
      const src = frontend.folder('src');
      const components = src.folder('components');
      
      if (results.frontend.components) {
        Object.entries(results.frontend.components).forEach(([fileName, content]) => {
          if (fileName === 'App.jsx') {
            src.file(fileName, content);
          } else {
            components.file(fileName, content);
          }
        });
      }
      
      if (results.frontend.styles) {
        Object.entries(results.frontend.styles).forEach(([fileName, content]) => {
          src.file(fileName, content);
        });
      }
      
      if (results.frontend.package_json) {
        frontend.file('package.json', JSON.stringify(results.frontend.package_json, null, 2));
      }
    }
    
    // Tests
    const tests = zip.folder('tests');
    if (results.tester) {
      if (results.tester.backend_tests) {
        const backendTests = tests.folder('backend');
        Object.entries(results.tester.backend_tests).forEach(([fileName, content]) => {
          backendTests.file(fileName, content);
        });
      }
      
      if (results.tester.frontend_tests) {
        const frontendTests = tests.folder('frontend');
        Object.entries(results.tester.frontend_tests).forEach(([fileName, content]) => {
          frontendTests.file(fileName, content);
        });
      }
      
      if (results.tester.integration_tests) {
        const integrationTests = tests.folder('integration');
        Object.entries(results.tester.integration_tests).forEach(([fileName, content]) => {
          integrationTests.file(fileName, content);
        });
      }
    }
    
    // Deployment files
    if (results.deployment) {
      if (results.deployment.docker) {
        Object.entries(results.deployment.docker).forEach(([fileName, content]) => {
          zip.file(fileName, content);
        });
      }
      
      if (results.deployment.deploy) {
        Object.entries(results.deployment.deploy).forEach(([fileName, content]) => {
          zip.file(fileName, content);
        });
      }
      
      if (results.deployment.env) {
        Object.entries(results.deployment.env).forEach(([fileName, content]) => {
          zip.file(fileName, content);
        });
      }
    }
    
    // Generate and download zip
    const content = await zip.generateAsync({ type: 'blob' });
    saveAs(content, 'generated-project.zip');
  };
  
  // Handle file selection in the code viewer
  const handleFileSelect = (type, category, name, content) => {
    setActiveFile({ type, category, name, content });
  };
  
  // Get file extension for syntax highlighting
  const getFileExtension = (fileName) => {
    if (fileName.endsWith('.py')) return 'python';
    if (fileName.endsWith('.jsx')) return 'jsx';
    if (fileName.endsWith('.js')) return 'javascript';
    if (fileName.endsWith('.css')) return 'css';
    if (fileName.endsWith('.html')) return 'html';
    if (fileName.endsWith('.json')) return 'json';
    if (fileName.endsWith('.md')) return 'markdown';
    if (fileName.endsWith('.sh')) return 'bash';
    if (fileName.endsWith('.yml') || fileName.endsWith('.yaml')) return 'yaml';
    if (fileName.endsWith('.Dockerfile') || fileName === 'Dockerfile') return 'dockerfile';
    if (fileName.endsWith('.env')) return 'bash';
    return 'text';
  };
  
  // Preview URL for generated app (simulated)
  const getPreviewUrl = () => {
    return `http://localhost:3000/preview?jobId=${jobId}`;
  };
  
  // Generate a code preview list from results
  const getCodeFiles = (agentType) => {
    if (!results || !results[agentType]) return [];
    
    const files = [];
    const agentData = results[agentType];
    
    // Process different categories of files
    Object.entries(agentData).forEach(([category, items]) => {
      if (typeof items === 'object' && !Array.isArray(items)) {
        Object.entries(items).forEach(([name, content]) => {
          if (typeof content === 'string') {
            files.push({
              type: agentType,
              category,
              name,
              content
            });
          }
        });
      }
    });
    
    return files;
  };

  // Agent icons
  const agentIcons = {
    planner: '🧠',
    frontend: '🎨',
    backend: '⚙️',
    tester: '🧪',
    deployment: '🚀'
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
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

      {/* Prompt Input Area */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-effect rounded-2xl p-6 mb-8"
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

      {/* Main content area (only visible when processing or when results are available) */}
      {(isProcessing || results) && (
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Agent Status Visualizer */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-effect rounded-2xl p-6"
          >
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
              <span className="mr-3">🔄</span>
              Agent Pipeline
            </h2>
            <div className="space-y-4">
              {Object.entries(agentStatuses).map(([agent, status]) => (
                <motion.div
                  key={agent}
                  className={`flex items-center p-3 rounded-lg transition-all duration-300 ${
                    status === 'running' ? 'bg-blue-500 bg-opacity-30 agent-glow' :
                    status === 'completed' ? 'bg-green-500 bg-opacity-30' : 
                    'bg-gray-500 bg-opacity-20'
                  }`}
                  animate={status === 'running' ? { scale: [1, 1.02, 1] } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <div className={`text-2xl mr-3 ${status === 'running' ? 'typing' : ''}`}>
                    {agentIcons[agent]}
                  </div>
                  <div className="flex-1">
                    <div className="text-white font-semibold capitalize">
                      {agent} Agent
                    </div>
                    <div className="text-sm text-gray-300">
                      {status === 'running' ? 'Processing...' :
                      status === 'completed' ? 'Completed' : 'Waiting'}
                    </div>
                  </div>
                  <div className="ml-3">
                    {status === 'running' && (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    )}
                    {status === 'completed' && (
                      <div className="text-green-400 text-xl">✓</div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
          
          {/* Agent Logs */}
          <LogViewer logs={logs} />
        </div>
      )}
      
      {/* Main Content Area - conditional rendering based on state */}
      {isProcessing && (
        <motion.div 
          initial={{opacity: 0, y: 20}}
          animate={{opacity: 1, y: 0}}
          className="grid md:grid-cols-2 gap-8 mb-8"
        >
          {/* Agent Status Visualizer */}
          <AgentStatusVisualizer 
            agents={[
              {
                name: 'Planning Agent',
                description: 'Analyzes requirements and creates app structure',
                status: agentStatuses.planner,
                completionTime: agentStatuses.planner === 'completed' ? 3 : null
              },
              {
                name: 'Frontend Developer Agent',
                description: 'Designs and implements UI components',
                status: agentStatuses.frontend,
                completionTime: agentStatuses.frontend === 'completed' ? 8 : null
              },
              {
                name: 'Backend Engineer Agent',
                description: 'Creates API endpoints and database models',
                status: agentStatuses.backend,
                completionTime: agentStatuses.backend === 'completed' ? 6 : null
              },
              {
                name: 'Testing Agent',
                description: 'Writes tests and validates functionality',
                status: agentStatuses.tester,
                completionTime: agentStatuses.tester === 'completed' ? 4 : null
              },
              {
                name: 'Deployment Engineer Agent',
                description: 'Prepares deployment configuration',
                status: agentStatuses.deployment,
                completionTime: agentStatuses.deployment === 'completed' ? 2 : null
              }
            ]}
          />
          
          {/* Agent Logs */}
          <LogViewer logs={logs} />
        </motion.div>
      )}

      {/* Results View */}
      {results && (
        <motion.div 
          initial={{opacity: 0, y: 20}}
          animate={{opacity: 1, y: 0}}
          className="mb-8"
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center">
              <span className="mr-3">✨</span>
              Generated App
            </h2>
            <motion.button
              whileHover={{scale: 1.05}}
              whileTap={{scale: 0.95}}
              onClick={downloadProject}
              className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg"
            >
              <span className="mr-2">⬇️</span>
              Download Project
            </motion.button>
          </div>
          
          {/* Code Preview */}
          <CodeViewer 
            results={results} 
          />
        </motion.div>
      )}

      {/* Preview & Deploy Panel */}
      {results && (
        <motion.div 
          initial={{opacity: 0, y: 20}}
          animate={{opacity: 1, y: 0}}
          className="mt-8 mb-8"
        >
          <DeploymentPanel 
            isGenerationComplete={results !== null}
            onPreview={() => window.open(getPreviewUrl(), '_blank')}
            onDeploy={() => alert('Deployment simulation started!')}
          />
        </motion.div>
      )}

      {/* Subscription Panel - Always visible */}
      <motion.div
        initial={{opacity: 0, y: 20}}
        animate={{opacity: 1, y: 0}}
        transition={{delay: 0.3}}
        className="mt-8"
      >
        <SubscriptionPanel />
      </motion.div>
    </div>
  );
};

export default HomePage;
