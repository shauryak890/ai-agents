import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const LivePreview = ({ results, isVisible = true, jobId = null }) => {
  const [previewUrl, setPreviewUrl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasContent, setHasContent] = useState(false);

  useEffect(() => {
    // Check if we have actual content to display
    if (!results) {
      setIsLoading(false);
      setHasContent(false);
      return;
    }
    
    // Check if we have frontend code to preview
    const hasFrontendContent = results?.frontend && 
      (results.frontend.components || results.frontend.styles);
      
    setHasContent(!!hasFrontendContent);
    
    if (!hasFrontendContent || !jobId) {
      setIsLoading(false);
      return;
    }

    // Create a real preview using the backend service
    const preparePreview = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/api/preview/prepare/${jobId}`, {
          method: 'POST',
        });
        
        if (response.ok) {
          const data = await response.json();
          setPreviewUrl(`http://localhost:8000/preview/${jobId}/`);
          setError(null);
        } else {
          console.error('Failed to prepare preview');
          setError('Failed to prepare preview');
        }
      } catch (error) {
        console.error('Error preparing preview:', error);
        setError('Error connecting to preview server');
      } finally {
        setIsLoading(false);
      }
    };
    
    preparePreview();
  }, [results, jobId]);

  return (
    <div className={`${isVisible ? 'block' : 'hidden'} h-full w-full`}>
      {!results ? (
        <div className="flex items-center justify-center h-full bg-gray-800 rounded-lg p-8">
          <div className="text-center">
            <p className="text-gray-400">Submit your prompt to generate an application.</p>
          </div>
        </div>
      ) : isLoading ? (
        <div className="flex items-center justify-center h-full bg-gray-50">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
          <p className="text-gray-600 ml-4">Preparing preview...</p>
        </div>
      ) : error ? (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center h-full bg-red-50"
        >
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-red-600 mb-2">Preview Error</h2>
          <p className="text-red-500">{error}</p>
        </motion.div>
      ) : !previewUrl ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center h-full bg-gray-50"
        >
          <div className="text-4xl mb-4">🚀</div>
          <h2 className="text-xl font-semibold mb-2">Your app preview will appear here</h2>
          <p className="text-gray-600">Submit your prompt to generate an application</p>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="w-full h-full rounded-lg overflow-hidden border border-gray-200 bg-white"
        >
          <iframe
            src={previewUrl}
            title="App Preview"
            className="w-full h-full"
            sandbox="allow-scripts allow-forms allow-same-origin"
            loading="lazy"
          />
        </motion.div>
      )}
    </div>
  );
};

export default LivePreview;
