import React, { useRef, useEffect } from 'react';
import { Terminal } from 'lucide-react';

const LogViewer = ({ logs = [] }) => {
  const logContainerRef = useRef(null);

  // Auto-scroll to bottom when logs update
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Helper to format the log message based on its type
  const formatLogMessage = (log) => {
    const type = log.type || 'info';
    const agentName = log.agent || 'System';
    
    let className = 'text-gray-300'; // default style
    
    switch (type.toLowerCase()) {
      case 'error':
        className = 'text-red-400';
        break;
      case 'warning':
        className = 'text-yellow-400';
        break;
      case 'success':
        className = 'text-green-400';
        break;
      case 'info':
        className = 'text-blue-400';
        break;
      case 'system':
        className = 'text-purple-400';
        break;
      default:
        break;
    }
    
    return (
      <div className={`py-1 ${className}`}>
        <span className="opacity-70">[{log.timestamp || new Date().toISOString()}]</span>{' '}
        <span className="font-semibold">{agentName}:</span>{' '}
        <span>{log.message}</span>
      </div>
    );
  };

  return (
    <div className="bg-gray-800 bg-opacity-50 p-6 rounded-lg backdrop-blur-sm border border-gray-700">
      <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
        <Terminal className="w-5 h-5" /> Agent Logs
      </h2>
      
      <div 
        ref={logContainerRef}
        className="bg-gray-900 rounded-lg p-4 font-mono text-sm overflow-y-auto"
        style={{ 
          maxHeight: '300px',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 italic">No logs available yet...</div>
        ) : (
          logs.map((log, index) => (
            <div key={index}>
              {formatLogMessage(log)}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LogViewer;
