import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  PlayIcon,
  ChartBarIcon,
  UserGroupIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import TaskStatusCard, { TaskStatusCardData, TaskStatus } from './TaskStatusCard';

interface ExecutionStep {
  id: string;
  agentName: string;
  stepName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  duration?: number;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: string;
}

interface IntermediateResult {
  id: string;
  title: string;
  content: string;
  type: 'data' | 'chart' | 'insight' | 'recommendation';
  timestamp: string;
  data?: Record<string, unknown>;
}

interface TaskLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  agentName: string;
  message: string;
}

interface TaskDetailPanelProps {
  task: TaskStatusCardData;
  isOpen: boolean;
  onClose: () => void;
  onViewReport?: (taskId: string) => void;
  onRetry?: (taskId: string) => void;
  onDelete?: (taskId: string) => void;
  onCancel?: (taskId: string) => void;
}

const statusConfig = {
  pending: {
    icon: ClockIcon,
    text: '等待中',
    color: 'text-gray-500',
    bgColor: 'bg-gray-100',
  },
  processing: {
    icon: ArrowPathIcon,
    text: '处理中',
    color: 'text-blue-500',
    bgColor: 'bg-blue-100',
  },
  completed: {
    icon: CheckCircleIcon,
    text: '已完成',
    color: 'text-green-500',
    bgColor: 'bg-green-100',
  },
  failed: {
    icon: ExclamationCircleIcon,
    text: '失败',
    color: 'text-red-500',
    bgColor: 'bg-red-100',
  },
};

