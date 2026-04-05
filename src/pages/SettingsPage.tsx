import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UserIcon,
  HomeIcon,
  ShieldCheckIcon,
  BellIcon,
  SunIcon,
  MoonIcon,
  ComputerDesktopIcon,
  CheckIcon,
  ClipboardDocumentListIcon,
  ChevronRightIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import AvatarUploader from '@/components/AvatarUploader';
import Mascot from '@/components/mascot/Mascot';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useMascot } from '@/contexts/MascotContext';
import api from '@/services/api';
import showToast from '@/utils/toast';

type TabType = 'profile' | 'housing' | 'security' | 'notifications' | 'appearance' | 'mascot';

interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  theme: string;
  language: string;
  notification_preferences: Record<string, boolean>;
}

interface Preferences {
  theme: string;
  language: string;
  notification_preferences: Record<string, boolean>;
}

const SettingsPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('profile');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    username: '',
  });
  
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  
  const [preferences, setPreferences] = useState<Preferences>({
    theme: 'system',
    language: 'zh',
    notification_preferences: {
      email_report_completed: true,
      email_comment_mention: true,
      email_comment_reply: true,
      push_report_completed: true,
      push_comment_mention: true,
      push_comment_reply: true,
    },
  });

  const [housingProfile, setHousingProfile] = useState({
    age: '',
    gender: '',
    occupation: '',
    monthly_income: '',
    family_structure: '',
    has_children: false,
    current_city: '',
    current_district: '',
    work_city: '',
    work_district: '',
    commute_preference: '',
    house_type_preference: '',
    budget_min: '',
    budget_max: '',
    down_payment: '',
    loan_need: false,
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const [profileRes, prefsRes, housingRes] = await Promise.all([
        api.get('/users/me'),
        api.get('/users/me/preferences'),
        api.get('/consult/profile').catch(() => ({ data: { profile: null } })),
      ]);
      
      setProfile(profileRes.data);
      setProfileForm({
        full_name: profileRes.data.full_name || '',
        username: profileRes.data.username || '',
      });
      
      setPreferences({
        theme: prefsRes.data.theme || 'system',
        language: prefsRes.data.language || 'zh',
        notification_preferences: prefsRes.data.notification_preferences || preferences.notification_preferences,
      });

      if (housingRes.data.profile) {
        const hp = housingRes.data.profile;
        setHousingProfile({
          age: hp.age?.toString() || '',
          gender: hp.gender || '',
          occupation: hp.occupation || '',
          monthly_income: hp.monthly_income?.toString() || '',
          family_structure: hp.family_structure || '',
          has_children: hp.has_children || false,
          current_city: hp.current_city || '',
          current_district: hp.current_district || '',
          work_city: hp.work_city || '',
          work_district: hp.work_district || '',
          commute_preference: hp.commute_preference || '',
          house_type_preference: hp.house_type_preference || '',
          budget_min: hp.budget_min?.toString() || '',
          budget_max: hp.budget_max?.toString() || '',
          down_payment: hp.down_payment?.toString() || '',
          loan_need: hp.loan_need || false,
        });
      }
    } catch {
      showToast.error('加载设置失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProfileSave = async () => {
    setIsSaving(true);
    try {
      await api.put('/users/me', profileForm);
      showToast.success('资料已更新');
      await refreshUser?.();
      loadSettings();
    } catch {
      showToast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      showToast.error('两次输入的密码不一致');
      return;
    }
    
    if (passwordForm.new_password.length < 6) {
      showToast.error('密码长度至少6位');
      return;
    }
    
    setIsSaving(true);
    try {
      await api.put('/users/me/password', {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      showToast.success('密码已更新');
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch {
      showToast.error('密码更新失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handlePreferencesSave = async () => {
    setIsSaving(true);
    try {
      await api.put('/users/me/preferences', preferences);
      setTheme(preferences.theme as 'light' | 'dark' | 'system');
      showToast.success('偏好设置已更新');
    } catch {
      showToast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarChange = (avatarUrl: string) => {
    setProfile(prev => prev ? { ...prev, avatar_url: avatarUrl } : null);
    refreshUser?.();
  };

  const tabs = [
    { id: 'profile' as TabType, label: '个人资料', icon: UserIcon },
    { id: 'housing' as TabType, label: '购房画像', icon: HomeIcon },
    { id: 'security' as TabType, label: '账号安全', icon: ShieldCheckIcon },
    { id: 'notifications' as TabType, label: '通知设置', icon: BellIcon },
    { id: 'appearance' as TabType, label: '外观', icon: SunIcon },
    { id: 'mascot' as TabType, label: '吉祥物', icon: SparklesIcon },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">设置</h1>
      
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="flex flex-col md:flex-row">
          {/* Sidebar */}
          <div className="md:w-48 border-b md:border-b-0 md:border-r border-gray-100 dark:border-gray-700">
            <nav className="p-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
                    transition-colors text-left
                    ${activeTab === tab.id
                      ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }
                  `}
                >
                  <tab.icon className="w-5 h-5" />
                  {tab.label}
                </button>
              ))}
              
              <div className="border-t border-gray-100 dark:border-gray-700 my-2" />
              
              <button
                onClick={() => navigate('/settings/audit-logs')}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <ClipboardDocumentListIcon className="w-5 h-5" />
                  操作日志
                </div>
                <ChevronRightIcon className="w-4 h-4" />
              </button>
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">个人资料</h2>
                
                <div className="flex items-center gap-6">
                  <AvatarUploader
                    currentAvatar={profile?.avatar_url}
                    onAvatarChange={handleAvatarChange}
                    size="lg"
                  />
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      点击更换头像
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      支持 JPG、PNG，最大 5MB
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      用户名
                    </label>
                    <input
                      type="text"
                      value={profileForm.username}
                      onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      显示名称
                    </label>
                    <input
                      type="text"
                      value={profileForm.full_name}
                      onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      邮箱
                    </label>
                    <input
                      type="email"
                      value={profile?.email || ''}
                      disabled
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400"
                    />
                    <p className="text-xs text-gray-400 mt-1">邮箱不可修改</p>
                  </div>

                  <button
                    onClick={handleProfileSave}
                    disabled={isSaving}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {isSaving ? '保存中...' : '保存更改'}
                  </button>
                </div>
              </div>
            )}

            {/* Housing Profile Tab */}
            {activeTab === 'housing' && (
              <HousingProfileTab
                profile={housingProfile}
                setProfile={setHousingProfile}
                isSaving={isSaving}
                setIsSaving={setIsSaving}
              />
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">修改密码</h2>
                
                <div className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      当前密码
                    </label>
                    <input
                      type="password"
                      value={passwordForm.current_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      新密码
                    </label>
                    <input
                      type="password"
                      value={passwordForm.new_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      确认新密码
                    </label>
                    <input
                      type="password"
                      value={passwordForm.confirm_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    />
                  </div>

                  <button
                    onClick={handlePasswordChange}
                    disabled={isSaving || !passwordForm.current_password || !passwordForm.new_password}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {isSaving ? '更新中...' : '更新密码'}
                  </button>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">通知设置</h2>
                
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">邮件通知</h3>
                    <div className="space-y-3">
                      {[
                        { key: 'email_report_completed', label: '报告生成完成' },
                        { key: 'email_comment_mention', label: '评论中@提及' },
                        { key: 'email_comment_reply', label: '评论回复' },
                      ].map((item) => (
                        <label key={item.key} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">{item.label}</span>
                          <button
                            onClick={() => setPreferences({
                              ...preferences,
                              notification_preferences: {
                                ...preferences.notification_preferences,
                                [item.key]: !preferences.notification_preferences[item.key],
                              },
                            })}
                            className={`
                              relative w-11 h-6 rounded-full transition-colors
                              ${preferences.notification_preferences[item.key] ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'}
                            `}
                          >
                            <span
                              className={`
                                absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform
                                ${preferences.notification_preferences[item.key] ? 'translate-x-5' : ''}
                              `}
                            />
                          </button>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">站内通知</h3>
                    <div className="space-y-3">
                      {[
                        { key: 'push_report_completed', label: '报告生成完成' },
                        { key: 'push_comment_mention', label: '评论中@提及' },
                        { key: 'push_comment_reply', label: '评论回复' },
                      ].map((item) => (
                        <label key={item.key} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">{item.label}</span>
                          <button
                            onClick={() => setPreferences({
                              ...preferences,
                              notification_preferences: {
                                ...preferences.notification_preferences,
                                [item.key]: !preferences.notification_preferences[item.key],
                              },
                            })}
                            className={`
                              relative w-11 h-6 rounded-full transition-colors
                              ${preferences.notification_preferences[item.key] ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'}
                            `}
                          >
                            <span
                              className={`
                                absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform
                                ${preferences.notification_preferences[item.key] ? 'translate-x-5' : ''}
                              `}
                            />
                          </button>
                        </label>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={handlePreferencesSave}
                    disabled={isSaving}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {isSaving ? '保存中...' : '保存设置'}
                  </button>
                </div>
              </div>
            )}

            {/* Appearance Tab */}
            {activeTab === 'appearance' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">外观设置</h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      主题
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: 'light', label: '浅色', icon: SunIcon },
                        { value: 'dark', label: '深色', icon: MoonIcon },
                        { value: 'system', label: '跟随系统', icon: ComputerDesktopIcon },
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => {
                            setPreferences({ ...preferences, theme: option.value });
                            setTheme(option.value as 'light' | 'dark' | 'system');
                          }}
                          className={`
                            flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors
                            ${preferences.theme === option.value
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                              : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                            }
                          `}
                        >
                          <option.icon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{option.label}</span>
                          {preferences.theme === option.value && (
                            <CheckIcon className="w-4 h-4 text-primary-600" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      语言
                    </label>
                    <select
                      value={preferences.language}
                      onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
                      className="w-full max-w-xs px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="zh">简体中文</option>
                      <option value="en">English</option>
                    </select>
                  </div>

                  <button
                    onClick={handlePreferencesSave}
                    disabled={isSaving}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {isSaving ? '保存中...' : '保存设置'}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'mascot' && (
              <MascotSettingsTab />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const MascotSettingsTab: React.FC = () => {
  const { preferences, setPreferences, resetPosition } = useMascot();
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      localStorage.setItem('mascot_preferences', JSON.stringify(preferences));
      showToast.success('吉祥物设置已保存');
    } catch {
      showToast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">吉祥物设置</h2>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div>
            <p className="font-medium text-gray-900 dark:text-white">启用吉祥物</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">在页面右下角显示房小智</p>
          </div>
          <button
            onClick={() => setPreferences({ enabled: !preferences.enabled })}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences.enabled ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences.enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="font-medium text-gray-900 dark:text-white mb-3">吉祥物大小</p>
          <div className="grid grid-cols-4 gap-3">
            {[
              { value: 'sm', label: '小' },
              { value: 'md', label: '中' },
              { value: 'lg', label: '大' },
              { value: 'xl', label: '超大' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setPreferences({ size: option.value as 'sm' | 'md' | 'lg' | 'xl' })}
                className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                  preferences.size === option.value
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-600'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div>
            <p className="font-medium text-gray-900 dark:text-white">所有场景显示</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">关闭后仅在空状态时显示</p>
          </div>
          <button
            onClick={() => setPreferences({ showInAllScenes: !preferences.showInAllScenes })}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences.showInAllScenes ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences.showInAllScenes ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">重置位置</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">将吉祥物恢复到默认位置</p>
            </div>
            <button
              onClick={resetPosition}
              className="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
            >
              重置
            </button>
          </div>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="font-medium text-gray-900 dark:text-white mb-3">预览</p>
          <div className="flex items-center justify-center p-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
            <Mascot
              emotion="happy"
              size={preferences.size}
              animate
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
            拖拽吉祥物可移动位置，点击可触发互动
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={isSaving}
          className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          {isSaving ? '保存中...' : '保存设置'}
        </button>
      </div>
    </div>
  );
};

interface HousingProfileProps {
  profile: {
    age: string;
    gender: string;
    occupation: string;
    monthly_income: string;
    family_structure: string;
    has_children: boolean;
    current_city: string;
    current_district: string;
    work_city: string;
    work_district: string;
    commute_preference: string;
    house_type_preference: string;
    budget_min: string;
    budget_max: string;
    down_payment: string;
    loan_need: boolean;
  };
  setProfile: React.Dispatch<React.SetStateAction<typeof profile>>;
  isSaving: boolean;
  setIsSaving: React.Dispatch<React.SetStateAction<boolean>>;
}

const HousingProfileTab: React.FC<HousingProfileProps> = ({ profile, setProfile, isSaving, setIsSaving }) => {
  const handleSave = async () => {
    setIsSaving(true);
    try {
      const data = {
        age: profile.age ? parseInt(profile.age) : undefined,
        gender: profile.gender || undefined,
        occupation: profile.occupation || undefined,
        monthly_income: profile.monthly_income ? parseInt(profile.monthly_income) : undefined,
        family_structure: profile.family_structure || undefined,
        has_children: profile.has_children || undefined,
        current_city: profile.current_city || undefined,
        current_district: profile.current_district || undefined,
        work_city: profile.work_city || undefined,
        work_district: profile.work_district || undefined,
        commute_preference: profile.commute_preference || undefined,
        house_type_preference: profile.house_type_preference || undefined,
        budget_min: profile.budget_min ? parseInt(profile.budget_min) : undefined,
        budget_max: profile.budget_max ? parseInt(profile.budget_max) : undefined,
        down_payment: profile.down_payment ? parseInt(profile.down_payment) : undefined,
        loan_need: profile.loan_need || undefined,
      };

      await api.put('/consult/profile', data);
      showToast.success('购房画像已保存');
    } catch {
      showToast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  const updateField = (field: string, value: string | boolean) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">购房画像</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          完善您的购房画像，获得更精准的智能推荐
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">基本信息</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">年龄</label>
              <input
                type="number"
                value={profile.age}
                onChange={(e) => updateField('age', e.target.value)}
                placeholder="如：30"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">性别</label>
              <select
                value={profile.gender}
                onChange={(e) => updateField('gender', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              >
                <option value="">请选择</option>
                <option value="male">男</option>
                <option value="female">女</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">职业</label>
              <select
                value={profile.occupation}
                onChange={(e) => updateField('occupation', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              >
                <option value="">请选择</option>
                <option value="IT/互联网">IT/互联网</option>
                <option value="金融">金融</option>
                <option value="教育">教育</option>
                <option value="医疗">医疗</option>
                <option value="政府/事业单位">政府/事业单位</option>
                <option value="制造业">制造业</option>
                <option value="销售">销售</option>
                <option value="创业者">创业者</option>
                <option value="其他">其他</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">月收入（元）</label>
              <input
                type="number"
                value={profile.monthly_income}
                onChange={(e) => updateField('monthly_income', e.target.value)}
                placeholder="如：30000"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">家庭情况</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">家庭结构</label>
              <select
                value={profile.family_structure}
                onChange={(e) => updateField('family_structure', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              >
                <option value="">请选择</option>
                <option value="单身">单身</option>
                <option value="夫妻">夫妻</option>
                <option value="有子女">有子女</option>
                <option value="三代同堂">三代同堂</option>
              </select>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <span className="text-sm text-gray-600 dark:text-gray-400">是否有子女</span>
              <button
                onClick={() => updateField('has_children', !profile.has_children)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  profile.has_children ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    profile.has_children ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">居住与工作</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">现居城市</label>
                <input
                  type="text"
                  value={profile.current_city}
                  onChange={(e) => updateField('current_city', e.target.value)}
                  placeholder="如：深圳"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">现居区域</label>
                <input
                  type="text"
                  value={profile.current_district}
                  onChange={(e) => updateField('current_district', e.target.value)}
                  placeholder="如：南山"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">工作城市</label>
                <input
                  type="text"
                  value={profile.work_city}
                  onChange={(e) => updateField('work_city', e.target.value)}
                  placeholder="如：深圳"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">工作区域</label>
                <input
                  type="text"
                  value={profile.work_district}
                  onChange={(e) => updateField('work_district', e.target.value)}
                  placeholder="如：福田"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">通勤偏好</label>
              <select
                value={profile.commute_preference}
                onChange={(e) => updateField('commute_preference', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              >
                <option value="">请选择</option>
                <option value="地铁">地铁优先</option>
                <option value="开车">开车优先</option>
                <option value="公交">公交优先</option>
                <option value="步行">步行优先</option>
              </select>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">购房需求</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">户型偏好</label>
              <select
                value={profile.house_type_preference}
                onChange={(e) => updateField('house_type_preference', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              >
                <option value="">请选择</option>
                <option value="一居室">一居室</option>
                <option value="两居室">两居室</option>
                <option value="三居室">三居室</option>
                <option value="四居室及以上">四居室及以上</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">预算下限（万）</label>
                <input
                  type="number"
                  value={profile.budget_min}
                  onChange={(e) => updateField('budget_min', e.target.value)}
                  placeholder="如：300"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">预算上限（万）</label>
                <input
                  type="number"
                  value={profile.budget_max}
                  onChange={(e) => updateField('budget_max', e.target.value)}
                  placeholder="如：500"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">首付能力（万）</label>
              <input
                type="number"
                value={profile.down_payment}
                onChange={(e) => updateField('down_payment', e.target.value)}
                placeholder="如：150"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <span className="text-sm text-gray-600 dark:text-gray-400">是否需要贷款</span>
              <button
                onClick={() => updateField('loan_need', !profile.loan_need)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  profile.loan_need ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    profile.loan_need ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          {isSaving ? '保存中...' : '保存画像'}
        </button>
      </div>
    </div>
  );
};

export default SettingsPage;
