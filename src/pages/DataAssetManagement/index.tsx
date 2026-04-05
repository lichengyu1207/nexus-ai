import { useState, useCallback, useMemo, lazy, Suspense } from 'react';
import { motion } from 'framer-motion';
import { Bars3Icon } from '@heroicons/react/24/outline';
import { AssetTree } from './components/AssetTree';
import { AssetToolbar } from './components/AssetToolbar';
import { AssetList } from './components/AssetList';
import { AssetDetailDrawer } from './components/AssetDetailDrawer';
import { CreateAssetModal } from './components/CreateAssetModal';
import { QualityDashboard } from './components/QualityDashboard';
import { useAssets } from './hooks/useAssets';
import { useAssetTree } from './hooks/useAssetTree';
import type { TreeNode, Asset, ViewMode } from './types';

const LineageGraph = lazy(() => import('./components/LineageGraph'));

export default function DataAssetManagement() {
  const [selectedFolderId, setSelectedFolderId] = useState<string | undefined>();
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [selectedAssetIds, setSelectedAssetIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('card');
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [assetTypeFilter, setAssetTypeFilter] = useState<string | undefined>();

  const {
    tree,
    isLoading: isTreeLoading,
    createFolder,
    deleteFolder,
  } = useAssetTree();

  const {
    assets,
    isLoading: isAssetsLoading,
    hasMore,
    createAsset,
    deleteAsset,
    isCreating,
    isDeleting,
    refetch: refetchAssets,
  } = useAssets({
    parentId: selectedFolderId,
    type: assetTypeFilter,
    search: searchQuery,
  });

  const filteredAssets = useMemo(() => {
    if (!searchQuery) return assets;
    const query = searchQuery.toLowerCase();
    return assets.filter(
      (asset) =>
        asset.name.toLowerCase().includes(query) ||
        asset.description?.toLowerCase().includes(query) ||
        asset.tags.some((tag) => tag.toLowerCase().includes(query))
    );
  }, [assets, searchQuery]);

  const handleSelectNode = useCallback((node: TreeNode) => {
    if (node.type === 'folder') {
      setSelectedFolderId(node.id === 'root' ? undefined : node.id);
    } else {
      setSelectedAssetId(node.id);
      setIsDetailDrawerOpen(true);
    }
  }, []);

  const handleAssetClick = useCallback((asset: Asset) => {
    setSelectedAssetId(asset.id);
    setIsDetailDrawerOpen(true);
  }, []);

  const handleSelectAsset = useCallback((id: string, selected: boolean) => {
    setSelectedAssetIds((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(
    (selected: boolean) => {
      if (selected) {
        setSelectedAssetIds(new Set(filteredAssets.map((a) => a.id)));
      } else {
        setSelectedAssetIds(new Set());
      }
    },
    [filteredAssets]
  );

  const handleDeleteAsset = useCallback(
    (asset: Asset) => {
      deleteAsset(asset.id);
      setSelectedAssetIds((prev) => {
        const next = new Set(prev);
        next.delete(asset.id);
        return next;
      });
    },
    [deleteAsset]
  );

  const handleBatchDelete = useCallback(() => {
    selectedAssetIds.forEach((id) => deleteAsset(id));
    setSelectedAssetIds(new Set());
  }, [selectedAssetIds, deleteAsset]);

  const handleCreateAsset = useCallback(
    (data: Partial<Asset>) => {
      createAsset(data, {
        onSuccess: () => {
          setIsCreateModalOpen(false);
          refetchAssets();
        },
      });
    },
    [createAsset, refetchAssets]
  );

  const handleImport = useCallback(() => {
    console.log('Import assets');
  }, []);

  const handleExport = useCallback(() => {
    const selectedAssets = assets.filter((a) => selectedAssetIds.has(a.id));
    const data = selectedAssets.map((a) => ({
      名称: a.name,
      类型: a.type,
      描述: a.description || '',
      标签: a.tags.join(', '),
      创建时间: a.createdAt,
    }));

    const csv = [
      Object.keys(data[0] || {}).join(','),
      ...data.map((row) => Object.values(row).join(',')),
    ].join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'assets-export.csv';
    a.click();
    URL.revokeObjectURL(url);
  }, [assets, selectedAssetIds]);

  const handleCreateFolder = useCallback(
    (parentId?: string) => {
      const name = prompt('请输入文件夹名称');
      if (name) {
        createFolder({ name, parentId, type: 'folder' });
      }
    },
    [createFolder]
  );

  const handleDeleteFolder = useCallback(
    (node: TreeNode) => {
      if (confirm(`确定要删除文件夹 "${node.name}" 吗？`)) {
        deleteFolder(node.id);
      }
    },
    [deleteFolder]
  );

  return (
    <div className="h-screen flex bg-gray-950 text-white">
      <motion.div
        initial={false}
        animate={{ width: isSidebarOpen ? 300 : 0 }}
        transition={{ duration: 0.2 }}
        className="flex-shrink-0 border-r border-white/10 overflow-hidden"
      >
        <div className="w-[300px] h-full bg-gray-900/50 backdrop-blur-sm">
          <AssetTree
            tree={tree}
            selectedId={selectedFolderId}
            onSelect={handleSelectNode}
            onCreateFolder={handleCreateFolder}
            onDeleteFolder={handleDeleteFolder}
            isLoading={isTreeLoading}
          />
        </div>
      </motion.div>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center gap-4 p-4 border-b border-white/10">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <Bars3Icon className="w-5 h-5 text-gray-400" />
          </button>

          <h1 className="text-xl font-bold text-white">数据资产管理</h1>

          <div className="ml-auto">
            <QualityDashboard />
          </div>
        </div>

        <AssetToolbar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onCreate={() => setIsCreateModalOpen(true)}
          onImport={handleImport}
          onExport={handleExport}
          selectedCount={selectedAssetIds.size}
          onBatchDelete={handleBatchDelete}
          onBatchExport={handleExport}
        />

        <div className="flex-1 overflow-hidden p-4">
          {viewMode === 'lineage' && selectedAssetId ? (
            <div className="h-full">
              <Suspense fallback={<div className="h-full flex items-center justify-center">加载中...</div>}>
                <LineageGraph assetId={selectedAssetId} height={600} />
              </Suspense>
            </div>
          ) : (
            <AssetList
              assets={filteredAssets}
              viewMode={viewMode}
              isLoading={isAssetsLoading}
              selectedIds={selectedAssetIds}
              onAssetClick={handleAssetClick}
              onSelect={handleSelectAsset}
              onSelectAll={handleSelectAll}
              onDelete={handleDeleteAsset}
              hasMore={hasMore}
              onLoadMore={() => {}}
            />
          )}
        </div>
      </div>

      <AssetDetailDrawer
        assetId={selectedAssetId}
        isOpen={isDetailDrawerOpen}
        onClose={() => {
          setIsDetailDrawerOpen(false);
          setSelectedAssetId(null);
        }}
        onDelete={handleDeleteAsset}
      />

      <CreateAssetModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateAsset}
        isLoading={isCreating}
        parentId={selectedFolderId}
      />
    </div>
  );
}

export { AssetTree } from './components/AssetTree';
export { AssetToolbar } from './components/AssetToolbar';
export { AssetList } from './components/AssetList';
export { AssetDetailDrawer } from './components/AssetDetailDrawer';
export { LineageGraph } from './components/LineageGraph';
export { CreateAssetModal } from './components/CreateAssetModal';
export { QualityDashboard } from './components/QualityDashboard';
export * from './types';
export * from './hooks/useAssets';
export * from './hooks/useAssetTree';
export * from './hooks/useAssetDetail';
export * from './hooks/useLineage';
export * from './hooks/useQualityStats';
