import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ClockIcon,
  ArrowUturnLeftIcon,
  DocumentDuplicateIcon,
} from '@heroicons/react/24/outline';
import type { WorkflowVersion } from '../types';

interface VersionHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  versions: WorkflowVersion[];
  currentVersion: number;
  onRollback: (version: WorkflowVersion) => void;
  onCompare: (version1: WorkflowVersion, version2: WorkflowVersion) => void;
}

export function VersionHistoryModal({
  isOpen,
  onClose,
  versions,
  currentVersion,
  onRollback,
}: VersionHistoryModalProps) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-slate-800 rounded-xl border border-slate-700/50 w-full max-w-2xl max-h-[80vh] overflow-hidden"
        >
          <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
            <div className="flex items-center gap-2">
              <ClockIcon className="w-5 h-5 text-amber-400" />
              <h2 className="text-lg font-semibold text-white">版本历史</h2>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          <div className="p-4 overflow-y-auto max-h-[60vh]">
            {versions.length === 0 ? (
              <div className="text-center py-8">
                <ClockIcon className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">暂无版本历史</p>
              </div>
            ) : (
              <div className="space-y-2">
                {versions.map((version) => (
                  <motion.div
                    key={version.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`
                      flex items-center justify-between p-4 rounded-lg border
                      ${version.version === currentVersion
                        ? 'bg-amber-500/10 border-amber-500/30'
                        : 'bg-slate-900/50 border-slate-700/30 hover:border-slate-600'
                      }
                    `}
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white">v{version.version}</span>
                        {version.published && (
                          <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded">
                            已发布
                          </span>
                        )}
                        {version.version === currentVersion && (
                          <span className="px-2 py-0.5 text-xs bg-amber-500/20 text-amber-400 rounded">
                            当前版本
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-slate-400">
                        {new Date(version.createdAt).toLocaleString('zh-CN')}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50 transition-colors"
                        title="选择对比"
                      >
                        <DocumentDuplicateIcon className="w-4 h-4" />
                      </button>
                      {version.version !== currentVersion && (
                        <button
                          onClick={() => onRollback(version)}
                          className="p-2 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-amber-500/20 transition-colors"
                          title="回滚到此版本"
                        >
                          <ArrowUturnLeftIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

export default VersionHistoryModal;
