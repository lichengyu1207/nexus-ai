import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AgentMarket from '@/components/market/AgentMarket';
import MyAgents from '@/components/market/MyAgents';

type TabType = 'market' | 'my-agents';

const MarketPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('market');

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: 'market', label: '人才市场', icon: '🏪' },
    { id: 'my-agents', label: '我的智能体', icon: '👥' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            智能体人才市场
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            招募、培养智能体，激活羁绊关系，打造专属团队
          </p>
        </motion.div>

        <div className="mb-6">
          <div className="flex space-x-1 bg-white dark:bg-gray-800 rounded-lg p-1 shadow-sm">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md
                  text-sm font-medium transition-all duration-200
                  ${activeTab === tab.id
                    ? 'bg-primary-500 text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'market' && (
            <motion.div
              key="market"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
            >
              <AgentMarket />
            </motion.div>
          )}

          {activeTab === 'my-agents' && (
            <motion.div
              key="my-agents"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <MyAgents />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default MarketPage;
