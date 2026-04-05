import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircleIcon, 
  ClockIcon, 
  ExclamationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface RealtimeStatusProps {
  taskId: string;
  onStatusChange?: (status: TaskStatus) => void;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

interface TaskStatus {
  task_id: string;
  status: 'queued' | 'planning' | 'reviewing' | 'executing' | 'completed' | 'failed';
  progress: number;
  current_province?: 'zhongshu' | 'menxia' | 'shangshu';
  current_department?: string;
  current_step?: string;
  result?: any;
  error?: string;
  workflow_steps?: WorkflowStep[];
}

interface WorkflowStep {
  id: string;
  province: string;
  department?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  started_at?: string;
  completed_at?: string;
}

interface SSEEvent {
  type: 'status_update' | 'step_start' | 'step_complete' | 'progress' | 'error' | 'completed';
  task_id: string;
  data: {
    status?: string;
    progress?: number;
    current_province?: string;
    current_department?: string;
    current_step?: string;
    step?: WorkflowStep;
    result?: any;
    error?: string;
  };
  timestamp: string;
}

const statusConfig = {
  queued: { icon: ClockIcon, color: 'text-yellow-500', bgColor: 'bg-yellow-100', label: '排队中' },
  planning: { icon: ClockIcon, color: 'text-purple-500', bgColor: 'bg-purple-100', label: '中书省规划中' },
  reviewing: { icon: ClockIcon, color: 'text-blue-500', bgColor: 'bg-blue-100', label: '门下省审核中' },
  executing: { icon: ArrowPathIcon, color: 'text-green-500', bgColor: 'bg-green-100', label: '尚书省执行中' },
  completed: { icon: CheckCircleIcon, color: 'text-green-500', bgColor: 'bg-green-100', label: '已完成' },
  failed: { icon: ExclamationCircleIcon, color: 'text-red-500', bgColor: 'bg-red-100', label: '失败' },
};

const RealtimeStatus: React.FC<RealtimeStatusProps> = ({
  taskId,
  onStatusChange,
  onComplete,
  onError,
}) => {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const handleEvent = useCallback((event: SSEEvent) => {
    if (event.task_id !== taskId) return;

    setStatus((prev) => {
      const newStatus: TaskStatus = {
        task_id: taskId,
        status: (event.data.status as TaskStatus['status']) || prev?.status || 'queued',
        progress: event.data.progress ?? prev?.progress ?? 0,
        current_province: event.data.current_province as TaskStatus['current_province'] || prev?.current_province,
        current_department: event.data.current_department || prev?.current_department,
        current_step: event.data.current_step || prev?.current_step,
        result: event.data.result || prev?.result,
        error: event.data.error || prev?.error,
        workflow_steps: event.data.step
          ? [...(prev?.workflow_steps || []).filter(s => s.id !== event.data.step!.id), event.data.step!]
          : prev?.workflow_steps,
      };

      onStatusChange?.(newStatus);

      if (event.type === 'completed' && event.data.result) {
        onComplete?.(event.data.result);
      }

      if (event.type === 'error' && event.data.error) {
        onError?.(event.data.error);
      }

      return newStatus;
    });
  }, [taskId, onStatusChange, onComplete, onError]);

  useEffect(() => {
    if (!taskId) return;

    const eventSource = new EventSource(`/api/sse/tasks/${taskId}/stream`);

    eventSource.onopen = () => {
      setIsConnected(true);
      setConnectionError(null);
    };

    eventSource.onmessage = (event) => {
      try {
        const data: SSEEvent = JSON.parse(event.data);
        handleEvent(data);
      } catch (e) {
        console.error('Failed to parse SSE event:', e);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      setIsConnected(false);
      setConnectionError('连接中断，正在重连...');
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [taskId, handleEvent]);

  if (!status) {
    return (
      <div className="flex items-center justify-center p-4">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full"
        />
        <span className="ml-2 text-gray-500">正在获取任务状态...</span>
      </div>
    );
  }

  const currentConfig = statusConfig[status.status] || statusConfig.queued;
  const StatusIcon = currentConfig.icon;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
      {/* 连接状态 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-500">
            {isConnected ? '实时连接' : connectionError || '已断开'}
          </span>
        </div>
        <span className="text-xs text-gray-400">
          更新于 {new Date().toLocaleTimeString()}
        </span>
      </div>

      {/* 状态显示 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${currentConfig.bgColor}`}>
            {status.status === 'executing' ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <StatusIcon className={`w-5 h-5 ${currentConfig.color}`} />
              </motion.div>
            ) : (
              <StatusIcon className={`w-5 h-5 ${currentConfig.color}`} />
            )}
          </div>
          <div>
            <span className="font-medium text-gray-900 dark:text-white">
              {currentConfig.label}
            </span>
            {status.current_step && (
              <p className="text-sm text-gray-500">{status.current_step}</p>
            )}
          </div>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-primary-600">{status.progress}%</span>
        </div>
      </div>

      {/* 进度条 */}
      <div className="mt-4">
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${status.progress}%` }}
            transition={{ duration: 0.5 }}
            className="bg-primary-500 h-2 rounded-full"
          />
        </div>
      </div>

      {/* 错误信息 */}
      {status.error && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-600 dark:text-red-400">{status.error}</p>
        </div>
      )}
    </div>
  );
};

export default RealtimeStatus;
