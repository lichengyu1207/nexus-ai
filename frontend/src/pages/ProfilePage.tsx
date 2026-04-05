import React, { useState, useEffect } from 'react';

interface UserInfo {
  id: string;
  email: string;
  username: string;
  avatar_url: string;
  phone: string;
  role: string;
  integral: number;
  membership_level: string;
  membership_expires: string | null;
  source: string;
  source_name: string;
  created_at: string;
}

const ProfilePage: React.FC = () => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [message, setMessage] = useState({ type: '', text: '' });

  const [profileForm, setProfileForm] = useState({
    username: '',
    phone: '',
  });

  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  useEffect(() => {
    fetchUser();
  }, []);

  const fetchUser = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setProfileForm({
          username: data.username || '',
          phone: data.phone || '',
        });
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profileForm),
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setMessage({ type: 'success', text: '个人资料已更新' });
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '更新失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误' });
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setMessage({ type: 'error', text: '两次输入的密码不一致' });
      return;
    }

    if (passwordForm.newPassword.length < 6) {
      setMessage({ type: 'error', text: '密码长度至少6位' });
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/auth/password', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword,
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: '密码已更新' });
        setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '密码修改失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误' });
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('avatar', file);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/auth/avatar', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setUser(prev => prev ? { ...prev, avatar_url: data.avatar_url } : null);
        setMessage({ type: 'success', text: '头像已更新' });
      } else {
        setMessage({ type: 'error', text: '头像上传失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误' });
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">个人中心</h1>

      {message.text && (
        <div className={`mb-4 p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          {message.text}
        </div>
      )}

      <div className="flex gap-2 mb-6">
        {['profile', 'security'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg ${
              activeTab === tab
                ? 'bg-primary text-white'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            {tab === 'profile' ? '个人资料' : '账户安全'}
          </button>
        ))}
      </div>

      {activeTab === 'profile' && user && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-6 mb-6">
            <div className="relative">
              <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center text-4xl overflow-hidden">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" />
                ) : (
                  user.username?.charAt(0).toUpperCase() || 'U'
                )}
              </div>
              <label className="absolute bottom-0 right-0 w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center cursor-pointer hover:bg-primaryDark">
                📷
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="hidden"
                />
              </label>
            </div>
            <div>
              <h2 className="text-xl font-medium">{user.username || '用户'}</h2>
              <p className="text-gray-500">{user.email}</p>
              <div className="flex gap-2 mt-2">
                <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs">
                  {user.membership_level || '免费用户'}
                </span>
                <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                  {user.integral} 积分
                </span>
              </div>
            </div>
          </div>

          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
              <input
                type="text"
                value={profileForm.username}
                onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
                className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
              <input
                type="email"
                value={user.email}
                disabled
                className="w-full border rounded-lg px-4 py-2 bg-gray-50 text-gray-500"
              />
              <p className="text-xs text-gray-500 mt-1">邮箱不可修改</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">手机号</label>
              <input
                type="tel"
                value={profileForm.phone}
                onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="可选"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">注册来源</label>
              <div className="bg-gray-50 rounded-lg px-4 py-2 text-gray-600">
                {user.source_name || user.source || '直接访问'}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">注册时间</label>
              <div className="bg-gray-50 rounded-lg px-4 py-2 text-gray-600">
                {new Date(user.created_at).toLocaleString('zh-CN')}
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="w-full bg-primary text-white py-3 rounded-lg hover:bg-primaryDark disabled:opacity-50"
            >
              {saving ? '保存中...' : '保存资料'}
            </button>
          </form>
        </div>
      )}

      {activeTab === 'security' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">修改密码</h2>
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">当前密码</label>
              <input
                type="password"
                value={passwordForm.currentPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">新密码</label>
              <input
                type="password"
                value={passwordForm.newPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="至少6位"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">确认新密码</label>
              <input
                type="password"
                value={passwordForm.confirmPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
                required
              />
            </div>

            <button
              type="submit"
              disabled={saving}
              className="w-full bg-primary text-white py-3 rounded-lg hover:bg-primaryDark disabled:opacity-50"
            >
              {saving ? '修改中...' : '修改密码'}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t">
            <h3 className="text-lg font-medium mb-4 text-red-600">危险操作</h3>
            <button
              onClick={() => {
                if (confirm('确定要注销账户吗？此操作不可撤销！')) {
                  // 账户注销逻辑
                }
              }}
              className="border border-red-500 text-red-500 px-4 py-2 rounded-lg hover:bg-red-50"
            >
              注销账户
            </button>
            <p className="text-sm text-gray-500 mt-2">
              注销账户将删除所有数据，此操作不可撤销
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
