import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { X, Minimize2, Maximize2 } from 'lucide-react';

const Terminal = ({ logs = [], terminalOutput = [], isVisible = false, onClose = () => {} }) => {
  const terminalRef = useRef(null);
  const [animated, setAnimated] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  
  // Auto-scroll to bottom when new logs come in
  useEffect(() => {
    if (terminalRef.current && isVisible && !isMinimized) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [animated, isVisible, terminalOutput, isMinimized]);

  // Animate logs appearing one by one for a more realistic terminal effect
  useEffect(() => {
    const combinedLogs = [...logs, ...terminalOutput.map(item => ({
      message: item.content,
      type: item.type,
      timestamp: new Date().toISOString()
    }))];
    
    if (combinedLogs.length > currentIndex && isVisible) {
      const timer = setTimeout(() => {
        setAnimated(prev => [...prev, combinedLogs[currentIndex]]);
        setCurrentIndex(currentIndex + 1);
      }, 50); // Faster animation
      
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
    
    // For CrewAI specific messages
    if (log.message) {
      if (log.message.includes('Planning Architect')) return 'text-green-400';
      if (log.message.includes('Backend Engineer')) return 'text-yellow-400';
      if (log.message.includes('Frontend Developer')) return 'text-purple-400';
      if (log.message.includes('Quality Assurance Engineer')) return 'text-pink-400';
      if (log.message.includes('DevOps Engineer')) return 'text-cyan-400';
      
      // Task statuses
      if (log.message.includes('Completed')) return 'text-green-300';
      if (log.message.includes('Executing Task')) return 'text-blue-300';
      if (log.message.includes('Thinking')) return 'text-amber-300';
      
      // Headers and important sections
      if (log.message.startsWith('#')) return 'text-blue-500 font-bold';
      if (log.message.startsWith('## Final Answer')) return 'text-green-500 font-bold';
      if (log.message.includes('Crew Execution Started')) return 'text-purple-500 font-bold';
      if (log.message.includes('Task Completion')) return 'text-green-500 font-bold';
    }
    
    // Fall back to agent-based coloring if available
    if (log.agent) {
      switch (log.agent) {
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
    
    // Handle special formatting for CrewAI tasks
    if (message.includes('Task:') || message.includes('Agent:')) {
      return <span className="whitespace-pre-line font-medium">{message}</span>;
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
          <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
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
          
          {/* Add sample progress messages if no logs yet */}
          {animated.length === 0 && (
            <>
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="mb-2 leading-relaxed py-1 border-l-2 border-blue-500/70 pl-2 bg-blue-900/20 rounded-r py-2 pr-2"
              >
                <span className="text-gray-500 mr-2 text-xs">[{formatTime(new Date())}]</span>
                <span className="font-semibold text-green-400 mr-2">System:</span>
                <span className="text-blue-300">Crew Execution Started with 5 specialized AI agents</span>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
                className="mb-2 leading-relaxed py-1 border-l-2 border-blue-500/70 pl-2"
              >
                <span className="text-gray-500 mr-2 text-xs">[{formatTime(new Date())}]</span>
                <span className="font-semibold text-green-400 mr-2">Planning Architect:</span>
                <span className="text-white">Analyzing requirements and creating system architecture</span>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.4 }}
                className="mb-2 leading-relaxed py-1 border-l-2 border-blue-500/70 pl-2"
              >
                <span className="text-gray-500 mr-2 text-xs">[{formatTime(new Date())}]</span>
                <span className="font-semibold text-yellow-400 mr-2">Backend Engineer:</span>
                <span className="text-white">Preparing database schema and API endpoints</span>
              </motion.div>
            </>
          )}
          
          {/* Render all log entries */}
          {animated.map((log, index) => {
            // Determine what type of message we're showing
            const isCrewAIMessage = log.message && (
              log.message.includes('Agent:') || 
              log.message.includes('Task:') || 
              log.message.includes('Crew Execution')
            );
            
            const isHeaderMessage = log.message && 
              (log.message.startsWith('#') || log.message.includes('Crew Execution Started'));

            const isCompletedMessage = log.message && 
              (log.message.includes('Completed') || log.message.includes('Task Completion'));
            
            const isSystemMessage = log.type === 'info' || log.type === 'error';
            
            return (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                key={index} 
                className={`mb-2 leading-relaxed py-1 ${isCrewAIMessage ? 'border-l-2 border-blue-500/70 pl-2' : ''}
                  ${isHeaderMessage ? 'bg-blue-900/20 rounded-r py-2 pr-2' : ''}
                  ${isCompletedMessage ? 'bg-green-900/20 rounded-r py-2 pr-2' : ''}
                `}
              >
                {/* Timestamp */}
                <span className="text-gray-500 mr-2 text-xs">[{formatTime(log.timestamp)}]</span>
                
                {/* Agent name or message type label */}
                {log.agent && (
                  <span className={`font-semibold ${getMessageColor(log)} mr-2`}>{log.agent}:</span>
                )}
                
                {isSystemMessage && (
                  <span className={`font-medium px-1.5 py-0.5 rounded text-xs mr-2 ${
                    log.type === 'error' ? 'bg-red-900/30 text-red-400' : 'bg-blue-900/30 text-blue-400'
                  }`}>
                    {log.type === 'error' ? 'ERROR' : 'SYSTEM'}
                  </span>
                )}
                
                {/* Formatted message content */}
                <span className={`${getMessageColor(log)}`}>
                  {formatMessage(log.message)}
                </span>
              </motion.div>
            );
          })}
          
          {/* Show waiting message or prompt cursor */}
          {isVisible && animated.length === 0 && (
            <div className="text-gray-500">Waiting for CrewAI agent activity...</div>
          )}
          
          {isVisible && animated.length > 0 && (
            <div className="inline-block mt-1">
              <span className="text-green-400">$</span>
              <span className="ml-1 animate-pulse">_</span>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
};

export default Terminal;
