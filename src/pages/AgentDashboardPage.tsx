import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  UserGroupIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  PlayIcon,
  CogIcon,
  ChartBarIcon,
  BoltIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';
import toast from '@/utils/toast';

interface AgentStatus {
  id: string;
  name: string;
  department: string;
  status: 'idle' | 'busy' | 'auto' | 'offline';
  current_task?: string;
  current_task_id?: string;
  efficiency: number;
  level: number;
  work_time_seconds: number;
  performance_today: number;
  avatar?: string;
}

interface TaskInfo {
  id: string;
  type: string;
  description: string;
  status: string;
  progress: number;
  assigned_agents: Array<{ id: string; name: string; avatar?: string }>;
  start_time: string;
  estimated_end_time?: string;
}

interface AgentLog {
  id: string;
  agent_name: string;
  action: string;
  timestamp: string;
}

interface DashboardStats {
  total_agents: number;
  online_agents: number;
  busy_agents: number;
  idle_agents: number;
  today_tasks: number;
  completed_tasks: number;
  today_points: number;
  total_points: number;
}

const departmentConfig: Record<string, { color: string; icon: string; label: string }> = {
  li: { color: 'bg-purple-500', icon: '👤', label: '吏部' },
  hu: { color: 'bg-green-500', icon: '💰', label: '户部' },
  li_guan: { color: 'bg-blue-500', icon: '📝', label: '礼部' },
  bing: { color: 'bg-red-500', icon: '⚔️', label: '兵部' },
  xing: { color: 'bg-orange-500', icon: '⚖️', label: '刑部' },
  gong: { color: 'bg-yellow-500', icon: '🔧', label: '工部' },
  attack: { color: 'bg-red-600', icon: '🎯', label: '攻击' },
  defense: { color: 'bg-blue-600', icon: '🛡️', label: '防御' },
  memory: { color: 'bg-indigo-500', icon: '🧠', label: '记忆' },
};

const AgentDashboardPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [showTaskPanel, setShowTaskPanel] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentStatus | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  const loadDashboard = useCallback(async () => {
    try {
      const [agentsRes, tasksRes, statsRes, logsRes] = await Promise.all([
        api.get('/dashboard/agents-status'),
        api.get('/dashboard/current-tasks'),
        api.get('/dashboard/stats'),
        api.get('/dashboard/logs?limit=50'),
      ]);

      setAgents(agentsRes.data.agents || []);
      setTasks(tasksRes.data.tasks || []);
      setStats(statsRes.data);
      setLogs(logsRes.data.logs || []);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      toast.error('加载仪表盘失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 30000);
    return () => clearInterval(interval);
  }, [loadDashboard]);

  useEffect(() => {
    const userId = localStorage.getItem('userId');
    if (!userId) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/dashboard/ws/${userId}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      wsRef.current.onerror = () => {
        console.log('WebSocket connection error');
      };
    } catch {
      console.log('WebSocket not available');
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'agent_status_update':
        setAgents(prev => prev.map(agent => 
          agent.id === data.agent_id 
            ? { ...agent, status: data.status, current_task: data.task_id ? '执行任务中' : undefined }
            : agent
        ));
        break;
      case 'task_started':
        loadDashboard();
        break;
      case 'task_progress':
        setTasks(prev => prev.map(task =>
          task.id === data.task_id
            ? { ...task, progress: data.progress }
            : task
        ));
        break;
      case 'log':
        setLogs(prev => [data, ...prev.slice(0, 49)]);
        break;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'bg-green-500';
      case 'busy': return 'bg-yellow-500';
      case 'auto': return 'bg-blue-500';
      case 'offline': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'idle': return '空闲';
      case 'busy': return '忙碌';
      case 'auto': return '自主工作';
      case 'offline': return '离线';
      default: return '未知';
    }
  };

  const formatWorkTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`;
    return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`;
  };

  const renderAgentCard = (agent: AgentStatus) => {
    const config = departmentConfig[agent.department] || { color: 'bg-gray-500', icon: '🤖', label: agent.department };
    
    return (
      <motion.div
        key={agent.id}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={{ scale: 1.02 }}
        onClick={() => setSelectedAgent(agent)}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 cursor-pointer hover:shadow-md transition-shadow"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-lg ${config.color} flex items-center justify-center text-2xl`}>
              {config.icon}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{agent.name}</h3>
              <p className="text-sm text-gray-500">{config.label}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)} animate-pulse`} />
            <span className="text-xs text-gray-500">{getStatusLabel(agent.status)}</span>
          </div>
        </div>

        {agent.status !== 'idle' && agent.current_task && (
          <div className="bg-gray-50 rounded-lg p-2 mb-3">
            <p className="text-sm text-gray-600 truncate">{agent.current_task}</p>
            {agent.work_time_seconds > 0 && (
              <p className="text-xs text-gray-400 mt-1">
                已工作: {formatWorkTime(agent.work_time_seconds)}
              </p>
            )}
          </div>
        )}

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-1">
            <BoltIcon className="w-4 h-4 text-yellow-500" />
            <span className="text-gray-600">Lv.{agent.level}</span>
          </div>
          <div className="flex items-center gap-1">
            <ChartBarIcon className="w-4 h-4 text-blue-500" />
            <span className="text-gray-600">效率 {Math.round(agent.efficiency * 100)}%</span>
          </div>
          <div className="flex items-center gap-1">
            <CheckCircleIcon className="w-4 h-4 text-green-500" />
            <span className="text-gray-600">{agent.performance_today}</span>
          </div>
        </div>
      </motion.div>
    );
  };

  const renderTaskCard = (task: TaskInfo) => (
    <motion.div
      key={task.id}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <CogIcon className="w-5 h-5 text-blue-500" />
          <span className="font-medium text-gray-900">{task.type}</span>
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${
          task.status === 'processing' ? 'bg-blue-100 text-blue-700' :
          task.status === 'completed' ? 'bg-green-100 text-green-700' :
          'bg-gray-100 text-gray-700'
        }`}>
          {task.status}
        </span>
      </div>

      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{task.description}</p>

      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
          <span>进度</span>
          <span>{Math.round(task.progress * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${task.progress * 100}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex -space-x-2">
          {task.assigned_agents.slice(0, 3).map((agent, idx) => (
            <div
              key={idx}
              className="w-8 h-8 rounded-full bg-blue-500 border-2 border-white flex items-center justify-center text-white text-xs"
            >
              {agent.name?.[0] || 'A'}
            </div>
          ))}
          {task.assigned_agents.length > 3 && (
            <div className="w-8 h-8 rounded-full bg-gray-300 border-2 border-white flex items-center justify-center text-gray-600 text-xs">
              +{task.assigned_agents.length - 3}
            </div>
          )}
        </div>
        <span className="text-xs text-gray-400">
          {new Date(task.start_time).toLocaleString('zh-CN')}
        </span>
      </div>
    </motion.div>
  );

  const renderStatsCards = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <UserGroupIcon className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{stats?.total_agents || 0}</p>
            <p className="text-sm text-gray-500">智能体总数</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <BoltIcon className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{stats?.idle_agents || 0}</p>
            <p className="text-sm text-gray-500">空闲智能体</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-yellow-100 rounded-lg">
            <ClockIcon className="w-6 h-6 text-yellow-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{stats?.today_tasks || 0}</p>
            <p className="text-sm text-gray-500">今日任务</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <CheckCircleIcon className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{stats?.completed_tasks || 0}</p>
            <p className="text-sm text-gray-500">已完成任务</p>
          </div>
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <ArrowPathIcon className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <UserGroupIcon className="w-8 h-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">智能体监控中心</h1>
          </div>
          <button
            onClick={() => setShowTaskPanel(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            新建任务
          </button>
        </div>

        {renderStatsCards()}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">智能体状态</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                <AnimatePresence>
                  {agents.map(renderAgentCard)}
                </AnimatePresence>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">进行中的任务</h2>
              {tasks.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CogIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>暂无进行中的任务</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <AnimatePresence>
                    {tasks.map(renderTaskCard)}
                  </AnimatePresence>
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">实时日志</h2>
              <div
                ref={logsContainerRef}
                className="h-96 overflow-y-auto space-y-2 font-mono text-sm"
              >
                {logs.map((log, idx) => (
                  <div
                    key={log.id || idx}
                    className="flex items-start gap-2 p-2 bg-gray-50 rounded"
                  >
                    <span className="text-gray-400 text-xs whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString('zh-CN')}
                    </span>
                    <span className="text-blue-600 font-medium">{log.agent_name}</span>
                    <span className="text-gray-600">{log.action}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showTaskPanel && (
          <TaskAssignmentPanel
            onClose={() => setShowTaskPanel(false)}
            onTaskCreated={() => {
              setShowTaskPanel(false);
              loadDashboard();
            }}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {selectedAgent && (
          <AgentDetailModal
            agent={selectedAgent}
            onClose={() => setSelectedAgent(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

interface TaskAssignmentPanelProps {
  onClose: () => void;
  onTaskCreated: () => void;
}

const TaskAssignmentPanel: React.FC<TaskAssignmentPanelProps> = ({ onClose, onTaskCreated }) => {
  const [taskType, setTaskType] = useState('analysis');
  const [input, setInput] = useState('');
  const [autoAssign, setAutoAssign] = useState(true);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadRecommendations();
  }, [taskType]);

  const loadRecommendations = async () => {
    try {
      const res = await api.get(`/dashboard/task-assignment-options?task_type=${taskType}`);
      setRecommendations(res.data.recommendations || []);
      if (autoAssign && res.data.auto_assign_recommendation) {
        setSelectedAgents(res.data.auto_assign_recommendation);
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  };

  const handleSubmit = async () => {
    if (!input.trim()) {
      toast.error('请输入任务内容');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post('/dashboard/start-task', {
        task_type: taskType,
        input: input,
        auto_assign: autoAssign,
        agent_ids: autoAssign ? undefined : selectedAgents,
      });
      toast.success('任务已创建');
      onTaskCreated();
    } catch (error) {
      toast.error('创建任务失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">创建新任务</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">任务类型</label>
            <select
              value={taskType}
              onChange={e => setTaskType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="analysis">房产分析</option>
              <option value="consult">智能咨询</option>
              <option value="data_collection">数据采集</option>
              <option value="report">报告生成</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">任务内容</label>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="请输入任务描述..."
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="autoAssign"
              checked={autoAssign}
              onChange={e => setAutoAssign(e.target.checked)}
              className="rounded border-gray-300"
            />
            <label htmlFor="autoAssign" className="text-sm text-gray-600">
              自动分配智能体
            </label>
          </div>

          {!autoAssign && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">选择智能体</label>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {recommendations.map(rec => (
                  <label
                    key={rec.agent_id}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedAgents.includes(rec.agent_id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedAgents.includes(rec.agent_id)}
                        onChange={e => {
                          if (e.target.checked) {
                            setSelectedAgents([...selectedAgents, rec.agent_id]);
                          } else {
                            setSelectedAgents(selectedAgents.filter(id => id !== rec.agent_id));
                          }
                        }}
                        className="rounded border-gray-300"
                      />
                      <span className="font-medium">{rec.agent_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">{rec.reason}</span>
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                        {Math.round(rec.score * 100)}%
                      </span>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 p-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {isSubmitting ? '创建中...' : '创建任务'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

interface AgentDetailModalProps {
  agent: AgentStatus;
  onClose: () => void;
}

const AgentDetailModal: React.FC<AgentDetailModalProps> = ({ agent, onClose }) => {
  const config = departmentConfig[agent.department] || { color: 'bg-gray-500', icon: '🤖', label: agent.department };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-white rounded-xl shadow-xl max-w-md w-full"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className={`w-16 h-16 rounded-xl ${config.color} flex items-center justify-center text-3xl`}>
              {config.icon}
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">{agent.name}</h3>
              <p className="text-gray-500">{config.label}</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-500">状态</span>
              <span className={`flex items-center gap-2`}>
                <span className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                {getStatusLabel(agent.status)}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-500">等级</span>
              <span className="font-medium">Lv.{agent.level}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-500">效率</span>
              <span className="font-medium">{Math.round(agent.efficiency * 100)}%</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-500">今日完成</span>
              <span className="font-medium">{agent.performance_today} 个任务</span>
            </div>
            {agent.current_task && (
              <div className="py-2">
                <span className="text-gray-500 block mb-1">当前任务</span>
                <p className="text-sm bg-gray-50 p-2 rounded">{agent.current_task}</p>
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end p-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
          >
            关闭
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default AgentDashboardPage;
