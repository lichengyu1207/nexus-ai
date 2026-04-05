import React, { useState, useEffect, useRef } from 'react';

interface LogEntry {
  id: string;
  timestamp: string;
  agentName: string;
  agentAvatar: string;
  action: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

interface LiveLogProps {
  maxEntries?: number;
}

const LiveLog: React.FC<LiveLogProps> = ({ maxEntries = 50 }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (!isPaused && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, isPaused]);

  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8000/api/dashboard/ws`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'log') {
            addLog(data.payload);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        setTimeout(connectWebSocket, 3000);
      };

      wsRef.current.onerror = () => {
        console.log('WebSocket connection failed, using mock data');
        startMockLogs();
      };
    } catch (error) {
      console.log('WebSocket not available, using mock data');
      startMockLogs();
    }
  };

  const startMockLogs = () => {
    const mockLogs: Omit<LogEntry, 'id' | 'timestamp'>[] = [
      { agentName: '需求分析师', agentAvatar: '📊', action: '开始分析用户需求...', type: 'info' },
      { agentName: '数据采集师', agentAvatar: '🔍', action: '正在查询区域均价数据...', type: 'info' },
      { agentName: '数据采集师', agentAvatar: '🔍', action: '成功获取深圳南山区房价数据', type: 'success' },
      { agentName: '市场分析师', agentAvatar: '📈', action: '开始分析市场趋势...', type: 'info' },
      { agentName: '风险评估师', agentAvatar: '⚖️', action: '检查房产合规性...', type: 'warning' },
      { agentName: '报告撰写师', agentAvatar: '📝', action: '生成分析报告...', type: 'info' },
      { agentName: '数据采集师', agentAvatar: '🔍', action: '采集周边配套设施数据...', type: 'info' },
      { agentName: '市场分析师', agentAvatar: '📈', action: '完成市场趋势分析', type: 'success' },
    ];

    let index = 0;
    const interval = setInterval(() => {
      if (isPaused) return;
      if (index < mockLogs.length) {
        addLog(mockLogs[index]);
        index++;
      } else {
        index = 0;
      }
    }, 2000);

    return () => clearInterval(interval);
  };

  const addLog = (log: Omit<LogEntry, 'id' | 'timestamp'>) => {
    const newLog: LogEntry = {
      ...log,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
    };

    setLogs(prev => {
      const updated = [...prev, newLog];
      return updated.slice(-maxEntries);
    });
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getTypeStyles = (type: LogEntry['type']) => {
    switch (type) {
      case 'success':
        return 'text-fluent-jade-600 bg-fluent-jade-50';
      case 'warning':
        return 'text-fluent-gold-600 bg-fluent-gold-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-fluent-deepOcean-500 bg-fluent-deepOcean-50';
    }
  };

  const getTypeIcon = (type: LogEntry['type']) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'warning':
        return '⚠';
      case 'error':
        return '✕';
      default:
        return '●';
    }
  };

  return (
    <div className="acrylic rounded-xl shadow-fluent-md border border-white/30 overflow-hidden">
      <div className="flex items-center justify-between p-3 border-b border-fluent-deepOcean-100 bg-fluent-deepOcean-50/50">
        <div className="flex items-center gap-2">
          <span className="text-lg">📡</span>
          <h3 className="font-semibold text-fluent-deepOcean-500">实时日志</h3>
          <span className="flex items-center gap-1 text-xs text-fluent-jade-600">
            <span className="w-2 h-2 rounded-full bg-fluent-jade-500 animate-pulse"></span>
            实时更新中
          </span>
        </div>
        <button
          onClick={() => setIsPaused(!isPaused)}
          className={`text-xs px-3 py-1 rounded-lg transition-colors ${
            isPaused
              ? 'bg-fluent-jade-100 text-fluent-jade-700'
              : 'bg-fluent-deepOcean-100 text-fluent-deepOcean-500 hover:bg-fluent-deepOcean-200'
          }`}
        >
          {isPaused ? '▶ 继续' : '⏸ 暂停'}
        </button>
      </div>

      <div
        ref={logContainerRef}
        className="h-48 overflow-y-auto p-3 space-y-2 scrollbar-thin"
        style={{ scrollbarWidth: 'thin' }}
      >
        {logs.length === 0 ? (
          <div className="text-center py-8 text-fluent-deepOcean-300">
            <p>等待日志...</p>
          </div>
        ) : (
          logs.map(log => (
            <div
              key={log.id}
              className={`flex items-start gap-2 p-2 rounded-lg ${getTypeStyles(log.type)} text-sm animate-fade-in`}
            >
              <span className="text-xs text-fluent-deepOcean-300 font-mono whitespace-nowrap">
                {formatTime(log.timestamp)}
              </span>
              <span className="text-lg">{log.agentAvatar}</span>
              <div className="flex-1 min-w-0">
                <span className="font-medium">{log.agentName}</span>
                <span className="text-fluent-deepOcean-300 mx-1">:</span>
                <span className="break-words">{log.action}</span>
              </div>
              <span className={`text-xs ${
                log.type === 'success' ? 'text-fluent-jade-500' :
                log.type === 'warning' ? 'text-fluent-gold-500' :
                log.type === 'error' ? 'text-red-500' :
                'text-fluent-deepOcean-300'
              }`}>
                {getTypeIcon(log.type)}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LiveLog;
