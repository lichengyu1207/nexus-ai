import { motion } from 'framer-motion';
import {
  PlusIcon,
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  Squares2X2Icon,
  ListBulletIcon,
  ShareIcon,
} from '@heroicons/react/24/outline';
import type { ViewMode } from '../types';

export interface AssetToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onCreate: () => void;
  onImport: () => void;
  onExport: () => void;
  selectedCount?: number;
  onBatchDelete?: () => void;
  onBatchExport?: () => void;
}

export function AssetToolbar({
  searchQuery,
  onSearchChange,
  viewMode,
  onViewModeChange,
  onCreate,
  onImport,
  onExport,
  selectedCount = 0,
  onBatchDelete,
  onBatchExport,
}: AssetToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 p-4 bg-white/5 border-b border-white/10">
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onCreate}
        className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-gray-900 font-medium rounded-lg hover:bg-amber-400 transition-colors"
      >
        <PlusIcon className="w-5 h-5" />
        新建资产
      </motion.button>

      <div className="flex items-center gap-2">
        <button
          onClick={onImport}
          className="flex items-center gap-1.5 px-3 py-2 text-gray-300 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
        >
          <ArrowUpTrayIcon className="w-4 h-4" />
          <span className="text-sm">导入</span>
        </button>

        <button
          onClick={onExport}
          className="flex items-center gap-1.5 px-3 py-2 text-gray-300 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
        >
          <ArrowDownTrayIcon className="w-4 h-4" />
          <span className="text-sm">导出</span>
        </button>
      </div>

      <div className="flex-1 min-w-[200px] max-w-md">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input
            type="text"
            placeholder="搜索资产名称、标签..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-transparent"
          />
        </div>
      </div>

      <div className="flex items-center gap-1 p-1 bg-white/5 rounded-lg">
        <button
          onClick={() => onViewModeChange('list')}
          className={`p-2 rounded-md transition-colors ${
            viewMode === 'list' ? 'bg-amber-500/20 text-amber-400' : 'text-gray-400 hover:text-white'
          }`}
          title="列表视图"
        >
          <ListBulletIcon className="w-5 h-5" />
        </button>
        <button
          onClick={() => onViewModeChange('card')}
          className={`p-2 rounded-md transition-colors ${
            viewMode === 'card' ? 'bg-amber-500/20 text-amber-400' : 'text-gray-400 hover:text-white'
          }`}
          title="卡片视图"
        >
          <Squares2X2Icon className="w-5 h-5" />
        </button>
        <button
          onClick={() => onViewModeChange('lineage')}
          className={`p-2 rounded-md transition-colors ${
            viewMode === 'lineage' ? 'bg-amber-500/20 text-amber-400' : 'text-gray-400 hover:text-white'
          }`}
          title="血缘图视图"
        >
          <ShareIcon className="w-5 h-5" />
        </button>
      </div>

      {selectedCount > 0 && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="flex items-center gap-2 px-3 py-2 bg-amber-500/20 border border-amber-500/30 rounded-lg"
        >
          <span className="text-sm text-amber-400">已选择 {selectedCount} 项</span>
          {onBatchExport && (
            <button
              onClick={onBatchExport}
              className="px-2 py-1 text-xs bg-white/10 text-white rounded hover:bg-white/20 transition-colors"
            >
              批量导出
            </button>
          )}
          {onBatchDelete && (
            <button
              onClick={onBatchDelete}
              className="px-2 py-1 text-xs bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-colors"
            >
              批量删除
            </button>
          )}
        </motion.div>
      )}
    </div>
  );
}
