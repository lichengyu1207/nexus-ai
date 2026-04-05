import React, { useState, useEffect } from 'react';

interface SettingItem {
  key: string;
  value: any;
  type: string;
  description: string;
  group: string;
  options?: string[];
  min?: number;
  max?: number;
}

interface SettingsGroup {
  [key: string]: SettingItem;
}

interface GroupedSettings {
  groups: {
    [groupName: string]: SettingsGroup;
  };
}

const groupLabels: Record<string, string> = {
  general: '基本设置',
  security: '安全设置',
  notification: '通知设置',
  ai: 'AI设置',
  valuation: '估值设置',
  integral: '积分设置',
  system: '系统设置'
};

const AdminSettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<GroupedSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeGroup, setActiveGroup] = useState('general');
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/admin/settings', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
        
        const groups = Object.keys(data.groups);
        if (groups.length > 0 && !groups.includes(activeGroup)) {
          setActiveGroup(groups[0]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleValueChange = (key: string, value: any) => {
    setEditedValues(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (Object.keys(editedValues).length === 0) return;
    
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/admin/settings', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ settings: editedValues })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(result.message);
        setEditedValues({});
        setHasChanges(false);
        fetchSettings();
      } else {
        const error = await response.json();
        alert(error.detail || '保存失败');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleReloadCache = async () => {
    if (!confirm('确定要重新加载设置缓存吗？')) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/admin/settings/reload-cache', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        alert('缓存已重新加载');
        fetchSettings();
      } else {
        alert('重新加载失败');
      }
    } catch (error) {
      console.error('Failed to reload cache:', error);
      alert('重新加载失败');
    }
  };

  const renderInput = (setting: SettingItem) => {
    const currentValue = editedValues.hasOwnProperty(setting.key) 
      ? editedValues[setting.key] 
      : setting.value;
    
    switch (setting.type) {
      case 'boolean':
        return (
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={currentValue === true}
              onChange={(e) => handleValueChange(setting.key, e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            <span className="ml-3 text-sm font-medium text-gray-900">
              {currentValue ? '开启' : '关闭'}
            </span>
          </label>
        );
      
      case 'number':
      case 'integer':
        return (
          <input
            type="number"
            value={currentValue ?? ''}
            onChange={(e) => handleValueChange(setting.key, setting.type === 'integer' ? parseInt(e.target.value) : parseFloat(e.target.value))}
            min={setting.min}
            max={setting.max}
            className="w-full max-w-xs border rounded px-3 py-2"
          />
        );
      
      case 'select':
        return (
          <select
            value={currentValue ?? ''}
            onChange={(e) => handleValueChange(setting.key, e.target.value)}
            className="w-full max-w-xs border rounded px-3 py-2"
          >
            {setting.options?.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );
      
      case 'text':
      case 'textarea':
        return (
          <textarea
            value={currentValue ?? ''}
            onChange={(e) => handleValueChange(setting.key, e.target.value)}
            className="w-full border rounded px-3 py-2"
            rows={3}
          />
        );
      
      default:
        return (
          <input
            type="text"
            value={currentValue ?? ''}
            onChange={(e) => handleValueChange(setting.key, e.target.value)}
            className="w-full max-w-md border rounded px-3 py-2"
          />
        );
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center py-10">加载中...</div>
      </div>
    );
  }

  if (!settings || Object.keys(settings.groups).length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-10 text-gray-500">暂无设置项</div>
      </div>
    );
  }

  const groups = Object.keys(settings.groups);
  const currentSettings = settings.groups[activeGroup] || {};

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">系统设置</h1>
        <div className="flex gap-2">
          <button
            onClick={handleReloadCache}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            重新加载缓存
          </button>
          {hasChanges && (
            <button
              onClick={handleSave}
              disabled={saving}
              className="bg-primary text-white px-4 py-2 rounded hover:bg-primary/90 disabled:opacity-50"
            >
              {saving ? '保存中...' : '保存更改'}
            </button>
          )}
        </div>
      </div>
      
      <div className="flex gap-6">
        <div className="w-48 flex-shrink-0">
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {groups.map(group => (
              <button
                key={group}
                onClick={() => setActiveGroup(group)}
                className={`w-full text-left px-4 py-3 border-b last:border-b-0 ${
                  activeGroup === group 
                    ? 'bg-primary text-white' 
                    : 'hover:bg-gray-50'
                }`}
              >
                {groupLabels[group] || group}
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex-1">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold">
                {groupLabels[activeGroup] || activeGroup}
              </h2>
            </div>
            
            <div className="divide-y">
              {Object.entries(currentSettings).map(([key, setting]) => (
                <div key={key} className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="flex-1">
                      <label className="block font-medium text-gray-700 mb-1">
                        {setting.description || key}
                      </label>
                      <div className="text-xs text-gray-400 mb-2">{key}</div>
                      {renderInput(setting)}
                    </div>
                    {editedValues.hasOwnProperty(key) && (
                      <button
                        onClick={() => {
                          const newEdited = { ...editedValues };
                          delete newEdited[key];
                          setEditedValues(newEdited);
                          if (Object.keys(newEdited).length === 0) {
                            setHasChanges(false);
                          }
                        }}
                        className="text-gray-400 hover:text-gray-600"
                        title="撤销更改"
                      >
                        ↩️
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {Object.keys(currentSettings).length === 0 && (
              <div className="p-8 text-center text-gray-500">
                该分组暂无设置项
              </div>
            )}
          </div>
        </div>
      </div>
      
      {hasChanges && (
        <div className="fixed bottom-0 left-0 right-0 bg-yellow-50 border-t border-yellow-200 p-4">
          <div className="flex justify-between items-center max-w-6xl mx-auto">
            <div className="text-yellow-800">
              您有 {Object.keys(editedValues).length} 项未保存的更改
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setEditedValues({});
                  setHasChanges(false);
                }}
                className="px-4 py-2 border rounded hover:bg-white"
              >
                放弃更改
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-primary text-white px-4 py-2 rounded hover:bg-primary/90 disabled:opacity-50"
              >
                {saving ? '保存中...' : '保存更改'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminSettingsPage;
