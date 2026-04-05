import React, { useState } from 'react';
import DemoExperience from './DemoExperience';

const DemoButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="group relative inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 overflow-hidden"
      >
        <span className="absolute inset-0 bg-gradient-to-r from-amber-400 via-orange-400 to-red-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        <span className="relative flex items-center gap-2">
          <span className="text-xl">🏠</span>
          <span>体验周瑜帮你选房</span>
          <span className="ml-1 px-2 py-0.5 bg-white/20 rounded-full text-xs">一键体验</span>
        </span>
        
        <span className="absolute -top-1 -right-1 w-3 h-3">
          <span className="absolute inset-0 bg-white rounded-full animate-ping opacity-75" />
          <span className="relative block w-3 h-3 bg-white rounded-full" />
        </span>
      </button>

      <DemoExperience isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
};

export default DemoButton;
