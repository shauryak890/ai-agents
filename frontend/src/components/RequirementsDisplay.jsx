import React from 'react';
import { motion } from 'framer-motion';

const RequirementsDisplay = ({ requirements, isVisible = false }) => {
  // Display loading state if requirements is null/undefined
  if (!requirements) {
    return (
      <div className="flex items-center justify-center h-full bg-white rounded-lg p-8">
        <p className="text-gray-500">No requirements analysis available.</p>
      </div>
    );
  }

  if (!isVisible) {
    return null;
  }

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { staggerChildren: 0.05 }
    }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  // Safe access to requirements data with defaults
  const appName = requirements.app_name || 'Application';
  const description = requirements.description || 'A web application based on your requirements.';
  
  // Normalize sections format handling both array and object formats
  const sections = [];
  
  if (requirements.sections) {
    // Handle if sections is an array of objects with title/content
    if (Array.isArray(requirements.sections)) {
      sections.push(...requirements.sections);
    } 
    // Handle if sections is an object with key/value pairs
    else if (typeof requirements.sections === 'object') {
      Object.entries(requirements.sections).forEach(([key, value]) => {
        // Skip sections with empty arrays
        if (Array.isArray(value) && value.length === 0) return;
        
        sections.push({
          title: key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' '),
          content: Array.isArray(value) ? value : [value]
        });
      });
    }
  }

  return (
    <motion.div 
      className="w-full h-full overflow-auto bg-white rounded-lg p-4"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <motion.h2 
        className="text-2xl font-bold mb-2 text-gray-800"
        variants={itemVariants}
      >
        {appName}
      </motion.h2>
      
      <motion.p 
        className="text-gray-600 mb-6"
        variants={itemVariants}
      >
        {description}
      </motion.p>
      
      {sections.map((section, index) => (
        <motion.div 
          key={index} 
          className="mb-6"
          variants={itemVariants}
        >
          <h3 className="text-lg font-semibold mb-2 text-gray-700 border-b pb-1">
            {section.title}
          </h3>
          
          {Array.isArray(section.content) ? (
            <ul className="list-disc pl-5 space-y-1">
              {section.content.map((item, itemIndex) => (
                <li key={itemIndex} className="text-gray-700">
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-700">
              {section.content}
            </p>
          )}
        </motion.div>
      ))}
      
      {requirements.enhanced_prompt && (
        <motion.div 
          className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200"
          variants={itemVariants}
        >
          <h3 className="text-lg font-semibold mb-2 text-gray-700">
            Enhanced Prompt
          </h3>
          <p className="text-gray-700 whitespace-pre-line">
            {requirements.enhanced_prompt}
          </p>
        </motion.div>
      )}
    </motion.div>
  );
};

export default RequirementsDisplay;
