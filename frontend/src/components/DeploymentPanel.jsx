import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, ArrowUpCircle, Loader2, CheckCircle, XCircle } from 'lucide-react';

const DeploymentPanel = ({ isGenerationComplete, onPreview, onDeploy }) => {
  const [previewStatus, setPreviewStatus] = useState('idle'); // idle, loading, success, error
  const [deployStatus, setDeployStatus] = useState('idle'); // idle, loading, success, error

  const handlePreview = async () => {
    if (!isGenerationComplete || previewStatus === 'loading') return;
    
    setPreviewStatus('loading');
    try {
      await onPreview();
      setPreviewStatus('success');
    } catch (error) {
      console.error('Preview error:', error);
      setPreviewStatus('error');
      setTimeout(() => setPreviewStatus('idle'), 3000);
    }
  };

  const handleDeploy = async () => {
    if (!isGenerationComplete || deployStatus === 'loading') return;
    
    setDeployStatus('loading');
    try {
      await onDeploy();
      setDeployStatus('success');
    } catch (error) {
      console.error('Deployment error:', error);
      setDeployStatus('error');
      setTimeout(() => setDeployStatus('idle'), 3000);
    }
  };

  // Helper to get button content based on status
  const getButtonContent = (status, action, icon) => {
    switch (status) {
      case 'loading':
        return (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            {action === 'preview' ? 'Generating Preview...' : 'Deploying...'}
          </>
        );
      case 'success':
        return (
          <>
            <CheckCircle className="w-5 h-5 mr-2" />
            {action === 'preview' ? 'Preview Ready' : 'Deployed Successfully'}
          </>
        );
      case 'error':
        return (
          <>
            <XCircle className="w-5 h-5 mr-2" />
            {action === 'preview' ? 'Preview Failed' : 'Deployment Failed'}
          </>
        );
      default:
        return (
          <>
            {icon}
            {action === 'preview' ? 'Preview App' : 'Deploy App'}
          </>
        );
    }
  };

  return (
    <div className="bg-gray-800 bg-opacity-50 p-6 rounded-lg backdrop-blur-sm border border-gray-700">
      <h2 className="text-xl font-semibold text-white mb-4">Preview & Deploy</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <motion.button
          whileHover={{ scale: isGenerationComplete ? 1.03 : 1 }}
          whileTap={{ scale: isGenerationComplete ? 0.97 : 1 }}
          onClick={handlePreview}
          disabled={!isGenerationComplete}
          className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium ${
            !isGenerationComplete
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : previewStatus === 'success'
              ? 'bg-green-600 text-white'
              : previewStatus === 'error'
              ? 'bg-red-600 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {getButtonContent(previewStatus, 'preview', <Eye className="w-5 h-5 mr-2" />)}
        </motion.button>
        
        <motion.button
          whileHover={{ scale: isGenerationComplete ? 1.03 : 1 }}
          whileTap={{ scale: isGenerationComplete ? 0.97 : 1 }}
          onClick={handleDeploy}
          disabled={!isGenerationComplete}
          className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium ${
            !isGenerationComplete
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : deployStatus === 'success'
              ? 'bg-green-600 text-white'
              : deployStatus === 'error'
              ? 'bg-red-600 text-white'
              : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
          }`}
        >
          {getButtonContent(deployStatus, 'deploy', <ArrowUpCircle className="w-5 h-5 mr-2" />)}
        </motion.button>
      </div>
      
      <p className="text-gray-400 text-sm mt-4 text-center">
        {isGenerationComplete 
          ? 'Your app is ready for preview and deployment!' 
          : 'Generate your app first to enable preview and deployment options.'}
      </p>
    </div>
  );
};

export default DeploymentPanel;
