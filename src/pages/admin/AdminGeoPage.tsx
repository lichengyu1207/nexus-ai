import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronRightIcon, MagnifyingGlassIcon, MapPinIcon, BuildingOfficeIcon, HomeIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';

interface GeoNode {
  id: string;
  name: string;
  type: 'province' | 'city' | 'district' | 'street' | 'community';
  stats: {
    cityCount?: number;
    districtCount?: number;
    streetCount?: number;
    communityCount?: number;
    userCount?: number;
    houseCount?: number;
    address?: string;
    avgPrice?: number;
  };
  hasChildren: boolean;
  path?: string;
}

interface TreeNodeProps {
  node: GeoNode;
  level: number;
  onSelect: (node: GeoNode) => void;
  selectedId: string | null;
  expandedIds: Set<string>;
  onToggle: (id: string) => void;
  loadChildren: (parentId: string, parentType: string) => Promise<GeoNode[]>;
  childrenData: Map<string, GeoNode[]>;
}

const TreeNode: React.FC<TreeNodeProps> = ({
  node,
  level,
  onSelect,
  selectedId,
  expandedIds,
  onToggle,
  loadChildren,
  childrenData,
}) => {
  const isExpanded = expandedIds.has(node.id);
  const isSelected = selectedId === node.id;
  const children = childrenData.get(node.id) || [];
  const hasChildren = node.hasChildren;

  const handleToggle = async () => {
    if (!isExpanded && hasChildren && children.length === 0) {
      await loadChildren(node.id, node.type);
    }
    onToggle(node.id);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'province': return '🏛️';
      case 'city': return '🏙️';
      case 'district': return '📍';
      case 'street': return '🛣️';
      case 'community': return '🏠';
      default: return '📌';
    }
  };

  const getStatsText = (node: GeoNode) => {
    const parts: string[] = [];
    if (node.stats.cityCount) parts.push(`${node.stats.cityCount}市`);
    if (node.stats.districtCount) parts.push(`${node.stats.districtCount}区`);
    if (node.stats.communityCount) parts.push(`${node.stats.communityCount}小区`);
    if (node.stats.userCount) parts.push(`${node.stats.userCount}用户`);
    return parts.length > 0 ? `(${parts.join(', ')})` : '';
  };

  return (
    <div>
      <div
        className={`flex items-center gap-1 py-1.5 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 rounded ${isSelected ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={() => onSelect(node)}
      >
        {hasChildren ? (
          <button onClick={(e) => { e.stopPropagation(); handleToggle(); }} className="p-0.5">
            {isExpanded ? (
              <ChevronDownIcon className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronRightIcon className="w-4 h-4 text-gray-500" />
            )}
          </button>
        ) : (
          <span className="w-5" />
        )}
        <span className="mr-1">{getTypeIcon(node.type)}</span>
        <span className="text-sm text-gray-900 dark:text-white">{node.name}</span>
        <span className="text-xs text-gray-500 ml-1">{getStatsText(node)}</span>
      </div>
      {isExpanded && children.length > 0 && (
        <div>
          {children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
              selectedId={selectedId}
              expandedIds={expandedIds}
              onToggle={onToggle}
              loadChildren={loadChildren}
              childrenData={childrenData}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const NodeDetail: React.FC<{ node: GeoNode | null }> = ({ node }) => {
  if (!node) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <MapPinIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>选择左侧树节点查看详情</p>
        </div>
      </div>
    );
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'province': return '省份';
      case 'city': return '城市';
      case 'district': return '区县';
      case 'street': return '街道';
      case 'community': return '小区';
      default: return type;
    }
  };

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">
          {node.type === 'province' ? '🏛️' : node.type === 'city' ? '🏙️' : node.type === 'district' ? '📍' : node.type === 'street' ? '🛣️' : '🏠'}
        </span>
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">{node.name}</h2>
          <p className="text-sm text-gray-500">{getTypeLabel(node.type)}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {node.stats.cityCount !== undefined && (
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-600">{node.stats.cityCount}</div>
            <div className="text-xs text-gray-500">城市</div>
          </div>
        )}
        {node.stats.districtCount !== undefined && (
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-600">{node.stats.districtCount}</div>
            <div className="text-xs text-gray-500">区县</div>
          </div>
        )}
        {node.stats.communityCount !== undefined && (
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-purple-600">{node.stats.communityCount}</div>
            <div className="text-xs text-gray-500">小区</div>
          </div>
        )}
        {node.stats.userCount !== undefined && (
          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-orange-600">{node.stats.userCount}</div>
            <div className="text-xs text-gray-500">用户</div>
          </div>
        )}
        {node.stats.houseCount !== undefined && (
          <div className="bg-cyan-50 dark:bg-cyan-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-cyan-600">{node.stats.houseCount}</div>
            <div className="text-xs text-gray-500">房源</div>
          </div>
        )}
        {node.stats.avgPrice !== undefined && (
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-red-600">{(node.stats.avgPrice / 10000).toFixed(1)}万</div>
            <div className="text-xs text-gray-500">均价/㎡</div>
          </div>
        )}
      </div>

      {node.stats.address && (
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">地址</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">{node.stats.address}</p>
        </div>
      )}

      {node.path && (
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">路径</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">{node.path}</p>
        </div>
      )}
    </div>
  );
};

const AdminGeoPage: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<GeoNode | null>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [childrenData, setChildrenData] = useState<Map<string, GeoNode[]>>(new Map());
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<GeoNode[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const { data: roots, isLoading: rootsLoading } = useQuery({
    queryKey: ['geo-tree-roots'],
    queryFn: async () => {
      const res = await fetch('/api/admin/geo/tree/roots', { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to fetch roots');
      return res.json();
    },
  });

  const loadChildren = async (parentId: string, parentType: string): Promise<GeoNode[]> => {
    if (childrenData.has(parentId)) {
      return childrenData.get(parentId)!;
    }

    try {
      const res = await fetch(
        `/api/admin/geo/tree/children?parentId=${parentId}&parentType=${parentType}`,
        { credentials: 'include' }
      );
      if (!res.ok) throw new Error('Failed to fetch children');
      const children = await res.json();
      setChildrenData((prev) => new Map(prev).set(parentId, children));
      return children;
    } catch (error) {
      console.error('Failed to load children:', error);
      return [];
    }
  };

  const handleToggle = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const res = await fetch(`/api/admin/geo/search?q=${encodeURIComponent(query)}&limit=10`, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Search failed');
      const results = await res.json();
      setSearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchSelect = (result: GeoNode) => {
    setSelectedNode(result);
    setSearchQuery('');
    setSearchResults([]);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">城市数据可视化</h1>
      </div>

      <div className="flex-1 flex gap-4 min-h-0">
        <div className="w-80 bg-white dark:bg-gray-800 rounded-lg shadow flex flex-col">
          <div className="p-3 border-b dark:border-gray-700">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索城市、区域、小区..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              {searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto">
                  {searchResults.map((result) => (
                    <button
                      key={result.id}
                      onClick={() => handleSearchSelect(result)}
                      className="w-full px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                    >
                      <span className="text-sm">
                        {result.type === 'province' ? '🏛️' : result.type === 'city' ? '🏙️' : result.type === 'district' ? '📍' : result.type === 'street' ? '🛣️' : '🏠'}
                      </span>
                      <div>
                        <div className="text-sm text-gray-900 dark:text-white">{result.name}</div>
                        <div className="text-xs text-gray-500">{result.path}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {rootsLoading ? (
              <div className="text-center py-4 text-gray-500">加载中...</div>
            ) : roots && roots.length > 0 ? (
              roots.map((root: GeoNode) => (
                <TreeNode
                  key={root.id}
                  node={root}
                  level={0}
                  onSelect={setSelectedNode}
                  selectedId={selectedNode?.id || null}
                  expandedIds={expandedIds}
                  onToggle={handleToggle}
                  loadChildren={loadChildren}
                  childrenData={childrenData}
                />
              ))
            ) : (
              <div className="text-center py-4 text-gray-500">暂无数据</div>
            )}
          </div>
        </div>

        <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow overflow-y-auto">
          <NodeDetail node={selectedNode} />
        </div>
      </div>
    </div>
  );
};

export default AdminGeoPage;
