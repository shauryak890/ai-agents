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
    <div className="bg-gradient-to-br from-gray-800/70 to-gray-900/70 p-8 rounded-xl backdrop-blur-sm border border-gray-700/50 shadow-xl">
      <h2 className="text-xl font-semibold text-white mb-2 flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-blue-400" /> Describe Your App
      </h2>
      <p className="text-gray-300 mb-4">
        Provide details about your application idea, and our specialized AI crew will collaborate to build it for you.
      </p>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={promptValue}
          onChange={(e) => handleChange(e.target.value)}
          disabled={processing}
          className="w-full h-32 bg-gray-900/80 text-white rounded-xl p-4 focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none border border-gray-700/50 shadow-inner placeholder-gray-500"
          placeholder={placeholder || "E.g., Create a facebook clone application with user profiles, news feed, and messaging features..."}
        ></textarea>
        
        <div className="flex justify-end">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            type="submit"
            disabled={processing || !promptValue.trim()}
            className={`flex items-center gap-2 px-8 py-3 rounded-xl text-white font-medium shadow-lg ${
              processing || !promptValue.trim()
                ? 'bg-gray-700 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700'
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
