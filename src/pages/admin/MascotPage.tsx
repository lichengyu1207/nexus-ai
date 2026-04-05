import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  SparklesIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface MascotQuote {
  id: string;
  category: string;
  content: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

interface MascotStats {
  total_clicks: number;
  total_drag_events: number;
  total_scene_triggers: number;
  clicks_today: number;
  popular_scenes: Array<{ scene: string; count: number }>;
  recent_interactions: Array<{ type: string; user_id: string; time: string }>;
}

const MascotPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'quotes' | 'stats'>('quotes');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingQuote, setEditingQuote] = useState<MascotQuote | null>(null);
  const [newQuoteText, setNewQuoteText] = useState('');
  const [newQuoteCategory, setNewQuoteCategory] = useState('random');

  const { data: quotesData, isLoading: quotesLoading } = useQuery({
    queryKey: ['mascotQuotes'],
    queryFn: async () => {
      const response = await api.get('/admin/mascot/quotes');
      return response.data;
    },
  });

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['mascotStats'],
    queryFn: async () => {
      const response = await api.get('/admin/mascot/stats');
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: { text: string; category: string }) => {
      const response = await api.post('/admin/mascot/quotes', {
        content: data.text,
        category: data.category,
      });
      return response.data;
    },
    onSuccess: () => {
      showToast.success('语录添加成功');
      setShowAddModal(false);
      setNewQuoteText('');
      setNewQuoteCategory('random');
    },
    onError: () => {
      showToast.error('添加失败');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (quoteId: string) => {
      const response = await api.delete(`/admin/mascot/quotes/${quoteId}`);
      return response.data;
    },
    onSuccess: () => {
      showToast.success('语录删除成功');
    },
    onError: () => {
      showToast.error('删除失败');
    },
  });

  const getCategoryLabel = (category: string): string => {
    const labels: Record<string, string> = {
      default: '默认',
      thinking: '思考',
      happy: '开心',
      confused: '困惑',
      surprised: '惊讶',
      comforting: '安慰',
      easterEgg: '彩蛋',
      random: '随机',
      loading: '加载',
      success: '成功',
      error: '错误',
      reminder: '提醒',
      funny: '搞怪',
      abstract: '抽象',
      encourage: '鼓励',
      professional: '专业',
    };
    return labels[category] || category;
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      default: 'bg-gray-100 text-gray-700',
      thinking: 'bg-blue-100 text-blue-700',
      happy: 'bg-green-100 text-green-700',
      confused: 'bg-yellow-100 text-yellow-700',
      surprised: 'bg-purple-100 text-purple-700',
      comforting: 'bg-pink-100 text-pink-700',
      easterEgg: 'bg-orange-100 text-orange-700',
      random: 'bg-indigo-100 text-indigo-700',
      loading: 'bg-cyan-100 text-cyan-700',
      success: 'bg-emerald-100 text-emerald-700',
      error: 'bg-red-100 text-red-700',
      reminder: 'bg-amber-100 text-amber-700',
      funny: 'bg-rose-100 text-rose-700',
      abstract: 'bg-violet-100 text-violet-700',
      encourage: 'bg-teal-100 text-teal-700',
      professional: 'bg-slate-100 text-slate-700',
    };
    return colors[category] || 'bg-gray-100 text-gray-700';
  };

  const handleAddQuote = () => {
    if (!newQuoteText.trim()) {
      showToast.error('请输入语录内容');
      return;
    }
    createMutation.mutate({ text: newQuoteText, category: newQuoteCategory });
  };

  const handleDeleteQuote = (quoteId: string) => {
    if (confirm('确定要删除这条语录吗？')) {
      deleteMutation.mutate(quoteId);
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">吉祥物管理</h1>
          <p className="text-gray-500 mt-1">管理房小智的表情和语录</p>
        </div>
        <div className="flex items-center gap-2">
          <SparklesIcon className="w-8 h-8 text-primary-600" />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-500">总点击次数</p>
              <p className="text-xl font-bold text-gray-900">{statsData?.total_clicks ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-500">总互动次数</p>
              <p className="text-xl font-bold text-gray-900">{statsData?.total_interactions ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <ChartBarIcon className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">彩蛋触发</p>
              <p className="text-xl font-bold text-gray-900">{statsData?.easter_egg_triggers ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <SparklesIcon className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">场景数</p>
              <p className="text-xl font-bold text-gray-900">{Object.keys(statsData?.by_scene || {}).length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('quotes')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'quotes'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <ChatBubbleLeftRightIcon className="w-5 h-5 inline mr-2" />
            语录管理
          </button>
          <button
            onClick={() => setActiveTab('stats')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'stats'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <ChartBarIcon className="w-5 h-5 inline mr-2" />
            互动统计
          </button>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'quotes' && (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">语录列表</h2>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <PlusIcon className="w-5 h-5" />
              添加语录
            </button>
          </div>

          {quotesLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {quotesData?.quotes?.map((quote: MascotQuote) => (
                <div key={quote.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                  <div className="flex-1">
                    <p className="text-gray-900">{quote.content}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(quote.category)}`}>
                        {getCategoryLabel(quote.category)}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(quote.created_at).toLocaleDateString('zh-CN')}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setEditingQuote(quote);
                        setNewQuoteText(quote.content);
                        setNewQuoteCategory(quote.category);
                        setShowAddModal(true);
                      }}
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <PencilIcon className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDeleteQuote(quote.id)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">热门场景</h2>
            <div className="space-y-3">
              {Object.entries(statsData?.by_scene || {}).map(([scene, count], index) => (
                <div key={scene} className="flex items-center gap-4">
                  <span className="w-8 h-8 flex items-center justify-center bg-gray-100 rounded-full text-sm font-medium text-gray-600">
                    {index + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">{scene}</span>
                      <span className="text-gray-500">{count as number} 次</span>
                    </div>
                    <div className="mt-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-500 rounded-full"
                        style={{ width: `${((count as number) / Math.max(...Object.values(statsData?.by_scene || {}))) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
              {Object.keys(statsData?.by_scene || {}).length === 0 && (
                <p className="text-center text-gray-500 py-4">暂无场景数据</p>
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">每日统计</h2>
            <div className="space-y-2">
              {statsData?.daily_stats?.map((stat: any, index: number) => (
                <div key={index} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <span className="text-gray-600">{stat.date}</span>
                  <span className="font-medium">{stat.count} 次互动</span>
                </div>
              ))}
              {(!statsData?.daily_stats || statsData.daily_stats.length === 0) && (
                <p className="text-center text-gray-500 py-4">暂无统计数据</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">
                {editingQuote ? '编辑语录' : '添加语录'}
              </h3>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setEditingQuote(null);
                  setNewQuoteText('');
                  setNewQuoteCategory('random');
                }}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  语录内容
                </label>
                <textarea
                  value={newQuoteText}
                  onChange={(e) => setNewQuoteText(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="输入语录内容..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  分类
                </label>
                <select
                  value={newQuoteCategory}
                  onChange={(e) => setNewQuoteCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="default">默认</option>
                  <option value="thinking">思考</option>
                  <option value="happy">开心</option>
                  <option value="confused">困惑</option>
                  <option value="surprised">惊讶</option>
                  <option value="comforting">安慰</option>
                  <option value="easterEgg">彩蛋</option>
                  <option value="random">随机</option>
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setEditingQuote(null);
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleAddQuote}
                  disabled={createMutation.isPending}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
                >
                  {createMutation.isPending ? '保存中...' : '保存'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MascotPage;
