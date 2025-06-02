import React, { useState } from 'react';
import ValidationFixer from './ValidationFixer';

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
    <div className="p-6 bg-gray-800 rounded-lg">
      <div className="mb-6 flex items-center">
        <div className={`w-4 h-4 rounded-full mr-2 ${getBadgeColor(validationData.valid)}`}></div>
        <h3 className="text-xl font-semibold text-white">
          Validation {validationData.valid ? 'Successful' : 'Failed'}
        </h3>
      </div>

      <div className="mb-6">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-gray-700 p-4 rounded-lg">
            <p className="text-gray-400 text-sm mb-1">Files Checked</p>
            <p className="text-2xl font-bold text-white">{validationData.file_count}</p>
          </div>
          <div className="bg-gray-700 p-4 rounded-lg">
            <p className="text-gray-400 text-sm mb-1">Errors Found</p>
            <p className="text-2xl font-bold text-white">{validationData.error_count}</p>
          </div>
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
        <div className="mb-6 p-4 bg-amber-900 bg-opacity-50 rounded-lg">
          <h4 className="text-amber-300 font-medium mb-2">Warnings</h4>
          <ul className="list-disc list-inside text-amber-200">
            {validationData.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </div>
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
    </div>
  );
};

export default ValidationResults;
