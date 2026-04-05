import { useState } from 'react';
import { motion } from 'framer-motion';
import { useUserSettings } from '../hooks/useUserSettings';
import type { Theme, Language, NotificationSettings } from '../types';

const themeOptions: { value: Theme; label: string; icon: string }[] = [
  { value: 'dark', label: '深色模式', icon: '🌙' },
  { value: 'light', label: '浅色模式', icon: '☀️' },
  { value: 'system', label: '跟随系统', icon: '💻' },
];

const languageOptions: { value: Language; label: string }[] = [
  { value: 'zh', label: '简体中文' },
  { value: 'en', label: 'English' },
];

export function PersonalSettings() {
  const { settings, isLoading, updateTheme, updateLanguage, updateNotifications, updateVoiceEnabled, isUpdating } = useUserSettings();
  const [activeSection, setActiveSection] = useState<string>('theme');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleThemeChange = async (theme: Theme) => {
    await updateTheme(theme);
  };

  const handleLanguageChange = async (language: Language) => {
    await updateLanguage(language);
  };

  const handleNotificationChange = async (key: keyof NotificationSettings, value: boolean | string) => {
    const newNotifications = {
      ...settings?.notifications,
      [key]: value,
    } as NotificationSettings;
    await updateNotifications(newNotifications);
  };

  const handleVoiceChange = async (enabled: boolean) => {
    await updateVoiceEnabled(enabled);
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-700/50 pb-4">
        <h2 className="text-xl font-semibold text-white">个人设置</h2>
        <p className="text-gray-400 text-sm mt-1">自定义您的使用体验</p>
      </div>

      <div className="flex gap-2 mb-6">
        {[
          { key: 'theme', label: '主题' },
          { key: 'language', label: '语言' },
          { key: 'notifications', label: '通知' },
          { key: 'voice', label: '配音' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveSection(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeSection === tab.key
                ? 'bg-amber-500 text-slate-900'
                : 'bg-slate-800 text-gray-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <motion.div
        key={activeSection}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50"
      >
        {activeSection === 'theme' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white mb-4">主题设置</h3>
            <div className="grid grid-cols-3 gap-4">
              {themeOptions.map((option) => (
                <motion.button
                  key={option.value}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleThemeChange(option.value)}
                  disabled={isUpdating}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    settings?.theme === option.value
                      ? 'border-amber-500 bg-amber-500/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="text-3xl mb-2">{option.icon}</div>
                  <div className="text-white font-medium">{option.label}</div>
                </motion.button>
              ))}
            </div>
          </div>
        )}

        {activeSection === 'language' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white mb-4">语言设置</h3>
            <div className="space-y-2">
              {languageOptions.map((option) => (
                <label
                  key={option.value}
                  className={`flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-all ${
                    settings?.language === option.value
                      ? 'border-amber-500 bg-amber-500/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <input
                    type="radio"
                    name="language"
                    value={option.value}
                    checked={settings?.language === option.value}
                    onChange={() => handleLanguageChange(option.value)}
                    className="w-4 h-4 text-amber-500 bg-slate-700 border-slate-600"
                  />
                  <span className="text-white">{option.label}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {activeSection === 'notifications' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white mb-4">通知设置</h3>
            <div className="space-y-4">
              <label className="flex items-center justify-between p-4 rounded-lg bg-slate-900/50">
                <div>
                  <p className="text-white font-medium">邮件通知</p>
                  <p className="text-gray-500 text-sm">接收重要更新的邮件通知</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings?.notifications?.email ?? false}
                  onChange={(e) => handleNotificationChange('email', e.target.checked)}
                  className="w-5 h-5 rounded text-amber-500 bg-slate-700 border-slate-600"
                />
              </label>

              <label className="flex items-center justify-between p-4 rounded-lg bg-slate-900/50">
                <div>
                  <p className="text-white font-medium">站内信</p>
                  <p className="text-gray-500 text-sm">在平台内接收通知消息</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings?.notifications?.inApp ?? false}
                  onChange={(e) => handleNotificationChange('inApp', e.target.checked)}
                  className="w-5 h-5 rounded text-amber-500 bg-slate-700 border-slate-600"
                />
              </label>

              <div className="p-4 rounded-lg bg-slate-900/50">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-white font-medium">Webhook</p>
                    <p className="text-gray-500 text-sm">接收事件的Webhook推送</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={!!settings?.notifications?.webhook}
                    onChange={(e) => handleNotificationChange('webhook', e.target.checked ? '' : undefined as unknown as string)}
                    className="w-5 h-5 rounded text-amber-500 bg-slate-700 border-slate-600"
                  />
                </div>
                {settings?.notifications?.webhook !== undefined && (
                  <input
                    type="url"
                    value={settings?.notifications?.webhook ?? ''}
                    onChange={(e) => handleNotificationChange('webhook', e.target.value)}
                    placeholder="https://your-webhook-url.com"
                    className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700
                      text-white text-sm focus:outline-none focus:border-amber-500"
                  />
                )}
              </div>
            </div>
          </div>
        )}

        {activeSection === 'voice' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white mb-4">配音设置</h3>
            <label className="flex items-center justify-between p-4 rounded-lg bg-slate-900/50">
              <div>
                <p className="text-white font-medium">任务完成配音</p>
                <p className="text-gray-500 text-sm">任务完成时播放提示音</p>
              </div>
              <input
                type="checkbox"
                checked={settings?.voiceEnabled ?? false}
                onChange={(e) => handleVoiceChange(e.target.checked)}
                className="w-5 h-5 rounded text-amber-500 bg-slate-700 border-slate-600"
              />
            </label>
          </div>
        )}
      </motion.div>
    </div>
  );
}
