import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, CheckIcon } from '@heroicons/react/24/outline';
import { useState, useEffect } from 'react';
import type { NotificationPreference, NotificationType } from './types';
import { NOTIFICATION_TYPE_CONFIG, DEFAULT_NOTIFICATION_PREFERENCES } from './types';

export interface NotificationSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  preferences: NotificationPreference[];
  onUpdatePreferences: (preferences: NotificationPreference[]) => void;
  isUpdating?: boolean;
}

export function NotificationSettingsModal({
  isOpen,
  onClose,
  preferences,
  onUpdatePreferences,
  isUpdating = false,
}: NotificationSettingsModalProps) {
  const [localPreferences, setLocalPreferences] = useState<NotificationPreference[]>(
    preferences
  );

  useEffect(() => {
    setLocalPreferences(preferences);
  }, [preferences]);

  const handleToggle = (
    type: NotificationType,
    field: keyof Omit<NotificationPreference, 'type'>
  ) => {
    setLocalPreferences((prev) =>
      prev.map((pref) =>
        pref.type === type ? { ...pref, [field]: !pref[field] } : pref
      )
    );
  };

  const handleSave = () => {
    onUpdatePreferences(localPreferences);
  };

  const hasChanges =
    JSON.stringify(localPreferences) !== JSON.stringify(preferences);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-gray-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden"
            role="dialog"
            aria-label="通知偏好设置"
          >
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <h2 className="text-lg font-semibold text-white">通知偏好设置</h2>
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-white/10 transition-colors"
                aria-label="关闭"
              >
                <XMarkIcon className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <div className="p-4 max-h-[60vh] overflow-y-auto">
              <div className="space-y-4">
                {localPreferences.map((pref) => {
                  const config = NOTIFICATION_TYPE_CONFIG[pref.type];
                  return (
                    <div
                      key={pref.type}
                      className="p-3 bg-white/5 rounded-lg border border-white/10"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className={`text-sm font-medium ${config.color}`}>
                          {config.label}
                        </span>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={pref.enabled}
                            onChange={() => handleToggle(pref.type, 'enabled')}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-amber-500/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-500" />
                        </label>
                      </div>

                      <div
                        className={`space-y-2 ${!pref.enabled ? 'opacity-50 pointer-events-none' : ''}`}
                      >
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-400">弹窗提醒</span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={pref.popup}
                              onChange={() => handleToggle(pref.type, 'popup')}
                              className="sr-only peer"
                              disabled={!pref.enabled}
                            />
                            <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-amber-500/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-500" />
                          </label>
                        </div>

                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-400">通知中心显示</span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={pref.inApp}
                              onChange={() => handleToggle(pref.type, 'inApp')}
                              className="sr-only peer"
                              disabled={!pref.enabled}
                            />
                            <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-amber-500/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-500" />
                          </label>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 p-4 border-t border-white/10">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || isUpdating}
                className={`
                  flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all
                  ${
                    hasChanges && !isUpdating
                      ? 'bg-amber-500 text-gray-900 hover:bg-amber-400'
                      : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  }
                `}
              >
                {isUpdating ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  >
                    <CheckIcon className="w-4 h-4" />
                  </motion.div>
                ) : (
                  <CheckIcon className="w-4 h-4" />
                )}
                保存设置
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
