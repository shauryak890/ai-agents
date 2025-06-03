import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const AgentStatusVisualizer = ({ agentStatuses, logs, onStatusUpdate }) => {
  // Keep track of last task messages per agent
  const [agentTasks, setAgentTasks] = useState({});
  
  // Effect to parse logs and extract latest tasks and update agent statuses
  useEffect(() => {
    if (!logs || logs.length === 0) return;
    
    // Process new logs to extract agent tasks
    const newTasks = {...agentTasks};
    // Track any status changes we need to make
    const statusUpdates = {};
    
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
            } else if (status.includes('Executing Task')) {
              statusUpdates[agentKey] = 'running';
              newTasks[agentKey] = status;
            } else if (status.includes('Executing')) {
              statusUpdates[agentKey] = 'running';
              newTasks[agentKey] = "Executing task...";
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
          }
        } else {
          // If we can't determine the agent, look for task ID and update Frontend by default
          // This is based on the observation that Frontend tasks are often executing without clear agent labels
          const taskIdMatch = log.message.match(/Task: ([0-9a-f-]+)/i);
          if (taskIdMatch) {
            statusUpdates['frontend'] = 'running';
            newTasks['frontend'] = "Working on task: " + taskIdMatch[1].substring(0, 8) + "...";
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
          }
        }
      }
    });
    
    // Update tasks
    setAgentTasks(newTasks);
    
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
    const totalAgents = Object.keys(agentStatuses).length;
    
    // Count agents by status
    const completedAgents = Object.values(agentStatuses).filter(status => status === 'completed').length;
    const runningAgents = Object.values(agentStatuses).filter(status => status === 'running').length;
    const pendingAgents = Object.values(agentStatuses).filter(status => status === 'pending').length;
    
    // Progressive weighting system:
    // - Each completed agent contributes 20% to the total (5 agents × 20% = 100%)
    // - Running agents contribute 10% plus a partial amount based on task messages
    // - Add 5% baseline progress when any agent is running (for setup work)
    
    let progress = 0;
    
    // Add completed agent progress (20% each)
    progress += completedAgents * 20;
    
    // Add running agent progress (10% each plus a bit more for active tasks)
    progress += runningAgents * 10;
    
    // Add baseline progress when any work is happening
    if (runningAgents > 0 || completedAgents > 0) {
      progress += 5;
    }
    
    // If we have any tasks recorded, add additional progress
    const taskCount = Object.keys(agentTasks).length;
    if (taskCount > 0) {
      // Each recorded task adds a small amount of progress
      progress += Math.min(5, taskCount * 1);
    }
    
    // Cap at 100%
    return Math.min(100, Math.round(progress));
  };

  // Get current task for an agent, using both agentTasks state and logs
  const getCurrentTask = (agentName) => {
    // If we have a stored task for this agent, use it
    if (agentTasks[agentName]) {
      return agentTasks[agentName];
    }
    
    // Otherwise, fallback to older method of parsing logs directly
    if (!logs || logs.length === 0) return "Waiting...";
    
    // Convert agent names to match the log format
    const agentMapping = {
      'planner': 'Planning Architect',
      'backend': 'Backend Engineer',
      'frontend': 'Frontend Developer',
      'tester': 'Quality Assurance Engineer',
      'deployment': 'DevOps Engineer'
    };
    
    const searchName = agentMapping[agentName] || agentName;
    
    // Find the latest log entry for this agent
    const agentLogs = logs.filter(log => 
      log.message && log.message.includes(searchName)
    );
    
    if (agentLogs.length > 0) {
      const latest = agentLogs[agentLogs.length - 1];
      // Extract task name if available
      if (latest.message) {
        const taskMatch = latest.message.match(/Task: (.*?)$/m);
        return taskMatch ? taskMatch[1] : "Working...";
      }
    }
    
    return agentStatuses[agentName] === 'pending' ? "Waiting..." : "Working...";
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8 bg-gradient-to-br from-gray-800/80 to-gray-900/80 p-6 rounded-xl border border-gray-700/50 shadow-xl backdrop-blur-sm"
    >
      <div className="flex justify-between items-center mb-5">
        <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
          CrewAI Collaboration Pipeline
        </h3>
        <div className="text-right bg-gray-800/70 py-1 px-3 rounded-full border border-gray-700/50">
          <span className="text-sm text-blue-400 font-medium">Progress: {calculateProgress()}%</span>
        </div>
      </div>

      {/* Overall progress bar */}
      <div className="w-full bg-gray-800/60 rounded-full h-3 mb-8 overflow-hidden shadow-inner border border-gray-700/30">
        <motion.div 
          initial={{ width: '0%' }}
          animate={{ width: `${calculateProgress()}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full"
        />
      </div>
      
      <div className="grid md:grid-cols-5 gap-4">
        {Object.entries(agentStatuses).map(([agent, status]) => {
          const agentDisplayNames = {
            'planner': 'Planning Architect',
            'backend': 'Backend Engineer',
            'frontend': 'Frontend Developer',
            'tester': 'QA Engineer',
            'deployment': 'DevOps Engineer'
          };
          
          const agentIcons = {
            'planner': '🧠',
            'frontend': '🎨',
            'backend': '⚙️',
            'tester': '🧪',
            'deployment': '🚀'
          };
          
          return (
            <motion.div 
              key={agent} 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: parseInt(Object.keys(agentStatuses).indexOf(agent) / 10) }}
              className="text-center p-4 bg-gray-800/70 backdrop-blur-sm rounded-xl border border-gray-700/40 overflow-hidden"
            >
              <div className={`mx-auto h-16 w-16 rounded-full flex items-center justify-center ${getStatusColor(status)} transition-all duration-500 shadow-lg border-2 border-gray-700/30`}>
                <span className="text-2xl">{agentIcons[agent]}</span>
              </div>
              <h4 className="mt-3 text-sm font-bold text-white">{agentDisplayNames[agent]}</h4>
              <div className={`mt-1 text-xs rounded-full px-2 py-0.5 inline-block ${
                status === 'pending' ? 'bg-gray-700/50 text-gray-300' : 
                status === 'running' ? 'bg-blue-500/20 text-blue-300' : 
                status === 'completed' ? 'bg-green-500/20 text-green-300' : 
                'bg-red-500/20 text-red-300'
              } capitalize font-medium`}>{status}</div>
              
              {/* Current task */}
              {status !== 'pending' && (
                <div className="mt-3 text-xs text-gray-400 truncate px-1 min-h-[2rem] bg-gray-900/50 p-2 rounded-lg">
                  {getCurrentTask(agent)}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

export default AgentStatusVisualizer;
