import React, { useState, useEffect } from 'react';

interface Emotion {
  id: string;
  name: string;
  emoji: string;
  image_url: string;
  description: string;
  created_at: string;
}

interface Quote {
  id: string;
  text: string;
  emotion: string;
  category: string;
  active: boolean;
  click_count: number;
  created_at: string;
}

interface MascotStats {
  total_clicks: number;
  total_interactions: number;
  top_quotes: { text: string; count: number }[];
  emotion_distribution: { emotion: string; count: number }[];
}

const emotionOptions = ['happy', 'thinking', 'excited', 'confused', 'sleepy', 'wink'];
const categoryOptions = ['general', 'greeting', 'analysis', 'help', 'source'];

const emotionLabels: Record<string, string> = {
  happy: '开心',
  thinking: '思考',
  excited: '兴奋',
  confused: '困惑',
  sleepy: '困倦',
  wink: '眨眼',
};

const categoryLabels: Record<string, string> = {
  general: '通用',
  greeting: '问候',
  analysis: '分析',
  help: '帮助',
  source: '来源专属',
};

const AdminMascotPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('stats');
  const [emotions, setEmotions] = useState<Emotion[]>([]);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [stats, setStats] = useState<MascotStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<Quote | null>(null);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    text: '',
    emotion: 'happy',
    category: 'general',
    active: true,
  });

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      if (activeTab === 'stats') {
        const res = await fetch('http://localhost:8000/api/admin/mascot/stats', { headers });
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } else if (activeTab === 'emotions') {
        const res = await fetch('http://localhost:8000/api/admin/mascot/emotions', { headers });
        if (res.ok) {
          const data = await res.json();
          setEmotions(data.emotions || []);
        }
      } else if (activeTab === 'quotes') {
        const res = await fetch('http://localhost:8000/api/admin/mascot/quotes', { headers });
        if (res.ok) {
          const data = await res.json();
          setQuotes(data.quotes || []);
        }
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveQuote = async () => {
    if (!formData.text.trim()) {
      alert('请输入语录内容');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const url = editingItem
        ? `http://localhost:8000/api/admin/mascot/quotes/${editingItem.id}`
        : 'http://localhost:8000/api/admin/mascot/quotes';
      const method = editingItem ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setShowModal(false);
        setEditingItem(null);
        setFormData({ text: '', emotion: 'happy', category: 'general', active: true });
        fetchData();
      } else {
        const error = await response.json();
        alert(error.detail || '保存失败');
      }
    } catch (error) {
      console.error('Failed to save:', error);
      alert('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteQuote = async (id: string) => {
    if (!confirm('确定要删除此语录吗？')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/mascot/quotes/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        fetchData();
      } else {
        alert('删除失败');
      }
    } catch (error) {
      console.error('Failed to delete:', error);
      alert('删除失败');
    }
  };

  const handleToggleQuote = async (id: string, active: boolean) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/mascot/quotes/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ active }),
      });

      if (response.ok) {
        fetchData();
      }
    } catch (error) {
      console.error('Failed to toggle:', error);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">吉祥物管理</h1>
        {activeTab === 'quotes' && (
          <button
            onClick={() => {
              setEditingItem(null);
              setFormData({ text: '', emotion: 'happy', category: 'general', active: true });
              setShowModal(true);
            }}
            className="bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark"
          >
            添加语录
          </button>
        )}
      </div>

      <div className="flex gap-2 mb-6">
        {[
          { key: 'stats', label: '互动统计' },
          { key: 'emotions', label: '表情管理' },
          { key: 'quotes', label: '语录管理' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded ${
              activeTab === tab.key ? 'bg-primary text-white' : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-10">加载中...</div>
      ) : (
        <>
          {activeTab === 'stats' && stats && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="text-sm text-gray-500">总点击次数</div>
                  <div className="text-3xl font-bold text-primary">{stats.total_clicks}</div>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="text-sm text-gray-500">总互动次数</div>
                  <div className="text-3xl font-bold text-green-600">{stats.total_interactions}</div>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="text-sm text-gray-500">语录总数</div>
                  <div className="text-3xl font-bold text-blue-600">{quotes.length || 0}</div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium mb-4">热门语录 TOP 10</h3>
                  <div className="space-y-3">
                    {stats.top_quotes.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                        <div className="flex items-center gap-3">
                          <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                            index < 3 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-200 text-gray-600'
                          }`}>
                            {index + 1}
                          </span>
                          <span className="text-sm truncate max-w-xs">{item.text}</span>
                        </div>
                        <span className="text-sm font-medium">{item.count} 次</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium mb-4">表情使用分布</h3>
                  <div className="space-y-3">
                    {stats.emotion_distribution.map((item) => (
                      <div key={item.emotion} className="flex items-center justify-between">
                        <span>{emotionLabels[item.emotion] || item.emotion}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary rounded-full h-2"
                              style={{
                                width: `${(item.count / Math.max(...stats.emotion_distribution.map(e => e.count))) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-sm text-gray-500">{item.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'emotions' && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">表情</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">名称</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">描述</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {emotions.map((emotion) => (
                    <tr key={emotion.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-3xl">
                        {emotion.emoji}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {emotionLabels[emotion.name] || emotion.name}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {emotion.description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(emotion.created_at).toLocaleDateString('zh-CN')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'quotes' && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">语录</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">表情</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">分类</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">点击次数</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {quotes.map((quote) => (
                    <tr key={quote.id}>
                      <td className="px-6 py-4 text-sm max-w-md">
                        {quote.text}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                          {emotionLabels[quote.emotion] || quote.emotion}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {categoryLabels[quote.category] || quote.category}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {quote.click_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleToggleQuote(quote.id, !quote.active)}
                          className={`px-2 py-1 rounded text-xs ${
                            quote.active
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-500'
                          }`}
                        >
                          {quote.active ? '启用' : '禁用'}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => {
                            setEditingItem(quote);
                            setFormData({
                              text: quote.text,
                              emotion: quote.emotion,
                              category: quote.category,
                              active: quote.active,
                            });
                            setShowModal(true);
                          }}
                          className="text-primary hover:underline mr-3"
                        >
                          编辑
                        </button>
                        <button
                          onClick={() => handleDeleteQuote(quote.id)}
                          className="text-red-600 hover:underline"
                        >
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">
              {editingItem ? '编辑语录' : '添加语录'}
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">语录内容</label>
                <textarea
                  value={formData.text}
                  onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  rows={3}
                  placeholder="输入吉祥物要说的内容..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">关联表情</label>
                <select
                  value={formData.emotion}
                  onChange={(e) => setFormData({ ...formData, emotion: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                >
                  {emotionOptions.map((emotion) => (
                    <option key={emotion} value={emotion}>
                      {emotionLabels[emotion]}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                >
                  {categoryOptions.map((category) => (
                    <option key={category} value={category}>
                      {categoryLabels[category]}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="active"
                  checked={formData.active}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                  className="h-4 w-4 text-primary border-gray-300 rounded"
                />
                <label htmlFor="active" className="ml-2 text-sm text-gray-700">
                  启用此语录
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowModal(false);
                  setEditingItem(null);
                }}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleSaveQuote}
                disabled={saving}
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primaryDark disabled:opacity-50"
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminMascotPage;
