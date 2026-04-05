import React, { useState, useEffect } from 'react';
import api from '../../services/api';

interface VersionSummary {
  id: string;
  version: string;
  title: string;
  effective_date: string;
  is_current: number;
  created_at?: string;
  agreement_count: number;
}

interface Stats {
  total_users: number;
  agreed_users: number;
  pending_users: number;
  latest_version: string | null;
  version_distribution: { version: string; count: number }[];
}

export default function AdminPrivacyPage() {
  const [versions, setVersions] = useState<VersionSummary[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newVersion, setNewVersion] = useState({
    version: '',
    title: '',
    content: '',
    effective_date: new Date().toISOString().split('T')[0]
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [versionsRes, statsRes] = await Promise.all([
        api.get('/api/admin/privacy/versions'),
        api.get('/api/admin/privacy/stats')
      ]);
      setVersions(versionsRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVersion = async () => {
    if (!newVersion.version || !newVersion.title || !newVersion.content) {
      alert('请填写所有必填字段');
      return;
    }

    setSaving(true);
    try {
      await api.post('/api/admin/privacy/versions', newVersion);
      setShowCreateModal(false);
      setNewVersion({
        version: '',
        title: '',
        content: '',
        effective_date: new Date().toISOString().split('T')[0]
      });
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '创建失败');
    } finally {
      setSaving(false);
    }
  };

  const handleActivate = async (versionId: string) => {
    if (!confirm('确定要激活此版本吗？激活后用户需要重新同意隐私政策。')) {
      return;
    }

    try {
      await api.put(`/api/admin/privacy/versions/${versionId}/activate`);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '激活失败');
    }
  };

  const handleDelete = async (versionId: string) => {
    if (!confirm('确定要删除此版本吗？此操作不可恢复。')) {
      return;
    }

    try {
      await api.delete(`/api/admin/privacy/versions/${versionId}`);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '删除失败');
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">隐私政策管理</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          发布新版本
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">总用户数</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_users}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">已同意用户</div>
            <div className="text-2xl font-bold text-green-600">{stats.agreed_users}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">待同意用户</div>
            <div className="text-2xl font-bold text-orange-600">{stats.pending_users}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">当前版本</div>
            <div className="text-2xl font-bold text-blue-600">{stats.latest_version || '-'}</div>
          </div>
        </div>
      )}

      {stats && stats.version_distribution.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <h3 className="text-lg font-semibold mb-4">版本分布</h3>
          <div className="space-y-2">
            {stats.version_distribution.map((item) => (
              <div key={item.version} className="flex items-center gap-2">
                <div className="w-24 text-sm text-gray-600">{item.version || '未同意'}</div>
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-blue-500 h-4 rounded-full"
                    style={{ width: `${(item.count / stats.total_users) * 100}%` }}
                  />
                </div>
                <div className="w-16 text-sm text-gray-600 text-right">{item.count}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">版本</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">标题</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">生效日期</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">状态</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">同意人数</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {versions.map((v) => (
              <tr key={v.id}>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{v.version}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{v.title}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{v.effective_date}</td>
                <td className="px-4 py-3">
                  {v.is_current === 1 ? (
                    <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">当前版本</span>
                  ) : (
                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">历史版本</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">{v.agreement_count}</td>
                <td className="px-4 py-3 text-sm">
                  {v.is_current !== 1 && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleActivate(v.id)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        激活
                      </button>
                      <button
                        onClick={() => handleDelete(v.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        删除
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold">发布新隐私政策版本</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  版本号 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newVersion.version}
                  onChange={(e) => setNewVersion({ ...newVersion, version: e.target.value })}
                  placeholder="例如: 2.0"
                  className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  标题 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newVersion.title}
                  onChange={(e) => setNewVersion({ ...newVersion, title: e.target.value })}
                  placeholder="例如: 用户隐私政策"
                  className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  生效日期 <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={newVersion.effective_date}
                  onChange={(e) => setNewVersion({ ...newVersion, effective_date: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  政策内容 (Markdown格式) <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={newVersion.content}
                  onChange={(e) => setNewVersion({ ...newVersion, content: e.target.value })}
                  rows={15}
                  placeholder="# 用户隐私政策&#10;&#10;## 1. 引言&#10;..."
                  className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
              </div>
            </div>
            <div className="p-4 border-t flex justify-end gap-2">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition"
              >
                取消
              </button>
              <button
                onClick={handleCreateVersion}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
              >
                {saving ? '创建中...' : '创建版本'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
