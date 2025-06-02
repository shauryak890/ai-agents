import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const LivePreview = ({ results, isVisible = true }) => {
  const [previewHtml, setPreviewHtml] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!results) {
      setPreviewHtml(generatePlaceholderPreview());
      setIsLoading(false);
      return;
    }

    try {
      // Generate HTML preview from results
      const html = generatePreviewFromResults(results);
      setPreviewHtml(html);
      setIsLoading(false);
    } catch (error) {
      console.error('Error generating preview:', error);
      setPreviewHtml(generateErrorPreview());
      setIsLoading(false);
    }
  }, [results]);

  const generatePlaceholderPreview = () => {
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <title>App Preview</title>
          <style>
            body {
              font-family: system-ui, -apple-system, sans-serif;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              height: 100vh;
              margin: 0;
              background: #f5f5f5;
              color: #333;
            }
            .placeholder {
              text-align: center;
              padding: 2rem;
            }
            .icon {
              font-size: 4rem;
              margin-bottom: 1rem;
            }
          </style>
        </head>
        <body>
          <div class="placeholder">
            <div class="icon">🚀</div>
            <h2>Your app preview will appear here</h2>
            <p>Submit your prompt to generate an application</p>
          </div>
        </body>
      </html>
    `;
  };

  const generateErrorPreview = () => {
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Preview Error</title>
          <style>
            body {
              font-family: system-ui, -apple-system, sans-serif;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              height: 100vh;
              margin: 0;
              background: #fff0f0;
              color: #d32f2f;
            }
            .error {
              text-align: center;
              padding: 2rem;
            }
            .icon {
              font-size: 4rem;
              margin-bottom: 1rem;
            }
          </style>
        </head>
        <body>
          <div class="error">
            <div class="icon">⚠️</div>
            <h2>Preview Error</h2>
            <p>There was an error generating the preview</p>
          </div>
        </body>
      </html>
    `;
  };

  const generatePreviewFromResults = (results) => {
    // Extract relevant parts from the results
    let html = '<!DOCTYPE html><html><head><title>Generated App Preview</title>';
    
    // Add styles from frontend results if available
    if (results.frontend && results.frontend.styles && results.frontend.styles['App.css']) {
      html += `<style>${results.frontend.styles['App.css']}</style>`;
    } else {
      // Default styling
      html += `
        <style>
          body { 
            font-family: system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f8f9fa;
            color: #333;
          }
          .app-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          }
          header {
            padding: 20px 0;
            border-bottom: 1px solid #eee;
            margin-bottom: 20px;
          }
          h1, h2 {
            margin-top: 0;
          }
          .feature-list {
            list-style-type: none;
            padding: 0;
          }
          .feature-list li {
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
          }
          .feature-list li:last-child {
            border-bottom: none;
          }
          .tech-pill {
            display: inline-block;
            background: #e9ecef;
            padding: 4px 10px;
            border-radius: 30px;
            margin-right: 8px;
            margin-bottom: 8px;
            font-size: 14px;
          }
          .button {
            background: #4F46E5;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
          }
          .button:hover {
            background: #4338CA;
          }
        </style>
      `;
    }
    
    html += '</head><body>';
    
    // Add main container
    html += '<div class="app-container">';
    
    // Add header with app title based on prompt or planning results
    if (results.planner && results.planner.features) {
      const features = results.planner.features;
      const techStack = results.planner.tech_stack || [];
      
      html += `
        <header>
          <h1>Generated App Preview</h1>
          <p>A preview of your generated application</p>
        </header>
        
        <div class="content">
          <h2>Features</h2>
          <ul class="feature-list">
            ${features.map(feature => `<li>${feature}</li>`).join('')}
          </ul>
          
          <h2>Tech Stack</h2>
          <div class="tech-stack-pills">
            ${techStack.map(tech => `<span class="tech-pill">${tech}</span>`).join('')}
          </div>
          
          <div style="margin-top: 30px;">
            <button class="button" style="opacity: 0.7; cursor: help;" title="This is a preview only. The actual app would be accessible after deployment." disabled>Try App (Preview Only)</button>
          </div>
        </div>
      `;
    } else {
      // Fallback content
      html += `
        <header>
          <h1>App Preview</h1>
          <p>Your application is being generated</p>
        </header>
        
        <div class="content">
          <p>The preview will update as agent work is completed.</p>
          <div style="margin-top: 30px;">
            <button class="button">Sample Button</button>
          </div>
        </div>
      `;
    }
    
    html += '</div></body></html>';
    
    return html;
  };

  return (
    <div className={`${isVisible ? 'block' : 'hidden'} h-full w-full`}>
      {isLoading ? (
        <div className="flex items-center justify-center h-full bg-gray-800">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="w-full h-full rounded-lg overflow-hidden border border-gray-700 bg-white"
        >
          <iframe
            srcDoc={previewHtml}
            title="App Preview"
            className="w-full h-full"
            sandbox="allow-same-origin"
          />
        </motion.div>
      )}
    </div>
  );
};

export default LivePreview;
