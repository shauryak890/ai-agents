import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { X, Minimize2, Maximize2, Terminal as TerminalIcon } from 'lucide-react';

const Terminal = ({ logs = [], terminalOutput = [], isVisible = false, onClose = () => {} }) => {
  const terminalRef = useRef(null);
  const [animated, setAnimated] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [groupedLogs, setGroupedLogs] = useState({});
  
  // Auto-scroll to bottom when new logs come in
  useEffect(() => {
    if (terminalRef.current && isVisible && !isMinimized) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [animated, isVisible, terminalOutput, isMinimized]);

  // Process and group logs by task/agent for better readability
  useEffect(() => {
    const combinedLogs = [...logs, ...terminalOutput.map(item => ({
      message: item.content,
      type: item.type,
      timestamp: new Date().toISOString()
    }))];
    
    // Group logs by task ID or agent
    const groups = {};
    
    combinedLogs.forEach(log => {
      if (!log.message) return;
      
      // Try to extract task ID
      const taskIdMatch = log.message.match(/Task: ([0-9a-f-]+)/i);
      const agentMatch = log.message.match(/Agent: ([\w\s]+)/i) || 
                         log.message.match(/# Agent: ([\w\s]+)/i);
      
      let groupKey = 'system';
      
      if (taskIdMatch) {
        groupKey = `task-${taskIdMatch[1].substring(0, 8)}`;
      } else if (agentMatch) {
        groupKey = `agent-${agentMatch[1].trim().toLowerCase().replace(/\s+/g, '-')}`;
      } else if (log.agent) {
        groupKey = `agent-${log.agent.toLowerCase().replace(/\s+/g, '-')}`;
      }
      
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      
      groups[groupKey].push(log);
    });
    
    setGroupedLogs(groups);
    
    // Still animate logs appearing one by one for a more realistic terminal effect
    if (combinedLogs.length > currentIndex && isVisible) {
      const timer = setTimeout(() => {
        setAnimated(prev => [...prev, combinedLogs[currentIndex]]);
        setCurrentIndex(currentIndex + 1);
      }, 20); // Even faster animation
      
      return () => clearTimeout(timer);
    }
  }, [logs, terminalOutput, currentIndex, isVisible]);

  if (!isVisible) {
    return null;
  }
  
  // Colorize based on content or agent
  const getMessageColor = (log) => {
    // First check for specific log types
    if (log.type === 'error') return 'text-red-400';
    if (log.type === 'info') return 'text-blue-400';
    if (log.type === 'success') return 'text-green-400';
    if (log.type === 'warning') return 'text-yellow-400';
    
    // For CrewAI specific messages
    if (log.message) {
      // Task status messages
      if (log.message.includes('Task Completed') || log.message.includes('Completed:')) return 'text-green-300 font-bold';
      if (log.message.includes('Task:') && log.message.includes('Status:')) return 'text-blue-300';
      
      // Agent-specific coloring
      if (log.message.includes('Planning Architect')) return 'text-green-400';
      if (log.message.includes('Backend Engineer')) return 'text-yellow-400';
      if (log.message.includes('Frontend Developer')) return 'text-purple-400';
      if (log.message.includes('Quality Assurance Engineer')) return 'text-pink-400';
      if (log.message.includes('DevOps Engineer')) return 'text-cyan-400';
      
      // Task statuses
      if (log.message.includes('Completed')) return 'text-green-300';
      if (log.message.includes('Executing Task')) return 'text-blue-300';
      if (log.message.includes('Thinking')) return 'text-amber-300';
      
      // CrewAI specific patterns
      if (log.message.includes('🚀 Crew:')) return 'text-purple-500 font-bold';
      if (log.message.includes('📋 Task:')) return 'text-blue-400';
      if (log.message.includes('Assigned to:')) return 'text-yellow-400';
      if (log.message.includes('Status: ✅')) return 'text-green-500';
      
      // Headers and important sections
      if (log.message.startsWith('#')) return 'text-blue-500 font-bold';
      if (log.message.startsWith('## Final Answer')) return 'text-green-500 font-bold';
      if (log.message.includes('Crew Execution Started')) return 'text-purple-500 font-bold';
      if (log.message.includes('Task Completion')) return 'text-green-500 font-bold';
    }
    
    // Fall back to agent-based coloring if available
    if (log.agent) {
      switch (log.agent) {
        case 'Planning Architect':
          return 'text-green-400';
        case 'Backend Engineer':
          return 'text-yellow-400';
        case 'Frontend Developer':
          return 'text-purple-400';
        case 'Quality Assurance Engineer':
        case 'QA Engineer':
          return 'text-pink-400';
        case 'DevOps Engineer':
          return 'text-cyan-400';
        case 'Prompt Analyzer':
          return 'text-blue-400';
        case 'System':
          return 'text-gray-400';
        default:
          return 'text-white';
      }
    }
    
    return 'text-white';
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
      return '';
    }
  };
  
  // Format message content with proper styling for CrewAI output
  const formatMessage = (message) => {
    if (!message) return '';
    
    // Handle code blocks
    if (message.includes('```')) {
      const parts = message.split('```');
      return parts.map((part, i) => {
        // Even indices are normal text, odd indices are code blocks
        if (i % 2 === 0) {
          return <span key={i} className="whitespace-pre-line">{part}</span>;
        } else {
          // Extract language if specified (e.g., ```json)
          const codeLines = part.split('\n');
          const language = codeLines[0] || '';
          const code = codeLines.slice(1).join('\n');
          
          return (
            <pre key={i} className="bg-gray-950 p-2 rounded my-2 overflow-x-auto">
              {language && <div className="text-xs text-gray-500 mb-1">{language}</div>}
              <code>{code}</code>
            </pre>
          );
        }
      });
    }
    
    // Handle CrewAI task tree visualization
    if (message.includes('🚀 Crew:')) {
      return (
        <div className="font-mono">
          {message.split('\n').map((line, i) => {
            // Style different parts of the task tree
            if (line.includes('🚀 Crew:')) {
              return <div key={i} className="text-purple-400 font-bold">{line}</div>;
            } else if (line.includes('📋 Task:')) {
              return <div key={i} className="text-blue-400 ml-2">{line}</div>;
            } else if (line.includes('Assigned to:')) {
              return <div key={i} className="text-yellow-400 ml-4">{line}</div>;
            } else if (line.includes('Status: ✅')) {
              return <div key={i} className="text-green-500 ml-4">{line}</div>;
            } else if (line.includes('Status:')) {
              return <div key={i} className="text-blue-400 ml-4">{line}</div>;
            } else {
              return <div key={i}>{line}</div>;
            }
          })}
        </div>
      );
    }
    
    // Handle Task Completion boxes
    if (message.includes('Task Completion') && message.includes('─')) {
      return (
        <div className="font-mono bg-gray-800 rounded border border-green-500/30 p-1 my-1">
          {message.split('\n').map((line, i) => (
            <div key={i} className={
              line.includes('Task Completed') ? 'text-green-400 font-bold' : 
              line.includes('Agent:') ? 'text-yellow-400' : ''
            }>
              {line}
            </div>
          ))}
        </div>
      );
    }
    
    // Handle special formatting for CrewAI tasks
    if (message.includes('Task:') || message.includes('Agent:')) {
      return <span className="whitespace-pre-line font-medium">{message}</span>;
    }
    
    // Handle thinking states with special formatting
    if (message.includes('Thinking...')) {
      return (
        <div className="flex items-center space-x-2">
          <span className="whitespace-pre-line">{message}</span>
          <span className="inline-block">
            <span className="animate-pulse">.</span>
            <span className="animate-pulse delay-100">.</span>
            <span className="animate-pulse delay-200">.</span>
          </span>
        </div>
      );
    }
    
    // Handle task IDs with better formatting
    const taskIdMatch = message.match(/Task: ([0-9a-f-]+)/i);
    if (taskIdMatch) {
      const beforeId = message.substring(0, message.indexOf(taskIdMatch[1]));
      const id = taskIdMatch[1];
      const afterId = message.substring(message.indexOf(taskIdMatch[1]) + id.length);
      
      return (
        <span className="whitespace-pre-line">
          {beforeId}
          <span className="bg-blue-900/30 px-1 rounded font-mono text-blue-300">{id.substring(0, 8)}...</span>
          {afterId}
        </span>
      );
    }
    
    return <span className="whitespace-pre-line">{message}</span>;
  };

  // Handle terminal control functions
  const handleMinimize = () => {
    setIsMinimized(!isMinimized);
    setIsMaximized(false); // Reset maximize state when minimizing
  };

  const handleMaximize = () => {
    setIsMaximized(!isMaximized);
    setIsMinimized(false); // Reset minimize state when maximizing
  };

  const handleClose = () => {
    onClose();
  };
  
  // Group logs by agent for more organized display
  const renderLogsByGroup = () => {
    // Flatten logs for rendering
    const flatLogs = [];
    
    // First add system logs
    if (groupedLogs['system']) {
      flatLogs.push(...groupedLogs['system']);
    }
    
    // Then add agent logs in a specific order
    const agentOrder = [
      'agent-planning-architect',
      'agent-backend-engineer',
      'agent-frontend-developer',
      'agent-qa-engineer',
      'agent-devops-engineer',
      'agent-prompt-analyzer'
    ];
    
    agentOrder.forEach(agentKey => {
      if (groupedLogs[agentKey]) {
        flatLogs.push(...groupedLogs[agentKey]);
      }
    });
    
    // Add any remaining task logs
    Object.keys(groupedLogs)
      .filter(key => key.startsWith('task-') && !agentOrder.includes(key))
      .forEach(taskKey => {
        flatLogs.push(...groupedLogs[taskKey]);
      });
    
    // Add any other logs we haven't categorized
    Object.keys(groupedLogs)
      .filter(key => !key.startsWith('agent-') && !key.startsWith('task-') && key !== 'system')
      .forEach(otherKey => {
        flatLogs.push(...groupedLogs[otherKey]);
      });
    
    return flatLogs.slice(0, animated.length).map((log, index) => (
      <div key={index} className={`mb-2 ${getMessageColor(log)}`}>
        <div className="flex items-start">
          <div className="text-xs text-gray-500 mr-2 mt-1 font-mono">{formatTime(log.timestamp)}</div>
          <div className="flex-1">
            {log.agent && (
              <span className="font-bold mr-2">[{log.agent}]</span>
            )}
            {formatMessage(log.message)}
          </div>
        </div>
      </div>
    ));
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{
        opacity: 1,
        scale: isMaximized ? 1.03 : 1,
        height: isMinimized ? '58px' : 'auto'
      }}
      transition={{ duration: 0.3 }}
      className={`w-full flex flex-col shadow-2xl ${isMaximized ? 'fixed inset-0 z-50' : 'relative'}`}
    >
      {/* Terminal Header with Controls */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 rounded-t-xl p-3 flex items-center border-b border-gray-700/50">
        {/* Terminal control buttons */}
        <div className="flex space-x-2 ml-2">
          <button 
            onClick={handleClose}
            className="w-3.5 h-3.5 bg-red-500 hover:bg-red-600 rounded-full shadow-glow-red flex items-center justify-center group transition-all duration-200"
            aria-label="Close terminal"
          >
            <X className="w-2 h-2 text-red-100 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
          <button 
            onClick={handleMinimize}
            className="w-3.5 h-3.5 bg-yellow-500 hover:bg-yellow-600 rounded-full shadow-glow-yellow flex items-center justify-center group transition-all duration-200"
            aria-label="Minimize terminal"
          >
            <Minimize2 className="w-2 h-2 text-yellow-100 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
          <button 
            onClick={handleMaximize}
            className="w-3.5 h-3.5 bg-green-500 hover:bg-green-600 rounded-full shadow-glow-green flex items-center justify-center group transition-all duration-200"
            aria-label="Maximize terminal"
          >
            <Maximize2 className="w-2 h-2 text-green-100 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        </div>
        
        {/* Terminal title */}
        <div className="text-gray-300 text-sm font-semibold mx-auto flex items-center">
          <TerminalIcon className="w-4 h-4 mr-2" />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">CrewAI Terminal</span>
        </div>
      </div>
      
      {/* Terminal Content - only show if not minimized */}
      {!isMinimized && (
        <div 
          ref={terminalRef}
          className={`flex-1 bg-gray-900/90 backdrop-blur-sm p-4 text-white font-mono text-sm overflow-auto rounded-b-xl border-x border-b border-gray-800/50 ${isMaximized ? 'h-[calc(100vh-58px)]' : 'max-h-[400px]'}`}
        >
          <div className="pb-3 border-b border-gray-700/50 mb-3 flex items-center">
            <div className="bg-green-500/20 text-green-400 px-2 py-1 rounded mr-2 font-bold">$</div>
            <span className="text-blue-300 font-semibold">CrewAI multi-agent process initialized</span>
            <div className="ml-auto text-xs text-gray-500">{formatTime(new Date())}</div>
          </div>
          
          {/* Render logs in a more organized way */}
          <div className="space-y-1">
            {renderLogsByGroup()}
          </div>
          
          {/* Active cursor */}
          <div className="flex items-center mt-3 animate-pulse">
            <div className="text-green-400 mr-2">$</div>
            <div className="w-2 h-4 bg-green-400"></div>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default Terminal;
