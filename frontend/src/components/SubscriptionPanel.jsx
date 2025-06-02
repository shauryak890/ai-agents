import React from 'react';
import { motion } from 'framer-motion';
import { Check, Star } from 'lucide-react';

const SubscriptionPanel = () => {
  const plans = [
    {
      name: 'Free',
      description: 'Basic access to AI app generation',
      price: '$0',
      features: [
        'Generate simple apps',
        'Basic code generation',
        'Standard LLM models',
        'Limited downloads per day'
      ],
      color: 'from-blue-600 to-blue-800',
      recommended: false
    },
    {
      name: 'Pro',
      description: 'Advanced features for serious developers',
      price: '$19/mo',
      features: [
        'Generate complex apps',
        'Advanced code optimization',
        'Priority generation queue',
        'Unlimited downloads',
        'Access to all agent types',
        'Custom deployment options'
      ],
      color: 'from-purple-600 to-indigo-800',
      recommended: true
    }
  ];

  return (
    <div className="bg-gray-800 bg-opacity-50 p-6 rounded-lg backdrop-blur-sm border border-gray-700">
      <h2 className="text-xl font-semibold text-white mb-4">Subscription Plans</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {plans.map((plan, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`relative rounded-lg border ${
              plan.recommended 
                ? 'border-purple-500' 
                : 'border-gray-700'
            } overflow-hidden`}
          >
            {plan.recommended && (
              <div className="absolute top-0 right-0 bg-purple-500 text-white text-xs font-medium px-2 py-1 flex items-center">
                <Star className="w-3 h-3 mr-1" /> RECOMMENDED
              </div>
            )}
            
            <div className={`bg-gradient-to-br ${plan.color} p-4`}>
              <h3 className="text-xl font-bold text-white">{plan.name}</h3>
              <p className="text-gray-200 text-sm">{plan.description}</p>
              <p className="text-white text-2xl font-bold mt-2">{plan.price}</p>
            </div>
            
            <div className="p-4 bg-gray-900">
              <ul className="space-y-2">
                {plan.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-start text-gray-300 text-sm">
                    <Check className="w-4 h-4 text-green-500 mr-2 mt-0.5" />
                    {feature}
                  </li>
                ))}
              </ul>
              
              <button 
                className={`w-full mt-4 py-2 rounded-md font-medium ${
                  plan.recommended
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-gray-700 hover:bg-gray-600 text-white'
                }`}
              >
                {plan.recommended ? 'Upgrade Now' : 'Current Plan'}
              </button>
            </div>
          </motion.div>
        ))}
      </div>
      
      <p className="text-gray-400 text-sm mt-4 text-center">
        All plans include access to our open-source tools and community support.
      </p>
    </div>
  );
};

export default SubscriptionPanel;
