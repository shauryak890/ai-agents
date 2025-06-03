import React, { useState } from 'react';
import ValidationFixer from './ValidationFixer';
import { motion } from 'framer-motion';

const ValidationResults = ({ validation, jobId }) => {
  const [expandedFile, setExpandedFile] = useState(null);
  const [validationData, setValidationData] = useState(validation);

  // Update local state when props change
  React.useEffect(() => {
    setValidationData(validation);
  }, [validation]);

  // Handle when fixes have been applied
  const handleFixComplete = (updatedResults) => {
    if (updatedResults?.validation) {
      setValidationData(updatedResults.validation);
    }
  };

  if (!validationData) {
    return (
      <div className="p-6 bg-gray-800 rounded-lg">
        <p className="text-gray-400">No validation data available.</p>
      </div>
    );
  }

  const toggleFile = (filePath) => {
    if (expandedFile === filePath) {
      setExpandedFile(null);
    } else {
      setExpandedFile(filePath);
    }
  };

  // Get the badge color based on validation status
  const getBadgeColor = (isValid) => {
    return isValid ? 'bg-green-500' : 'bg-red-500';
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="p-6 bg-gradient-to-br from-gray-800/90 to-gray-900/90 rounded-xl border border-gray-700/50 shadow-xl backdrop-blur-sm"
    >
      <div className="mb-6 flex items-center">
        <motion.div 
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          className={`w-5 h-5 rounded-full mr-3 shadow-lg ${getBadgeColor(validationData.valid)}`}
        />
        <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-purple-400">
          Validation {validationData.valid ? 'Successful' : 'Failed'}
        </h3>
      </div>

      <div className="mb-6">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-gray-700/80 to-gray-800/80 p-4 rounded-xl border border-gray-600/30 shadow-lg"
          >
            <p className="text-gray-400 text-sm mb-1 font-medium">Files Checked</p>
            <p className="text-2xl font-bold text-blue-300">{validationData.file_count}</p>
          </motion.div>
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-gray-700/80 to-gray-800/80 p-4 rounded-xl border border-gray-600/30 shadow-lg"
          >
            <p className="text-gray-400 text-sm mb-1 font-medium">Errors Found</p>
            <p className="text-2xl font-bold text-red-300">{validationData.error_count}</p>
          </motion.div>
        </div>
      </div>
      
      {/* Add ValidationFixer if there are errors */}
      {!validationData.valid && validationData.error_count > 0 && (
        <ValidationFixer 
          jobId={jobId} 
          validation={validationData} 
          onFixComplete={handleFixComplete} 
        />
      )}

      {/* Show warnings if any */}
      {validationData.warnings && validationData.warnings.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-6 p-4 bg-gradient-to-r from-amber-900/50 to-amber-800/40 rounded-xl border border-amber-700/30 shadow-lg"
        >
          <div className="flex items-center mb-2">
            <svg className="w-5 h-5 text-amber-300 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h4 className="text-amber-300 font-medium">Warnings</h4>
          </div>
          <ul className="list-disc list-inside text-amber-200 pl-2">
            {validationData.warnings.map((warning, idx) => (
              <li key={idx} className="mb-1">{warning}</li>
            ))}
          </ul>
        </motion.div>
      )}

      {/* Show file errors */}
      {Object.keys(validationData.errors || {}).length > 0 && (
        <div className="mb-6">
          <h4 className="text-white font-medium mb-3">Files with Errors</h4>
          <div className="space-y-3">
            {Object.entries(validationData.errors).map(([filePath, errors]) => (
              <div key={filePath} className="border border-red-800 bg-red-900 bg-opacity-20 rounded-lg overflow-hidden">
                <button 
                  className="w-full p-3 text-left flex items-center justify-between hover:bg-red-900 hover:bg-opacity-30"
                  onClick={() => toggleFile(filePath)}
                >
                  <span className="font-mono text-red-300">{filePath}</span>
                  <div className="flex items-center">
                    <span className="bg-red-600 text-white text-xs px-2 py-1 rounded-full mr-2">{errors.length} errors</span>
                    <span>{expandedFile === filePath ? '▼' : '▶'}</span>
                  </div>
                </button>
                
                {expandedFile === filePath && (
                  <div className="bg-gray-900 p-3 border-t border-red-800">
                    <ul className="text-sm text-red-300 space-y-2">
                      {errors.map((error, idx) => (
                        <li key={idx} className="font-mono">{error}</li>
                      ))}
                    </ul>
                    
                    {/* Show fix suggestions */}
                    {validationData.fix_suggestions && validationData.fix_suggestions[filePath] && (
                      <div className="mt-3 pt-3 border-t border-gray-700">
                        <h5 className="text-blue-400 font-medium mb-2">Fix Suggestions</h5>
                        <ul className="list-disc list-inside text-blue-300 text-sm">
                          {validationData.fix_suggestions[filePath].map((suggestion, idx) => (
                            <li key={idx}>{suggestion}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Show additional information if validation passed */}
      {validationData.valid && (
        <div className="p-4 bg-green-900 bg-opacity-20 rounded-lg border border-green-800">
          <h4 className="text-green-300 font-medium mb-2">
            <span className="mr-2">✓</span>
            Code Validation Successful
          </h4>
          <p className="text-green-200">
            All files were validated successfully. The code should be free of syntax errors and common issues.
          </p>
        </div>
      )}
    </motion.div>
  );
};

export default ValidationResults;
