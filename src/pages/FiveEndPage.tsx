import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import fiveEndApi, { EndType } from '@/api/fiveEnd';

const endTypeNames: Record<EndType, string> = {
  government: '政端',
  enterprise: '企端',
  education: '教端',
  standard: '标端',
  public: '公端',
};

const endTypeColors: Record<EndType, string> = {
  government: 'bg-red-500',
  enterprise: 'bg-blue-500',
  education: 'bg-green-500',
  standard: 'bg-purple-500',
  public: 'bg-orange-500',
};

const FiveEndPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'clusters' | 'events' | 'proposals'>('clusters');

  const { data: status } = useQuery({
    queryKey: ['fiveEndStatus'],
    queryFn: fiveEndApi.getStatus,
  });

  const { data: clusters } = useQuery({
    queryKey: ['fiveEndClusters'],
    queryFn: fiveEndApi.getClusters,
  });

  const { data: events } = useQuery({
    queryKey: ['fiveEndEvents'],
    queryFn: () => fiveEndApi.getEvents(50),
  });

  const { data: proposals } = useQuery({
    queryKey: ['fiveEndProposals'],
    queryFn: () => fiveEndApi.getProposals('pending'),
  });

  const voteMutation = useMutation({
    mutationFn: (params: { proposalId: string; choice: 'for' | 'against' | 'abstain' }) =>
      fiveEndApi.vote({
        proposal_id: params.proposalId,
        voter_end: 'government',
        voter_agent: 'admin',
        choice: params.choice,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['fiveEndProposals'] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">五端协同系统</h2>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {(Object.keys(endTypeNames) as EndType[]).map((endType, idx) => (
          <motion.div
            key={endType}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className={`${endTypeColors[endType]} rounded-xl p-5 text-white`}
          >
            <p className="text-white/80 text-sm">{endTypeNames[endType]}</p>
            <p className="text-2xl font-bold mt-1">
              {status?.connected_ends?.includes(endType) ? '已连接' : '离线'}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500">消息队列</p>
          <p className="text-2xl font-bold">{status?.message_queue_size || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500">活跃事件</p>
          <p className="text-2xl font-bold">{status?.active_events || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500">黑板条目</p>
          <p className="text-2xl font-bold">{status?.blackboard_entries || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500">待决提案</p>
          <p className="text-2xl font-bold">{status?.pending_proposals || 0}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <div className="flex">
            {[
              { id: 'clusters', label: '端集群', icon: '🏢' },
              { id: 'events', label: '跨端事件', icon: '📨' },
              { id: 'proposals', label: '共识提案', icon: '🗳️' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'clusters' | 'events' | 'proposals')}
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
            {activeTab === 'clusters' && (
              <motion.div key="clusters" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {clusters?.clusters?.map((cluster) => (
                    <div key={cluster.end_type} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`w-10 h-10 rounded-full ${endTypeColors[cluster.end_type]} flex items-center justify-center text-white font-bold`}>
                          {endTypeNames[cluster.end_type].charAt(0)}
                        </div>
                        <div>
                          <p className="font-medium">{cluster.name}</p>
                          <p className="text-xs text-gray-500">{cluster.agents.length} 智能体</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className={`px-2 py-0.5 rounded ${
                          cluster.status === 'active' ? 'bg-green-100 text-green-700' :
                          cluster.status === 'busy' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {cluster.status}
                        </span>
                        <span className="text-gray-500">{cluster.message_count} 消息</span>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'events' && (
              <motion.div key="events" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {events?.events?.map((event) => (
                    <div key={event.id} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-xs ${endTypeColors[event.source_end]} text-white`}>
                            {endTypeNames[event.source_end]}
                          </span>
                          <span className="text-sm">{event.event_type}</span>
                        </div>
                        <span className={`text-xs ${event.processed ? 'text-green-500' : 'text-yellow-500'}`}>
                          {event.processed ? '已处理' : '待处理'}
                        </span>
                      </div>
                    </div>
                  ))}
                  {(!events?.events || events.events.length === 0) && (
                    <p className="text-center py-8 text-gray-500">暂无事件</p>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === 'proposals' && (
              <motion.div key="proposals" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="space-y-3">
                  {proposals?.proposals?.map((proposal) => (
                    <div key={proposal.id} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{proposal.title}</span>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          proposal.status === 'voting' ? 'bg-blue-100 text-blue-700' :
                          proposal.status === 'approved' ? 'bg-green-100 text-green-700' :
                          'bg-yellow-100 text-yellow-700'
                        }`}>
                          {proposal.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{proposal.description}</p>
                      <div className="flex items-center justify-between">
                        <div className="text-xs text-gray-500">
                          赞成: {proposal.votes_for} | 反对: {proposal.votes_against} | 弃权: {proposal.votes_abstain}
                        </div>
                        {proposal.status === 'voting' && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => voteMutation.mutate({ proposalId: proposal.id, choice: 'for' })}
                              className="px-2 py-1 bg-green-500 text-white rounded text-xs"
                            >
                              赞成
                            </button>
                            <button
                              onClick={() => voteMutation.mutate({ proposalId: proposal.id, choice: 'against' })}
                              className="px-2 py-1 bg-red-500 text-white rounded text-xs"
                            >
                              反对
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {(!proposals?.proposals || proposals.proposals.length === 0) && (
                    <p className="text-center py-8 text-gray-500">暂无提案</p>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default FiveEndPage;
