import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { saveAs } from 'file-saver';
import JSZip from 'jszip';

// Import components
import PromptInput from './PromptInput';
import AgentStatusVisualizer from './AgentStatusVisualizer';
import LogViewer from './LogViewer';
import CodeViewer from './CodeViewer';
import DeploymentPanel from './DeploymentPanel';
import LivePreview from './LivePreview';
import Navbar from './Navbar';
import ValidationResults from './ValidationResults';

const HomePage = () => {
  // State
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState(null);
  const [activeTab, setActiveTab] = useState('code'); // For code/preview tabs
  const [activeFileTab, setActiveFileTab] = useState('frontend'); // For file selection
  const [activeFile, setActiveFile] = useState(null);
  
  // Agent icons
  const agentIcons = {
    planner: '🧠',
    frontend: '🎨',
    backend: '⚙️',
    tester: '🧪',
    deployment: '🚀'
  };
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
  
  // Effect to check validation results and switch to validation tab when errors are found
  useEffect(() => {
    if (results?.validation && results.validation.error_count > 0) {
      // Auto-switch to validation tab if there are errors
      setActiveTab('validation');
    }
  }, [results]);
  
  // Handle form submission
  const handleSubmit = async (promptValue) => {
    // Use the prompt from state or the argument
    const inputPrompt = promptValue || prompt;
    if (!inputPrompt.trim()) return;
    
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
      const response = await axios.post('/api/generate', { prompt: inputPrompt });
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
    setActiveFileTab(type); // Update the active file tab when selecting a file
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
    // This is used for the external preview button
    // For the embedded preview, we use the LivePreview component
    return `http://localhost:3000/preview?jobId=${jobId}`;
  };

  // Check if preview is available
  const isPreviewAvailable = () => {
    return jobId !== null && results !== null;
  };

  // Generate a code preview list from results
  const getCodeFiles = (agentType) => {
    if (!results || !results[agentType]) return [];
    const agentResult = results[agentType];
    const files = [];
    
    // Process all file categories for the agent
    Object.keys(agentResult).forEach(category => {
      if (typeof agentResult[category] === 'object') {
        Object.keys(agentResult[category]).forEach(fileName => {
          files.push({
            name: fileName,
            content: agentResult[category][fileName],
            category: category,
            type: agentType
          });
        });
      }
    });
    
    return files;
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Fixed Navbar */}
      <Navbar />
      
      <div className="container mx-auto px-4 pt-24 pb-16">  {/* Added pt-24 to account for navbar height */}
      
      {/* Main welcome section with app description */}
      {!isProcessing && !results && (
        <div className="max-w-5xl mx-auto text-center mb-12">
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600 mb-4"
          >
            Build Apps with AI Agents
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl text-gray-300 max-w-3xl mx-auto mb-10"
          >
            Describe your app idea, and our specialized AI agents will build a complete, functional application for you in minutes.
          </motion.p>
          
          {/* Single Prompt Input */}
          <motion.div 
            initial={{opacity: 0, y: 20}}
            animate={{opacity: 1, y: 0}}
            className="max-w-4xl mx-auto mb-12"
          >
            <PromptInput 
              value={prompt}
              onChange={setPrompt}
              onSubmit={handleSubmit}
              isProcessing={isProcessing}
            />
          </motion.div>
          
          {/* Live Preview */}
          <motion.div 
            initial={{opacity: 0, y: 20}}
            animate={{opacity: 1, y: 0}}
            transition={{ delay: 0.2 }}
            className="mb-12 bg-gray-800 rounded-lg overflow-hidden shadow-2xl" 
            style={{ height: '400px' }}
          >
            <h3 className="bg-gray-700 p-3 text-lg font-medium text-white flex items-center">
              <span className="inline-block w-3 h-3 rounded-full bg-green-400 mr-2"></span>
              Live Preview
            </h3>
            <LivePreview results={null} isVisible={true} />
          </motion.div>

          {/* Examples Section */}
          <motion.h2 
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            transition={{ delay: 0.3 }}
            className="text-2xl font-bold text-white mb-6"
          >
            Start with a Template
          </motion.h2>
          
          <motion.div 
            initial={{opacity: 0, y: 20}}
            animate={{opacity: 1, y: 0}}
            transition={{ delay: 0.4 }}
            className="grid md:grid-cols-3 gap-6">
            {[
              {
                emoji: "📊",
                title: "Dashboard App",
                description: "Create a data dashboard with charts and filters"
              },
              {
                emoji: "📝",
                title: "Todo Application",
                description: "Build a task manager with categories and due dates"
              },
              {
                emoji: "🛒",
                title: "E-commerce Store",
                description: "Design a simple online store with product listings"
              }
            ].map((item, i) => (
              <motion.div
                key={i}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.98 }}
                className="bg-gray-800 bg-opacity-50 backdrop-blur-sm p-6 rounded-xl border border-gray-700 cursor-pointer"
                onClick={() => setPrompt(item.description)}
              >
                <div className="text-3xl mb-3">{item.emoji}</div>
                <h3 className="text-xl font-medium text-white mb-2">{item.title}</h3>
                <p className="text-gray-400">{item.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      )}
      
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
          
          {/* Tabs for Code and Preview */}
          <div className="mb-4">
            <div className="flex border-b border-gray-700">
              <button 
                className={`py-2 px-4 ${activeTab === 'code' ? 'text-blue-400 border-b-2 border-blue-400 font-medium' : 'text-gray-400 hover:text-gray-300'}`}
                onClick={() => setActiveTab('code')}
              >
                Code
              </button>
              <button 
                className={`py-2 px-4 ${activeTab === 'preview' ? 'text-blue-400 border-b-2 border-blue-400 font-medium' : 'text-gray-400 hover:text-gray-300'}`}
                onClick={() => setActiveTab('preview')}
              >
                Live Preview
              </button>
              <button 
                className={`py-2 px-4 ${activeTab === 'validation' ? 'text-blue-400 border-b-2 border-blue-400 font-medium' : 'text-gray-400 hover:text-gray-300'}`}
                onClick={() => setActiveTab('validation')}
              >
                Validation {results?.validation?.error_count > 0 && <span className="ml-1 px-2 py-1 text-xs bg-red-500 text-white rounded-full">{results.validation.error_count}</span>}
              </button>
            </div>
          </div>
          
          {/* Code Preview */}
          <div className={activeTab === 'code' ? 'block' : 'hidden'}>
            <CodeViewer results={results} />
          </div>
          
          {/* Live Preview */}
          <div className={activeTab === 'preview' ? 'block' : 'hidden'} style={{ height: '600px' }}>
            <LivePreview results={results} isVisible={activeTab === 'preview'} />
          </div>
          
          {/* Validation Results */}
          <div className={activeTab === 'validation' ? 'block' : 'hidden'}>
            <ValidationResults validation={results?.validation} jobId={jobId} />
          </div>
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
            onPreview={() => {
              alert('This is a simulated preview. In a production environment, this would open the deployed application. Currently, the app exists only as generated code that can be downloaded.');
            }}
            onDeploy={() => alert('Deployment simulation started! In a production environment, this would deploy your application to a hosting service.')}
          />
        </motion.div>
      )}

      </div>
    </div>
  );
};

export default HomePage;
