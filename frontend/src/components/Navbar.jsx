import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Menu, X, ChevronDown } from 'lucide-react';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showSubscriptionMenu, setShowSubscriptionMenu] = useState(false);
  
  return (
    <nav className="bg-gray-900 bg-opacity-90 backdrop-blur-sm border-b border-gray-800 fixed w-full top-0 z-50">
      <div className="container mx-auto px-4 py-3">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <div className="flex items-center">
            <motion.div 
              initial={{ rotate: 0 }}
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              className="w-8 h-8 mr-3 text-blue-500 flex items-center justify-center"
            >
              <span className="text-xl">🤖</span>
            </motion.div>
            <span className="text-white text-xl font-bold">AI Agents</span>
          </div>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            <a href="#" className="text-gray-300 hover:text-white transition-colors">Home</a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors">Examples</a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors">Docs</a>
            
            {/* Subscription Dropdown */}
            <div className="relative">
              <button
                className="flex items-center text-gray-300 hover:text-white transition-colors"
                onClick={() => setShowSubscriptionMenu(!showSubscriptionMenu)}
              >
                Subscription <ChevronDown className="ml-1 w-4 h-4" />
              </button>
              
              {/* Dropdown Menu */}
              {showSubscriptionMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-gray-800 rounded-lg shadow-lg border border-gray-700 py-2">
                  <div className="px-4 py-3 border-b border-gray-700">
                    <h3 className="text-white font-medium">Subscription Plans</h3>
                    <p className="text-gray-400 text-sm">Choose the right plan for you</p>
                  </div>
                  
                  <div className="px-4 py-2 hover:bg-gray-700 cursor-pointer">
                    <div className="flex justify-between">
                      <span className="text-white font-medium">Free</span>
                      <span className="text-gray-300">$0/mo</span>
                    </div>
                    <p className="text-gray-400 text-sm">Basic access to AI app generation</p>
                  </div>
                  
                  <div className="px-4 py-2 hover:bg-gray-700 cursor-pointer">
                    <div className="flex justify-between">
                      <span className="text-white font-medium">Pro</span>
                      <span className="text-blue-400">$29/mo</span>
                    </div>
                    <p className="text-gray-400 text-sm">Advanced features and priority access</p>
                  </div>
                  
                  <div className="px-4 py-3 border-t border-gray-700">
                    <button className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm">
                      Upgrade Now
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors">
              Sign In
            </button>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button 
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-300 hover:text-white"
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-gray-800 py-4 px-4">
          <div className="flex flex-col space-y-4">
            <a href="#" className="text-gray-300 hover:text-white transition-colors py-2">Home</a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors py-2">Examples</a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors py-2">Docs</a>
            
            {/* Mobile Subscription Section */}
            <div className="py-2 mt-2">
              <button
                onClick={() => setShowSubscriptionMenu(!showSubscriptionMenu)}
                className="flex items-center w-full text-left text-gray-300 hover:text-white transition-colors"
              >
                Subscription <ChevronDown className="ml-1 w-4 h-4" />
              </button>
              
              {showSubscriptionMenu && (
                <div className="mt-2 bg-gray-700 rounded-md p-4">
                  <div className="flex justify-between mb-3">
                    <span className="text-white">Free</span>
                    <span className="text-gray-300">$0/mo</span>
                  </div>
                  <div className="flex justify-between mb-3">
                    <span className="text-white">Pro</span>
                    <span className="text-blue-400">$29/mo</span>
                  </div>
                  <button className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm mt-2">
                    Upgrade Now
                  </button>
                </div>
              )}
            </div>
            
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors">
              Sign In
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
