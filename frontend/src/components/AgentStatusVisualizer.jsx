import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const AgentStatusVisualizer = ({ agentStatuses, logs, onStatusUpdate }) => {
  // Keep track of last task messages per agent
  const [agentTasks, setAgentTasks] = useState({});
  // Track individual agent progress percentages
  const [agentProgress, setAgentProgress] = useState({
    planner: 0,
    frontend: 0,
    backend: 0,
    tester: 0,
    deployment: 0
  });
  
  // Effect to parse logs and extract latest tasks and update agent statuses
  useEffect(() => {
    if (!logs || logs.length === 0) return;
    
    // Process new logs to extract agent tasks
    const newTasks = {...agentTasks};
    // Track any status changes we need to make
    const statusUpdates = {};
    // Track progress updates
    const progressUpdates = {...agentProgress};
    
    logs.forEach(log => {
      if (!log.message) return;
      
      // Map from agent name to our internal key
      const getAgentKey = (agentName) => {
        const name = agentName.toLowerCase();
        if (name.includes('planning') || name.includes('architect')) return 'planner';
        if (name.includes('front')) return 'frontend';
        if (name.includes('back')) return 'backend';
        if (name.includes('quality') || name.includes('qa') || name.includes('tester')) return 'tester';
        if (name.includes('devops') || name.includes('deployment')) return 'deployment';
        return null;
      };
      
      // Pattern 1: Check for agent task information with format: # Agent: X
      if (log.message.includes('# Agent:')) {
        // Extract agent name
        const agentMatch = log.message.match(/# Agent: ([\w\s]+)/i);
        if (agentMatch) {
          const agentName = agentMatch[1].trim();
          const agentKey = getAgentKey(agentName);
            
          if (agentKey) {
            // Mark this agent as running
            statusUpdates[agentKey] = 'running';
            
            // Extract task information if available
            let taskInfo = "Working...";
            
            // Check for task description
            const taskMatch = log.message.match(/## Task: ([^\n]+)/i);
            if (taskMatch) {
              taskInfo = taskMatch[1].trim();
            }
            
            // Update the tasks state
            newTasks[agentKey] = taskInfo;
            
            // Increment progress for this agent (start of task = 25%)
            progressUpdates[agentKey] = Math.max(progressUpdates[agentKey], 25);
          }
        }
      }
      
      // Pattern 2: Status indicators in standard format
      if (log.message.includes('Status: ✅ Completed')) {
        // Find which agent this completion belongs to
        const agentMatch = log.message.match(/Agent:\s+([\w\s]+)/i);
        if (agentMatch) {
          const agentName = agentMatch[1].trim();
          const agentKey = getAgentKey(agentName);
          
          if (agentKey) {
            statusUpdates[agentKey] = 'completed';
            newTasks[agentKey] = "Task completed";
            progressUpdates[agentKey] = 100; // Completed = 100%
          }
        }
      }
      
      // Pattern 3: Task execution status in tree format
      if (log.message.includes('Assigned to:') && log.message.includes('Status:')) {
        // Extract assignment and status
        const assignmentMatch = log.message.match(/Assigned to:\s+([\w\s]+)/i);
        const statusMatch = log.message.match(/Status:\s+([^\n]+)/i);
        
        if (assignmentMatch && statusMatch) {
          const agentName = assignmentMatch[1].trim();
          const agentKey = getAgentKey(agentName);
          const status = statusMatch[1].trim();
          
          if (agentKey) {
            if (status.includes('✅ Completed')) {
              statusUpdates[agentKey] = 'completed';
              newTasks[agentKey] = "Task completed";
              progressUpdates[agentKey] = 100; // Completed = 100%
            } else if (status.includes('Executing Task')) {
              statusUpdates[agentKey] = 'running';
              newTasks[agentKey] = status;
              progressUpdates[agentKey] = Math.max(progressUpdates[agentKey], 50); // Executing = at least 50%
            } else if (status.includes('Executing')) {
              statusUpdates[agentKey] = 'running';
              newTasks[agentKey] = "Executing task...";
              progressUpdates[agentKey] = Math.max(progressUpdates[agentKey], 40); // Generic executing = at least 40%
            }
          }
        }
      }
      
      // Pattern 3b: Look for Status: Executing Task format directly
      if (log.message.includes('Status: Executing Task')) {
        // Find which agent this execution belongs to by looking at surrounding lines
        const agentMatch = log.message.match(/Assigned to:\s+([\w\s]+)/i) || log.message.match(/Agent:\s+([\w\s]+)/i);
        
        if (agentMatch) {
          const agentName = agentMatch[1].trim();
          const agentKey = getAgentKey(agentName);
          
          if (agentKey) {
            statusUpdates[agentKey] = 'running';
            newTasks[agentKey] = "Executing task...";
            progressUpdates[agentKey] = Math.max(progressUpdates[agentKey], 50); // Executing = at least 50%
          }
        } else {
          // If we can't determine the agent, look for task ID and update Frontend by default
          // This is based on the observation that Frontend tasks are often executing without clear agent labels
          const taskIdMatch = log.message.match(/Task: ([0-9a-f-]+)/i);
          if (taskIdMatch) {
            statusUpdates['frontend'] = 'running';
            newTasks['frontend'] = "Working on task: " + taskIdMatch[1].substring(0, 8) + "...";
            progressUpdates['frontend'] = Math.max(progressUpdates['frontend'], 40);
          }
        }
      }
      
      // Pattern 4: Direct task completion message
      if (log.message.includes('Task Completed')) {
        const agentMatch = log.message.match(/Agent:\s+([\w\s]+)/i);
        if (agentMatch) {
          const agentName = agentMatch[1].trim();
          const agentKey = getAgentKey(agentName);
            
          if (agentKey) {
            statusUpdates[agentKey] = 'completed';
            newTasks[agentKey] = "Task completed";
            progressUpdates[agentKey] = 100; // Completed = 100%
          }
        }
      }
      
      // Pattern 5: Detect thinking states
      if (log.message.includes('Thinking') || log.message.includes('thinking')) {
        const agentMatch = log.message.match(/Agent:\s+([\w\s]+)/i);
        if (agentMatch) {
          const agentName = agentMatch[1].trim();
          const agentKey = getAgentKey(agentName);
            
          if (agentKey) {
            statusUpdates[agentKey] = 'running';
            newTasks[agentKey] = "Thinking...";
            progressUpdates[agentKey] = Math.max(progressUpdates[agentKey], 30); // Thinking = at least 30%
          }
        }
      }
      
      // Pattern 6: Detect specific progress indicators
      if (log.message.includes('started working on')) {
        const agentMatch = log.message.match(/Agent:\s+([\w\s]+)/i);
        if (agentMatch) {
          const agentName = agentMatch[1].trim();
          const agentKey = getAgentKey(agentName);
            
          if (agentKey) {
            statusUpdates[agentKey] = 'running';
            progressUpdates[agentKey] = Math.max(progressUpdates[agentKey], 20); // Just started = at least 20%
          }
        }
      }
      
      // Pattern 7: Detect progress percentages in messages
      const progressMatch = log.message.match(/(\d+)% complete/i);
      if (progressMatch) {
        const percentage = parseInt(progressMatch[1]);
        const agentMatch = log.message.match(/Agent:\s+([\w\s]+)/i);
        if (agentMatch) {
          const agentName = agentMatch[1].trim();
          const agentKey = getAgentKey(agentName);
            
          if (agentKey && !isNaN(percentage)) {
            progressUpdates[agentKey] = Math.max(progressUpdates[agentKey], percentage);
          }
        }
      }
    });
    
    // Update tasks
    setAgentTasks(newTasks);
    
    // Update progress
    setAgentProgress(progressUpdates);
    
    // Update statuses if we have changes
    if (Object.keys(statusUpdates).length > 0) {
      // Notify parent component about status changes
      // Use a callback if provided, otherwise handle internally
      if (typeof onStatusUpdate === 'function') {
        onStatusUpdate(statusUpdates);
      }
    }
  }, [logs]);
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-gray-600';
      case 'running': return 'bg-blue-500 animate-pulse';
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-600';
    }
  };

  // Calculate overall progress percentage with improved weighting
  const calculateProgress = () => {
    // Use the individual agent progress values for more accurate calculation
    const weights = {
      planner: 0.25,    // Planning is 25% of the work
      backend: 0.25,    // Backend is 25% of the work
      frontend: 0.25,   // Frontend is 25% of the work
      tester: 0.15,     // Testing is 15% of the work
      deployment: 0.10  // Deployment is 10% of the work
    };
    
    let totalProgress = 0;
    
    // Calculate weighted progress
    Object.keys(agentProgress).forEach(agent => {
      totalProgress += agentProgress[agent] * weights[agent];
    });
    
    // Ensure progress is at least 5% when any agent is running
    if (totalProgress < 5 && Object.values(agentStatuses).some(status => status === 'running')) {
      totalProgress = 5;
    }
    
    // Cap at 100%
    return Math.min(100, Math.round(totalProgress));
  };

  // Get current task for an agent, using both agentTasks state and logs
  const getCurrentTask = (agentName) => {
    // If we have a stored task for this agent, use it
    if (agentTasks[agentName]) {
      return agentTasks[agentName];
    }
    
    // Default task messages based on status
    switch (agentStatuses[agentName]) {
      case 'pending':
        return 'Waiting for previous tasks to complete...';
      case 'running':
        return 'Working...';
      case 'completed':
        return 'Task completed';
      case 'failed':
        return 'Task failed';
      default:
        return 'Waiting...';
    }
  };

  return (
    <div className="bg-gradient-to-br from-gray-800/70 to-gray-900/70 p-6 rounded-xl backdrop-blur-sm border border-gray-700/50 shadow-xl">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">CrewAI Collaboration Pipeline</h2>
        <div className="text-blue-400 font-semibold">Progress: {calculateProgress()}%</div>
      </div>
      
      <div className="h-2 w-full bg-gray-800 rounded-full mb-6 overflow-hidden">
        <motion.div 
          className="h-full bg-gradient-to-r from-blue-500 to-purple-600"
          initial={{ width: '0%' }}
          animate={{ width: `${calculateProgress()}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {Object.entries(agentStatuses).map(([agent, status]) => (
          <div key={agent} className="bg-gray-800/60 backdrop-blur-sm rounded-lg p-4 border border-gray-700/50 flex flex-col items-center">
            {/* Agent Icon */}
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-2 ${getStatusColor(status)}`}>
              {agent === 'planner' && (
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" />
                </svg>
              )}
              {agent === 'backend' && (
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                </svg>
              )}
              {agent === 'frontend' && (
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.083 9h1.946c.089-1.546.383-2.97.837-4.118A6.004 6.004 0 004.083 9zM10 2a8 8 0 100 16 8 8 0 000-16zm0 2c-.076 0-.232.032-.465.262-.238.234-.497.623-.737 1.182-.389.907-.673 2.142-.766 3.556h3.936c-.093-1.414-.377-2.649-.766-3.556-.24-.56-.5-.948-.737-1.182C10.232 4.032 10.076 4 10 4zm3.971 5c-.089-1.546-.383-2.97-.837-4.118A6.004 6.004 0 0115.917 9h-1.946zm-2.003 2H8.032c.093 1.414.377 2.649.766 3.556.24.56.5.948.737 1.182.233.23.389.262.465.262.076 0 .232-.032.465-.262.238-.234.498-.623.737-1.182.389-.907.673-2.142.766-3.556zm1.166 4.118c.454-1.147.748-2.572.837-4.118h1.946a6.004 6.004 0 01-2.783 4.118zm-6.268 0C6.412 13.97 6.118 12.546 6.03 11H4.083a6.004 6.004 0 002.783 4.118z" clipRule="evenodd" />
                </svg>
              )}
              {agent === 'tester' && (
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              )}
              {agent === 'deployment' && (
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            
            {/* Agent Name */}
            <h3 className="text-lg font-semibold text-white capitalize">
              {agent === 'planner' ? 'Planning Architect' : 
               agent === 'backend' ? 'Backend Engineer' :
               agent === 'frontend' ? 'Frontend Developer' :
               agent === 'tester' ? 'QA Engineer' :
               agent === 'deployment' ? 'DevOps Engineer' : agent}
            </h3>
            
            {/* Agent Status */}
            <div className="mt-1 text-sm font-medium">
              {status === 'running' ? (
                <div className="text-blue-400 flex items-center">
                  <div className="w-2 h-2 rounded-full bg-blue-400 mr-2 animate-pulse"></div>
                  {getCurrentTask(agent)}
                </div>
              ) : status === 'completed' ? (
                <div className="text-green-400 flex items-center">
                  <div className="w-2 h-2 rounded-full bg-green-400 mr-2"></div>
                  Completed
                </div>
              ) : status === 'failed' ? (
                <div className="text-red-400 flex items-center">
                  <div className="w-2 h-2 rounded-full bg-red-400 mr-2"></div>
                  Failed
                </div>
              ) : (
                <div className="text-gray-400 flex items-center">
                  <div className="w-2 h-2 rounded-full bg-gray-400 mr-2"></div>
                  Pending
                </div>
              )}
            </div>
            
            {/* Progress Indicator */}
            <div className="w-full h-1 bg-gray-700 rounded-full mt-3 overflow-hidden">
              <motion.div 
                className={`h-full ${status === 'completed' ? 'bg-green-500' : 'bg-blue-500'}`}
                initial={{ width: '0%' }}
                animate={{ width: `${agentProgress[agent]}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentStatusVisualizer;
