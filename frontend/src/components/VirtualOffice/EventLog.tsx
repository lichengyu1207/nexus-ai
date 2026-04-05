import React from 'react';
import './EventLog.css';

interface Event {
  type: string;
  data: any;
  timestamp: number;
}

interface EventLogProps {
  events: Event[];
}

const EventLog: React.FC<EventLogProps> = ({ events }) => {
  // 事件类型的显示名称
  const eventTypeNames: Record<string, string> = {
    'WORKFLOW_START': '工作流开始',
    'WORKFLOW_COMPLETE': '工作流完成',
    'WORKFLOW_ERROR': '工作流错误',
    'AGENT_START': '智能体开始',
    'AGENT_COMPLETE': '智能体完成',
    'AGENT_ERROR': '智能体错误',
    'STEP_START': '步骤开始',
    'STEP_COMPLETE': '步骤完成',
    'STEP_ERROR': '步骤错误'
  };

  // 获取事件的显示名称
  const getEventTypeName = (type: string): string => {
    return eventTypeNames[type] || type;
  };

  // 获取事件的样式类
  const getEventStyle = (type: string): string => {
    if (type.includes('ERROR')) {
      return 'event-error';
    } else if (type.includes('COMPLETE')) {
      return 'event-success';
    } else if (type.includes('START')) {
      return 'event-info';
    }
    return 'event-default';
  };

  // 格式化时间戳
  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // 限制显示的事件数量
  const recentEvents = events.slice(-20);

  return (
    <div className="event-log-container">
      <div className="event-log-header">
        <h3>事件日志</h3>
        <div className="event-count">
          共 {events.length} 条事件
        </div>
      </div>
      
      <div className="event-log-body">
        {recentEvents.length === 0 ? (
          <div className="no-events">
            暂无事件日志
          </div>
        ) : (
          <div className="events-list">
            {recentEvents.map((event, index) => (
              <div 
                key={index} 
                className={`event-item ${getEventStyle(event.type)}`}
              >
                <div className="event-time">
                  {formatTimestamp(event.timestamp)}
                </div>
                <div className="event-content">
                  <div className="event-type">
                    {getEventTypeName(event.type)}
                  </div>
                  <div className="event-data">
                    {renderEventData(event.data)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// 渲染事件数据
const renderEventData = (data: any): React.ReactNode => {
  if (!data) return null;

  // 处理常见的事件数据格式
  if (data.error) {
    return <span className="error-message">{data.error}</span>;
  }

  if (data.query) {
    return <span>查询: {data.query}</span>;
  }

  if (data.agent_type) {
    return <span>智能体: {data.agent_type}</span>;
  }

  if (data.workflow_name) {
    return <span>工作流: {data.workflow_name}</span>;
  }

  // 尝试显示其他数据
  try {
    const dataStr = JSON.stringify(data);
    if (dataStr.length > 100) {
      return <span>{dataStr.substring(0, 100)}...</span>;
    }
    return <span>{dataStr}</span>;
  } catch {
    return <span>无法显示事件数据</span>;
  }
};

export default EventLog;