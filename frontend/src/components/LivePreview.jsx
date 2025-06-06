import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const LivePreview = ({ results, isVisible = true, jobId = null }) => {
  const [previewUrl, setPreviewUrl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasContent, setHasContent] = useState(false);
  const [htmlPreview, setHtmlPreview] = useState('');

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
    
    // Try to extract HTML content for direct preview
    try {
      // Look for HTML files in the results
      let htmlContent = '';
      
      // Check in frontend/components or similar paths
      if (results.frontend && results.frontend.components) {
        const htmlFiles = Object.entries(results.frontend.components)
          .filter(([filename]) => filename.endsWith('.html'));
          
        if (htmlFiles.length > 0) {
          htmlContent = htmlFiles[0][1]; // Use the first HTML file
        }
      }
      
      // If no HTML found in components, check other places
      if (!htmlContent && results.code) {
        const htmlFiles = Object.entries(results.code)
          .filter(([filename]) => filename.endsWith('.html'));
          
        if (htmlFiles.length > 0) {
          htmlContent = htmlFiles[0][1]; // Use the first HTML file
        }
      }
      
      // If we found HTML content, create a preview
      if (htmlContent) {
        setHtmlPreview(htmlContent);
        setIsLoading(false);
        return;
      }
    } catch (e) {
      console.error('Error extracting HTML for preview:', e);
    }
    
    if (!hasFrontendContent || !jobId) {
      setIsLoading(false);
      return;
    }

    // Create a real preview using the backend service
    const preparePreview = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/preview/prepare/${jobId}`, {
          method: 'POST',
        });
        
        if (response.ok) {
          const data = await response.json();
          setPreviewUrl(`/preview/${jobId}/`);
          setError(null);
        } else {
          console.error('Failed to prepare preview');
          setError('Preview server not available. Download the code to run it locally.');
        }
      } catch (error) {
        console.error('Error preparing preview:', error);
        setError('Preview server not available. Download the code to run it locally.');
      } finally {
        setIsLoading(false);
      }
    };
    
    preparePreview();
  }, [results, jobId]);

  // Render HTML preview directly in the component
  const renderHtmlPreview = () => {
    if (!htmlPreview) return null;
    
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="w-full h-full rounded-lg overflow-hidden border border-gray-200 bg-white"
      >
        <iframe
          srcDoc={htmlPreview}
          title="HTML Preview"
          className="w-full h-full"
          sandbox="allow-scripts"
          loading="lazy"
        />
      </motion.div>
    );
  };

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
      ) : htmlPreview ? (
        renderHtmlPreview()
      ) : error ? (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center h-full bg-gray-50"
        >
          <div className="text-4xl mb-4">ℹ️</div>
          <h2 className="text-xl font-semibold mb-2">Preview Not Available</h2>
          <p className="text-gray-600 max-w-md text-center">
            {error}
          </p>
          <p className="text-gray-500 mt-4">
            Your code has been generated successfully and can be viewed in the Code tab.
          </p>
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
