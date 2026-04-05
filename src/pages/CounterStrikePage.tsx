import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import counterstrikeApi from '@/api/counterstrike';

const CounterstrikePage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'threats' | 'honeypots' | 'actions'>('threats');

  const { data: status } = useQuery({
    queryKey: ['counterstrikeStatus'],
    queryFn: counterstrikeApi.getStatus,
  });

  const { data: threats, isLoading: threatsLoading } = useQuery({
    queryKey: ['counterstrikeThreats'],
    queryFn: counterstrikeApi.getActiveThreats,
  });

  const { data: honeypots } = useQuery({
    queryKey: ['counterstrikeHoneypots'],
    queryFn: counterstrikeApi.listHoneypots,
  });

  const { data: actions } = useQuery({
    queryKey: ['counterstrikeActions'],
    queryFn: counterstrikeApi.getCounterStrikeHistory,
  });

  const blockMutation = useMutation({
    mutationFn: async (threatId: string) => {
      // 这里应该实现阻止威胁的逻辑
      console.log('Blocking threat:', threatId);
      return { success: true };
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['counterstrikeThreats', 'counterstrikeStatus'] }),
  });

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case 'low': return 'bg-green-500';
      case 'medium': return 'bg-yellow-500';
      case 'high': return 'bg-orange-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">反击系统</h2>
        <span className={`px-3 py-1 rounded-full text-white text-sm ${getThreatLevelColor(status?.threat_level || 'low')}`}>
          威胁等级: {status?.threat_level || 'low'}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-5 text-white"
        >
          <p className="text-red-100 text-sm">已阻止威胁</p>
          <p className="text-3xl font-bold mt-1">{status?.total_threats_blocked || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-5 text-white"
        >
          <p className="text-purple-100 text-sm">活跃蜜罐</p>
          <p className="text-3xl font-bold mt-1">{status?.active_honeypots || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-5 text-white"
        >
          <p className="text-orange-100 text-sm">活跃反击</p>
          <p className="text-3xl font-bold mt-1">{status?.active_counterstrikes || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white"
        >
          <p className="text-blue-100 text-sm">系统状态</p>
          <p className="text-3xl font-bold mt-1">{status?.is_active ? '运行中' : '待机'}</p>
        </motion.div>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <div className="flex">
            {[
              { id: 'threats', label: '威胁列表', icon: '🛡️' },
              { id: 'honeypots', label: '蜜罐系统', icon: '🍯' },
              { id: 'actions', label: '反击行动', icon: '⚔️' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'threats' | 'honeypots' | 'actions')}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium ${
                  activeTab === tab.id
                    ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-4">
          <AnimatePresence mode="wait">
            {activeTab === 'threats' && (
              <motion.div key="threats" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {threatsLoading ? (
                  <p className="text-center py-8 text-gray-500">加载中...</p>
                ) : threats?.threats?.length === 0 ? (
                  <p className="text-center py-8 text-gray-500">暂无威胁</p>
                ) : (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {threats?.threats?.map((threat) => (
                      <div key={threat.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                        <div>
                          <p className="font-medium text-sm">{threat.threat_type}</p>
                          <p className="text-xs text-gray-500">{threat.source_ip} · {threat.description}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            threat.status === 'blocked' ? 'bg-green-100 text-green-700' :
                            threat.status === 'investigating' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {threat.status}
                          </span>
                          {threat.status !== 'blocked' && (
                            <button
                              onClick={() => blockMutation.mutate(threat.id)}
                              className="px-2 py-1 bg-red-500 text-white rounded text-xs"
                            >
                              阻止
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'honeypots' && (
              <motion.div key="honeypots" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="grid grid-cols-2 gap-4">
                  {honeypots?.honeypots?.map((hp) => (
                    <div key={hp.id} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{hp.honeypot_type}</span>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          hp.status === 'active' ? 'bg-green-100 text-green-700' :
                          hp.status === 'triggered' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {hp.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">触发次数: {hp.triggered_count}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'actions' && (
              <motion.div key="actions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="space-y-2">
                  {actions?.actions?.map((action) => (
                    <div key={action.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{action.action_type}</p>
                        <p className="text-xs text-gray-500">目标: {action.target_ip}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        action.status === 'active' ? 'bg-green-100 text-green-700' :
                        action.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {action.status}
                      </span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default CounterstrikePage;
