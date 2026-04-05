import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { ChevronUpIcon, ChevronDownIcon, BugAntIcon } from '@heroicons/react/24/outline';

const DebugPanel: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (import.meta.env.PROD) return null;
  
  const { user } = useAuth();
  const source = localStorage.getItem('user_source') || 'unknown';
  
  return (
    <div className="fixed bottom-4 left-4 bg-gray-900 text-white rounded-lg opacity-90 text-xs z-50 font-mono overflow-hidden shadow-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full px-3 py-2 bg-gray-800 hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BugAntIcon className="w-4 h-4 text-green-400" />
          <span className="text-green-400 font-bold">Debug</span>
        </div>
        {isExpanded ? (
          <ChevronDownIcon className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronUpIcon className="w-4 h-4 text-gray-400" />
        )}
      </button>
      
      {isExpanded && (
        <div className="p-3 space-y-1 border-t border-gray-700">
          <div className="text-gray-400">User: <span className="text-white">{user?.email || '未登录'}</span></div>
          <div className="text-gray-400">Source: <span className="text-white">{source}</span></div>
          <div className="text-gray-400">Role: <span className="text-white">{user?.role || 'guest'}</span></div>
          <div className="text-gray-400">Admin: <span className={user?.is_admin ? 'text-green-400' : 'text-gray-500'}>{user?.is_admin ? 'Yes' : 'No'}</span></div>
        </div>
      )}
    </div>
  );
};

export default DebugPanel;
