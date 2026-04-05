import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import AgentCard from './AgentCard';
import DataFlow from './DataFlow';
import EventLog from './EventLog';
import WorkflowProgress from './WorkflowProgress';
import './VirtualOffice.css';

interface ReportData {
  summary_report?: {
    summary?: string;
    [key: string]: unknown;
  };
  report_stats?: {
    generated_reports?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

interface TaskResult {
  report?: ReportData;
  [key: string]: unknown;
}

interface TaskStatus {
  task_id: string;
  status: 'IDLE' | 'INITIALIZING' | 'RUNNING' | 'SUCCESS' | 'FAILED';
  progress: number;
  agents: AgentSummary[];
  result?: TaskResult;
  error?: string;
}

interface AgentSummary {
  id: string;
  name: string;
  avatar: string;
  status: 'idle' | 'working' | 'completed' | 'error';
  started_at?: number;
  completed_at?: number;
}

interface Event {
  type: string;
  data: { message?: string; [key: string]: unknown };
  timestamp: number;
}

const VirtualOffice: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [isReplayMode, setIsReplayMode] = useState(false);
  const [replayProgress, setReplayProgress] = useState(0);

  // 初始化WebSocket连接
  useEffect(() => {
    if (!taskId) return;

    // 连接到WebSocket端点，传递taskId作为查询参数
    const ws = new WebSocket(`ws://localhost:8001/api/v1/ws/events?client_id=${taskId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      // 连接成功后，添加一个系统事件
      setEvents(prev => [...prev, {
        type: 'system',
        data: { message: '已连接到AI智能体团队' },
        timestamp: Date.now()
      }]);
      
      // 订阅任务相关事件
      ws.send(JSON.stringify({
        action: 'subscribe',
        event_type: '*'
      }));
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setEvents(prev => [...prev, {
          type: data.type || data.event_type || 'unknown',
          data: data.payload || data.data || {},
          timestamp: Date.now()
        }]);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }, [taskId]);

  // 轮询获取任务状态
  const fetchTaskStatus = useCallback(async () => {
    if (!taskId) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}`);
      if (response.ok) {
        const data = await response.json();
        setTaskStatus(data);
      } else {
        console.error('Failed to fetch task status:', response.status);
      }
    } catch (error) {
      console.error('Error fetching task status:', error);
    }
  }, [taskId]);

  useEffect(() => {
    fetchTaskStatus();
    const interval = setInterval(fetchTaskStatus, 2000);
    return () => clearInterval(interval);
  }, [fetchTaskStatus]);

  // 处理回放控制
  const handleReplay = () => {
    setIsReplayMode(true);
    setReplayProgress(0);
  };

  const handlePauseReplay = () => {
    setIsReplayMode(false);
  };

  const handleReplayProgress = (progress: number) => {
    setReplayProgress(progress);
  };

  // 获取代理列表
  const agents = taskStatus?.agents || [];

  // 渲染初始等待状态
  const renderIdleState = () => (
    <div className="idle-state">
      <div className="idle-office">
        <div className="office-empty">
          <div className="empty-desk">
            <div className="desk-icon">🖥️</div>
            <div className="chair-icon">💺</div>
          </div>
          <div className="empty-desk">
            <div className="desk-icon">🖥️</div>
            <div className="chair-icon">💺</div>
          </div>
          <div className="empty-desk">
            <div className="desk-icon">🖥️</div>
            <div className="chair-icon">💺</div>
          </div>
        </div>
        <div className="idle-message">
          <h3>🤖 AI智能体团队待命中</h3>
          <p>提交分析请求后，智能体团队将立即开始工作</p>
          <div className="waiting-animation">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        </div>
      </div>
    </div>
  );

