import React, { useState, useEffect } from 'react';
import './AnalysisProgress.css';

interface AnalysisStep {
  id: string;
  name: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  message?: string;
}

interface AgentInfo {
  id: string;
  name: string;
  avatar: string;
  status: 'idle' | 'working' | 'completed' | 'error';
  task?: string;
}

interface AnalysisProgressProps {
  status: 'idle' | 'initializing' | 'analyzing' | 'completed' | 'error';
  progress: number;
  steps?: AnalysisStep[];
  agents?: AgentInfo[];
  result?: {
    summary?: string;
    details?: Record<string, unknown>;
  };
  error?: string;
  onViewReport?: () => void;
  onRetry?: () => void;
  showAgents?: boolean;
}

const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  status,
  progress,
  steps = [],
  agents = [],
  result,
  error,
  onViewReport,
  onRetry,
  showAgents = true,
}) => {
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedProgress(progress);
    }, 100);
    return () => clearTimeout(timer);
  }, [progress]);

  const defaultSteps: AnalysisStep[] = steps.length > 0 ? steps : [
    { id: '1', name: '接收分析请求', status: status !== 'idle' ? 'completed' : 'pending' },
    { id: '2', name: '唤醒AI智能体团队', status: status === 'initializing' ? 'active' : status === 'analyzing' || status === 'completed' ? 'completed' : 'pending' },
    { id: '3', name: '启动数据采集引擎', status: status === 'analyzing' && progress < 30 ? 'active' : progress >= 30 ? 'completed' : 'pending' },
    { id: '4', name: '执行深度分析', status: status === 'analyzing' && progress >= 30 && progress < 70 ? 'active' : progress >= 70 ? 'completed' : 'pending' },
    { id: '5', name: '生成分析报告', status: status === 'analyzing' && progress >= 70 ? 'active' : status === 'completed' ? 'completed' : 'pending' },
  ];

  const defaultAgents: AgentInfo[] = agents.length > 0 ? agents : [
    { id: '1', name: '吏部', avatar: '👔', status: status === 'analyzing' ? 'working' : status === 'completed' ? 'completed' : 'idle', task: '团队协调' },
    { id: '2', name: '户部', avatar: '📊', status: status === 'analyzing' ? 'working' : status === 'completed' ? 'completed' : 'idle', task: '数据管理' },
    { id: '3', name: '礼部', avatar: '🎯', status: status === 'analyzing' ? 'working' : status === 'completed' ? 'completed' : 'idle', task: '咨询服务' },
    { id: '4', name: '兵部', avatar: '🔍', status: status === 'analyzing' ? 'working' : status === 'completed' ? 'completed' : 'idle', task: '数据采集' },
    { id: '5', name: '刑部', avatar: '⚖️', status: status === 'analyzing' ? 'working' : status === 'completed' ? 'completed' : 'idle', task: '风险审核' },
    { id: '6', name: '工部', avatar: '📝', status: status === 'analyzing' ? 'working' : status === 'completed' ? 'completed' : 'idle', task: '报告生成' },
  ];

  const renderIdleState = () => (
    <div className="analysis-idle">
      <div className="idle-animation">
        <div className="empty-desks">
          {[1, 2, 3].map((i) => (
            <div key={i} className="empty-desk">
              <div className="desk-icon">🖥️</div>
              <div className="chair-icon">💺</div>
            </div>
          ))}
        </div>
      </div>
      <h3>AI智能体团队待命中</h3>
      <p>提交分析请求后，智能体团队将立即开始工作</p>
      <div className="waiting-dots">
        <span className="dot"></span>
        <span className="dot"></span>
        <span className="dot"></span>
      </div>
    </div>
  );

  const renderInitializingState = () => (
    <div className="analysis-initializing">
      <div className="loading-spinner"></div>
      <h3>正在初始化分析任务...</h3>
      <div className="init-steps">
        {defaultSteps.map((step, index) => (
          <div 
            key={step.id} 
            className={`init-step ${step.status}`}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <span className="step-icon">
              {step.status === 'completed' ? '✓' : step.status === 'active' ? '⟳' : '○'}
            </span>
            <span className="step-text">{step.name}</span>
          </div>
        ))}
      </div>
      <p className="init-tip">系统正在为您准备分析环境，请稍候...</p>
    </div>
  );

  const renderAnalyzingState = () => (
    <div className="analysis-working">
      <div className="progress-section">
        <div className="progress-header">
          <h3>分析进行中</h3>
          <span className="progress-percent">{animatedProgress}%</span>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${animatedProgress}%` }}
          ></div>
        </div>
        <div className="progress-steps">
          {defaultSteps.map((step) => (
            <div key={step.id} className={`progress-step ${step.status}`}>
              <span className="step-indicator"></span>
              <span className="step-name">{step.name}</span>
            </div>
          ))}
        </div>
      </div>

      {showAgents && (
        <div className="agents-section">
          <h4>智能体团队</h4>
          <div className="agents-grid">
            {defaultAgents.map((agent) => (
              <div key={agent.id} className={`agent-card ${agent.status}`}>
                <div className="agent-avatar">{agent.avatar}</div>
                <div className="agent-info">
                  <span className="agent-name">{agent.name}</span>
                  <span className="agent-task">{agent.task}</span>
                </div>
                <div className={`agent-status-indicator ${agent.status}`}></div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderCompletedState = () => (
    <div className="analysis-completed">
      <div className="success-icon">✅</div>
      <h3>分析完成！</h3>
      <p>智能体团队已完成所有分析任务</p>
      
      {result && (
        <div className="result-preview">
          <h4>分析结果预览</h4>
          <div className="result-summary">
            {result.summary || '分析已完成，点击下方按钮查看完整报告'}
          </div>
          {result.details && (
            <div className="result-details">
              {Object.entries(result.details).map(([key, value]) => (
                <div key={key} className="detail-item">
                  <span className="detail-label">{key}:</span>
                  <span className="detail-value">{String(value)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="completion-actions">
        {onViewReport && (
          <button className="view-report-btn" onClick={onViewReport}>
            查看完整报告
          </button>
        )}
      </div>

      {showAgents && (
        <div className="completed-agents">
          <h4>参与智能体</h4>
          <div className="agents-summary">
            {defaultAgents.map((agent) => (
              <div key={agent.id} className="agent-badge completed">
                <span>{agent.avatar}</span>
                <span>{agent.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderErrorState = () => (
    <div className="analysis-error">
      <div className="error-icon">❌</div>
      <h3>分析失败</h3>
      <p className="error-message">{error || '分析过程中出现错误'}</p>
      {onRetry && (
        <button className="retry-btn" onClick={onRetry}>
            重新分析
          </button>
      )}
    </div>
  );

  const renderContent = () => {
    switch (status) {
      case 'idle':
        return renderIdleState();
      case 'initializing':
        return renderInitializingState();
      case 'analyzing':
        return renderAnalyzingState();
      case 'completed':
        return renderCompletedState();
      case 'error':
        return renderErrorState();
      default:
        return renderIdleState();
    }
  };

  return (
    <div className={`analysis-progress-container ${status}`}>
      {renderContent()}
    </div>
  );
};

export default AnalysisProgress;
