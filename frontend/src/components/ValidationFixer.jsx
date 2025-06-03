import React, { useState } from 'react';
import axios from 'axios';

const ValidationFixer = ({ jobId, validation, onFixComplete }) => {
  const [isFixing, setIsFixing] = useState(false);
  const [fixProgress, setFixProgress] = useState(0);
  
  // Count total files with errors
  const errorCount = validation?.errors ? Object.keys(validation.errors).length : 0;
  
  const handleFixAll = async () => {
    if (!jobId || !validation || !validation.errors || Object.keys(validation.errors).length === 0) {
      return;
    }
    
    setIsFixing(true);
    setFixProgress(0);
    
    try {
      // Call backend API to fix all validation issues with full URL
      const response = await axios.post(`http://localhost:8000/api/jobs/${jobId}/fix-validation`);
      
      if (response.data.success) {
        // Update UI with fixed code
        setFixProgress(100);
        
        // Notify parent component that fixes have been applied
        if (onFixComplete && typeof onFixComplete === 'function') {
          onFixComplete(response.data.results);
        }
      } else {
        console.error('Failed to fix validation issues:', response.data.message);
      }
    } catch (error) {
      console.error('Error fixing validation issues:', error);
    } finally {
      setIsFixing(false);
    }
  };
  
  // If no validation errors, don't show the component
  if (!validation || !validation.errors || Object.keys(validation.errors).length === 0) {
    return null;
  }
  
  return (
    <div className="mb-6">
      <div className="flex items-center justify-between p-4 bg-blue-900 bg-opacity-30 rounded-lg border border-blue-700">
        <div>
          <h4 className="text-blue-300 font-medium">
            Detected {errorCount} {errorCount === 1 ? 'file' : 'files'} with validation issues
          </h4>
          <p className="text-blue-200 text-sm mt-1">
            Automatic fixes are available for common syntax errors
          </p>
        </div>
        
        <button
          onClick={handleFixAll}
          disabled={isFixing}
          className={`px-4 py-2 rounded-md text-white font-medium flex items-center ${
            isFixing ? 'bg-gray-600' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isFixing ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Fixing...
            </>
          ) : (
            <>
              <span className="mr-2">🔧</span>
              Fix All Issues
            </>
          )}
        </button>
      </div>
      
      {isFixing && (
        <div className="mt-2">
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${fixProgress}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ValidationFixer;
