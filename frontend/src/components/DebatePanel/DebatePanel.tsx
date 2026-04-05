import React, { useState, useEffect } from 'react';
import './DebatePanel.css';

interface DebateTurn {
  id: string;
  session_id: string;
  agent_name: string;
  content: string;
  turn_number: number;
  created_at: string;
}

interface DebateSession {
  id: string;
  task_id: string;
  topic: string;
  participants: string[];
  turns: DebateTurn[];
  started_at: string;
  ended_at?: string;
  status: string;
  current_turn: number;
  max_turns: number;
}

interface DebatePanelProps {
  taskId: string;
  isOpen: boolean;
  onClose: () => void;
}

const DebatePanel: React.FC<DebatePanelProps> = ({ taskId, isOpen, onClose }) => {
  const [debates, setDebates] = useState<DebateSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId || !isOpen) return;
    
    fetchDebates();
    const interval = setInterval(fetchDebates, 3000); // 每3秒刷新
    
    return () => clearInterval(interval);
  }, [taskId, isOpen]);

  const fetchDebates = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}/debate`);
      if (response.ok) {
        const data = await response.json();
        setDebates(data || []);
      }
    } catch (error) {
      console.error('Error fetching debates:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAgentAvatar = (agentName: string): string => {
    const avatars: { [key: string]: string } = {
      'requirement_analyzer': '🔍',
      'data_collector': '📊',
      'data_cleaner': '🧹',
      'data_verifier': '✅',
      'market_analyst': '📈',
      'report_generator': '📄'
    };
    return avatars[agentName] || '🤖';
  };

  const getAgentName = (agentName: string): string => {
    const names: { [key: string]: string } = {
      'requirement_analyzer': '需求分析师',
      'data_collector': '数据采集师',
      'data_cleaner': '数据清洗师',
      'data_verifier': '数据验证师',
      'market_analyst': '市场分析师',
      'report_generator': '报告生成师'
    };
    return names[agentName] || agentName;
  };

  const getAgentColor = (agentName: string): string => {
    const colors: { [key: string]: string } = {
      'requirement_analyzer': '#3b82f6',
      'data_collector': '#10b981',
      'data_cleaner': '#f59e0b',
      'data_verifier': '#8b5cf6',
      'market_analyst': '#ef4444',
      'report_generator': '#06b6d4'
    };
    return colors[agentName] || '#6b7280';
  };

  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const toggleSession = (sessionId: string) => {
    setExpandedSession(expandedSession === sessionId ? null : sessionId);
  };

  if (!isOpen) return null;

  return (
    <div className="debate-panel-overlay">
      <div className="debate-panel">
        <div className="debate-header">
          <h3>🗣️ 专家观点交锋</h3>
          <button onClick={onClose} className="close-button">✕</button>
        </div>

        <div className="debate-content">
          {loading ? (
            <div className="loading">加载中...</div>
          ) : debates.length === 0 ? (
            <div className="no-debates">
              <p>暂无辩论记录</p>
              <p className="hint">当代理之间出现分歧时，系统会自动启动辩论</p>
            </div>
          ) : (
            <div className="debates-list">
              {debates.map((debate) => (
                <div key={debate.id} className="debate-session">
                  <div 
                    className="session-header"
                    onClick={() => toggleSession(debate.id)}
                  >
                    <div className="session-title">
                      <span className="topic-icon">💬</span>
                      <span className="topic-text">{debate.topic}</span>
                    </div>
                    <div className="session-meta">
                      <span className={`status-badge ${debate.status}`}>
                        {debate.status === 'active' ? '进行中' : '已完成'}
                      </span>
                      <span className="turns-count">
                        {debate.current_turn}/{debate.max_turns * debate.participants.length} 回合
                      </span>
                      <span className="expand-icon">
                        {expandedSession === debate.id ? '▼' : '▶'}
                      </span>
                    </div>
                  </div>

                  {expandedSession === debate.id && (
                    <div className="session-turns">
                      <div className="participants">
                        <span>参与者：</span>
                        {debate.participants.map((participant, index) => (
                          <span 
                            key={index} 
                            className="participant-badge"
                            style={{ backgroundColor: getAgentColor(participant) }}
                          >
                            {getAgentAvatar(participant)} {getAgentName(participant)}
                          </span>
                        ))}
                      </div>

                      <div className="turns-list">
                        {debate.turns.map((turn, index) => (
                          <div 
                            key={turn.id} 
                            className="turn-item"
                            style={{ borderLeftColor: getAgentColor(turn.agent_name) }}
                          >
                            <div className="turn-header">
                              <span className="agent-avatar">{getAgentAvatar(turn.agent_name)}</span>
                              <span className="agent-name">{getAgentName(turn.agent_name)}</span>
                              <span className="turn-number">回合 {turn.turn_number}</span>
                              <span className="turn-time">{formatTime(turn.created_at)}</span>
                            </div>
                            <div className="turn-content">
                              {turn.content}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="debate-footer">
          <div className="debate-stats">
            <span>共 {debates.length} 个辩论</span>
            <span>•</span>
            <span>{debates.filter(d => d.status === 'active').length} 个进行中</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DebatePanel;