const TaskDetailPanel: React.FC<TaskDetailPanelProps> = ({
  task,
  isOpen,
  onClose,
  onViewReport,
  onRetry,
  onDelete,
  onCancel,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'steps' | 'results' | 'logs'>('overview');
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  const config = statusConfig[task.status];
  const StatusIcon = config.icon;

  const executionSteps: ExecutionStep[] = useMemo(() => {
    return [
      {
        id: 'step-1',
        agentName: '中书省',
        stepName: '需求解析',
        status: 'completed',
        startTime: task.startTime,
        endTime: task.startTime,
        duration: 0.2,
      },
      {
        id: 'step-2',
        agentName: '户部',
        stepName: '数据采集',
        status: task.status === 'pending' ? 'pending' : 'completed',
        startTime: task.startTime,
        duration: 2.5,
      },
      {
        id: 'step-3',
        agentName: '工部',
        stepName: '数据分析',
        status: task.status === 'processing' ? 'running' : task.status === 'completed' ? 'completed' : 'pending',
        startTime: task.startTime,
        duration: 3.1,
      },
      {
        id: 'step-4',
        agentName: '刑部',
        stepName: '合规检查',
        status: task.status === 'completed' ? 'completed' : 'pending',
        duration: 0.5,
      },
      {
        id: 'step-5',
        agentName: '礼部',
        stepName: '报告生成',
        status: task.status === 'completed' ? 'completed' : 'pending',
        duration: 1.2,
      },
    ];
  }, [task.status, task.startTime]);

  const intermediateResults: IntermediateResult[] = useMemo(() => {
    if (task.status === 'completed' && task.result?.keyMetrics) {
      return Object.entries(task.result.keyMetrics).map(([key, value], index) => ({
        id: `result-${index}`,
        title: key,
        content: String(value),
        type: 'data' as const,
        timestamp: task.estimatedFinish || new Date().toISOString(),
      }));
    }
    return [];
  }, [task.status, task.result]);

  const logs: TaskLog[] = useMemo(() => {
    const baseLogs: TaskLog[] = [
      {
        id: 'log-1',
        timestamp: task.startTime || new Date().toISOString(),
        level: 'info' as const,
        agentName: '系统',
        message: `任务创建: ${task.name || task.query}`,
      },
    ];
    
    if (task.status === 'processing') {
      baseLogs.push(
        {
          id: 'log-2',
          timestamp: new Date().toISOString(),
          level: 'info' as const,
          agentName: '中书省',
          message: '正在解析用户需求...',
        },
        {
          id: 'log-3',
          timestamp: new Date().toISOString(),
          level: 'info' as const,
          agentName: '户部',
          message: '正在采集房产数据...',
        }
      );
    }
    
    if (task.status === 'failed') {
      baseLogs.push({
        id: 'log-error',
        timestamp: new Date().toISOString(),
        level: 'error' as const,
        agentName: '系统',
        message: task.error || '任务执行失败',
      });
    }
    
    if (task.status === 'completed') {
      baseLogs.push({
        id: 'log-complete',
        timestamp: task.estimatedFinish || new Date().toISOString(),
        level: 'info' as const,
        agentName: '礼部',
        message: '报告生成完成',
      });
    }
    
    return baseLogs;
  }, [task.status, task.name, task.query, task.error, task.startTime, task.estimatedFinish]);

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    return `${(seconds / 60).toFixed(1)}min`;
  };

  const formatTime = (dateStr?: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, x: '100%' }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-2xl bg-white dark:bg-gray-900 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${config.bgColor}`}>
                    <StatusIcon className={`w-5 h-5 ${config.color}`} />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                      任务详情
                    </h2>
                    <p className="text-sm text-gray-500">{task.taskId}</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <XMarkIcon className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-4 mb-4">
                    <h3 className="text-base font-medium text-gray-900 dark:text-white">
                      {task.name || task.query || '未命名任务'}
                    </h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.color}`}>
                      {config.text}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                      <CalendarIcon className="w-4 h-4" />
                      <span>创建: {formatTime(task.startTime || task.created_at)}</span>
                    </div>
                    {task.status === 'completed' && task.estimatedFinish && (
                      <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                        <CheckCircleIcon className="w-4 h-4" />
                        <span>完成: {formatTime(task.estimatedFinish)}</span>
                      </div>
                    )}
                    {task.cost !== undefined && (
                      <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                        <CurrencyDollarIcon className="w-4 h-4" />
                        <span>消耗: {task.cost} 积分</span>
                      </div>
                    )}
                    {task.agentsUsed && task.agentsUsed.length > 0 && (
                      <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                        <UserGroupIcon className="w-4 h-4" />
                        <span>智能体: {task.agentsUsed.length} 个</span>
                      </div>
                    )}
                  </div>

                  {task.status === 'processing' && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600 dark:text-gray-300">进度</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">{task.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${task.progress}%` }}
                          className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div className="border-b border-gray-200 dark:border-gray-700">
                  <div className="flex">
                    {(['overview', 'steps', 'results', 'logs'] as const).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab as typeof activeTab)}
                        className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                          activeTab === tab
                            ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                            : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
                        }`}
                      >
                        {tab === 'overview' && '概览'}
                        {tab === 'steps' && '执行步骤'}
                        {tab === 'results' && '中间结果'}
                        {tab === 'logs' && '实时日志'}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                  <AnimatePresence mode="wait">
                    {activeTab === 'overview' && (
                      <motion.div
                        key="overview"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="space-y-4"
                      >
                        {task.inputParams && Object.keys(task.inputParams).length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">输入参数</h4>
                            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2">
                              {Object.entries(task.inputParams).map(([key, value]) => (
                                <div key={key} className="flex justify-between text-sm">
                                  <span className="text-gray-500">{key}</span>
                                  <span className="text-gray-900 dark:text-white">{String(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {task.result?.summary && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">结果摘要</h4>
                            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                              <p className="text-sm text-gray-700 dark:text-gray-300">{task.result.summary}</p>
                            </div>
                          </div>
                        )}

                        {task.error && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">错误信息</h4>
                            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
                              <p className="text-sm text-red-600 dark:text-red-400">{task.error}</p>
                            </div>
                          </div>
                        )}
                      </motion.div>
                    )}

                    {activeTab === 'steps' && (
                      <motion.div
                        key="steps"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="space-y-3"
                      >
                        {executionSteps.map((step, index) => (
                          <motion.div
                            key={step.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden"
                          >
                            <button
                              onClick={() => setExpandedStep(expandedStep === step.id ? null : step.id)}
                              className="w-full p-3 flex items-center justify-between text-left"
                            >
                              <div className="flex items-center gap-3">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                  step.status === 'completed' ? 'bg-green-100 text-green-600' :
                                  step.status === 'running' ? 'bg-blue-100 text-blue-600' :
                                  step.status === 'failed' ? 'bg-red-100 text-red-600' :
                                  'bg-gray-100 text-gray-400'
                                }`}>
                                  {step.status === 'completed' && <CheckCircleIcon className="w-4 h-4" />}
                                  {step.status === 'running' && <PlayIcon className="w-4 h-4 animate-pulse" />}
                                  {step.status === 'failed' && <ExclamationCircleIcon className="w-4 h-4" />}
                                  {step.status === 'pending' && <ClockIcon className="w-4 h-4" />}
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                                    {step.stepName}
                                  </p>
                                  <p className="text-xs text-gray-500">{step.agentName}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className={`text-xs font-medium ${
                                  step.status === 'completed' ? 'text-green-600' :
                                  step.status === 'running' ? 'text-blue-600' :
                                  step.status === 'failed' ? 'text-red-600' :
                                  'text-gray-400'
                                }`}>
                                  {step.status === 'completed' ? '已完成' :
                                   step.status === 'running' ? '进行中' :
                                   step.status === 'failed' ? '失败' :
                                   '等待中'}
                                </span>
                                <span className="text-xs text-gray-400">
                                  {formatDuration(step.duration)}
                                </span>
                                {expandedStep === step.id ? (
                                  <ChevronUpIcon className="w-4 h-4 text-gray-400" />
                                ) : (
                                  <ChevronDownIcon className="w-4 h-4 text-gray-400" />
                                )}
                              </div>
                            </button>

                            <AnimatePresence>
                              {expandedStep === step.id && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: 'auto', opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  className="border-t border-gray-200 dark:border-gray-700 p-3 space-y-2"
                                >
                                  {step.input && (
                                    <div>
                                      <span className="text-xs text-gray-500">输入:</span>
                                      <pre className="mt-1 text-xs bg-gray-100 dark:bg-gray-700 p-2 rounded overflow-x-auto">
                                        {JSON.stringify(step.input, null, 2)}
                                      </pre>
                                    </div>
                                  )}
                                  {step.output && (
                                    <div>
                                      <span className="text-xs text-gray-500">输出:</span>
                                      <pre className="mt-1 text-xs bg-gray-100 dark:bg-gray-700 p-2 rounded overflow-x-auto">
                                        {JSON.stringify(step.output, null, 2)}
                                      </pre>
                                    </div>
                                  )}
                                  {step.error && (
                                    <div>
                                      <span className="text-xs text-red-500">错误:</span>
                                      <p className="mt-1 text-xs text-red-600">{step.error}</p>
                                    </div>
                                  )}
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </motion.div>
                        ))}
                      </motion.div>
                    )}

                    {activeTab === 'results' && (
                      <motion.div
                        key="results"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="space-y-3"
                      >
                        {intermediateResults.length === 0 ? (
                          <div className="text-center py-8 text-gray-500">
                            {task.status === 'completed' ? '暂无中间结果' : '任务完成后将显示中间结果'}
                          </div>
                        ) : (
                          intermediateResults.map((result, index) => (
                            <motion.div
                              key={result.id}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: index * 0.05 }}
                              className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3"
                            >
                              <div className="flex items-start gap-3">
                                <div className={`p-2 rounded-lg ${
                                  result.type === 'data' ? 'bg-blue-100 text-blue-600' :
                                  result.type === 'chart' ? 'bg-purple-100 text-purple-600' :
                                  result.type === 'insight' ? 'bg-yellow-100 text-yellow-600' :
                                  'bg-green-100 text-green-600'
                                }`}>
                                  {result.type === 'chart' ? (
                                    <ChartBarIcon className="w-4 h-4" />
                                  ) : (
                                    <DocumentTextIcon className="w-4 h-4" />
                                  )}
                                </div>
                                <div className="flex-1">
                                  <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                                    {result.title}
                                  </h4>
                                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                                    {result.content}
                                  </p>
                                </div>
                              </div>
                            </motion.div>
                          ))
                        )}
                      </motion.div>
                    )}

                    {activeTab === 'logs' && (
                      <motion.div
                        key="logs"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="space-y-2"
                      >
                        {logs.map((log, index) => (
                          <motion.div
                            key={log.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.02 }}
                            className={`flex items-start gap-3 p-2 rounded-lg ${
                              log.level === 'error' ? 'bg-red-50 dark:bg-red-900/20' :
                              log.level === 'warning' ? 'bg-yellow-50 dark:bg-yellow-900/20' :
                              'bg-gray-50 dark:bg-gray-800/50'
                            }`}
                          >
                            <span className="text-xs text-gray-400 font-mono">
                              {formatTime(log.timestamp)}
            </span>
                            <span className={`text-xs font-medium ${
                              log.level === 'error' ? 'text-red-600' :
                              log.level === 'warning' ? 'text-yellow-600' :
                              'text-blue-600'
                            }`}>
                              [{log.agentName}]
                            </span>
                            <span className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                              {log.message}
                            </span>
                          </motion.div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              <div className="border-t border-gray-200 dark:border-gray-700 p-4">
                <div className="flex items-center justify-end gap-2">
                  {task.status === 'processing' && onCancel && (
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => onCancel(task.taskId)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                    >
                      <XMarkIcon className="w-4 h-4" />
                      取消任务
                    </motion.button>
                  )}
                  {task.status === 'completed' && onViewReport && (
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => onViewReport(task.taskId)}
                      className="flex items-center gap-1.5 px-4 py-1.5 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-sm font-medium rounded-lg hover:shadow-lg transition-shadow"
                    >
                      <DocumentTextIcon className="w-4 h-4" />
                      查看完整报告
                    </motion.button>
                  )}
                  {task.status === 'failed' && onRetry && (
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => onRetry(task.taskId)}
                      className="flex items-center gap-1.5 px-4 py-1.5 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-sm font-medium rounded-lg hover:shadow-lg transition-shadow"
                    >
                      <ArrowPathIcon className="w-4 h-4" />
                      重试任务
                    </motion.button>
                  )}
                  {onDelete && (
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => onDelete(task.taskId)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                    >
                      <ExclamationCircleIcon className="w-4 h-4" />
                      删除任务
                    </motion.button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default TaskDetailPanel;
