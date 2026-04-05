import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronRightIcon,
  ChevronDownIcon,
  FolderIcon,
  FolderOpenIcon,
  PlusIcon,
  EllipsisHorizontalIcon,
} from '@heroicons/react/24/outline';
import type { TreeNode, AssetType } from '../types';
import { ASSET_TYPE_CONFIG } from '../types';

export interface AssetTreeProps {
  tree: TreeNode[];
  selectedId?: string;
  onSelect: (node: TreeNode) => void;
  onCreateFolder?: (parentId?: string) => void;
  onRenameFolder?: (node: TreeNode) => void;
  onDeleteFolder?: (node: TreeNode) => void;
  onMoveAsset?: (assetId: string, targetFolderId?: string) => void;
  isLoading?: boolean;
}

interface TreeNodeItemProps {
  node: TreeNode;
  level: number;
  selectedId?: string;
  expandedIds: Set<string>;
  onSelect: (node: TreeNode) => void;
  onToggle: (id: string) => void;
  onContextMenu: (e: React.MouseEvent, node: TreeNode) => void;
}

const TreeNodeItem = ({
  node,
  level,
  selectedId,
  expandedIds,
  onSelect,
  onToggle,
  onContextMenu,
}: TreeNodeItemProps) => {
  const isExpanded = expandedIds.has(node.id);
  const isSelected = selectedId === node.id;
  const hasChildren = node.children && node.children.length > 0;
  const isFolder = node.type === 'folder';

  const config = node.type !== 'folder' ? ASSET_TYPE_CONFIG[node.type as AssetType] : null;
  const Icon = isFolder ? (isExpanded ? FolderOpenIcon : FolderIcon) : null;

  const handleClick = () => {
    onSelect(node);
    if (isFolder && hasChildren) {
      onToggle(node.id);
    }
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle(node.id);
  };

  return (
    <div role="treeitem" aria-selected={isSelected} aria-expanded={isFolder ? isExpanded : undefined}>
      <motion.div
        className={`
          flex items-center gap-2 px-2 py-1.5 cursor-pointer rounded-lg
          transition-colors select-none
          ${isSelected ? 'bg-amber-500/20 text-amber-400' : 'hover:bg-white/5 text-gray-300'}
        `}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleClick}
        onContextMenu={(e) => onContextMenu(e, node)}
        whileHover={{ x: 2 }}
      >
        {isFolder && (
          <button
            onClick={handleToggle}
            className="p-0.5 rounded hover:bg-white/10"
            aria-label={isExpanded ? '折叠' : '展开'}
          >
            <motion.div
              animate={{ rotate: isExpanded ? 90 : 0 }}
              transition={{ duration: 0.15 }}
            >
              <ChevronRightIcon className="w-4 h-4 text-gray-500" />
            </motion.div>
          </button>
        )}

        {!isFolder && <span className="w-5" />}

        <span className={`flex items-center gap-1.5 ${config?.color ?? ''}`}>
          {Icon ? (
            <Icon className="w-4 h-4 text-amber-400" />
          ) : config ? (
            <span className="w-4 h-4 flex items-center justify-center text-xs">
              {config.icon === 'DatabaseIcon' && '🗄️'}
              {config.icon === 'TableCellsIcon' && '📊'}
              {config.icon === 'BookOpenIcon' && '📚'}
            </span>
          ) : null}
          <span className="text-sm truncate">{node.name}</span>
        </span>

        {node.assetCount !== undefined && node.assetCount > 0 && (
          <span className="ml-auto text-xs text-gray-500 bg-white/5 px-1.5 py-0.5 rounded">
            {node.assetCount}
          </span>
        )}
      </motion.div>

      <AnimatePresence>
        {isFolder && isExpanded && hasChildren && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {node.children!.map((child) => (
              <TreeNodeItem
                key={child.id}
                node={child}
                level={level + 1}
                selectedId={selectedId}
                expandedIds={expandedIds}
                onSelect={onSelect}
                onToggle={onToggle}
                onContextMenu={onContextMenu}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export function AssetTree({
  tree,
  selectedId,
  onSelect,
  onCreateFolder,
  onRenameFolder,
  onDeleteFolder,
  isLoading,
}: AssetTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [contextMenu, setContextMenu] = useState<{
    node: TreeNode;
    x: number;
    y: number;
  } | null>(null);

  const handleToggle = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleContextMenu = useCallback((e: React.MouseEvent, node: TreeNode) => {
    e.preventDefault();
    setContextMenu({ node, x: e.clientX, y: e.clientY });
  }, []);

  const handleCloseContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  const handleCreateSubfolder = useCallback(() => {
    if (contextMenu && onCreateFolder) {
      onCreateFolder(contextMenu.node.id);
    }
    handleCloseContextMenu();
  }, [contextMenu, onCreateFolder, handleCloseContextMenu]);

  const handleRename = useCallback(() => {
    if (contextMenu && onRenameFolder) {
      onRenameFolder(contextMenu.node);
    }
    handleCloseContextMenu();
  }, [contextMenu, onRenameFolder, handleCloseContextMenu]);

  const handleDelete = useCallback(() => {
    if (contextMenu && onDeleteFolder) {
      onDeleteFolder(contextMenu.node);
    }
    handleCloseContextMenu();
  }, [contextMenu, onDeleteFolder, handleCloseContextMenu]);

  const handleCreateRootFolder = useCallback(() => {
    onCreateFolder?.();
  }, [onCreateFolder]);

  const expandAll = useCallback(() => {
    const getAllFolderIds = (nodes: TreeNode[]): string[] => {
      return nodes.flatMap((n) =>
        n.type === 'folder' ? [n.id, ...getAllFolderIds(n.children ?? [])] : []
      );
    };
    setExpandedIds(new Set(getAllFolderIds(tree)));
  }, [tree]);

  const collapseAll = useCallback(() => {
    setExpandedIds(new Set());
  }, []);

  const treeWithRoot = useMemo(
    () => [
      {
        id: 'root',
        name: '全部资产',
        type: 'folder' as const,
        children: tree,
      },
    ],
    [tree]
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col" role="tree" aria-label="资产目录树">
      <div className="flex items-center justify-between p-2 border-b border-white/10">
        <span className="text-sm font-medium text-gray-400">资产目录</span>
        <div className="flex items-center gap-1">
          <button
            onClick={expandAll}
            className="p-1 text-xs text-gray-500 hover:text-white transition-colors"
            title="展开全部"
          >
            展开
          </button>
          <span className="text-gray-600">|</span>
          <button
            onClick={collapseAll}
            className="p-1 text-xs text-gray-500 hover:text-white transition-colors"
            title="折叠全部"
          >
            折叠
          </button>
          <button
            onClick={handleCreateRootFolder}
            className="p-1 rounded hover:bg-white/10 transition-colors"
            title="新建文件夹"
          >
            <PlusIcon className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {treeWithRoot.map((node) => (
          <TreeNodeItem
            key={node.id}
            node={node}
            level={0}
            selectedId={selectedId}
            expandedIds={expandedIds}
            onSelect={onSelect}
            onToggle={handleToggle}
            onContextMenu={handleContextMenu}
          />
        ))}
      </div>

      <AnimatePresence>
        {contextMenu && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={handleCloseContextMenu}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed z-50 bg-gray-800 border border-white/10 rounded-lg shadow-xl py-1 min-w-[140px]"
              style={{ left: contextMenu.x, top: contextMenu.y }}
            >
              {contextMenu.node.type === 'folder' && (
                <button
                  onClick={handleCreateSubfolder}
                  className="w-full px-3 py-1.5 text-sm text-left text-gray-300 hover:bg-white/5 flex items-center gap-2"
                >
                  <PlusIcon className="w-4 h-4" />
                  新建子文件夹
                </button>
              )}
              <button
                onClick={handleRename}
                className="w-full px-3 py-1.5 text-sm text-left text-gray-300 hover:bg-white/5 flex items-center gap-2"
              >
                <EllipsisHorizontalIcon className="w-4 h-4" />
                重命名
              </button>
              <button
                onClick={handleDelete}
                className="w-full px-3 py-1.5 text-sm text-left text-red-400 hover:bg-red-500/10 flex items-center gap-2"
              >
                <EllipsisHorizontalIcon className="w-4 h-4" />
                删除
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
