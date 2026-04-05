import React, { useState, useEffect } from 'react';
import './AgentCard.css';

interface Agent {
  id: string;
  name: string;
  avatar: string;
  status: string;
  started_at?: number;
  completed_at?: number;
}

interface AgentCardProps {
  agent: Agent;
  isReplayMode: boolean;
  replayProgress: number;
}

const AgentCard: React.FC<AgentCardProps> = ({ agent, isReplayMode, replayProgress }) => {
  const [thinkingLogs, setThinkingLogs] = useState<string[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);

  // 模拟智能体思考日志
  useEffect(() => {
    if (agent.status === 'running') {
      const logInterval = setInterval(() => {
        const newLog = getThinkingLog(agent.name);
        setThinkingLogs(prev => {
          const updated = [...prev, newLog];
          return updated.slice(-5); // 只保留最近5条
        });
      }, 3000);

      return () => clearInterval(logInterval);
    }
  }, [agent.status, agent.name]);

  // 根据智能体类型生成思考日志
  const getThinkingLog = (agentName: string): string => {
    const logsMap: Record<string, string[]> = {
      requirement_analyzer: [
        '正在解析用户查询...',
        '提取关键信息：地址、户型、面积...',
        '验证需求的完整性...',
        '生成结构化需求...',
        '检查是否需要补充信息...'
      ],
      data_collector: [
        '从多个数据源采集数据...',
        '获取房产基本信息...',
        '收集历史成交数据...',
        '获取周边配套信息...',
        '整合多源数据...'
      ],
      data_cleaner: [
        '清洗和标准化数据...',
        '处理缺失值...',
        '标准化数据格式...',
        '移除异常值...',
        '生成干净的数据集...'
      ],
      data_verifier: [
        '验证数据一致性...',
        '交叉检查多个数据源...',
        '评估数据可信度...',
        '标记可疑数据...',
        '生成验证报告...'
      ],
      market_analyst: [
        '分析市场趋势...',
        '评估投资回报率...',
        '分析供需关系...',
        '预测未来走势...',
        '生成市场分析报告...'
      ],
      report_generator: [
        '整合分析结果...',
        '生成结构化报告...',
        '添加数据可视化...',
        '编写专业建议...',
        '完成最终报告...'
      ]
    };

    const logs = logsMap[agentName] || ['正在处理...', '分析数据中...', '生成结果...'];
    return logs[Math.floor(Math.random() * logs.length)];
  };

  // 获取状态样式
  const getStatusStyle = (status: string): string => {
    switch (status) {
      case 'running':
        return 'status-running';
      case 'completed':
        return 'status-success';
      case 'failed':
        return 'status-failed';
      case 'cancelled':
        return 'status-cancelled';
      default:
        return 'status-pending';
    }
  };

  // 获取状态文本
  const getStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
      running: '运行中',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消',
      pending: '等待中'
    };
    return statusMap[status] || status;
  };

  // 计算耗时
  const getDuration = (): string => {
    if (!agent.started_at) return '0s';
    const endTime = agent.completed_at || Date.now() / 1000;
    const duration = endTime - agent.started_at;
    return `${Math.round(duration)}s`;
  };

  return (
    <div className={`agent-card ${isReplayMode ? 'replay-mode' : ''}`}>
      <div className="agent-header">
        <div className="agent-avatar">
          <span className="avatar-emoji">{agent.avatar}</span>
        </div>
        <div className="agent-info">
          <h4 className="agent-name">{getAgentDisplayName(agent.name)}</h4>
          <div className={`agent-status ${getStatusStyle(agent.status)}`}>
            {getStatusText(agent.status)}
          </div>
        </div>
        <div className="agent-duration">
          {getDuration()}
        </div>
      </div>

      <div className="agent-body">
        {thinkingLogs.length > 0 && (
          <div className="thinking-logs">
            <h5>AI思考过程</h5>
            <div className="logs-container">
              {thinkingLogs.map((log, index) => (
                <div key={index} className="log-item">
                  <span className="log-dot"></span>
                  <span className="log-text">{log}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {agent.status === 'completed' && (
          <div className="agent-result">
            <button 
              className="view-details-button"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? '收起详情' : '查看完整思考过程'}
            </button>
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="agent-details">
          <p>智能体 {getAgentDisplayName(agent.name)} 已完成任务</p>
          <p>开始时间: {agent.started_at ? new Date(agent.started_at * 1000).toLocaleTimeString() : '-'}</p>
          <p>完成时间: {agent.completed_at ? new Date(agent.completed_at * 1000).toLocaleTimeString() : '-'}</p>
          <p>耗时: {getDuration()}</p>
        </div>
      )}
    </div>
  );
};

// 获取智能体显示名称
const getAgentDisplayName = (agentName: string): string => {
  const nameMap: Record<string, string> = {
    requirement_analyzer: '需求分析师',
    data_collector: '数据采集师',
    data_cleaner: '数据清洗师',
    data_verifier: '数据核验师',
    market_analyst: '市场分析师',
    report_generator: '报告生成师'
  };
  return nameMap[agentName] || agentName;
};

export default AgentCard;