import React, { useState } from 'react';

const platforms = [
  { value: 'wechat', label: '微信公众号' },
  { value: 'zhihu', label: '知乎' },
  { value: 'bilibili', label: 'B站' },
  { value: 'douyin', label: '抖音' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'weibo', label: '微博' },
  { value: 'other', label: '其他' },
];

const IPApplyPage: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    contact: '',
    platform: '',
    platform_id: '',
    followers: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [field]: e.target.value });
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/api/ip/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          ...formData,
          followers: parseInt(formData.followers) || 0,
        }),
      });
      
      const data = await res.json();
      if (data.success) {
        setSuccess(true);
      } else {
        setError(data.message || '申请失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || '申请失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="p-6 max-w-xl mx-auto">
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="text-4xl mb-4">✅</div>
          <h2 className="text-xl font-medium text-green-600 mb-2">申请已提交</h2>
          <p className="text-gray-500">
            我们将在1-3个工作日内审核您的申请，审核结果将通过您填写的联系方式通知您。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">房产IP扶持计划</h1>
      <p className="text-gray-500 mb-6">
        成为我们的合作伙伴，享受专属权益，获取佣金收益
      </p>

      <div className="bg-white rounded-lg shadow p-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              姓名/昵称 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={handleChange('name')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              联系方式（微信/手机） <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.contact}
              onChange={handleChange('contact')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              主要平台 <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.platform}
              onChange={handleChange('platform')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            >
              <option value="">请选择平台</option>
              {platforms.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              平台账号ID/名称 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.platform_id}
              onChange={handleChange('platform_id')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              粉丝数（约数） <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={formData.followers}
              onChange={handleChange('followers')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading || !formData.name || !formData.contact || !formData.platform}
            className="w-full bg-primary text-white py-3 rounded-md hover:bg-primaryDark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
                提交中...
              </span>
            ) : '提交申请'}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mt-6">
        <h3 className="text-lg font-medium mb-3">IP权益</h3>
        <ul className="text-sm text-gray-600 space-y-2">
          <li>• 专属推广链接，追踪用户来源</li>
          <li>• 用户付费后获得佣金分成</li>
          <li>• 快速分析工具，批量生成报告</li>
          <li>• 数据导出功能，便于内容创作</li>
          <li>• AI文章生成，提升创作效率</li>
        </ul>
      </div>
    </div>
  );
};

export default IPApplyPage;
