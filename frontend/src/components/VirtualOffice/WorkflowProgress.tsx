import React from 'react';
import './WorkflowProgress.css';

interface WorkflowProgressProps {
  progress: number;
  status: string;
}

const WorkflowProgress: React.FC<WorkflowProgressProps> = ({ progress, status }) => {
  // 获取状态的显示文本
  const getStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
      PENDING: '等待中',
      RUNNING: '运行中',
      SUCCESS: '已完成',
      FAILED: '失败',
      CANCELLED: '已取消'
    };
    return statusMap[status] || status;
  };

  // 获取状态样式
  const getStatusStyle = (status: string): string => {
    switch (status) {
      case 'RUNNING':
        return 'status-running';
      case 'SUCCESS':
        return 'status-success';
      case 'FAILED':
        return 'status-failed';
      case 'CANCELLED':
        return 'status-cancelled';
      default:
        return 'status-pending';
    }
  };

  // 获取进度百分比文本
  const getProgressText = (progress: number): string => {
    return `${Math.round(progress * 100)}%`;
  };

  return (
    <div className="workflow-progress">
      <div className="progress-header">
        <h3>工作流进度</h3>
        <div className={`progress-status ${getStatusStyle(status)}`}>
          {getStatusText(status)}
        </div>
      </div>
      
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${progress * 100}%` }}
          ></div>
        </div>
        <div className="progress-text">
          {getProgressText(progress)}
        </div>
      </div>

      {status === 'FAILED' && (
        <div className="error-message">
          工作流执行失败，请查看事件日志了解详情
        </div>
      )}

      {status === 'SUCCESS' && (
        <div className="success-message">
          工作流执行完成！
        </div>
      )}
    </div>
  );
};

export default WorkflowProgress;