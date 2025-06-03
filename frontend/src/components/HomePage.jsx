import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { saveAs } from 'file-saver';
import JSZip from 'jszip';

// Import components
import PromptInput from './PromptInput';
import AgentStatusVisualizer from './AgentStatusVisualizer';
import CodeViewer from './CodeViewer';
import DeploymentPanel from './DeploymentPanel';
import LivePreview from './LivePreview';
import ValidationResults from './ValidationResults';
import RequirementsDisplay from './RequirementsDisplay';
import Terminal from './Terminal';

// Logo SVG component
const CrewAILogo = () => (
  <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M18 3.375C18 3.375 22.5 9 31.5 9C31.5 9 31.5 24.75 18 32.625C4.5 24.75 4.5 9 4.5 9C13.5 9 18 3.375 18 3.375Z" fill="url(#crew_gradient)" stroke="#FFF" strokeWidth="2" />
    <path d="M18 8.4375C18 8.4375 20.25 11.25 25.125 11.25C25.125 11.25 25.125 19.6875 18 24.1875C10.875 19.6875 10.875 11.25 10.875 11.25C15.75 11.25 18 8.4375 18 8.4375Z" fill="#FFF" />
    <defs>
      <linearGradient id="crew_gradient" x1="4.5" y1="32.625" x2="31.5" y2="3.375" gradientUnits="userSpaceOnUse">
        <stop stopColor="#3B82F6" />
        <stop offset="1" stopColor="#8B5CF6" />
      </linearGradient>
    </defs>
  </svg>
);

const HomePage = () => {
  // State
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState(null);
  const [requirements, setRequirements] = useState(null);
  const [activeTab, setActiveTab] = useState('code'); // For code/preview tabs
  const [activeFile, setActiveFile] = useState(null);
  const [showTerminal, setShowTerminal] = useState(true); // Toggle terminal view - default to shown
  const [terminalOutput, setTerminalOutput] = useState([]); // Store formatted terminal output
  const [currentStep, setCurrentStep] = useState('waiting'); // Track current step in the process
  
  // CrewAI agent statuses
  const [agentStatuses, setAgentStatuses] = useState({
    planner: 'pending',    // Planning Architect
    backend: 'pending',    // Backend Engineer
    frontend: 'pending',   // Frontend Developer
    tester: 'pending',     // Quality Assurance Engineer
    deployment: 'pending'  // DevOps Engineer
  });
  
  // Progress tracking
  const [overallProgress, setOverallProgress] = useState(0);
  const [taskCompletionCount, setTaskCompletionCount] = useState(0);
  
  // WebSocket reference
  const wsRef = useRef(null);
  
  // Toggle terminal view
  const toggleTerminal = () => {
    setShowTerminal(!showTerminal);
  };

  // Handle downloading code
  const handleDownloadCode = () => {
    // Extract all code files from different result formats
    const extractFilesFromResults = (results) => {
      if (!results) return {};
      
      // First check if results.code exists (typical format)
      if (results.code && typeof results.code === 'object') {
        return results.code;
      }
      
      // Then check for files structure
      if (results.files && typeof results.files === 'object') {
        return results.files;
      }
      
      // Try to find code in CrewAI's nested structure
      const extractedFiles = {};
      
      // Look for code in sections like frontend, backend, etc.
      const sections = ['frontend', 'backend', 'deployment', 'tests'];
      let foundSections = false;
      
      sections.forEach(section => {
        if (results[section] && typeof results[section] === 'object') {
          foundSections = true;
          
          // Check for different possible structures
          if (results[section].files) {
            Object.entries(results[section].files).forEach(([filename, content]) => {
              extractedFiles[`${section}/${filename}`] = content;
            });
          } else if (results[section].code) {
            Object.entries(results[section].code).forEach(([filename, content]) => {
              extractedFiles[`${section}/${filename}`] = content;
            });
          }
        }
      });
      
      if (foundSections && Object.keys(extractedFiles).length > 0) {
        return extractedFiles;
      }
      
      // Look for any keys that seem like filenames
      const possibleFiles = Object.keys(results).filter(key => 
        key.includes('.') || /\.(js|jsx|ts|tsx|py|html|css|json|md)$/.test(key)
      );
      
      if (possibleFiles.length > 0) {
        const fileMap = {};
        possibleFiles.forEach(filename => {
          fileMap[filename] = results[filename];
        });
        return fileMap;
      }
      
      return {};
    };
    
    const allFiles = extractFilesFromResults(results);
    
    // Check if we have any files to download
    if (!results || Object.keys(allFiles).length === 0) {
      console.error('No code results available for download');
      // Show an error message to the user
      setTerminalOutput(prev => [...prev, { type: 'error', content: 'No code available for download. Please try again.' }]);
      return;
    }
    
    console.log('Preparing code download...', Object.keys(allFiles));
    const zip = new JSZip();
    
    // Add each file to the zip
    Object.entries(allFiles).forEach(([filename, content]) => {
      // Handle different folder structures
      zip.file(filename, content);
      console.log(`Added ${filename} to zip file`);
    });
    
    // Generate the zip file
    zip.generateAsync({ type: 'blob' })
      .then(content => {
        console.log('Zip file generated, initiating download...');
        
        // Use FileSaver to trigger the download
        saveAs(content, 'generated-code.zip');
        
        // Show success message in terminal
        setTerminalOutput(prev => [...prev, { type: 'success', content: 'Code downloaded successfully!' }]);
      })
      .catch(err => {
        console.error('Error generating zip file:', err);
        setTerminalOutput(prev => [...prev, { type: 'error', content: `Error generating zip file: ${err.message}` }]);
      });
  };
  
  // Simulation of progress updates for demo purposes - only when actually processing
  useEffect(() => {
    // Only run the simulation when we're actually processing a job
    if (!isProcessing) {
      // Reset all agent statuses to pending when not processing
      setAgentStatuses({
        planner: 'pending',
        backend: 'pending',
        frontend: 'pending',
        tester: 'pending',
        deployment: 'pending'
      });
      setLogs([]);
      return;
    }
    
    // Start simulation of engineer progress
    const simulationInterval = setInterval(() => {
      // Randomly choose which agent to update
      const agents = ['planner', 'backend', 'frontend', 'tester', 'deployment'];
      const randomAgent = agents[Math.floor(Math.random() * 3)]; // Focus on first 3 agents
      
      setAgentStatuses(prev => {
        const newStatuses = {...prev};
        
        // Simulate progress based on current state
        if (newStatuses.planner === 'pending') {
          newStatuses.planner = 'running';
        } else if (newStatuses.planner === 'running' && Math.random() > 0.7) {
          newStatuses.planner = 'completed';
          
          // Add a log entry
          setLogs(prevLogs => [
            ...prevLogs, 
            { message: '# Agent: Planning Architect\n## Task Completed: System architecture finalized' }
          ]);
          
          // Start next agent
          if (newStatuses.backend === 'pending') {
            newStatuses.backend = 'running';
          }
        }
        
        // Advance backend engineer
        if (newStatuses.backend === 'running' && newStatuses.planner === 'completed' && Math.random() > 0.8) {
          newStatuses.backend = 'completed';
          
          // Add a log entry
          setLogs(prevLogs => [
            ...prevLogs, 
            { message: '# Agent: Backend Engineer\n## Task Completed: API endpoints created' }
          ]);
          
          // Start frontend developer
          if (newStatuses.frontend === 'pending') {
            newStatuses.frontend = 'running';
          }
        }
        
        // Advance frontend developer
        if (newStatuses.frontend === 'running' && newStatuses.backend === 'completed' && Math.random() > 0.85) {
          newStatuses.frontend = 'completed';
          
          // Add a log entry
          setLogs(prevLogs => [
            ...prevLogs, 
            { message: '# Agent: Frontend Developer\n## Task Completed: UI components implemented' }
          ]);
          
          // Start QA engineer
          if (newStatuses.tester === 'pending') {
            newStatuses.tester = 'running';
          }
        }
        
        // Advance QA engineer
        if (newStatuses.tester === 'running' && newStatuses.frontend === 'completed' && Math.random() > 0.9) {
          newStatuses.tester = 'completed';
          
          // Add a log entry
          setLogs(prevLogs => [
            ...prevLogs, 
            { message: '# Agent: Quality Assurance Engineer\n## Task Completed: All tests passing' }
          ]);
          
          // Start DevOps engineer
          if (newStatuses.deployment === 'pending') {
            newStatuses.deployment = 'running';
          }
        }
        
        // Advance DevOps engineer
        if (newStatuses.deployment === 'running' && newStatuses.tester === 'completed' && Math.random() > 0.95) {
          newStatuses.deployment = 'completed';
          
          // Add a log entry
          setLogs(prevLogs => [
            ...prevLogs, 
            { message: '# Agent: DevOps Engineer\n## Task Completed: Deployment configuration ready' }
          ]);
        }
        
        return newStatuses;
      });
      
      // Add appropriate log messages for ongoing tasks
      setLogs(prevLogs => {
        // Only add a new log message occasionally
        if (Math.random() > 0.7) {
          const taskMessages = {
            planner: [
              '# Agent: Planning Architect\n## Analyzing system requirements',
              '# Agent: Planning Architect\n## Creating component diagram',
              '# Agent: Planning Architect\n## Finalizing architecture plan'
            ],
            backend: [
              '# Agent: Backend Engineer\n## Setting up database schema',
              '# Agent: Backend Engineer\n## Implementing API endpoints',
              '# Agent: Backend Engineer\n## Writing database queries'
            ],
            frontend: [
              '# Agent: Frontend Developer\n## Creating UI components',
              '# Agent: Frontend Developer\n## Setting up state management',
              '# Agent: Frontend Developer\n## Implementing responsive design'
            ],
            tester: [
              '# Agent: Quality Assurance Engineer\n## Writing test cases',
              '# Agent: Quality Assurance Engineer\n## Running integration tests',
              '# Agent: Quality Assurance Engineer\n## Fixing edge cases'
            ],
            deployment: [
              '# Agent: DevOps Engineer\n## Setting up CI/CD pipeline',
              '# Agent: DevOps Engineer\n## Configuring deployment environments',
              '# Agent: DevOps Engineer\n## Finalizing deployment scripts'
            ]
          };
          
          // Get the current statuses
          const runningAgents = Object.entries(agentStatuses)
            .filter(([_, status]) => status === 'running')
            .map(([agent]) => agent);
          
          if (runningAgents.length > 0) {
            // Choose a random running agent
            const agent = runningAgents[Math.floor(Math.random() * runningAgents.length)];
            const messages = taskMessages[agent];
            
            if (messages && messages.length > 0) {
              const message = messages[Math.floor(Math.random() * messages.length)];
              return [...prevLogs, { message }];
            }
          }
        }
        
        return prevLogs;
      });
      
    }, 3000); // Update every 3 seconds
    
    // Clean up the interval when component unmounts
    return () => clearInterval(simulationInterval);
  }, []); // Run once on component mount
  
  // Effect for establishing WebSocket connection
  useEffect(() => {
    if (jobId) {
      const wsUrl = `ws://${window.location.hostname}:8000/ws/${jobId}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setTerminalOutput(prev => [...prev, { type: 'info', content: 'WebSocket connected' }]);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLogs(prevLogs => [...prevLogs, data]);
        
        // Add to terminal output
        if (data.message) {
          setTerminalOutput(prev => [...prev, { type: 'message', content: data.message }]);

          // Parse CrewAI specific messages
          if (data.message.includes('Crew Execution Started')) {
            setCurrentStep('started');
            setOverallProgress(5);
            
            // Reset agent statuses on new execution
            setAgentStatuses({
              planner: 'running',    // Start with Planning Architect in running state
              backend: 'pending',    
              frontend: 'pending',  
              tester: 'pending',     
              deployment: 'pending'
            });
          }
          
          // Update agent statuses based on message content
          // Planning Architect status updates
          if (data.message.includes('Planning Architect') || data.message.includes('Architect Agent')) {
            if (data.message.includes('Task Completed') || data.message.includes('✅ Completed')) {
              setAgentStatuses(prev => ({ ...prev, planner: 'completed' }));
            } else if (!data.message.includes('Status: pending')) {
              setAgentStatuses(prev => ({ ...prev, planner: 'running' }));
            }
          }
          
          // Backend Engineer status updates
          if (data.message.includes('Backend Engineer')) {
            if (data.message.includes('Task Completed') || data.message.includes('✅ Completed')) {
              setAgentStatuses(prev => ({ ...prev, backend: 'completed' }));
            } else if (!data.message.includes('Status: pending')) {
              setAgentStatuses(prev => ({ ...prev, backend: 'running' }));
            }
          }
          
          // Frontend Developer status updates
          if (data.message.includes('Frontend Developer')) {
            if (data.message.includes('Task Completed') || data.message.includes('✅ Completed')) {
              setAgentStatuses(prev => ({ ...prev, frontend: 'completed' }));
            } else if (!data.message.includes('Status: pending')) {
              setAgentStatuses(prev => ({ ...prev, frontend: 'running' }));
            }
          }
          
          // QA Engineer status updates
          if (data.message.includes('QA Engineer') || data.message.includes('Quality Assurance')) {
            if (data.message.includes('Task Completed') || data.message.includes('✅ Completed')) {
              setAgentStatuses(prev => ({ ...prev, tester: 'completed' }));
            } else if (!data.message.includes('Status: pending')) {
              setAgentStatuses(prev => ({ ...prev, tester: 'running' }));
            }
          }
          
          // DevOps Engineer status updates
          if (data.message.includes('DevOps Engineer')) {
            if (data.message.includes('Task Completed') || data.message.includes('✅ Completed')) {
              setAgentStatuses(prev => ({ ...prev, deployment: 'completed' }));
            } else if (!data.message.includes('Status: pending')) {
              setAgentStatuses(prev => ({ ...prev, deployment: 'running' }));
            }
          }
          
          // Parse task information
          const taskMatch = data.message.match(/Task: ([0-9a-f-]+)/);
          if (taskMatch) {
            const taskId = taskMatch[1];
            // Track task ID and update relevant agent status
            console.log(`Detected task: ${taskId}`);
            
            // If we see a new task and can't determine which agent,
            // assume it's the next one in the pipeline
            if (data.message.includes('Executing Task')) {
              // Check the current state and advance the next pending agent
              setAgentStatuses(prev => {
                const newStatuses = {...prev};
                if (prev.planner === 'completed' && prev.backend === 'pending') {
                  newStatuses.backend = 'running';
                } else if (prev.backend === 'completed' && prev.frontend === 'pending') {
                  newStatuses.frontend = 'running';
                } else if (prev.frontend === 'completed' && prev.tester === 'pending') {
                  newStatuses.tester = 'running';
                } else if (prev.tester === 'completed' && prev.deployment === 'pending') {
                  newStatuses.deployment = 'running';
                }
                return newStatuses;
              });
            }
          }
          
          // Track agent progress
          if (data.message.includes('# Agent:')) {
            // Extract agent name
            const agentMatch = data.message.match(/# Agent: ([\\w\\s]+)/);
            if (agentMatch) {
              const agentName = agentMatch[1].trim();
              // Map the agent name to our state keys
              const agentKey = 
                agentName.toLowerCase().includes('planning') || agentName.toLowerCase().includes('architect') ? 'planner' : 
                agentName.toLowerCase().includes('front') ? 'frontend' : 
                agentName.toLowerCase().includes('back') ? 'backend' : 
                agentName.toLowerCase().includes('quality') || agentName.toLowerCase().includes('qa') ? 'tester' : 
                agentName.toLowerCase().includes('devops') ? 'deployment' : null;
                
              if (agentKey) {
                // Update agent status to running
                setAgentStatuses(prev => ({
                  ...prev, 
                  [agentKey]: 'running'
                }));
              }
            }
          }
          
          // Detect task completion
          if (data.message.includes('Task Completed')) {
            // Increment completed tasks counter
            setTaskCompletionCount(prev => prev + 1);
            setOverallProgress(prev => Math.min(prev + 20, 95)); // 5 tasks = 20% each
            
            // Check which agent completed
            const agentMatch = data.message.match(/Agent: ([\\w\\s]+)/);
            if (agentMatch) {
              const agentName = agentMatch[1].trim();
              // Map the agent name to our state keys
              const agentKey = 
                agentName.toLowerCase().includes('planning') || agentName.toLowerCase().includes('architect') ? 'planner' : 
                agentName.toLowerCase().includes('front') ? 'frontend' : 
                agentName.toLowerCase().includes('back') ? 'backend' : 
                agentName.toLowerCase().includes('quality') || agentName.toLowerCase().includes('qa') ? 'tester' : 
                agentName.toLowerCase().includes('devops') ? 'deployment' : null;
                
              if (agentKey) {
                // Update agent status to completed
                setAgentStatuses(prev => ({
                  ...prev, 
                  [agentKey]: 'completed'
                }));
              }
            }
          }
          
          // Detect Final Answer sections which contain code
          if (data.message.includes('## Final Answer:')) {
            setCurrentStep('generating');
          }
          
          // Detect Crew Completion message
          if (data.message.includes('Crew Execution Completed') || data.message.includes('Crew Completion')) {
            console.log('Crew execution completed, fetching results...');
            setTerminalOutput(prev => [...prev, { type: 'success', content: 'CrewAI execution completed successfully! Loading results...' }]);
            
            // Set all agents to completed state
            setAgentStatuses({
              planner: 'completed',
              backend: 'completed',
              frontend: 'completed',
              tester: 'completed',
              deployment: 'completed'
            });
            
            // Set progress to 100%
            setOverallProgress(100);
            
            // Immediately fetch the results instead of waiting for the next poll interval
            axios.get(`/api/jobs/${jobId}`)
              .then(response => {
                if (response.data.status === 'completed' || response.data.results) {
                  setResults(response.data.results);
                  if (response.data.results && response.data.results.requirements) {
                    setRequirements(response.data.results.requirements);
                  }
                  
                  // Keep isProcessing true until we actually show the results
                  // This prevents redirecting to the first page
                  setTimeout(() => {
                    setIsProcessing(false);
                    setCurrentStep('completed');
                    setActiveTab('code'); // Show code tab by default
                  }, 1000);
                }
              })
              .catch(error => {
                console.error('Error fetching results after completion:', error);
                // Even if there's an error, we should stop processing
                setIsProcessing(false);
              });
          }
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setTerminalOutput(prev => [...prev, { type: 'error', content: `WebSocket error: ${error.toString()}` }]);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setTerminalOutput(prev => [...prev, { type: 'info', content: 'WebSocket disconnected' }]);
      };
      
      wsRef.current = ws;
      
      return () => {
        ws.close();
      };
    }
  }, [jobId]);
  
  // Effect for polling job status
  useEffect(() => {
    let intervalId;
    
    if (jobId && isProcessing) {
      intervalId = setInterval(() => {
        axios.get(`/api/jobs/${jobId}`)
          .then(response => {
            if (response.data.status === 'completed') {
              // Don't immediately set isProcessing to false as it causes UI redirect
              // We'll do that after setting up the UI
              setResults(response.data.results);
              if (response.data.results && response.data.results.requirements) {
                setRequirements(response.data.results.requirements);
              }
              
              // Set final UI state
              setCurrentStep('completed');
              setActiveTab('code'); // Show code tab by default
              
              // Update all agent statuses to completed
              setAgentStatuses({
                planner: 'completed',
                backend: 'completed',
                frontend: 'completed',
                tester: 'completed',
                deployment: 'completed'
              });
              
              // Set progress to 100%
              setOverallProgress(100);
              
              // After a short delay, stop processing to ensure UI renders correctly
              setTimeout(() => {
                setIsProcessing(false);
              }, 500);
              
              clearInterval(intervalId);
            } else if (response.data.status === 'failed') {
              console.error('Job failed:', response.data.error);
              
              // Add error message to terminal
              setTerminalOutput(prev => [...prev, { type: 'error', content: `Job failed: ${response.data.error || 'Unknown error'}` }]);
              
              // Don't immediately set isProcessing to false
              // Let the user see the error message in the terminal
              setTimeout(() => {
                setIsProcessing(false);
              }, 2000);
              
              clearInterval(intervalId);
            }
          })
          .catch(error => {
            console.error('Error polling job status:', error);
          });
      }, 3000);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [jobId, isProcessing]);
  
  // Handle form submission
  const handleSubmit = (promptValue) => {
    setPrompt(promptValue);
    setIsProcessing(true);
    setLogs([]);
    setResults(null);
    setRequirements(null);
    setActiveTab('code');
    setAgentStatuses({
      planner: 'pending',
      backend: 'pending',
      frontend: 'pending',
      tester: 'pending',
      deployment: 'pending'
    });
    
    axios.post('/api/generate', { prompt: promptValue })
      .then(response => {
        setJobId(response.data.job_id);
      })
      .catch(error => {
        console.error('Error starting job:', error);
        setIsProcessing(false);
      });
  };
  
  // Download project as ZIP
  const downloadProject = () => {
    if (!results || !results.files) {
      return;
    }
    
    // Use same logic as handleDownloadCode
    handleDownloadCode();
  };
  
  return (
    <div className="min-h-screen text-white bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="container mx-auto px-4 pt-4 pb-32 relative z-10">
        {/* Header with logo and product name */}
        <div className="mb-12">
          <motion.div 
            initial={{opacity: 0, y: -20}}
            animate={{opacity: 1, y: 0}}
            className="flex items-center gap-4 mb-6"
          >
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
              <CrewAILogo />
            </div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
              CrewAI Studio
            </h1>
          </motion.div>
          
          <motion.p
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            transition={{delay: 0.1}}
            className="text-gray-300 mb-8 text-lg max-w-2xl"
          >
            Build complete web applications using multi-agent AI technology. 
            Watch in real-time as our specialized AI crew collaborates to bring your ideas to life.
          </motion.p>
          
          {isProcessing ? (
            <div className="bg-gray-800/80 backdrop-blur-sm border border-gray-700/50 rounded-xl p-5 shadow-lg">
              <div className="flex items-center mb-3">
                <div className="bg-blue-500/20 text-blue-400 p-2 rounded-lg mr-3">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-blue-300">Project In Progress</h3>
              </div>
              <p className="text-gray-300 mb-4">
                Your AI crew is currently working on generating your application based on the prompt:
                <span className="italic block mt-2 text-blue-200 bg-blue-900/30 p-2 rounded border border-blue-800/30">
                  "{prompt}"
                </span>
              </p>
              <div className="flex justify-between items-center">
                <button 
                  onClick={() => {
                    if (window.confirm('Are you sure you want to cancel the current job and start a new one? All progress will be lost.')) {
                      // Reset state
                      setIsProcessing(false);
                      setJobId(null);
                      setLogs([]);
                      setResults(null);
                      setRequirements(null);
                      setAgentStatuses({
                        planner: 'pending',
                        backend: 'pending',
                        frontend: 'pending',
                        tester: 'pending',
                        deployment: 'pending'
                      });
                    }
                  }}
                  className="text-red-400 hover:text-red-300 text-sm underline"
                >
                  Cancel current job
                </button>
                <div className="text-sm text-gray-400">Job ID: {jobId}</div>
              </div>
            </div>
          ) : (
            <PromptInput 
              onSubmit={handleSubmit} 
              initialValue={prompt}
            />
          )}
        </div>
        
        {/* Show CrewAI Agent Status Visualizer only when processing */}
        {isProcessing && (
          <div className="mb-8">
            <AgentStatusVisualizer 
              agentStatuses={agentStatuses}
              logs={logs} 
              onStatusUpdate={(updates) => {
                // Update agent statuses when the visualizer detects changes
                setAgentStatuses(prevStatuses => ({
                  ...prevStatuses,
                  ...updates
                }));
              }}
            />
          </div>
        )}
        
        {/* Toggle Terminal button */}
        <div className="fixed bottom-4 right-4 z-20">
          <motion.button
            whileHover={{scale: 1.05}}
            whileTap={{scale: 0.95}}
            onClick={toggleTerminal}
            className="bg-gray-800 p-3 rounded-full shadow-lg hover:bg-gray-700"
          >
            <span className="sr-only">Toggle Terminal</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="4 17 10 11 4 5"></polyline>
              <line x1="12" y1="19" x2="20" y2="19"></line>
            </svg>
          </motion.button>
        </div>
        
        {/* Terminal panel (togglable) */}
        {showTerminal && (
          <div className="fixed bottom-0 left-0 right-0 h-1/3 bg-gray-900 border-t border-gray-700 z-10">
            <Terminal 
              logs={logs} 
              terminalOutput={terminalOutput} 
              isVisible={showTerminal} 
              onClose={toggleTerminal}
            />
          </div>
        )}
        
        {/* Examples Section - Temporarily hidden */}
        {false && !isProcessing && !results && (
          <>
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
              className="grid md:grid-cols-3 gap-6"
            >
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
          </>
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
            
            {/* Tabs navigation */}
            <div className="flex border-b border-gray-700 mb-4">
              <button 
                className={`px-4 py-2 ${activeTab === 'requirements' ? 'text-blue-500 border-b-2 border-blue-500' : 'text-gray-400'}`}
                onClick={() => setActiveTab('requirements')}
              >
                Requirements
              </button>
              <button 
                className={`px-4 py-2 ${activeTab === 'code' ? 'text-blue-500 border-b-2 border-blue-500' : 'text-gray-400'}`}
                onClick={() => setActiveTab('code')}
              >
                Code
              </button>
              <button 
                className={`px-4 py-2 ${activeTab === 'preview' ? 'text-blue-500 border-b-2 border-blue-500' : 'text-gray-400'}`}
                onClick={() => setActiveTab('preview')}
              >
                Preview
              </button>
              <button 
                className={`px-4 py-2 ${activeTab === 'validation' ? 'text-blue-500 border-b-2 border-blue-500' : 'text-gray-400'}`}
                onClick={() => setActiveTab('validation')}
              >
                Validation
                {results?.validation?.error_count > 0 && (
                  <span className="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                    {results.validation.error_count}
                  </span>
                )}
              </button>
              
              {/* Download button in tab bar */}
              <div className="ml-auto">
                <button
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1 rounded flex items-center"
                  onClick={handleDownloadCode}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download
                </button>
              </div>
            </div>
            
            {/* Requirements Analysis Display */}
            <div className={activeTab === 'requirements' ? 'block' : 'hidden'} style={{ height: '600px' }}>
              {requirements ? (
                <RequirementsDisplay requirements={requirements} isVisible={activeTab === 'requirements'} />
              ) : (
                <div className="flex items-center justify-center h-full bg-gray-800 rounded-lg p-8">
                  <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                    <p className="text-gray-400">Analyzing prompt and determining requirements...</p>
                  </div>
                </div>
              )}
            </div>
            
            {/* Code Preview */}
            <div className={activeTab === 'code' ? 'block' : 'hidden'}>
              <CodeViewer results={results} onDownload={handleDownloadCode} />
            </div>
            
            {/* Live Preview */}
            <div className={activeTab === 'preview' ? 'block' : 'hidden'} style={{ height: '600px' }}>
              <LivePreview results={results} isVisible={activeTab === 'preview'} />
            </div>
            
            {/* Validation Results */}
            <div className={activeTab === 'validation' ? 'block' : 'hidden'} style={{ height: '600px' }}>
              {results?.validation ? (
                <div className="h-full overflow-auto p-4 bg-gray-800 rounded">
                  <ValidationResults 
                    validation={results.validation} 
                    onFixClick={(file, fixes) => {
                      console.log(`Fix requested for ${file}`, fixes);
                      // Here you would implement the actual fix functionality
                      // by sending a request to the backend or applying the fix locally
                    }}
                  />
                </div>
              ) : (
                <div className="flex h-full items-center justify-center text-gray-400">
                  No validation results available.
                </div>
              )}
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
