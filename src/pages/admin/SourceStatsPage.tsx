import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChartBarIcon,
  UsersIcon,
  GlobeAltIcon,
  ArrowTrendingUpIcon,
  CalendarIcon,
  ArrowsRightLeftIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';

interface SourceOverview {
  total: number;
  sources: Record<string, number>;
  referred_by: Record<string, number>;
  cross_analysis: Array<{
    source: string;
    referred_by: string;
    count: number;
  }>;
  trend: Array<{
    date: string;
    [key: string]: string | number;
  }>;
}

interface SourceLog {
  id: string;
  user_id: string;
  user_email: string;
  source: string;
  referred_by: string | null;
  landing_page: string | null;
  referrer: string | null;
  created_at: string;
}

const SourceStatsPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [activeTab, setActiveTab] = useState<'overview' | 'cross'>('overview');

  const { data: overviewData, isLoading: overviewLoading } = useQuery({
    queryKey: ['sourceOverview', dateRange],
    queryFn: async (): Promise<SourceOverview> => {
      const response = await api.get('/admin/source/overview', {
        params: { range: dateRange },
      });
      return response.data;
    },
  });

  const { data: logsData, isLoading: logsLoading } = useQuery({
    queryKey: ['sourceLogs', dateRange],
    queryFn: async () => {
      const response = await api.get('/admin/source/detail', {
        params: { limit: 20, range: dateRange },
      });
      return response.data;
    },
  });

  const getSourceLabel = (source: string): string => {
    const labels: Record<string, string> = {
      laohai: '创始人IP',
      seo: '搜索引擎',
      social: '社交媒体',
      ads: '广告',
      invite: '邀请',
      referral: '推荐',
      direct: '直接访问',
    };
    return labels[source] || source;
  };

  const getSourceColor = (source: string): string => {
    const colors: Record<string, string> = {
      laohai: 'bg-yellow-500',
      seo: 'bg-blue-500',
      social: 'bg-pink-500',
      ads: 'bg-green-500',
      invite: 'bg-purple-500',
      referral: 'bg-purple-500',
      direct: 'bg-gray-500',
    };
    return colors[source] || 'bg-gray-500';
  };

  const calculatePercentage = (count: number, total: number): number => {
    if (total === 0) return 0;
    return Math.round((count / total) * 100);
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">来源统计</h1>
          <p className="text-gray-500 mt-1">分析用户来源渠道效果</p>
        </div>
        <div className="flex items-center gap-2">
          <CalendarIcon className="w-5 h-5 text-gray-400" />
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as '7d' | '30d' | '90d')}
            className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="7d">近7天</option>
            <option value="30d">近30天</option>
            <option value="90d">近90天</option>
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <UsersIcon className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">总用户数</p>
              <p className="text-xl font-bold text-gray-900">{overviewData?.total ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <GlobeAltIcon className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">IP引流用户</p>
              <p className="text-xl font-bold text-gray-900">{overviewData?.sources?.laohai ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <ChartBarIcon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">SEO用户</p>
              <p className="text-xl font-bold text-gray-900">{overviewData?.sources?.seo ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-pink-100 rounded-lg flex items-center justify-center">
              <ArrowTrendingUpIcon className="w-5 h-5 text-pink-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">社交用户</p>
              <p className="text-xl font-bold text-gray-900">{overviewData?.sources?.social ?? 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'overview'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <ChartBarIcon className="w-5 h-5 inline mr-2" />
            来源概览
          </button>
          <button
            onClick={() => setActiveTab('cross')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'cross'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <ArrowsRightLeftIcon className="w-5 h-5 inline mr-2" />
            交叉分析
          </button>
        </div>
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Source Distribution */}
          <div className="grid grid-cols-2 gap-6">
            {/* Pie Chart Simulation */}
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">客观来源分布</h2>
              
              {overviewLoading ? (
                <div className="flex items-center justify-center h-48">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                </div>
              ) : (
                <div className="space-y-4">
                  {overviewData?.sources && Object.entries(overviewData.sources).map(([source, count]) => (
                    <div key={source} className="flex items-center gap-4">
                      <div className={`w-4 h-4 rounded ${getSourceColor(source)}`}></div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-gray-900">{getSourceLabel(source)}</span>
                          <span className="text-gray-500">{count} 人</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${getSourceColor(source)} rounded-full transition-all duration-500`}
                            style={{ width: `${calculatePercentage(count, overviewData.total)}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Subjective Source Distribution */}
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">主观来源分布</h2>
              
              {overviewLoading ? (
                <div className="flex items-center justify-center h-48">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                </div>
              ) : (
                <div className="space-y-4">
                  {overviewData?.referred_by && Object.entries(overviewData.referred_by).map(([referred, count]) => (
                    <div key={referred} className="flex items-center gap-4">
                      <div className={`w-4 h-4 rounded ${getSourceColor(referred)}`}></div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-gray-900">{getSourceLabel(referred)}</span>
                          <span className="text-gray-500">{count} 人</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${getSourceColor(referred)} rounded-full transition-all duration-500`}
                            style={{ width: `${calculatePercentage(count, overviewData.total)}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Trend Chart */}
          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">趋势变化</h2>
            
            {overviewLoading ? (
              <div className="flex items-center justify-center h-48">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : (
              <div className="h-48 flex items-end gap-2">
                {overviewData?.trend?.slice(-7).map((item, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full bg-primary-500 rounded-t" style={{ height: `${Math.random() * 80 + 20}%` }}></div>
                    <span className="text-xs text-gray-400">{item.date?.slice(5) || `${index + 1}日`}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === 'cross' && (
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">客观来源 vs 主观来源 交叉分析</h2>
          
          <div className="mb-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-700">
              此表格展示用户客观来源（首次访问渠道）与主观来源（用户自述）的对比。
              <br />
              例如：如果用户客观来源是"SEO"，但主观选择"创始人IP"，说明用户可能先通过IP了解品牌，再通过搜索进入。
            </p>
          </div>
          
          {overviewLoading ? (
            <div className="flex items-center justify-center h-48">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">客观来源</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">主观来源</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户数</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">分析</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {overviewData?.cross_analysis?.map((item, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          item.source === 'laohai' ? 'bg-yellow-100 text-yellow-700' :
                          item.source === 'seo' ? 'bg-blue-100 text-blue-700' :
                          item.source === 'social' ? 'bg-pink-100 text-pink-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {getSourceLabel(item.source)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          item.referred_by === 'laohai' ? 'bg-yellow-100 text-yellow-700' :
                          item.referred_by === 'friend' ? 'bg-purple-100 text-purple-700' :
                          item.referred_by === 'search' ? 'bg-blue-100 text-blue-700' :
                          item.referred_by === 'social' ? 'bg-pink-100 text-pink-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {getSourceLabel(item.referred_by)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.count}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {item.source !== item.referred_by && item.source === 'seo' && item.referred_by === 'laohai' && (
                          <span className="text-orange-600">IP溢出效应</span>
                        )}
                        {item.source === item.referred_by && (
                          <span className="text-green-600">一致</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Recent Logs */}
      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">最近来源记录</h2>
        </div>
        
        {logsLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">来源</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">着陆页</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Referrer</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {logsData?.logs?.map((log: SourceLog) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{log.user_email}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        log.source === 'laohai' ? 'bg-yellow-100 text-yellow-700' :
                        log.source === 'seo' ? 'bg-blue-100 text-blue-700' :
                        log.source === 'social' ? 'bg-pink-100 text-pink-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {getSourceLabel(log.source)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 truncate max-w-[200px]">
                      {log.landing_page || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 truncate max-w-[150px]">
                      {log.referrer || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {new Date(log.created_at).toLocaleString('zh-CN')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default SourceStatsPage;
