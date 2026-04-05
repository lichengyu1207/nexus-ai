import React, { useState, useEffect } from 'react';

interface IPDashboardData {
  ip_info: {
    id: string;
    name: string;
    status: string;
    commission_rate: number;
    referral_code: string;
    available_commission: number;
    total_commission: number;
  };
  total_referrals: number;
  valid_referrals: number;
  total_commission: number;
  available_commission: number;
  recent_referrals: any[];
}

interface Article {
  id: string;
  title: string;
  content: string;
  category: string;
  status: string;
  created_at: string;
}

const StatCard: React.FC<{
  title: string;
  value: number | string;
  icon: string;
  color: string;
  suffix?: string;
}> = ({ title, value, icon, color, suffix = '' }) => (
  <div className="bg-white rounded-lg shadow p-4 h-full">
    <div className="flex items-center mb-2">
      <span className={`text-xl mr-2`} style={{ color }}>{icon}</span>
      <span className="text-sm text-gray-500">{title}</span>
    </div>
    <div className="text-2xl font-bold">
      {typeof value === 'number' ? value.toLocaleString() : value}{suffix}
    </div>
  </div>
);

const IPDashboardPage: React.FC = () => {
  const [data, setData] = useState<IPDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'content' | 'tools'>('dashboard');
  
  // 内容营销相关状态
  const [articles, setArticles] = useState<Article[]>([]);
  const [generating, setGenerating] = useState(false);
  const [articleTopic, setArticleTopic] = useState('');
  const [articleCategory, setArticleCategory] = useState('market');
  
  // 批量分析相关状态
  const [batchAddresses, setBatchAddresses] = useState('');
  const [batchAnalyzing, setBatchAnalyzing] = useState(false);
  const [batchResults, setBatchResults] = useState<any[]>([]);

  useEffect(() => {
    fetchData();
    fetchArticles();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/api/ip/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await res.json();
      if (result.error) {
        setError(result.error);
      } else {
        setData(result);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || '获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchArticles = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/api/ip/articles', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await res.json();
      setArticles(result.articles || []);
    } catch (err) {
      console.error('Failed to fetch articles:', err);
    }
  };

  const copyReferralLink = () => {
    if (data?.ip_info?.referral_code) {
      const link = `${window.location.origin}/?ref=${data.ip_info.referral_code}`;
      navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const generateArticle = async () => {
    if (!articleTopic.trim()) return;
    
    setGenerating(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/api/ip/articles/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          topic: articleTopic,
          category: articleCategory,
        }),
      });
      const result = await res.json();
      if (result.article) {
        setArticles([result.article, ...articles]);
        setArticleTopic('');
      }
    } catch (err) {
      console.error('Failed to generate article:', err);
    } finally {
      setGenerating(false);
    }
  };

  const runBatchAnalysis = async () => {
    if (!batchAddresses.trim()) return;
    
    const addresses = batchAddresses.split('\n').filter(a => a.trim());
    if (addresses.length === 0) return;
    
    setBatchAnalyzing(true);
    setBatchResults([]);
    
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/api/ip/batch-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ addresses }),
      });
      const result = await res.json();
      setBatchResults(result.results || []);
    } catch (err) {
      console.error('Failed to run batch analysis:', err);
    } finally {
      setBatchAnalyzing(false);
    }
  };

  const exportData = async (type: 'referrals' | 'articles' | 'analysis') => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/api/ip/export/${type}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type}_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export data:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
          {error}
        </div>
        <a 
          href="/ip-apply" 
          className="inline-block mt-4 bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark"
        >
          申请成为IP合作伙伴
        </a>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">IP工作台</h1>
        <span className={`px-3 py-1 rounded-full text-sm ${
          data.ip_info.status === 'active' 
            ? 'bg-green-100 text-green-700' 
            : 'bg-gray-100 text-gray-600'
        }`}>
          {data.ip_info.status === 'active' ? '已激活' : data.ip_info.status}
        </span>
      </div>

      {/* 标签页导航 */}
      <div className="flex gap-2 mb-6 border-b">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2 border-b-2 transition-colors ${
            activeTab === 'dashboard' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          📊 数据概览
        </button>
        <button
          onClick={() => setActiveTab('content')}
          className={`px-4 py-2 border-b-2 transition-colors ${
            activeTab === 'content' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          📝 内容营销
        </button>
        <button
          onClick={() => setActiveTab('tools')}
          className={`px-4 py-2 border-b-2 transition-colors ${
            activeTab === 'tools' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          🔧 专属工具
        </button>
      </div>

      {/* 数据概览 */}
      {activeTab === 'dashboard' && (
        <>
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">您的专属推广链接</h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={`${window.location.origin}/?ref=${data.ip_info.referral_code}`}
                readOnly
                className="flex-1 px-3 py-2 border border-gray-300 rounded bg-gray-50 text-sm"
              />
              <button
                onClick={copyReferralLink}
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primaryDark transition-colors"
              >
                {copied ? '已复制' : '复制'}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              佣金比例: {data.ip_info.commission_rate}%
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              title="总推广用户"
              value={data.total_referrals}
              icon="👥"
              color="#1976d2"
            />
            <StatCard
              title="有效推广"
              value={data.valid_referrals}
              icon="📈"
              color="#2e7d32"
            />
            <StatCard
              title="累计佣金"
              value={data.total_commission / 100}
              icon="💰"
              color="#ed6c02"
              suffix="元"
            />
            <StatCard
              title="可提现"
              value={data.available_commission / 100}
              icon="🏦"
              color="#9c27b0"
              suffix="元"
            />
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-medium mb-4">最近推广记录</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-3">用户ID</th>
                    <th className="text-left py-2 px-3">注册时间</th>
                    <th className="text-left py-2 px-3">状态</th>
                    <th className="text-left py-2 px-3">佣金</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_referrals.map((ref: any) => (
                    <tr key={ref.id} className="border-b hover:bg-gray-50">
                      <td className="py-2 px-3">{ref.user_id?.slice(0, 8)}...</td>
                      <td className="py-2 px-3">
                        {new Date(ref.referred_at).toLocaleDateString('zh-CN')}
                      </td>
                      <td className="py-2 px-3">
                        <span className={`px-2 py-1 rounded text-xs ${
                          ref.status === 'paid' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {ref.status}
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        {ref.commission_amount ? `${(ref.commission_amount / 100).toFixed(2)}元` : '-'}
                      </td>
                    </tr>
                  ))}
                  {data.recent_referrals.length === 0 && (
                    <tr>
                      <td colSpan={4} className="text-center py-4 text-gray-500">
                        暂无推广记录
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* 内容营销 */}
      {activeTab === 'content' && (
        <div className="space-y-6">
          {/* AI文章生成 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4">📝 AI文章生成</h3>
            <p className="text-sm text-gray-500 mb-4">
              输入房产相关话题，AI将为您生成专业的房产分析文章，可用于内容营销。
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">文章话题</label>
                <input
                  type="text"
                  value={articleTopic}
                  onChange={(e) => setArticleTopic(e.target.value)}
                  placeholder="例如：2024年上海房价走势分析"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">文章类型</label>
                <select
                  value={articleCategory}
                  onChange={(e) => setArticleCategory(e.target.value)}
                  className="border border-gray-300 rounded px-3 py-2"
                >
                  <option value="market">市场分析</option>
                  <option value="policy">政策解读</option>
                  <option value="guide">购房指南</option>
                  <option value="investment">投资建议</option>
                </select>
              </div>
              <button
                onClick={generateArticle}
                disabled={generating || !articleTopic.trim()}
                className="bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark disabled:opacity-50"
              >
                {generating ? '生成中...' : '生成文章'}
              </button>
            </div>
          </div>

          {/* 已生成文章列表 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">已生成文章</h3>
              <button
                onClick={() => exportData('articles')}
                className="text-sm text-primary hover:underline"
              >
                导出全部
              </button>
            </div>
            {articles.length > 0 ? (
              <div className="space-y-3">
                {articles.map((article) => (
                  <div key={article.id} className="border rounded p-4">
                    <h4 className="font-medium">{article.title}</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      {new Date(article.created_at).toLocaleDateString('zh-CN')}
                    </p>
                    <div className="flex gap-2 mt-2">
                      <button className="text-sm text-primary hover:underline">查看</button>
                      <button className="text-sm text-gray-500 hover:underline">复制</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">暂无文章，开始生成第一篇吧！</p>
            )}
          </div>
        </div>
      )}

      {/* 专属工具 */}
      {activeTab === 'tools' && (
        <div className="space-y-6">
          {/* 批量分析 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4">🔍 批量房产分析</h3>
            <p className="text-sm text-gray-500 mb-4">
              输入多个房产地址，系统将批量生成分析报告，方便您进行内容创作。
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">房产地址（每行一个）</label>
                <textarea
                  value={batchAddresses}
                  onChange={(e) => setBatchAddresses(e.target.value)}
                  placeholder="上海市浦东新区陆家嘴&#10;北京市朝阳区望京&#10;深圳市南山区科技园"
                  rows={5}
                  className="w-full border border-gray-300 rounded px-3 py-2"
                />
              </div>
              <button
                onClick={runBatchAnalysis}
                disabled={batchAnalyzing || !batchAddresses.trim()}
                className="bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark disabled:opacity-50"
              >
                {batchAnalyzing ? '分析中...' : '开始批量分析'}
              </button>
            </div>

            {batchResults.length > 0 && (
              <div className="mt-6">
                <h4 className="font-medium mb-2">分析结果</h4>
                <div className="space-y-2">
                  {batchResults.map((result, index) => (
                    <div key={index} className="border rounded p-3 bg-gray-50">
                      <p className="font-medium">{result.address}</p>
                      <p className="text-sm text-gray-500">{result.summary || '分析完成'}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 数据导出 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4">📊 数据导出</h3>
            <p className="text-sm text-gray-500 mb-4">
              导出您的推广数据、文章内容或分析报告，用于内容创作和数据分析。
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <button
                onClick={() => exportData('referrals')}
                className="border border-gray-300 rounded p-4 text-center hover:bg-gray-50 transition-colors"
              >
                <span className="text-2xl">👥</span>
                <p className="mt-2 font-medium">推广记录</p>
                <p className="text-xs text-gray-500">导出CSV</p>
              </button>
              <button
                onClick={() => exportData('articles')}
                className="border border-gray-300 rounded p-4 text-center hover:bg-gray-50 transition-colors"
              >
                <span className="text-2xl">📝</span>
                <p className="mt-2 font-medium">文章内容</p>
                <p className="text-xs text-gray-500">导出CSV</p>
              </button>
              <button
                onClick={() => exportData('analysis')}
                className="border border-gray-300 rounded p-4 text-center hover:bg-gray-50 transition-colors"
              >
                <span className="text-2xl">📊</span>
                <p className="mt-2 font-medium">分析报告</p>
                <p className="text-xs text-gray-500">导出CSV</p>
              </button>
            </div>
          </div>

          {/* 快捷工具 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4">⚡ 快捷工具</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <a
                href="/dashboard/property-analysis"
                className="border border-gray-300 rounded p-4 text-center hover:bg-gray-50 transition-colors"
              >
                <span className="text-2xl">🏠</span>
                <p className="mt-2 text-sm font-medium">房产分析</p>
              </a>
              <button className="border border-gray-300 rounded p-4 text-center hover:bg-gray-50 transition-colors">
                <span className="text-2xl">📈</span>
                <p className="mt-2 text-sm font-medium">市场数据</p>
              </button>
              <button className="border border-gray-300 rounded p-4 text-center hover:bg-gray-50 transition-colors">
                <span className="text-2xl">🗺️</span>
                <p className="mt-2 text-sm font-medium">地图标注</p>
              </button>
              <button className="border border-gray-300 rounded p-4 text-center hover:bg-gray-50 transition-colors">
                <span className="text-2xl">📊</span>
                <p className="mt-2 text-sm font-medium">数据图表</p>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IPDashboardPage;
