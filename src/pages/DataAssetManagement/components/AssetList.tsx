import { useState, useCallback, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FixedSizeList as List } from 'react-window';
import {
  StarIcon,
  CheckCircleIcon,
  PencilIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import type { Asset, ViewMode, AssetType } from '../types';
import { ASSET_TYPE_CONFIG } from '../types';

export interface AssetListProps {
  assets: Asset[];
  viewMode: ViewMode;
  loading: boolean;
  selectedIds: Set<string>;
  onAssetClick: (asset: Asset) => void;
  onSelect: (id: string, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
  onDelete: (id: string) => void;
  onEdit: (asset: Asset) => void;
  hasMore?: boolean;
  onLoadMore?: () => void;
}

const QualityStars = ({ score }: { score?: number }) => {
  if (score === undefined) return null;

  const fullStars = Math.floor(score / 20);
  const hasHalf = score % 20 >= 10;

  return (
    <div className="flex items-center gap-0.5">
      {[...Array(5)].map((_, i) => (
        <StarIcon
          key={i}
          className={`w-3.5 h-3.5 ${
            i < fullStars
              ? 'text-amber-400 fill-amber-400'
              : i === fullStars && hasHalf
                ? 'text-amber-400 fill-amber-400/50'
                : 'text-gray-600'
          }`}
        />
      ))}
    </div>
  );
};

const formatSize = (bytes?: number): string => {
  if (!bytes) return '-';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  return `${bytes.toFixed(1)} ${units[i]}`;
};

interface AssetCardProps {
  asset: Asset;
  isSelected: boolean;
  onClick: () => void;
  onSelect: (selected: boolean) => void;
  onDelete: () => void;
  onEdit: () => void;
}

const AssetCard = ({
  asset,
  isSelected,
  onClick,
  onSelect,
  onDelete,
  onEdit,
}: AssetCardProps) => {
  const config = ASSET_TYPE_CONFIG[asset.type];
  const timeAgo = formatDistanceToNow(new Date(asset.updatedAt), {
    addSuffix: true,
    locale: zhCN,
  });

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ y: -2 }}
      className={`
        group relative p-4 rounded-xl border cursor-pointer
        transition-all duration-200
        ${
          isSelected
            ? 'bg-amber-500/10 border-amber-500/50'
            : 'bg-white/5 border-white/10 hover:border-white/20 hover:bg-white/10'
        }
      `}
      onClick={onClick}
    >
      <div className="absolute top-2 left-2">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={(e) => {
            e.stopPropagation();
            onSelect(!isSelected);
          }}
          onClick={(e) => e.stopPropagation()}
          className="w-4 h-4 rounded border-gray-600 text-amber-500 focus:ring-amber-500/50"
        />
      </div>

      <div className="flex items-start justify-between mb-3 mt-4">
        <div className={`px-2 py-1 rounded-lg ${config.bgColor}`}>
          <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
        </div>
        <QualityStars score={asset.qualityScore} />
      </div>

      <h3 className="text-sm font-medium text-white truncate mb-1">{asset.name}</h3>
      <p className="text-xs text-gray-500 line-clamp-2 mb-3">
        {asset.description || '暂无描述'}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{timeAgo}</span>
        <span>{formatSize(asset.size)}</span>
      </div>

      <div className="flex flex-wrap gap-1 mt-2">
        {asset.tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="px-1.5 py-0.5 text-xs bg-white/5 text-gray-400 rounded"
          >
            {tag}
          </span>
        ))}
        {asset.tags.length > 3 && (
          <span className="px-1.5 py-0.5 text-xs text-gray-500">
            +{asset.tags.length - 3}
          </span>
        )}
      </div>

      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onEdit();
          }}
          className="p-1 rounded hover:bg-white/10"
          title="编辑"
        >
          <PencilIcon className="w-4 h-4 text-gray-400" />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-1 rounded hover:bg-white/10"
          title="删除"
        >
          <TrashIcon className="w-4 h-4 text-gray-400 hover:text-red-400" />
        </button>
      </div>
    </motion.div>
  );
};

interface AssetRowProps {
  asset: Asset;
  isSelected: boolean;
  onClick: () => void;
  onSelect: (selected: boolean) => void;
  onDelete: () => void;
  onEdit: () => void;
}

