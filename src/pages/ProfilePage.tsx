import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UserCircleIcon,
  EnvelopeIcon,
  CalendarIcon,
  LockClosedIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { authApi, User, UserStats } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

interface PasswordForm {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

const ProfilePage: React.FC = () => {
  const { user: authUser, logout } = useAuth();
  const navigate = useNavigate();
  
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const [passwordForm, setPasswordForm] = useState<PasswordForm>({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    setIsLoading(true);
    try {
      const [userData, statsData] = await Promise.all([
        authApi.getMe(),
        authApi.getStats(),
      ]);
      setUser(userData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load user data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordForm(prev => ({ ...prev, [name]: value }));
    setPasswordError(null);
    setPasswordSuccess(false);
  };

  const validatePasswordForm = (): boolean => {
    if (!passwordForm.old_password) {
      setPasswordError('请输入旧密码');
      return false;
    }
    if (!passwordForm.new_password) {
      setPasswordError('请输入新密码');
      return false;
    }
    if (passwordForm.new_password.length < 6) {
      setPasswordError('新密码长度至少6位');
      return false;
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('两次输入的新密码不一致');
      return false;
    }
    if (passwordForm.old_password === passwordForm.new_password) {
      setPasswordError('新密码不能与旧密码相同');
      return false;
    }
    return true;
  };

  const handleSubmitPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validatePasswordForm()) return;
    
    setIsChangingPassword(true);
    setPasswordError(null);
    
    try {
      await authApi.changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      });
      
      setPasswordSuccess(true);
      setPasswordForm({
        old_password: '',
        new_password: '',
        confirm_password: '',
      });
      
      setTimeout(() => setPasswordSuccess(false), 3000);
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      setPasswordError(err.response?.data?.detail || '密码修改失败');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <ArrowPathIcon className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">个人资料</h1>
        <p className="text-gray-600 mt-1">管理您的账户信息和安全设置</p>
      </div>

      {/* User Info Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <UserCircleIcon className="w-5 h-5 text-primary-600" />
            账户信息
          </h2>
        </div>
        <div className="p-6">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center">
              <UserCircleIcon className="w-12 h-12 text-primary-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900">
                {user?.full_name || '用户'}
              </h3>
              <div className="mt-2 space-y-1">
                <div className="flex items-center gap-2 text-gray-600">
                  <EnvelopeIcon className="w-4 h-4" />
                  <span>{user?.email}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <CalendarIcon className="w-4 h-4" />
                  <span>注册于 {formatDate(user?.created_at || null)}</span>
                </div>
              </div>
            </div>
            <div className="text-right">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                user?.role === 'admin' 
                  ? 'bg-purple-100 text-purple-700' 
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {user?.role === 'admin' ? '管理员' : '普通用户'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Card */}
      {stats && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <ChartBarIcon className="w-5 h-5 text-primary-600" />
              使用统计
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-gray-900">{stats.total_tasks}</p>
                <p className="text-sm text-gray-500 mt-1">总任务数</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-green-600">{stats.completed_tasks}</p>
                <p className="text-sm text-gray-500 mt-1">已完成</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-blue-600">{stats.running_tasks}</p>
                <p className="text-sm text-gray-500 mt-1">进行中</p>
              </div>
              <div className="bg-red-50 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-red-600">{stats.failed_tasks}</p>
                <p className="text-sm text-gray-500 mt-1">失败</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Password Change Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <LockClosedIcon className="w-5 h-5 text-primary-600" />
            修改密码
          </h2>
        </div>
        <div className="p-6">
          <form onSubmit={handleSubmitPassword} className="space-y-4 max-w-md">
            {/* Success Message */}
            {passwordSuccess && (
              <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
                <CheckCircleIcon className="w-5 h-5" />
                <span>密码修改成功！</span>
              </div>
            )}

            {/* Error Message */}
            {passwordError && (
              <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                <ExclamationCircleIcon className="w-5 h-5" />
                <span>{passwordError}</span>
              </div>
            )}

            <div>
              <label htmlFor="old_password" className="block text-sm font-medium text-gray-700 mb-1">
                旧密码
              </label>
              <input
                type="password"
                id="old_password"
                name="old_password"
                value={passwordForm.old_password}
                onChange={handlePasswordChange}
                placeholder="请输入当前密码"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-1">
                新密码
              </label>
              <input
                type="password"
                id="new_password"
                name="new_password"
                value={passwordForm.new_password}
                onChange={handlePasswordChange}
                placeholder="请输入新密码（至少6位）"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-1">
                确认新密码
              </label>
              <input
                type="password"
                id="confirm_password"
                name="confirm_password"
                value={passwordForm.confirm_password}
                onChange={handlePasswordChange}
                placeholder="请再次输入新密码"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isChangingPassword}
                className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isChangingPassword ? (
                  <>
                    <ArrowPathIcon className="w-4 h-4 animate-spin" />
                    修改中...
                  </>
                ) : (
                  <>
                    <LockClosedIcon className="w-4 h-4" />
                    修改密码
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white rounded-xl shadow-sm border border-red-200 overflow-hidden">
        <div className="p-6 border-b border-red-100">
          <h2 className="text-lg font-semibold text-red-700">危险操作</h2>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-700">退出登录</p>
              <p className="text-sm text-gray-500">退出当前账户，需要重新登录</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
            >
              退出登录
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
