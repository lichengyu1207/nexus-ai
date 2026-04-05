import React from 'react';

interface AgentSelectorProps {
  currentAgent: 'zhouyu' | 'luxun';
  onAgentChange: (agent: 'zhouyu' | 'luxun') => void;
}

const AgentSelector: React.FC<AgentSelectorProps> = ({ currentAgent, onAgentChange }) => {
  return (
    <div className="agent-selector">
      <button
        className={`agent-btn ${currentAgent === 'zhouyu' ? 'active' : ''}`}
        onClick={() => onAgentChange('zhouyu')}
      >
        周瑜 🎵
      </button>
      <button
        className={`agent-btn ${currentAgent === 'luxun' ? 'active' : ''}`}
        onClick={() => onAgentChange('luxun')}
      >
        陆逊 📜
      </button>
    </div>
  );
};

export default AgentSelector;
