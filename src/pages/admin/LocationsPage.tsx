import React, { useState, useEffect, useCallback } from 'react';
import {
  MapPinIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  TrashIcon,
  PencilIcon,
  CheckCircleIcon,
  XCircleIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { adminLocationsApi, Location, LocationStats, LocationUpdate } from '@/api/admin/locations';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';

const SOURCE_LABELS: Record<string, string> = {
  registration: '注册地址',
  interest: '兴趣地址',
  report: '报告地址',
};

const SOURCE_COLORS: Record<string, string> = {
  registration: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  interest: 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-400',
  report: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
};

const LocationsPage: React.FC = () => {
  const [locations, setLocations] = useState<Location[]>([]);
  const [stats, setStats] = useState<LocationStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [editingLocation, setEditingLocation] = useState<Location | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  
  const [filters, setFilters] = useState({
    source: '',
    is_geocoded: '',
    province: '',
    city: '',
    search: '',
  });

  const pageSize = 20;

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: any = { page, page_size: pageSize };
      
      if (filters.source) params.source = filters.source;
      if (filters.is_geocoded !== '') params.is_geocoded = filters.is_geocoded === 'true';
      if (filters.province) params.province = filters.province;
      if (filters.city) params.city = filters.city;
      if (filters.search) params.search = filters.search;

      const [locationsRes, statsRes] = await Promise.all([
        adminLocationsApi.list(params),
        adminLocationsApi.getStats(),
      ]);

      setLocations(locationsRes.locations);
      setTotal(locationsRes.total);
      setTotalPages(locationsRes.total_pages);
      setStats(statsRes);
    } catch {
      showToast.error('加载位置数据失败');
    } finally {
      setIsLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleGeocode = async (locationId: string) => {
    try {
      const result = await adminLocationsApi.geocode(locationId);
      showToast.success(result.message);
      loadData();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || '地理编码失败');
    }
  };

  const handleBatchGeocode = async () => {
    if (!confirm('确定要批量重新地理编码所有失败的地址吗？')) return;
    
    try {
      const result = await adminLocationsApi.batchGeocode();
      showToast.success(`成功: ${result.success_count}, 失败: ${result.fail_count}`);
      loadData();
    } catch {
      showToast.error('批量地理编码失败');
    }
  };

  const handleDelete = async (locationId: string) => {
    if (!confirm('确定要删除此位置记录吗？')) return;
    
    try {
      await adminLocationsApi.delete(locationId);
      showToast.success('删除成功');
      loadData();
    } catch {
      showToast.error('删除失败');
    }
  };

  const handleEdit = (location: Location) => {
    setEditingLocation(location);
    setShowEditModal(true);
  };

  const handleSaveEdit = async (data: LocationUpdate) => {
    if (!editingLocation) return;
    
    try {
      await adminLocationsApi.update(editingLocation.id, data);
      showToast.success('更新成功');
      setShowEditModal(false);
      setEditingLocation(null);
      loadData();
    } catch {
      showToast.error('更新失败');
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">地理位置管理</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">共 {total} 条记录</p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors ${
              showFilters 
                ? 'bg-primary-50 dark:bg-primary-900/30 border-primary-200 dark:border-primary-800 text-primary-600 dark:text-primary-400'
                : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'
            }`}
          >
            <FunnelIcon className="w-4 h-4" />
            筛选
          </button>
          
          <button
            onClick={handleBatchGeocode}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <GlobeAltIcon className="w-4 h-4" />
            批量地理编码
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">总位置数</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.geocoded}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">已编码</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.not_geocoded}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">未编码</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">按来源</p>
            <div className="flex flex-wrap gap-1">
              {Object.entries(stats.by_source).map(([source, count]) => (
                <span key={source} className="text-xs text-gray-600 dark:text-gray-400">
                  {SOURCE_LABELS[source]}: {count}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                来源
              </label>
              <select
                value={filters.source}
                onChange={(e) => setFilters({ ...filters, source: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              >
                <option value="">全部</option>
                <option value="registration">注册地址</option>
                <option value="interest">兴趣地址</option>
                <option value="report">报告地址</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                编码状态
              </label>
              <select
                value={filters.is_geocoded}
                onChange={(e) => setFilters({ ...filters, is_geocoded: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              >
                <option value="">全部</option>
                <option value="true">已编码</option>
                <option value="false">未编码</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                省份
              </label>
              <input
                type="text"
                value={filters.province}
                onChange={(e) => setFilters({ ...filters, province: e.target.value })}
                placeholder="输入省份"
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                搜索
              </label>
              <div className="relative">
                <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="地址、小区..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  className="w-full pl-9 pr-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                />
              </div>
            </div>
          </div>
          
          <div className="flex justify-end mt-4">
            <button
              onClick={() => {
                setFilters({ source: '', is_geocoded: '', province: '', city: '', search: '' });
                setPage(1);
              }}
              className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            >
              重置筛选
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <LoadingCard message="加载位置数据..." />
      ) : locations.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
          <MapPinIcon className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">暂无位置记录</h3>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">地址</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">来源</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">位置</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">坐标</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">状态</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">创建时间</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {locations.map((location) => (
                  <tr key={location.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <div className="max-w-xs">
                        <p className="text-sm text-gray-900 dark:text-white truncate">{location.address}</p>
                        {location.community && (
                          <p className="text-xs text-gray-500 dark:text-gray-400">{location.community}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
                        SOURCE_COLORS[location.source] || 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}>
                        {SOURCE_LABELS[location.source] || location.source}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm">
                        <p className="text-gray-900 dark:text-white">{location.province || '-'}</p>
                        <p className="text-gray-500 dark:text-gray-400">{location.city} {location.district}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 font-mono">
                      {location.longitude && location.latitude 
                        ? `${location.longitude.toFixed(4)}, ${location.latitude.toFixed(4)}`
                        : '-'
                      }
                    </td>
                    <td className="px-4 py-3">
                      {location.longitude && location.latitude ? (
                        <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400">
                          <CheckCircleIcon className="w-4 h-4" />
                          已编码
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-red-600 dark:text-red-400">
                          <XCircleIcon className="w-4 h-4" />
                          未编码
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {formatDate(location.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleEdit(location)}
                          className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                          title="编辑"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                        {!location.longitude && (
                          <button
                            onClick={() => handleGeocode(location.id)}
                            className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                            title="重新地理编码"
                          >
                            <GlobeAltIcon className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(location.id)}
                          className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                          title="删除"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                第 {page} 页，共 {totalPages} 页
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
                >
                  上一页
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingLocation && (
        <EditLocationModal
          location={editingLocation}
          onSave={handleSaveEdit}
          onClose={() => {
            setShowEditModal(false);
            setEditingLocation(null);
          }}
        />
      )}
    </div>
  );
};

interface EditLocationModalProps {
  location: Location;
  onSave: (data: LocationUpdate) => void;
  onClose: () => void;
}

const EditLocationModal: React.FC<EditLocationModalProps> = ({ location, onSave, onClose }) => {
  const [form, setForm] = useState<LocationUpdate>({
    address: location.address,
    country: location.country || '',
    province: location.province || '',
    city: location.city || '',
    district: location.district || '',
    street: location.street || '',
    community: location.community || '',
    longitude: location.longitude || undefined,
    latitude: location.latitude || undefined,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">编辑位置</h3>
        </div>
        
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              原始地址
            </label>
            <input
              type="text"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                国家
              </label>
              <input
                type="text"
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                省份
              </label>
              <input
                type="text"
                value={form.province}
                onChange={(e) => setForm({ ...form, province: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                城市
              </label>
              <input
                type="text"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                区县
              </label>
              <input
                type="text"
                value={form.district}
                onChange={(e) => setForm({ ...form, district: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                街道
              </label>
              <input
                type="text"
                value={form.street}
                onChange={(e) => setForm({ ...form, street: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                小区
              </label>
              <input
                type="text"
                value={form.community}
                onChange={(e) => setForm({ ...form, community: e.target.value })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                经度
              </label>
              <input
                type="number"
                step="0.0001"
                value={form.longitude || ''}
                onChange={(e) => setForm({ ...form, longitude: parseFloat(e.target.value) || undefined })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                纬度
              </label>
              <input
                type="number"
                step="0.0001"
                value={form.latitude || ''}
                onChange={(e) => setForm({ ...form, latitude: parseFloat(e.target.value) || undefined })}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
              />
            </div>
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              取消
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              保存
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LocationsPage;