  // 渲染初始化状态
  const renderInitializingState = () => (
    <div className="initialization-status">
      <div className="loading-animation">
        <div className="spinner"></div>
      </div>
      <h3>正在初始化分析任务...</h3>
      <div className="initialization-steps">
        <div className="step completed">
          <span className="step-icon">✓</span>
          <span className="step-text">接收分析请求</span>
        </div>
        <div className="step active">
          <span className="step-icon">⟳</span>
          <span className="step-text">唤醒AI智能体团队</span>
        </div>
        <div className="step">
          <span className="step-icon">○</span>
          <span className="step-text">启动数据采集引擎</span>
        </div>
        <div className="step">
          <span className="step-icon">○</span>
          <span className="step-text">准备分析环境</span>
        </div>
      </div>
      <p className="initialization-tip">
        💡 系统正在为您准备分析环境，请稍候...
      </p>
    </div>
  );

  // 渲染工作状态
  const renderWorkingState = () => (
    <>
      <WorkflowProgress 
        progress={taskStatus?.progress || 0}
        status={taskStatus?.status || 'RUNNING'}
      />

      <div className="office-main">
        <div className="agents-section">
          <h3>智能体团队</h3>
          <div className="agents-grid">
            {agents.map((agent) => (
              <AgentCard 
                key={agent.id}
                agent={agent}
                isReplayMode={isReplayMode}
                replayProgress={replayProgress}
              />
            ))}
          </div>
        </div>

        <div className="visualization-section">
          <DataFlow agents={agents} />
        </div>
      </div>

      <div className="office-footer">
        <EventLog events={events} />
      </div>
    </>
  );

  // 根据状态渲染不同内容
  const renderContent = () => {
    // 如果没有任务状态，显示等待状态
    if (!taskStatus) {
      return renderIdleState();
    }

    // 根据任务状态显示不同内容
    switch (taskStatus.status) {
      case 'IDLE':
        return renderIdleState();
      case 'INITIALIZING':
        return renderInitializingState();
      case 'RUNNING':
        return renderWorkingState();
      case 'SUCCESS':
        return (
          <>
            {renderWorkingState()}
            <div className="success-message">
              <h3>✅ 分析完成！</h3>
              <p>智能体团队已完成所有分析任务</p>
              {taskStatus.result && (
                <div className="report-actions">
                  <button 
                    className="view-report-button"
                    onClick={() => {
                      // 在新窗口中打开报告页面
                      window.open(`/report-page/${taskId}`, '_blank');
                    }}
                  >
                    📄 查看完整报告
                  </button>
                  {taskStatus.result.report && (
                    <div className="report-preview">
                      <h4>报告预览</h4>
                      <div className="report-summary">
                        {taskStatus.result.report.summary_report ? (
                          <div>
                            <p><strong>分析结果：</strong></p>
                            <p>{taskStatus.result.report.summary_report.summary || '分析已完成'}</p>
                            {taskStatus.result.report.report_stats && (
                              <div className="report-stats">
                                <p>生成报告数：{taskStatus.result.report.report_stats.generated_reports || 0}</p>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p>报告已生成，点击上方按钮查看完整报告</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        );
      case 'FAILED':
        return (
          <div className="error-state">
            <h3>❌ 分析失败</h3>
            <p>{taskStatus.error || '分析过程中出现错误'}</p>
          </div>
        );
      default:
        return renderIdleState();
    }
  };

  return (
    <div className="virtual-office">
      <div className="office-header">
        <h2>AI虚拟办公室</h2>
        <div className="office-controls">
          {taskStatus?.status === 'SUCCESS' && (
            <button 
              className="replay-button"
              onClick={handleReplay}
            >
              ▶ 回放分析过程
            </button>
          )}
          {isReplayMode && (
            <button 
              className="pause-button"
              onClick={handlePauseReplay}
            >
              ⏸ 暂停回放
            </button>
          )}
        </div>
      </div>

      {renderContent()}

      {isReplayMode && (
        <div className="replay-controls">
          <div className="replay-progress-bar">
            <div 
              className="replay-progress-fill"
              style={{ width: `${replayProgress}%` }}
            ></div>
          </div>
          <div className="replay-controls-buttons">
            <button onClick={() => handleReplayProgress(0)}>⏪ 重置</button>
            <button onClick={handlePauseReplay}>⏸ 暂停</button>
            <button onClick={() => handleReplayProgress(Math.min(replayProgress + 10, 100))}>▶️ 快进</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VirtualOffice;
