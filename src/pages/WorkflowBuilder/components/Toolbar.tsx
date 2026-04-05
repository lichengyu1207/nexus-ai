import { motion } from 'framer-motion';
import {
  CloudArrowUpIcon,
  PlayIcon,
  ClockIcon,
  ArrowsPointingInIcon,
  DocumentTextIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';

interface ToolbarProps {
  workflowName: string;
  version: number;
  hasUnsavedChanges: boolean;
  isSaving: boolean;
  isPublishing: boolean;
  onSave: () => void;
  onPublish: () => void;
  onTest: () => void;
  onShowVersions: () => void;
  onAutoLayout: () => void;
  onShowTemplates: () => void;
}

export function Toolbar({
  workflowName,
  version,
  hasUnsavedChanges,
  isSaving,
  isPublishing,
  onSave,
  onPublish,
  onTest,
  onShowVersions,
  onAutoLayout,
  onShowTemplates,
}: ToolbarProps) {
  return (
    <div className="h-14 bg-slate-800/80 backdrop-blur-sm border-b border-slate-700/50 px-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold text-white">{workflowName || '未命名工作流'}</h1>
          <span className="text-xs text-slate-400">v{version}</span>
          {hasUnsavedChanges && (
            <span className="text-xs text-amber-400">未保存</span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onSave}
          disabled={isSaving}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm
            transition-colors
            ${isSaving
              ? 'bg-slate-700/50 text-slate-400'
              : 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
            }
          `}
        >
          {isSaving ? (
            <div className="animate-spin w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full" />
          ) : (
            <CloudArrowUpIcon className="w-3.5 h-3.5" />
          )}
          {isSaving ? '保存中...' : '保存'}
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onPublish}
          disabled={isPublishing}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm
            transition-colors
            ${isPublishing
              ? 'bg-slate-700/50 text-slate-400'
              : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
            }
          `}
        >
          <CheckIcon className="w-3.5 h-3.5" />
          发布
        </motion.button>

        <div className="w-px h-6 bg-slate-700" />

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onTest}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors"
        >
          <PlayIcon className="w-3.5 h-3.5" />
          测试
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onShowVersions}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
        >
          <ClockIcon className="w-3.5 h-3.5" />
          版本历史
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onAutoLayout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
        >
          <ArrowsPointingInIcon className="w-3.5 h-3.5" />
          自动布局
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onShowTemplates}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
        >
          <DocumentTextIcon className="w-3.5 h-3.5" />
          模板市场
        </motion.button>
      </div>
    </div>
  );
}

export default Toolbar;
