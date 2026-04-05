import React from 'react';
import './DataFlow.css';

interface Agent {
  id: string;
  name: string;
  status: string;
}

interface DataFlowProps {
  agents: Agent[];
}

const DataFlow: React.FC<DataFlowProps> = ({ agents }) => {
  // 定义智能体执行顺序
  const agentOrder = [
    'requirement_analyzer',
    'data_collector',
    'data_cleaner',
    'data_verifier',
    'market_analyst',
    'report_generator'
  ];

  // 获取智能体的显示名称
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

  // 检查智能体是否存在
  const agentExists = (agentName: string): boolean => {
    return agents.some(agent => agent.name === agentName);
  };

  // 获取智能体状态
  const getAgentStatus = (agentName: string): string => {
    const agent = agents.find(a => a.name === agentName);
    return agent?.status || 'pending';
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
      default:
        return 'status-pending';
    }
  };

  return (
    <div className="data-flow-container">
      <h3>数据流动可视化</h3>
      <div className="flow-diagram">
        {agentOrder.map((agentName, index) => {
          const exists = agentExists(agentName);
          const status = getAgentStatus(agentName);
          
          return (
            <React.Fragment key={agentName}>
              <div className={`flow-node ${getStatusStyle(status)} ${!exists ? 'node-hidden' : ''}`}>
                <div className="node-content">
                  <div className="node-name">{getAgentDisplayName(agentName)}</div>
                  <div className={`node-status ${getStatusStyle(status)}`}>
                    {status === 'running' ? '运行中' : 
                     status === 'completed' ? '已完成' : 
                     status === 'failed' ? '失败' : '等待中'}
                  </div>
                </div>
              </div>
              
              {index < agentOrder.length - 1 && (
                <div className={`flow-arrow ${getStatusStyle(status)}`}>
                  <div className="arrow-line"></div>
                  <div className="arrow-head"></div>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
      
      <div className="flow-legend">
        <div className="legend-item">
          <span className="legend-dot status-running"></span>
          <span>运行中</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot status-success"></span>
          <span>已完成</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot status-failed"></span>
          <span>失败</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot status-pending"></span>
          <span>等待中</span>
        </div>
      </div>
    </div>
  );
};

export default DataFlow;