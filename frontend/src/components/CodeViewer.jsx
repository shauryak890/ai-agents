import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Folder, File, ArrowLeft } from 'lucide-react';

// Helper to determine language for syntax highlighting
const getLanguage = (filename) => {
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

const CodeViewer = ({ results }) => {
  const [activeTab, setActiveTab] = useState('frontend');
  const [currentFile, setCurrentFile] = useState(null);
  const [breadcrumbs, setBreadcrumbs] = useState([]);

  // Check if we have valid results
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

  // Get the current section data based on active tab
  const getCurrentSection = () => {
    switch (activeTab) {
      case 'frontend':
        return results.frontend || {};
      case 'backend':
        return results.backend || {};
      case 'tests':
        return results.tester || {};
      case 'deployment':
        return results.deployment || {};
      default:
        return {};
    }
  };

  const currentSection = getCurrentSection();

  // Render file browser
  const renderFileBrowser = () => {
    // If we're viewing a file, show its content
    if (currentFile) {
      const fileContent = typeof currentFile.content === 'object' 
        ? JSON.stringify(currentFile.content, null, 2)
        : currentFile.content;
        
      return (
        <>
          <div className="flex items-center mb-4 text-gray-300 text-sm">
            <button 
              onClick={() => {
                setCurrentFile(null);
                if (breadcrumbs.length > 0) {
                  // Pop the last item off the breadcrumbs
                  const newBreadcrumbs = [...breadcrumbs];
                  newBreadcrumbs.pop();
                  setBreadcrumbs(newBreadcrumbs);
                }
              }}
              className="flex items-center mr-2 text-blue-400 hover:text-blue-300"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> Back
            </button>
            <span className="mx-2">/</span>
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={index}>
                <span>{crumb}</span>
                <span className="mx-2">/</span>
              </React.Fragment>
            ))}
            <span className="text-white">{currentFile.name}</span>
          </div>
          
          <div className="bg-gray-900 rounded-lg overflow-hidden">
            <SyntaxHighlighter
              language={getLanguage(currentFile.name)}
              style={vscDarkPlus}
              customStyle={{ margin: 0, padding: '1rem', fontSize: '0.9rem' }}
              wrapLines={true}
              showLineNumbers={true}
            >
              {fileContent}
            </SyntaxHighlighter>
          </div>
        </>
      );
    }

    // Otherwise show the file browser
    const renderFileTree = (obj, path = []) => {
      return Object.entries(obj).map(([key, value]) => {
        // If value is a string, it's a file
        if (typeof value === 'string' || typeof value === 'object' && !Array.isArray(value)) {
          return (
            <div 
              key={key}
              onClick={() => {
                setCurrentFile({ name: key, content: value });
                setBreadcrumbs([...path]);
              }}
              className="flex items-center py-2 px-3 hover:bg-gray-700 rounded cursor-pointer"
            >
              <File className="w-4 h-4 mr-2 text-blue-400" />
              <span className="text-gray-300">{key}</span>
            </div>
          );
        }
        
        // If it's an object, it's a directory
        if (typeof value === 'object') {
          return (
            <div key={key} className="mb-2">
              <div className="flex items-center py-2 px-3 text-gray-200 font-medium">
                <Folder className="w-4 h-4 mr-2 text-yellow-400" />
                <span>{key}</span>
              </div>
              <div className="ml-4 border-l border-gray-700 pl-2">
                {renderFileTree(value, [...path, key])}
              </div>
            </div>
          );
        }
        
        return null;
      });
    };

    return renderFileTree(currentSection);
  };

  return (
    <div className="bg-gray-800 bg-opacity-50 p-6 rounded-lg backdrop-blur-sm border border-gray-700">
      <h2 className="text-xl font-semibold text-white mb-4">Generated Code</h2>
      
      {/* Tabs */}
      <div className="flex mb-4 border-b border-gray-700">
        {['frontend', 'backend', 'tests', 'deployment'].map((tab) => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab);
              setCurrentFile(null);
              setBreadcrumbs([]);
            }}
            className={`px-4 py-2 font-medium capitalize ${
              activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>
      
      {/* Code content */}
      <div className="mt-4 overflow-auto" style={{ maxHeight: '500px' }}>
        {renderFileBrowser()}
      </div>
    </div>
  );
};

export default CodeViewer;
