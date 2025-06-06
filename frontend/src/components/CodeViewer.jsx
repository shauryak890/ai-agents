import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Folder, File, ArrowLeft, Download, Code } from 'lucide-react';

// Helper to determine language for syntax highlighting
const getLanguage = (filename) => {
  if (!filename) return 'text';
  const extension = filename.split('.').pop().toLowerCase();
  const mapping = {
    js: 'javascript',
    jsx: 'jsx',
    ts: 'typescript',
    tsx: 'tsx',
    py: 'python',
    html: 'html',
    css: 'css',
    json: 'json',
    md: 'markdown',
    yml: 'yaml',
    yaml: 'yaml',
    sh: 'bash',
    bash: 'bash',
    dockerfile: 'dockerfile',
    txt: 'text',
  };
  return mapping[extension] || 'text';
};

const CodeViewer = ({ results, onDownload }) => {
  const [activeTab, setActiveTab] = useState('all');
  const [currentFile, setCurrentFile] = useState(null);
  const [breadcrumbs, setBreadcrumbs] = useState([]);
  const [files, setFiles] = useState({});
  
  // Extract files from results when they change
  useEffect(() => {
    if (results) {
      const extractedFiles = extractFilesFromResults(results);
      setFiles(extractedFiles);
      console.log('Extracted files:', Object.keys(extractedFiles));
    }
  }, [results]);

  // No results yet
  if (!results || Object.keys(results).length === 0) {
    return (
      <div className="bg-gray-800 bg-opacity-50 p-6 rounded-lg backdrop-blur-sm border border-gray-700">
        <h2 className="text-xl font-semibold text-white mb-4">Generated Code</h2>
        <div className="text-gray-400 text-center py-8">
          No code generated yet. Submit a prompt to start generating.
        </div>
      </div>
    );
  }

  // Extract files from various result formats
  function extractFilesFromResults(results) {
    // First check if results.code exists (typical format)
    if (results.code && typeof results.code === 'object') {
      console.log('Found code object in results');
      return results.code;
    }
    
    // Then check for files structure
    if (results.files && typeof results.files === 'object') {
      console.log('Found files object in results');
      return results.files;
    }
    
    // Try to find code in CrewAI's nested structure
    const extractedFiles = {};
    
    // Look for code in sections like frontend, backend, etc.
    const sections = ['frontend', 'backend', 'deployment', 'tests'];
    let foundSections = false;
    
    sections.forEach(section => {
      if (results[section] && typeof results[section] === 'object') {
        foundSections = true;
        
        // Check for different possible structures
        if (results[section].files) {
          Object.entries(results[section].files).forEach(([filename, content]) => {
            extractedFiles[`${section}/${filename}`] = content;
          });
        } else if (results[section].code) {
          Object.entries(results[section].code).forEach(([filename, content]) => {
            extractedFiles[`${section}/${filename}`] = content;
          });
        } else {
          // Handle case where section contains direct filename/content pairs
          Object.entries(results[section]).forEach(([key, value]) => {
            if (typeof value === 'string' && key.includes('.')) {
              extractedFiles[`${section}/${key}`] = value;
            } else if (typeof value === 'object') {
              Object.entries(value).forEach(([subKey, subValue]) => {
                if (typeof subValue === 'string' && subKey.includes('.')) {
                  extractedFiles[`${section}/${key}/${subKey}`] = subValue;
                }
              });
            }
          });
        }
      }
    });
    
    if (foundSections && Object.keys(extractedFiles).length > 0) {
      console.log('Found section-based code');
      return extractedFiles;
    }
    
    // If there's a raw_output field with code blocks, extract them
    if (results.raw_output && typeof results.raw_output === 'string') {
      const codeBlocks = extractCodeBlocksFromMarkdown(results.raw_output);
      if (Object.keys(codeBlocks).length > 0) {
        console.log('Extracted code blocks from raw_output');
        return codeBlocks;
      }
    }
    
    // Look for any keys that seem like filenames
    const possibleFiles = Object.keys(results).filter(key => 
      key.includes('.') || /\.(js|jsx|ts|tsx|py|html|css|json|md)$/.test(key)
    );
    
    if (possibleFiles.length > 0) {
      const fileMap = {};
      possibleFiles.forEach(filename => {
        fileMap[filename] = results[filename];
      });
      console.log('Found direct filename keys');
      return fileMap;
    }
    
    // Check if the results might be a JSON string that contains code
    if (typeof results === 'string') {
      try {
        const parsed = JSON.parse(results);
        if (parsed && typeof parsed === 'object') {
          return extractFilesFromResults(parsed); // Recursively check the parsed object
        }
      } catch (e) {
        // Not valid JSON, ignore
      }
    }
    
    console.log('No code files found in results', results);
    return {};
  }
  
  // Helper function to extract code blocks from markdown
  function extractCodeBlocksFromMarkdown(markdown) {
    const files = {};
    let fileCounter = 1;
    
    // Match code blocks with language specification
    const codeBlockRegex = /```(\w+)\n([\s\S]*?)```/g;
    let match;
    
    while ((match = codeBlockRegex.exec(markdown)) !== null) {
      const language = match[1];
      const code = match[2].trim();
      
      // Determine filename based on language
      let filename;
      switch (language) {
        case 'javascript':
        case 'js':
          filename = `script${fileCounter}.js`;
          break;
        case 'jsx':
          filename = `component${fileCounter}.jsx`;
          break;
        case 'python':
        case 'py':
          filename = `script${fileCounter}.py`;
          break;
        case 'html':
          filename = `page${fileCounter}.html`;
          break;
        case 'css':
          filename = `styles${fileCounter}.css`;
          break;
        case 'json':
          filename = `data${fileCounter}.json`;
          break;
        default:
          filename = `file${fileCounter}.${language || 'txt'}`;
      }
      
      files[filename] = code;
      fileCounter++;
    }
    
    return files;
  }

  // Render the file viewer
  const renderFileViewer = () => {
    // If viewing a specific file
    if (currentFile && files[currentFile]) {
      const fileContent = files[currentFile];
      const language = getLanguage(currentFile);
      
      return (
        <div className="p-4">
          {/* Breadcrumbs and back button */}
          <div className="flex items-center mb-4 text-gray-400 text-sm">
            <button 
              onClick={() => {
                setCurrentFile(null);
                setBreadcrumbs([]);
              }}
              className="flex items-center hover:text-blue-400 transition-colors"
            >
              <ArrowLeft size={16} className="mr-1" />
              Back to files
            </button>
            
            {breadcrumbs.length > 0 && (
              <div className="flex items-center ml-4">
                {breadcrumbs.map((crumb, index) => (
                  <React.Fragment key={index}>
                    <span className="mx-1">/</span>
                    <span>{crumb}</span>
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>
          
          {/* Filename header */}
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-medium text-gray-100">{currentFile}</h3>
            
            {/* Copy code button */}
            <button
              onClick={() => {
                navigator.clipboard.writeText(fileContent);
                // Show a toast or some feedback
                alert('Code copied to clipboard!');
              }}
              className="text-gray-400 hover:text-blue-400 flex items-center text-sm"
            >
              <Code size={14} className="mr-1" /> Copy code
            </button>
          </div>
          
          {/* Code display */}
          <div className="border border-gray-700 rounded-lg overflow-hidden">
            <SyntaxHighlighter
              language={language}
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                padding: '1rem',
                fontSize: '0.9rem',
                lineHeight: '1.5',
                maxHeight: '600px',
                backgroundColor: '#1e1e1e'
              }}
              showLineNumbers={true}
              wrapLines={true}
            >
              {fileContent || ''}
            </SyntaxHighlighter>
          </div>
        </div>
      );
    }
    
    // Otherwise show the file list
    const fileList = Object.keys(files);
    
    // Filter files based on active tab
    const filteredFiles = fileList.filter(filename => {
      if (activeTab === 'all') return true;
      return filename.toLowerCase().includes(activeTab.toLowerCase());
    });
    
    // Group files by directory if they contain path separators
    const hasDirectories = fileList.some(f => f.includes('/'));
    
    return (
      <div className="p-4">
        <h2 className="text-lg font-medium text-gray-100 mb-4">Generated Files</h2>
        
        {/* Tab navigation if we have different sections */}
        {hasDirectories && (
          <div className="flex mb-4 border-b border-gray-700 overflow-x-auto pb-1">
            {['all', 'frontend', 'backend', 'tests', 'deployment'].map(tab => (
              <button
                key={tab}
                className={`px-4 py-2 whitespace-nowrap ${activeTab === tab ? 'text-blue-500 border-b-2 border-blue-500' : 'text-gray-400 hover:text-gray-300'}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === 'all' ? 'All Files' : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        )}
        
        {/* File list */}
        <div className="grid gap-2">
          {filteredFiles.length === 0 ? (
            <div className="text-gray-400 py-4">
              No files found in this section. Try selecting a different tab or check the terminal for more information.
            </div>
          ) : (
            filteredFiles.map(filename => (
              <div 
                key={filename}
                onClick={() => {
                  setCurrentFile(filename);
                  // Set breadcrumbs if this is a nested path
                  const parts = filename.split('/');
                  if (parts.length > 1) {
                    setBreadcrumbs(parts.slice(0, -1));
                  }
                }}
                className="flex items-center p-3 bg-gray-700 bg-opacity-30 rounded-lg cursor-pointer hover:bg-opacity-50 transition-colors"
              >
                <File size={18} className="text-blue-400 mr-3 flex-shrink-0" />
                <div className="flex-1 overflow-hidden">
                  <div className="text-gray-200 truncate">
                    {/* Show just the filename without the path for cleaner display */}
                    {filename.includes('/') ? filename.split('/').pop() : filename}
                  </div>
                  {filename.includes('/') && (
                    <div className="text-xs text-gray-400 truncate">{filename}</div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-gray-800 bg-opacity-50 p-6 rounded-lg backdrop-blur-sm border border-gray-700">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">Generated Code</h2>
        
        {/* Download all button */}
        {Object.keys(files).length > 0 && (
          <button
            onClick={() => {
              if (typeof onDownload === 'function') {
                onDownload();
              } else {
                console.log('Download function not provided');
                alert('Download functionality is not available');
              }
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1 rounded flex items-center text-sm"
          >
            <Download size={14} className="mr-2" />
            Download All
          </button>
        )}
      </div>
      
      {/* File browser */}
      <div className="mt-4 overflow-auto bg-gray-900 bg-opacity-50 rounded-lg" style={{ maxHeight: '600px' }}>
        {renderFileViewer()}
      </div>
    </div>
  );
};

export default CodeViewer;
