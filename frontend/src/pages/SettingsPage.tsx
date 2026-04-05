import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Modal } from '../components/ui';
import { useUIStore, useUserStore } from '../stores';

interface UserInfo {
  id: string;
  email: string;
  username: string;
  role: string;
  integral: number;
  source: string | null;
  source_name: string | null;
  bonus_label: string | null;
  membership_level: string;
  membership_expires: string | null;
  created_at: string;
  avatar?: string;
}

interface NotificationSettings {
  email_notification: boolean;
  task_complete_notify: boolean;
  marketing_email: boolean;
  report_update_notify: boolean;
}

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { theme, setTheme, mascotEnabled, toggleMascot } = useUIStore();
  const { logout } = useUserStore();

  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [activeSection, setActiveSection] = useState('profile');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [notifications, setNotifications] = useState<NotificationSettings>({
    email_notification: true,
    task_complete_notify: true,
    marketing_email: false,
    report_update_notify: true,
  });

  useEffect(() => {
    fetchUser();
    fetchNotificationSettings();
  }, []);

  const fetchUser = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setFormData(prev => ({
          ...prev,
          username: userData.username || '',
          email: userData.email || '',
        }));
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchNotificationSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/users/me/settings/notifications', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
      }
    } catch (error) {
      console.error('Failed to fetch notification settings:', error);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleNotificationChange = (key: keyof NotificationSettings) => {
    setNotifications(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          username: formData.username,
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: '个人资料已更新' });
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '更新失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误，请稍后重试' });
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (formData.newPassword !== formData.confirmPassword) {
      setMessage({ type: 'error', text: '两次输入的密码不一致' });
      return;
    }

    if (formData.newPassword.length < 6) {
      setMessage({ type: 'error', text: '密码长度至少6位' });
      return;
    }

    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/auth/password', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_password: formData.currentPassword,
          new_password: formData.newPassword,
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: '密码已更新' });
        setFormData(prev => ({
          ...prev,
          currentPassword: '',
          newPassword: '',
          confirmPassword: '',
        }));
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '密码修改失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误，请稍后重试' });
    } finally {
      setSaving(false);
    }
  };

  const handleSaveNotifications = async () => {
    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/users/me/settings/notifications', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(notifications),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: '通知设置已保存' });
      } else {
        setMessage({ type: 'error', text: '保存失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误，请稍后重试' });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== '删除账户') {
      return;
    }

    setSaving(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/auth/account', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        logout();
        navigate('/');
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || '删除失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误，请稍后重试' });
    } finally {
      setSaving(false);
      setShowDeleteModal(false);
    }
  };

  const sections = [
    { id: 'profile', label: '个人资料', icon: '👤' },
    { id: 'security', label: '账户安全', icon: '🔒' },
    { id: 'notifications', label: '通知设置', icon: '🔔' },
    { id: 'appearance', label: '外观设置', icon: '🎨' },
    { id: 'danger', label: '危险操作', icon: '⚠️' },
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">账户设置</h1>

      {message.text && (
        <div className={`mb-4 p-4 rounded ${
          message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          {message.text}
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-6">
        {/* Sidebar */}
        <div className="md:w-48 flex-shrink-0">
          <nav className="bg-white rounded-lg shadow overflow-hidden">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full px-4 py-3 text-left flex items-center gap-3 transition-colors ${
                  activeSection === section.id
                    ? 'bg-primary text-white'
                    : 'hover:bg-gray-50'
                }`}
              >
                <span>{section.icon}</span>
                <span className="text-sm">{section.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          {/* Profile Section */}
          {activeSection === 'profile' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-medium mb-6">个人资料</h2>

              {/* Avatar */}
              <div className="flex items-center gap-4 mb-6">
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center text-3xl">
                  {user?.avatar ? (
                    <img src={user.avatar} alt="Avatar" className="w-full h-full rounded-full object-cover" />
                  ) : (
                    user?.username?.charAt(0).toUpperCase() || 'U'
                  )}
                </div>
                <div>
                  <Button variant="outline" size="sm">更换头像</Button>
                  <p className="text-xs text-gray-500 mt-1">支持 JPG、PNG，最大 2MB</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    用户名
                  </label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    邮箱
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    disabled
                    className="w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50 text-gray-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">邮箱不可修改</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      会员等级
                    </label>
                    <div className="bg-purple-50 text-purple-700 px-3 py-2 rounded inline-block">
                      {user?.membership_level || '免费用户'}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      积分余额
                    </label>
                    <div className="bg-primary/10 text-primary px-3 py-2 rounded inline-block">
                      {user?.integral || 0} 积分
                    </div>
                  </div>
                </div>

                {user?.membership_expires && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      会员到期时间
                    </label>
                    <p className="text-gray-600">
                      {new Date(user.membership_expires).toLocaleDateString('zh-CN')}
                    </p>
                  </div>
                )}

                <div className="pt-4">
                  <Button onClick={handleSaveProfile} loading={saving}>
                    保存资料
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Security Section */}
          {activeSection === 'security' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-medium mb-6">修改密码</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    当前密码
                  </label>
                  <input
                    type="password"
                    name="currentPassword"
                    value={formData.currentPassword}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    新密码
                  </label>
                  <input
                    type="password"
                    name="newPassword"
                    value={formData.newPassword}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                  <p className="text-xs text-gray-500 mt-1">密码长度至少6位</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    确认新密码
                  </label>
                  <input
                    type="password"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>

                <div className="pt-4">
                  <Button
                    onClick={handleChangePassword}
                    loading={saving}
                    disabled={!formData.currentPassword || !formData.newPassword}
                  >
                    修改密码
                  </Button>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t">
                <h3 className="text-md font-medium mb-4">登录设备</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">💻</span>
                      <div>
                        <p className="font-medium">当前设备</p>
                        <p className="text-xs text-gray-500">Windows · Chrome</p>
                      </div>
                    </div>
                    <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">当前</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Notifications Section */}
          {activeSection === 'notifications' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-medium mb-6">通知设置</h2>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">邮件通知</p>
                    <p className="text-sm text-gray-500">接收重要通知的邮件提醒</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.email_notification}
                      onChange={() => handleNotificationChange('email_notification')}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">任务完成通知</p>
                    <p className="text-sm text-gray-500">房产分析完成后发送通知</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.task_complete_notify}
                      onChange={() => handleNotificationChange('task_complete_notify')}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">报告更新通知</p>
                    <p className="text-sm text-gray-500">报告有更新时发送通知</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.report_update_notify}
                      onChange={() => handleNotificationChange('report_update_notify')}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">营销邮件</p>
                    <p className="text-sm text-gray-500">接收优惠活动和新功能介绍</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.marketing_email}
                      onChange={() => handleNotificationChange('marketing_email')}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                <div className="pt-4">
                  <Button onClick={handleSaveNotifications} loading={saving}>
                    保存设置
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Appearance Section */}
          {activeSection === 'appearance' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-medium mb-6">外观设置</h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    主题模式
                  </label>
                  <div className="flex gap-4">
                    <button
                      onClick={() => setTheme('light')}
                      className={`flex-1 p-4 border-2 rounded-lg transition-colors ${
                        theme === 'light' ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <span className="text-2xl block mb-2">☀️</span>
                      <span className="text-sm">浅色模式</span>
                    </button>
                    <button
                      onClick={() => setTheme('dark')}
                      className={`flex-1 p-4 border-2 rounded-lg transition-colors ${
                        theme === 'dark' ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <span className="text-2xl block mb-2">🌙</span>
                      <span className="text-sm">深色模式</span>
                    </button>
                    <button
                      onClick={() => setTheme('system')}
                      className={`flex-1 p-4 border-2 rounded-lg transition-colors ${
                        theme === 'system' ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <span className="text-2xl block mb-2">💻</span>
                      <span className="text-sm">跟随系统</span>
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">显示吉祥物</p>
                    <p className="text-sm text-gray-500">在页面右下角显示可爱的吉祥物</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={mascotEnabled}
                      onChange={toggleMascot}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Danger Zone */}
          {activeSection === 'danger' && (
            <div className="bg-white rounded-lg shadow p-6 border-2 border-red-200">
              <h2 className="text-lg font-medium mb-6 text-red-600">危险操作</h2>

              <div className="space-y-6">
                <div className="p-4 bg-red-50 rounded-lg">
                  <h3 className="font-medium text-red-700 mb-2">删除账户</h3>
                  <p className="text-sm text-red-600 mb-4">
                    删除账户将永久移除您的所有数据，包括分析报告、积分记录等。此操作不可撤销。
                  </p>
                  <Button
                    variant="outline"
                    className="border-red-500 text-red-500 hover:bg-red-50"
                    onClick={() => setShowDeleteModal(true)}
                  >
                    删除我的账户
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Delete Account Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="确认删除账户"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            您确定要删除账户吗？此操作将永久删除您的所有数据，且不可恢复。
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              请输入 <span className="font-bold">删除账户</span> 以确认
            </label>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500/50"
              placeholder="删除账户"
            />
          </div>
          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
              取消
            </Button>
            <Button
              className="bg-red-500 hover:bg-red-600"
              onClick={handleDeleteAccount}
              loading={saving}
              disabled={deleteConfirmText !== '删除账户'}
            >
              确认删除
            </Button>
          </div>
        </div>
      </Modal>

      {user?.created_at && (
        <p className="text-sm text-gray-500 mt-6 text-center">
          注册时间: {new Date(user.created_at).toLocaleDateString('zh-CN')}
        </p>
      )}
    </div>
  );
};

export default SettingsPage;
