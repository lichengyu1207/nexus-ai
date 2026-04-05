import React, { useState, useEffect } from 'react';
import './AgentChatPanel.css';

interface Message {
  id: string;
  task_id: string;
  from_agent: string;
  to_agent: string;
  type: string;
  content: { [key: string]: any };
  created_at: string;
  read_at?: string;
}

interface AgentChatPanelProps {
  taskId: string;
  isOpen: boolean;
  onClose: () => void;
}

const AgentChatPanel: React.FC<AgentChatPanelProps> = ({ taskId, isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (!taskId || !isOpen) return;
    
    fetchMessages();
    const interval = setInterval(fetchMessages, 2000); // 每2秒刷新
    
    return () => clearInterval(interval);
  }, [taskId, isOpen]);

  useEffect(() => {
    if (autoScroll && messages.length > 0) {
      scrollToBottom();
    }
  }, [messages, autoScroll]);

  const fetchMessages = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}/messages`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    const container = document.getElementById('chat-messages');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  };

  const getAgentAvatar = (agentName: string): string => {
    const avatars: { [key: string]: string } = {
      'requirement_analyzer': '🔍',
      'data_collector': '📊',
      'data_cleaner': '🧹',
      'data_verifier': '✅',
      'market_analyst': '📈',
      'report_generator': '📄',
      'admin': '👤'
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
      'report_generator': '报告生成师',
      'admin': '管理员'
    };
    return names[agentName] || agentName;
  };

  const getMessageTypeIcon = (type: string): string => {
    const icons: { [key: string]: string } = {
      'REQUEST': '📨',
      'RESPONSE': '✉️',
      'NOTIFY': '🔔',
      'DEBATE': '💬'
    };
    return icons[type] || '💬';
  };

  const getMessageTypeColor = (type: string): string => {
    const colors: { [key: string]: string } = {
      'REQUEST': '#3b82f6',
      'RESPONSE': '#10b981',
      'NOTIFY': '#f59e0b',
      'DEBATE': '#8b5cf6'
    };
    return colors[type] || '#6b7280';
  };

  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const filteredMessages = messages.filter(msg => {
    if (filter === 'all') return true;
    return msg.from_agent === filter || msg.to_agent === filter;
  });

  const uniqueAgents = Array.from(new Set(messages.flatMap(msg => [msg.from_agent, msg.to_agent])));

  if (!isOpen) return null;

  return (
    <div className="chat-panel-overlay">
      <div className="chat-panel">
        <div className="chat-header">
          <h3>🤖 代理对话流</h3>
          <div className="chat-controls">
            <select 
              value={filter} 
              onChange={(e) => setFilter(e.target.value)}
              className="agent-filter"
            >
              <option value="all">所有代理</option>
              {uniqueAgents.map(agent => (
                <option key={agent} value={agent}>
                  {getAgentName(agent)}
                </option>
              ))}
            </select>
            <label className="auto-scroll-toggle">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
              />
              自动滚动
            </label>
            <button onClick={onClose} className="close-button">✕</button>
          </div>
        </div>

        <div className="chat-messages" id="chat-messages">
          {loading ? (
            <div className="loading">加载中...</div>
          ) : filteredMessages.length === 0 ? (
            <div className="no-messages">暂无消息</div>
          ) : (
            filteredMessages.map((message, index) => (
              <div key={message.id || index} className="message-item">
                <div className="message-header">
                  <div className="message-from">
                    <span className="agent-avatar">{getAgentAvatar(message.from_agent)}</span>
                    <span className="agent-name">{getAgentName(message.from_agent)}</span>
                  </div>
                  <span className="message-arrow">→</span>
                  <div className="message-to">
                    <span className="agent-avatar">{getAgentAvatar(message.to_agent)}</span>
                    <span className="agent-name">{getAgentName(message.to_agent)}</span>
                  </div>
                </div>
                
                <div className="message-body">
                  <div className="message-type" style={{ color: getMessageTypeColor(message.type) }}>
                    {getMessageTypeIcon(message.type)} {message.type}
                  </div>
                  <div className="message-content">
                    {typeof message.content === 'string' 
                      ? message.content 
                      : JSON.stringify(message.content, null, 2)
                    }
                  </div>
                  <div className="message-time">
                    {formatTime(message.created_at)}
                    {message.read_at && <span className="read-status"> ✓已读</span>}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="chat-footer">
          <div className="message-stats">
            <span>共 {messages.length} 条消息</span>
            <span>•</span>
            <span>{uniqueAgents.length} 个代理参与</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentChatPanel;
