import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Send, Loader2 } from 'lucide-react';

const PromptInput = ({ value, onChange, onSubmit, isLoading, placeholder, isProcessing }) => {
  // Use external state if provided, otherwise use internal state
  const [localPrompt, setLocalPrompt] = useState('');
  
  // Determine which state and handlers to use
  const promptValue = value !== undefined ? value : localPrompt;
  const handleChange = onChange || setLocalPrompt;
  const processing = isLoading !== undefined ? isLoading : isProcessing;
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (promptValue.trim() && !processing) {
      onSubmit(promptValue);
    }
  };

  return (
    <div className="bg-gray-800 bg-opacity-50 p-6 rounded-lg backdrop-blur-sm border border-gray-700">
      <h2 className="text-xl font-semibold text-white mb-2 flex items-center gap-2">
        <Sparkles className="w-5 h-5" /> AI Agents App Builder
      </h2>
      <p className="text-gray-400 mb-4">
        Describe your app idea in detail, and our AI agents will build it for you.
      </p>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={promptValue}
          onChange={(e) => handleChange(e.target.value)}
          disabled={processing}
          className="w-full h-32 bg-gray-900 text-white rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
          placeholder={placeholder || "E.g., I need a movie recommendation app where users can browse, search, and save their favorite movies. It should have a clean UI with ratings and reviews..."}
        ></textarea>
        
        <div className="flex justify-end">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={processing || !promptValue.trim()}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg text-white font-medium ${
              processing || !promptValue.trim()
                ? 'bg-gray-700 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700'
            }`}
          >
            {processing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                Generate App
              </>
            )}
          </motion.button>
        </div>
      </form>
    </div>
  );
};

export default PromptInput;