const AssetRow = ({
  asset,
  isSelected,
  onClick,
  onSelect,
  onDelete,
  onEdit,
}: AssetRowProps) => {
  const config = ASSET_TYPE_CONFIG[asset.type];
  const timeAgo = formatDistanceToNow(new Date(asset.updatedAt), {
    addSuffix: true,
    locale: zhCN,
  });

  return (
    <motion.div
      layout
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={`
        group flex items-center gap-4 px-4 py-3 border-b border-white/5 cursor-pointer
        transition-colors
        ${isSelected ? 'bg-amber-500/10' : 'hover:bg-white/5'}
      `}
      onClick={onClick}
    >
      <input
        type="checkbox"
        checked={isSelected}
        onChange={(e) => {
          e.stopPropagation();
          onSelect(!isSelected);
        }}
        onClick={(e) => e.stopPropagation()}
        className="w-4 h-4 rounded border-gray-600 text-amber-500 focus:ring-amber-500/50"
      />

      <div className={`px-2 py-0.5 rounded ${config.bgColor}`}>
        <span className={`text-xs ${config.color}`}>{config.label}</span>
      </div>

      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-medium text-white truncate">{asset.name}</h3>
        <p className="text-xs text-gray-500 truncate">{asset.description || '暂无描述'}</p>
      </div>

      <div className="flex items-center gap-2">
        {asset.tags.slice(0, 2).map((tag) => (
          <span
            key={tag}
            className="px-1.5 py-0.5 text-xs bg-white/5 text-gray-400 rounded"
          >
            {tag}
          </span>
        ))}
      </div>

      <QualityStars score={asset.qualityScore} />

      <span className="text-xs text-gray-500 w-16 text-right">{formatSize(asset.size)}</span>

      <span className="text-xs text-gray-500 w-20 text-right">{timeAgo}</span>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onEdit();
          }}
          className="p-1 rounded hover:bg-white/10"
          title="编辑"
        >
          <PencilIcon className="w-4 h-4 text-gray-400" />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-1 rounded hover:bg-white/10"
          title="删除"
        >
          <TrashIcon className="w-4 h-4 text-gray-400 hover:text-red-400" />
        </button>
      </div>
    </motion.div>
  );
};

export function AssetList({
  assets,
  viewMode,
  loading,
  selectedIds,
  onAssetClick,
  onSelect,
  onSelectAll,
  onDelete,
  onEdit,
  hasMore,
  onLoadMore,
}: AssetListProps) {
  const allSelected = assets.length > 0 && assets.every((a) => selectedIds.has(a.id));
  const someSelected = assets.some((a) => selectedIds.has(a.id)) && !allSelected;

  const handleSelectAll = useCallback(() => {
    onSelectAll(!allSelected);
  }, [allSelected, onSelectAll]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (assets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring' }}
          className="text-5xl mb-4"
        >
          📦
        </motion.div>
        <p className="text-lg font-medium">暂无数据资产</p>
        <p className="text-sm text-gray-500 mt-1">点击右上角"新建资产"开始添加</p>
      </div>
    );
  }

  if (viewMode === 'card') {
    return (
      <div className="p-4">
        <div className="flex items-center gap-2 mb-4 px-2">
          <input
            type="checkbox"
            checked={allSelected}
            ref={(el) => {
              if (el) el.indeterminate = someSelected;
            }}
            onChange={handleSelectAll}
            className="w-4 h-4 rounded border-gray-600 text-amber-500 focus:ring-amber-500/50"
          />
          <span className="text-sm text-gray-400">全选</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <AnimatePresence>
            {assets.map((asset) => (
              <AssetCard
                key={asset.id}
                asset={asset}
                isSelected={selectedIds.has(asset.id)}
                onClick={() => onAssetClick(asset)}
                onSelect={(selected) => onSelect(asset.id, selected)}
                onDelete={() => onDelete(asset.id)}
                onEdit={() => onEdit(asset)}
              />
            ))}
          </AnimatePresence>
        </div>

        {hasMore && onLoadMore && (
          <div className="flex justify-center mt-6">
            <button
              onClick={onLoadMore}
              className="px-4 py-2 text-sm text-amber-400 bg-amber-500/10 rounded-lg hover:bg-amber-500/20 transition-colors"
            >
              加载更多
            </button>
          </div>
        )}
      </div>
    );
  }

  if (viewMode === 'lineage') {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        <p>血缘图视图将在选择具体资产后显示</p>
      </div>
    );
  }

  const listRef = useRef<any>(null);

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const asset = assets[index];
    return (
      <div style={style}>
        <AssetRow
          key={asset.id}
          asset={asset}
          isSelected={selectedIds.has(asset.id)}
          onClick={() => onAssetClick(asset)}
          onSelect={(selected) => onSelect(asset.id, selected)}
          onDelete={() => onDelete(asset.id)}
          onEdit={() => onEdit(asset)}
        />
      </div>
    );
  };

  return (
    <div className="divide-y divide-white/5">
      <div className="flex items-center gap-4 px-4 py-2 bg-white/5 sticky top-0">
        <input
          type="checkbox"
          checked={allSelected}
          ref={(el) => {
            if (el) el.indeterminate = someSelected;
          }}
          onChange={handleSelectAll}
          className="w-4 h-4 rounded border-gray-600 text-amber-500 focus:ring-amber-500/50"
        />
        <span className="text-xs text-gray-500 w-16">类型</span>
        <span className="text-xs text-gray-500 flex-1">名称</span>
        <span className="text-xs text-gray-500 w-24">标签</span>
        <span className="text-xs text-gray-500 w-20">质量</span>
        <span className="text-xs text-gray-500 w-16">大小</span>
        <span className="text-xs text-gray-500 w-20">更新</span>
        <span className="text-xs text-gray-500 w-12">操作</span>
      </div>

      <div style={{ height: 'calc(100vh - 300px)', overflow: 'auto' }}>
        <List
          ref={listRef}
          height={600}
          itemCount={assets.length}
          itemSize={60}
          width="100%"
        >
          {Row}
        </List>
      </div>

      {hasMore && onLoadMore && (
        <div className="flex justify-center py-4">
          <button
            onClick={onLoadMore}
            className="px-4 py-2 text-sm text-amber-400 bg-amber-500/10 rounded-lg hover:bg-amber-500/20 transition-colors"
          >
            加载更多
          </button>
        </div>
      )}
    </div>
  );
}
