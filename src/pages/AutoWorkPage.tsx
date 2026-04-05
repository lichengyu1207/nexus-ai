import React from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import autoWorkApi from '@/api/autoWork';

const AutoWorkPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: statsData, isLoading } = useQuery({
    queryKey: ['autoWorkStats'],
    queryFn: autoWorkApi.getStats,
  });

  const { data: logsData } = useQuery({
    queryKey: ['autoWorkLogs'],
    queryFn: () => autoWorkApi.getLogs(undefined, 20),
  });

  const setAutoWorkMutation = useMutation({
    mutationFn: autoWorkApi.setAutoWork,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['autoWorkStats'] }),
  });

  const triggerExecutionMutation = useMutation({
    mutationFn: autoWorkApi.triggerExecution,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['autoWorkStats', 'autoWorkLogs'] }),
  });

  const stats = statsData?.today_stats;
  const agents = statsData?.agents || [];
  const logs = logsData?.logs || [];

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`;
    return `${Math.floor(seconds / 3600)}小时`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">自主工作系统</h2>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => triggerExecutionMutation.mutate()}
          disabled={triggerExecutionMutation.isPending}
          className="px-4 py-2 bg-green-500 text-white rounded-lg disabled:opacity-50"
        >
          {triggerExecutionMutation.isPending ? '执行中...' : '触发执行'}
        </motion.button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white"
        >
          <p className="text-blue-100 text-sm">工作智能体</p>
          <p className="text-3xl font-bold mt-1">{stats?.active_agents || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-5 text-white"
        >
          <p className="text-green-100 text-sm">今日工作时长</p>
          <p className="text-3xl font-bold mt-1">{formatDuration(stats?.total_seconds || 0)}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-xl p-5 text-white"
        >
          <p className="text-yellow-100 text-sm">今日奖励</p>
          <p className="text-3xl font-bold mt-1">{stats?.total_reward || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-5 text-white"
        >
          <p className="text-purple-100 text-sm">总智能体</p>
          <p className="text-3xl font-bold mt-1">{agents.length}</p>
        </motion.div>
      </div>

      {/* Agents */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">智能体状态</h3>
        {isLoading ? (
          <p className="text-gray-500 text-center py-8">加载中...</p>
        ) : agents.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无智能体</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <div key={agent.agent_id} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{agent.name}</p>
                    <p className="text-xs text-gray-500">{agent.department}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    agent.status === 'working' ? 'bg-green-100 text-green-700' :
                    agent.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {agent.status === 'working' ? '工作中' : agent.status === 'completed' ? '已完成' : '空闲'}
                  </span>
                </div>
                <div className="text-xs text-gray-500 mb-2">
                  今日: {formatDuration(agent.daily_work_seconds)} / {formatDuration(agent.daily_work_limit)}
                </div>
                <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${Math.min((agent.daily_work_seconds / agent.daily_work_limit) * 100, 100)}%` }}
                  />
                </div>
                <button
                  onClick={() => setAutoWorkMutation.mutate({ 
                    agent_id: agent.agent_id, 
                    enabled: agent.status !== 'working' 
                  })}
                  className="mt-2 w-full py-1 text-xs bg-primary-500 text-white rounded disabled:opacity-50"
                  disabled={setAutoWorkMutation.isPending}
                >
                  {agent.status === 'working' ? '停止工作' : '开始工作'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Logs */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">工作日志</h3>
        {logs.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无工作记录</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {logs.map((log) => (
              <div key={log.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div>
                  <p className="font-medium text-sm">{log.agent_name}</p>
                  <p className="text-xs text-gray-500">{log.task_type}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-green-600">+{log.reward_earned}</p>
                  <p className="text-xs text-gray-400">{formatDuration(log.duration_seconds)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AutoWorkPage;
