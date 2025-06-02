import React from 'react';
import { motion } from 'framer-motion';
import { Code, Check, AlertCircle, Clock, Loader2 } from 'lucide-react';

const AgentStatusVisualizer = ({ agents }) => {
  // Status icons mapping
  const statusIcons = {
    pending: <Clock className="w-5 h-5" />,
    running: <Loader2 className="w-5 h-5 animate-spin" />,
    completed: <Check className="w-5 h-5" />,
    failed: <AlertCircle className="w-5 h-5" />
  };

  // Status colors mapping
  const statusColors = {
    pending: 'bg-gray-600',
    running: 'bg-blue-600',
    completed: 'bg-green-600',
    failed: 'bg-red-600'
  };

  return (
    <div className="bg-gray-800 bg-opacity-50 p-6 rounded-lg backdrop-blur-sm border border-gray-700">
      <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
        <Code className="w-5 h-5" /> Agent Status
      </h2>
      
      <div className="space-y-4">
        {agents.map((agent, index) => (
          <motion.div
            key={agent.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`flex items-center p-3 rounded-lg ${
              agent.status === 'running' 
                ? 'animate-pulse-slow shadow-lg shadow-blue-500/20' 
                : ''
            }`}
          >
            <div 
              className={`w-10 h-10 rounded-full flex items-center justify-center text-white mr-4 ${statusColors[agent.status]}`}
            >
              {statusIcons[agent.status]}
            </div>
            
            <div className="flex-grow">
              <h3 className="text-white font-medium">{agent.name}</h3>
              <p className="text-gray-400 text-sm">{agent.description}</p>
            </div>
            
            {agent.status === 'running' && (
              <motion.div 
                className="w-2 h-2 rounded-full bg-blue-500 mr-1"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
              />
            )}
            
            {agent.status === 'completed' && (
              <span className="text-xs text-gray-400">
                {agent.completionTime ? `${agent.completionTime}s` : ''}
              </span>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default AgentStatusVisualizer;
