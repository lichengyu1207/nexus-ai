import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const IPApplyPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    contact: '',
    platform: '',
    platform_id: '',
    followers: '',
    content_type: '',
    introduction: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/ip/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        alert('申请提交成功，请等待审核');
        navigate('/dashboard');
      } else {
        const error = await response.json();
        alert(error.detail || '申请提交失败');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-6">IP达人申请</h1>
        <p className="text-gray-500 mb-6">成为IP达人，享受专属权益和收益分成</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">真实姓名</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">联系方式</label>
            <input
              type="text"
              required
              value={formData.contact}
              onChange={(e) => setFormData({ ...formData, contact: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="手机号或微信号"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">平台</label>
            <select
              required
              value={formData.platform}
              onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="">请选择平台</option>
              <option value="抖音">抖音</option>
              <option value="小红书">小红书</option>
              <option value="B站">B站</option>
              <option value="微博">微博</option>
              <option value="微信公众号">微信公众号</option>
              <option value="其他">其他</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">平台账号ID</label>
            <input
              type="text"
              required
              value={formData.platform_id}
              onChange={(e) => setFormData({ ...formData, platform_id: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">粉丝数量</label>
            <input
              type="number"
              required
              value={formData.followers}
              onChange={(e) => setFormData({ ...formData, followers: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">内容类型</label>
            <input
              type="text"
              value={formData.content_type}
              onChange={(e) => setFormData({ ...formData, content_type: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
              placeholder="如：房产、财经、生活等"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">自我介绍</label>
            <textarea
              value={formData.introduction}
              onChange={(e) => setFormData({ ...formData, introduction: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 h-24 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-white py-3 rounded-lg hover:bg-primaryDark disabled:opacity-50"
          >
            {loading ? '提交中...' : '提交申请'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default IPApplyPage;
