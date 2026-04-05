import { useState } from 'react';
import { motion } from 'framer-motion';
import { useGlobalConfig } from '../hooks/useGlobalConfig';
import type { GlobalConfig as GlobalConfigType } from '../types';

const modelOptions = [
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
];

export function GlobalConfig() {
  const { config, isLoading, updateConfig, isUpdating } = useGlobalConfig();
  const [formData, setFormData] = useState<Partial<GlobalConfigType>>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleInputChange = (key: keyof GlobalConfigType, value: number | string) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    await updateConfig(formData);
    setHasChanges(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const handleReset = () => {
    setFormData({});
    setHasChanges(false);
    setSaveSuccess(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const currentConfig = { ...config, ...formData };

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-700/50 pb-4">
        <h2 className="text-xl font-semibold text-white">全局配置</h2>
        <p className="text-gray-400 text-sm mt-1">配置系统级参数</p>
      </div>

      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50 space-y-6">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">任务并发上限</label>
            <input
              type="number"
              value={currentConfig?.maxConcurrentTasks ?? 10}
              onChange={(e) => handleInputChange('maxConcurrentTasks', parseInt(e.target.value) || 1)}
              min={1}
              max={100}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700
                text-white focus:outline-none focus:border-amber-500"
            />
            <p className="text-xs text-gray-500 mt-1">系统同时运行的最大任务数</p>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">默认模型</label>
            <select
              value={currentConfig?.defaultModel ?? 'gpt-4'}
              onChange={(e) => handleInputChange('defaultModel', e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700
                text-white focus:outline-none focus:border-amber-500"
            >
              {modelOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">新任务默认使用的AI模型</p>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">API限流阈值</label>
            <input
              type="number"
              value={currentConfig?.rateLimitPerSecond ?? 100}
              onChange={(e) => handleInputChange('rateLimitPerSecond', parseInt(e.target.value) || 1)}
              min={1}
              max={1000}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700
                text-white focus:outline-none focus:border-amber-500"
            />
            <p className="text-xs text-gray-500 mt-1">每秒最大API请求数</p>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">数据保留天数</label>
            <input
              type="number"
              value={currentConfig?.dataRetentionDays ?? 30}
              onChange={(e) => handleInputChange('dataRetentionDays', parseInt(e.target.value) || 1)}
              min={1}
              max={365}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700
                text-white focus:outline-none focus:border-amber-500"
            />
            <p className="text-xs text-gray-500 mt-1">日志和记忆数据的保留天数</p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-700/50">
          <h3 className="text-sm font-medium text-gray-400 mb-4">高级设置</h3>
          <div className="grid grid-cols-2 gap-6">
            <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white">调试模式</span>
                <input
                  type="checkbox"
                  className="w-5 h-5 rounded text-amber-500 bg-slate-700 border-slate-600"
                />
              </div>
              <p className="text-xs text-gray-500">启用详细日志输出</p>
            </div>

            <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white">自动备份</span>
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-5 h-5 rounded text-amber-500 bg-slate-700 border-slate-600"
                />
              </div>
              <p className="text-xs text-gray-500">每日自动备份系统数据</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {saveSuccess && (
            <motion.span
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-green-400 text-sm"
            >
              ✓ 配置已保存
            </motion.span>
          )}
          {hasChanges && (
            <span className="text-amber-400 text-sm">有未保存的更改</span>
          )}
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleReset}
            disabled={!hasChanges}
            className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300
              hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            重置
          </button>
          <motion.button
            whileHover={{ scale: hasChanges ? 1.02 : 1 }}
            whileTap={{ scale: hasChanges ? 0.98 : 1 }}
            onClick={handleSave}
            disabled={!hasChanges || isUpdating}
            className="px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
              hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUpdating ? '保存中...' : '保存配置'}
          </motion.button>
        </div>
      </div>
    </div>
  );
}
