import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { EndName, EndInfo } from '../types';

interface EndInfoSidebarProps {
  endId: EndName;
}

const endDisplayNames: Record<string, string> = {
  university: '院校端',
  enterprise: '企业端',
  government: '政府端',
  association: '协会端',
  public: '公众端',
};

const endIcons: Record<string, string> = {
  university: '🎓',
  enterprise: '🏢',
  government: '🏛️',
  association: '🤝',
  public: '👥',
};

const mockEndInfo: Record<EndName, EndInfo> = {
  university: {
    id: 'university',
    displayName: '院校端',
    manager: '张教授',
    contact: 'zhang@university.edu.cn',
    apiCalls: 15234,
    lastActiveTime: new Date().toISOString(),
  },
  enterprise: {
    id: 'enterprise',
    displayName: '企业端',
    manager: '李经理',
    contact: 'li@enterprise.com',
    apiCalls: 23456,
    lastActiveTime: new Date(Date.now() - 3600000).toISOString(),
  },
  government: {
    id: 'government',
    displayName: '政府端',
    manager: '王主任',
    contact: 'wang@gov.cn',
    apiCalls: 8921,
    lastActiveTime: new Date(Date.now() - 7200000).toISOString(),
  },
  association: {
    id: 'association',
    displayName: '协会端',
    manager: '赵会长',
    contact: 'zhao@association.org',
    apiCalls: 5678,
    lastActiveTime: new Date(Date.now() - 1800000).toISOString(),
  },
  public: {
    id: 'public',
    displayName: '公众端',
    manager: '孙管理员',
    contact: 'sun@public.com',
    apiCalls: 34567,
    lastActiveTime: new Date().toISOString(),
  },
};

interface AnnouncementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (title: string, content: string) => void;
}

function AnnouncementModal({ isOpen, onClose, onSubmit }: AnnouncementModalProps) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  const handleSubmit = () => {
    if (title.trim() && content.trim()) {
      onSubmit(title, content);
      setTitle('');
      setContent('');
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50
              w-full max-w-md p-6 rounded-xl bg-slate-800 border border-slate-700"
          >
            <h3 className="text-lg font-semibold text-white mb-4">发布公告</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">标题</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                    text-white focus:outline-none focus:border-amber-500"
                  placeholder="请输入公告标题"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">内容</label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700
                    text-white focus:outline-none focus:border-amber-500 resize-none"
                  placeholder="请输入公告内容"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300 hover:bg-slate-600"
              >
                取消
              </button>
              <button
                onClick={handleSubmit}
                className="px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
                  hover:bg-amber-400"
              >
                发布
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function formatLastActive(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  
  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}小时前`;
  return date.toLocaleDateString('zh-CN');
}

export function EndInfoSidebar({ endId }: EndInfoSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showAnnouncementModal, setShowAnnouncementModal] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const endInfo = mockEndInfo[endId];

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const response = await fetch(`/api/ends/${endId}/export`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${endId}_data_${new Date().toISOString().split('T')[0]}.xlsx`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error('Export failed:', e);
    } finally {
      setIsExporting(false);
    }
  };

  const handleAnnouncement = async (title: string, content: string) => {
    try {
      await fetch(`/api/ends/${endId}/announcements`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      });
    } catch (e) {
      console.error('Announcement failed:', e);
    }
  };

  if (isCollapsed) {
    return (
      <motion.div
        initial={{ width: 280 }}
        animate={{ width: 48 }}
        className="bg-slate-900/50 backdrop-blur-md border-l border-slate-700/50"
      >
        <button
          onClick={() => setIsCollapsed(false)}
          className="w-full p-3 text-gray-400 hover:text-white transition-colors"
          aria-label="展开侧边栏"
        >
          ◀
        </button>
      </motion.div>
    );
  }

  return (
    <>
      <motion.div
        initial={{ width: 48 }}
        animate={{ width: 280 }}
        className="bg-slate-900/50 backdrop-blur-md border-l border-slate-700/50 overflow-hidden"
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">端信息</h3>
            <button
              onClick={() => setIsCollapsed(true)}
              className="text-gray-400 hover:text-white transition-colors"
              aria-label="折叠侧边栏"
            >
              ▶
            </button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50">
              <span className="text-3xl">{endIcons[endId]}</span>
              <div>
                <p className="text-white font-medium">{endDisplayNames[endId]}</p>
                <p className="text-gray-500 text-sm">ID: {endId}</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-slate-800/30">
                <p className="text-gray-500 text-xs mb-1">负责人</p>
                <p className="text-white">{endInfo.manager}</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/30">
                <p className="text-gray-500 text-xs mb-1">联系方式</p>
                <p className="text-white text-sm">{endInfo.contact}</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/30">
                <p className="text-gray-500 text-xs mb-1">API 调用统计</p>
                <p className="text-amber-400 text-lg font-semibold">
                  {endInfo.apiCalls.toLocaleString()}
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/30">
                <p className="text-gray-500 text-xs mb-1">最近活跃</p>
                <p className="text-white text-sm">
                  {formatLastActive(endInfo.lastActiveTime)}
                </p>
              </div>
            </div>

            <div className="pt-4 space-y-2">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowAnnouncementModal(true)}
                className="w-full py-2.5 rounded-lg bg-amber-500 text-slate-900 font-medium
                  hover:bg-amber-400 transition-colors"
              >
                📢 发布公告
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleExport}
                disabled={isExporting}
                className="w-full py-2.5 rounded-lg bg-slate-700 text-white font-medium
                  hover:bg-slate-600 transition-colors disabled:opacity-50"
              >
                {isExporting ? '导出中...' : '📊 导出数据'}
              </motion.button>
            </div>
          </div>
        </div>
      </motion.div>

      <AnnouncementModal
        isOpen={showAnnouncementModal}
        onClose={() => setShowAnnouncementModal(false)}
        onSubmit={handleAnnouncement}
      />
    </>
  );
}
