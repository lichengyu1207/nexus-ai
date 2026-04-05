import React, { useState, useEffect, useCallback } from 'react';
import {
  CogIcon,
  ArrowPathIcon,
  CheckIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { adminSettingsApi, SettingField } from '@/api/admin/settings';
import { SettingField as SettingFieldComponent } from '@/components/admin';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';
import { useAuth } from '@/contexts/AuthContext';

interface SettingsData {
  [key: string]: SettingField;
}

interface GroupedSettingsData {
  [group: string]: SettingsData;
}

const GROUP_LABELS: Record<string, string> = {
  '基础设置': '基础设置',
  '用户管理': '用户管理',
  '分析设置': '分析设置',
  '系统设置': '系统设置',
  '邮件设置': '邮件设置',
};

const AdminSettings: React.FC = () => {
  const { user } = useAuth();
  const [groupedSettings, setGroupedSettings] = useState<GroupedSettingsData>({});
  const [originalSettings, setOriginalSettings] = useState<GroupedSettingsData>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeGroup, setActiveGroup] = useState<string>('');
  const [hasChanges, setHasChanges] = useState(false);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await adminSettingsApi.getAll();
      setGroupedSettings(response.groups);
      setOriginalSettings(JSON.parse(JSON.stringify(response.groups)));
      
      const groups = Object.keys(response.groups);
      if (groups.length > 0 && !activeGroup) {
        setActiveGroup(groups[0]);
      }
    } catch {
      showToast.error('加载设置失败');
    } finally {
      setIsLoading(false);
    }
  }, [activeGroup]);

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    const changed = JSON.stringify(groupedSettings) !== JSON.stringify(originalSettings);
    setHasChanges(changed);
  }, [groupedSettings, originalSettings]);

  const handleValueChange = (group: string, key: string, value: any) => {
    setGroupedSettings((prev) => ({
      ...prev,
      [group]: {
        ...prev[group],
        [key]: {
          ...prev[group][key],
          value,
        },
      },
    }));
  };

  const handleSave = async () => {
    const changedSettings: Record<string, any> = {};

    Object.keys(groupedSettings).forEach((group) => {
      Object.keys(groupedSettings[group]).forEach((key) => {
        const current = groupedSettings[group][key].value;
        const original = originalSettings[group]?.[key]?.value;
        if (current !== original) {
          changedSettings[key] = current;
        }
      });
    });

    if (Object.keys(changedSettings).length === 0) {
      showToast.info('没有需要保存的更改');
      return;
    }

    setIsSaving(true);
    try {
      const result = await adminSettingsApi.updateAll(changedSettings);
      
      if (result.errors && Object.keys(result.errors).length > 0) {
        showToast.warning(`部分设置保存失败: ${Object.keys(result.errors).join(', ')}`);
      } else {
        showToast.success('设置已保存');
        setOriginalSettings(JSON.parse(JSON.stringify(groupedSettings)));
      }
    } catch {
      showToast.error('保存设置失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (!confirm('确定要放弃所有未保存的更改吗？')) return;
    setGroupedSettings(JSON.parse(JSON.stringify(originalSettings)));
    showToast.info('已恢复到上次保存的状态');
  };

  const handleReloadCache = async () => {
    try {
      await adminSettingsApi.reloadCache();
      showToast.success('缓存已重新加载');
      loadSettings();
    } catch {
      showToast.error('重新加载缓存失败');
    }
  };

  if (isLoading) {
    return <LoadingCard message="加载设置..." />;
  }

  const groups = Object.keys(groupedSettings);
  const currentSettings = activeGroup ? groupedSettings[activeGroup] || {} : {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">系统设置</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">管理系统全局配置</p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={handleReloadCache}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <ArrowPathIcon className="w-4 h-4" />
            刷新缓存
          </button>
        </div>
      </div>

      {/* Unsaved Changes Warning */}
      {hasChanges && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
            <span className="text-sm text-yellow-700 dark:text-yellow-400">
              您有未保存的更改
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              className="px-3 py-1.5 text-sm text-yellow-700 dark:text-yellow-400 hover:bg-yellow-100 dark:hover:bg-yellow-900/40 rounded"
            >
              放弃更改
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
            >
              {isSaving ? '保存中...' : '保存更改'}
            </button>
          </div>
        </div>
      )}

      <div className="flex gap-6">
        {/* Group Tabs */}
        <div className="w-48 flex-shrink-0">
          <nav className="space-y-1">
            {groups.map((group) => (
              <button
                key={group}
                onClick={() => setActiveGroup(group)}
                className={`
                  w-full text-left px-3 py-2 text-sm font-medium rounded-lg
                  transition-colors
                  ${activeGroup === group
                    ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                {GROUP_LABELS[group] || group}
              </button>
            ))}
          </nav>
        </div>

        {/* Settings Content */}
        <div className="flex-1">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {GROUP_LABELS[activeGroup] || activeGroup}
              </h3>
            </div>

            {Object.keys(currentSettings).length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                该分组暂无设置项
              </p>
            ) : (
              <div>
                {Object.entries(currentSettings).map(([key, setting]) => (
                  <SettingFieldComponent
                    key={key}
                    label={setting.description || key}
                    description={undefined}
                    type={setting.type as any}
                    value={setting.value}
                    onChange={(value) => handleValueChange(activeGroup, key, value)}
                    options={setting.options}
                    min={setting.min}
                    max={setting.max}
                    disabled={user?.role !== 'super_admin' && key.includes('smtp')}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Save Button (Fixed at bottom on mobile) */}
      {hasChanges && (
        <div className="fixed bottom-0 left-0 right-0 lg:left-64 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 lg:static lg:border-t-0 lg:bg-transparent lg:dark:bg-transparent lg:p-0">
          <div className="flex justify-end gap-3">
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              <CheckIcon className="w-4 h-4" />
              {isSaving ? '保存中...' : '保存设置'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminSettings;
