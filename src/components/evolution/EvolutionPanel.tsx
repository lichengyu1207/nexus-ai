import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ChartBarIcon,
  CogIcon,
  ArrowDownTrayIcon,
  ArrowUturnLeftIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import toast from '@/utils/toast';

interface AgentPerformance {
  agent_id: string;
  agent_type: string;
  performance_stats: {
    total_decisions: number;
    success_rate: number;
    error_rate: number;
    avg_execution_time: number;
    recent_success_rate: number;
    baseline_success_rate: number;
  };
  trajectory_count: number;
  diagnosis_count: number;
  suggestion_count: number;
}

interface Suggestion {
  suggestion_id: string;
  agent_id: string;
  suggestion_type: string;
  title: string;
  description: string;
  priority: number;
  impact_estimate: number;
  implementation_effort: string;
  status: string;
  created_at: number;
}

interface Version {
  version_id: string;
  version_number: string;
  created_at: number;
  performance_metrics: Record<string, number>;
  is_active: boolean;
  rollback_available: boolean;
}

const EvolutionPanel: React.FC = () => {
  const [report, setReport] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'suggestions' | 'versions'>('overview');

  const fetchReport = useCallback(async () => {
    try {
      const response = await api.get('/api/evolution/report');
      setReport(response.data);
    } catch (error) {
      console.error('Failed to fetch evolution report:', error);
    }
  }, []);

  const fetchSuggestions = useCallback(async () => {
    try {
      const response = await api.get('/api/evolution/suggestions');
      setSuggestions(response.data.suggestions || []);
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    }
  }, []);

  const fetchVersions = useCallback(async (agentId: string) => {
    try {
      const response = await api.get(`/api/evolution/versions/${agentId}`);
      setVersions(response.data.versions || []);
    } catch (error) {
      console.error('Failed to fetch versions:', error);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchReport(), fetchSuggestions()]);
      setLoading(false);
    };
    init();
  }, [fetchReport, fetchSuggestions]);

  useEffect(() => {
    if (selectedAgent) {
      fetchVersions(selectedAgent);
    }
  }, [selectedAgent, fetchVersions]);

  const handleApproveSuggestion = async (suggestionId: string) => {
    try {
      await api.post('/api/evolution/suggestions/approve', {
        suggestion_id: suggestionId,
        reviewer: 'admin',
      });
      toast.success('建议已批准');
      fetchSuggestions();
    } catch (error) {
      toast.error('批准失败');
    }
  };

  const handleApplySuggestion = async (suggestionId: string) => {
    try {
      await api.post('/api/evolution/suggestions/apply', {
        suggestion_id: suggestionId,
        reviewer: 'admin',
      });
      toast.success('建议已应用');
      fetchSuggestions();
      fetchReport();
    } catch (error) {
      toast.error('应用失败');
    }
  };

  const handleRejectSuggestion = async (suggestionId: string, reason: string) => {
    try {
      await api.post('/api/evolution/suggestions/reject', {
        suggestion_id: suggestionId,
        reviewer: 'admin',
        reason,
      });
      toast.success('建议已拒绝');
      fetchSuggestions();
    } catch (error) {
      toast.error('拒绝失败');
    }
  };

  const handleRollback = async (agentId: string) => {
    try {
      await api.post(`/api/evolution/rollback/${agentId}`);
      toast.success('版本已回滚');
      fetchVersions(agentId);
      fetchReport();
    } catch (error) {
      toast.error('回滚失败');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-500';
      case 'approved': return 'text-blue-500';
      case 'applied': return 'text-green-500';
      case 'rejected': return 'text-red-500';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-500';
    }
  };

  const getPriorityBadge = (priority: number) => {
    if (priority === 1) return 'bg-red-100 text-red-700';
    if (priority === 2) return 'bg-yellow-100 text-yellow-700';
    return 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <ArrowPathIcon className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">智能体自我进化系统</h2>
            <p className="text-gray-500 mt-1">三省六部制智能体的元认知与自我升级</p>
          </div>
          <button
            onClick={() => Promise.all([fetchReport(), fetchSuggestions()])}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowPathIcon className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="flex gap-4 mt-6">
          {(['overview', 'suggestions', 'versions'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {tab === 'overview' && '系统概览'}
              {tab === 'suggestions' && `改进建议 (${suggestions.length})`}
              {tab === 'versions' && '版本管理'}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {report && (
                <>
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-xl">
                      <div className="text-3xl font-bold text-purple-600">
                        {report.stats?.total_agents || 0}
                      </div>
                      <div className="text-sm text-purple-500">注册智能体</div>
                    </div>
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl">
                      <div className="text-3xl font-bold text-blue-600">
                        {report.stats?.total_diagnoses || 0}
                      </div>
                      <div className="text-sm text-blue-500">诊断次数</div>
                    </div>
                    <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl">
                      <div className="text-3xl font-bold text-green-600">
                        {report.stats?.suggestions_applied || 0}
                      </div>
                      <div className="text-sm text-green-500">已应用建议</div>
                    </div>
                    <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-xl">
                      <div className="text-3xl font-bold text-orange-600">
                        {report.pending_suggestions || 0}
                      </div>
                      <div className="text-sm text-orange-500">待处理建议</div>
                    </div>
                  </div>

                  <h3 className="text-lg font-semibold text-gray-800 mb-4">智能体性能监控</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(report.agents || {}).map(([agentId, agentData]: [string, any]) => {
                      const stats = agentData.performance_stats || {};
                      const successDiff = stats.recent_success_rate - stats.baseline_success_rate;
                      
                      return (
                        <motion.div
                          key={agentId}
                          whileHover={{ scale: 1.02 }}
                          onClick={() => {
                            setSelectedAgent(agentId);
                            setActiveTab('versions');
                          }}
                          className="p-4 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-3">
                            <span className="font-semibold text-gray-800">{agentId}</span>
                            <span className="text-xs px-2 py-1 bg-purple-100 text-purple-600 rounded">
                              {agentData.agent_type}
                            </span>
                          </div>
                          
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-500">成功率</span>
                              <span className={`font-medium ${
                                successDiff >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {(stats.recent_success_rate * 100 || 0).toFixed(1)}%
                                {successDiff !== 0 && (
                                  <span className="text-xs ml-1">
                                    {successDiff > 0 ? '↑' : '↓'}
                                  </span>
                                )}
                              </span>
                            </div>
                            
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  stats.recent_success_rate >= stats.baseline_success_rate
                                    ? 'bg-green-500'
                                    : 'bg-yellow-500'
                                }`}
                                style={{ width: `${(stats.recent_success_rate || 0) * 100}%` }}
                              />
                            </div>
                            
                            <div className="flex justify-between text-xs text-gray-400">
                              <span>决策: {stats.total_decisions || 0}</span>
                              <span>诊断: {agentData.diagnosis_count || 0}</span>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </>
              )}
            </motion.div>
          )}

          {activeTab === 'suggestions' && (
            <motion.div
              key="suggestions"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {suggestions.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <CheckCircleIcon className="w-12 h-12 mx-auto mb-4 text-green-400" />
                  <p>暂无待处理的改进建议</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {suggestions.map((suggestion) => (
                    <motion.div
                      key={suggestion.suggestion_id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-4 bg-gray-50 rounded-xl border border-gray-100"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityBadge(suggestion.priority)}`}>
                              P{suggestion.priority}
                            </span>
                            <span className="text-sm text-gray-500">{suggestion.agent_id}</span>
                            <span className={`text-xs ${getStatusColor(suggestion.status)}`}>
                              {suggestion.status}
                            </span>
                          </div>
                          
                          <h4 className="font-semibold text-gray-800 mb-1">{suggestion.title}</h4>
                          <p className="text-sm text-gray-600 mb-3">{suggestion.description}</p>
                          
                          <div className="flex gap-4 text-xs text-gray-400">
                            <span>影响预估: {(suggestion.impact_estimate * 100).toFixed(0)}%</span>
                            <span>实施难度: {suggestion.implementation_effort}</span>
                            <span>类型: {suggestion.suggestion_type}</span>
                          </div>
                        </div>
                        
                        <div className="flex gap-2 ml-4">
                          {suggestion.status === 'pending' && (
                            <>
                              <button
                                onClick={() => handleApproveSuggestion(suggestion.suggestion_id)}
                                className="px-3 py-1.5 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600"
                              >
                                批准
                              </button>
                              <button
                                onClick={() => handleRejectSuggestion(suggestion.suggestion_id, '管理员拒绝')}
                                className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300"
                              >
                                拒绝
                              </button>
                            </>
                          )}
                          {suggestion.status === 'approved' && (
                            <button
                              onClick={() => handleApplySuggestion(suggestion.suggestion_id)}
                              className="px-3 py-1.5 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600"
                            >
                              应用
                            </button>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'versions' && (
            <motion.div
              key="versions"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {!selectedAgent ? (
                <div className="text-center py-12 text-gray-500">
                  <CogIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p>请从概览页面选择一个智能体查看版本历史</p>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-800">
                      {selectedAgent} 版本历史
                    </h3>
                    <button
                      onClick={() => handleRollback(selectedAgent)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-orange-500 text-white rounded-lg text-sm hover:bg-orange-600"
                    >
                      <ArrowUturnLeftIcon className="w-4 h-4" />
                      回滚到上一版本
                    </button>
                  </div>
                  
                  <div className="space-y-3">
                    {versions.map((version, index) => (
                      <div
                        key={version.version_id}
                        className={`p-4 rounded-xl border ${
                          version.is_active
                            ? 'bg-green-50 border-green-200'
                            : 'bg-gray-50 border-gray-100'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={`w-3 h-3 rounded-full ${
                              version.is_active ? 'bg-green-500' : 'bg-gray-300'
                            }`} />
                            <span className="font-semibold text-gray-800">
                              v{version.version_number}
                            </span>
                            {version.is_active && (
                              <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">
                                当前版本
                              </span>
                            )}
                          </div>
                          <span className="text-sm text-gray-500">
                            {new Date(version.created_at * 1000).toLocaleString()}
                          </span>
                        </div>
                        
                        {Object.keys(version.performance_metrics).length > 0 && (
                          <div className="mt-3 flex gap-4 text-xs text-gray-500">
                            {Object.entries(version.performance_metrics).slice(0, 4).map(([key, value]) => (
                              <span key={key}>
                                {key}: {typeof value === 'number' ? value.toFixed(2) : value}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default EvolutionPanel;
