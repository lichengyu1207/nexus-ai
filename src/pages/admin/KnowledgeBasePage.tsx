import React, { useState, useEffect } from 'react';
import {
  BookOpenIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

type TabType = 'house-types' | 'district-prices' | 'district-info';

interface HouseType {
  id: string;
  type: string;
  min_area: number;
  max_area: number;
  avg_area: number;
  common_areas: number[];
  city: string | null;
  source: string | null;
}

interface DistrictPrice {
  id: string;
  city: string;
  district: string;
  avg_price_per_sqm: number;
  min_price_per_sqm: number;
  max_price_per_sqm: number;
  date: string;
  source: string | null;
}

interface DistrictInfo {
  id: string;
  city: string;
  district: string;
  introduction: string | null;
  transportation: string | null;
  education: string | null;
  commercial: string | null;
  future_plan: string | null;
  pros: string[];
  cons: string[];
}

const KnowledgeBasePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('house-types');
  const [houseTypes, setHouseTypes] = useState<HouseType[]>([]);
  const [districtPrices, setDistrictPrices] = useState<DistrictPrice[]>([]);
  const [districtInfos, setDistrictInfos] = useState<DistrictInfo[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [cityFilter, setCityFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [showImportModal, setShowImportModal] = useState(false);

  useEffect(() => {
    fetchData();
    fetchCities();
  }, [activeTab, cityFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = cityFilter ? `?city=${cityFilter}` : '';
      if (activeTab === 'house-types') {
        const res = await api.get(`/admin/knowledge-base/house-types${params}`);
        setHouseTypes(res.data.items);
      } else if (activeTab === 'district-prices') {
        const res = await api.get(`/admin/knowledge-base/district-prices${params}`);
        setDistrictPrices(res.data.items);
      } else {
        const res = await api.get(`/admin/knowledge-base/district-info${params}`);
        setDistrictInfos(res.data.items);
      }
    } catch (error) {
      showToast.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchCities = async () => {
    try {
      const res = await api.get('/admin/knowledge-base/cities');
      setCities(res.data.cities);
    } catch (error) {
      console.error('Failed to fetch cities:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除此记录吗？')) return;
    try {
      await api.delete(`/admin/knowledge-base/${activeTab}/${id}`);
      showToast.success('删除成功');
      fetchData();
    } catch (error) {
      showToast.error('删除失败');
    }
  };

  const handleExport = async () => {
    try {
      const response = await api.get(`/admin/knowledge-base/${activeTab}/export`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${activeTab}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      showToast.error('导出失败');
    }
  };

  const handleImport = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await api.post(`/admin/knowledge-base/${activeTab}/import`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      showToast.success(`成功导入 ${res.data.imported} 条记录`);
      if (res.data.errors?.length > 0) {
        showToast.error(`有 ${res.data.errors.length} 条记录导入失败`);
      }
      fetchData();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || '导入失败');
    }
    setShowImportModal(false);
  };

  const tabs = [
    { id: 'house-types' as TabType, label: '户型面积', icon: '🏠' },
    { id: 'district-prices' as TabType, label: '区域房价', icon: '💰' },
    { id: 'district-info' as TabType, label: '区域介绍', icon: '📍' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">知识库管理</h1>
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            className="flex items-center gap-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
            导出
          </button>
          <button
            onClick={() => setShowImportModal(true)}
            className="flex items-center gap-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            <ArrowUpTrayIcon className="w-4 h-4" />
            导入
          </button>
          <button
            onClick={() => { setEditingItem(null); setShowModal(true); }}
            className="flex items-center gap-1 px-3 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <PlusIcon className="w-4 h-4" />
            新增
          </button>
        </div>
      </div>

      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <select
          value={cityFilter}
          onChange={(e) => setCityFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
        >
          <option value="">全部城市</option>
          {cities.map((city) => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : activeTab === 'house-types' ? (
          <HouseTypesTable data={houseTypes} onEdit={(item) => { setEditingItem(item); setShowModal(true); }} onDelete={handleDelete} />
        ) : activeTab === 'district-prices' ? (
          <DistrictPricesTable data={districtPrices} onEdit={(item) => { setEditingItem(item); setShowModal(true); }} onDelete={handleDelete} />
        ) : (
          <DistrictInfoTable data={districtInfos} onEdit={(item) => { setEditingItem(item); setShowModal(true); }} onDelete={handleDelete} />
        )}
      </div>

      {showModal && (
        <EditModal
          type={activeTab}
          item={editingItem}
          cities={cities}
          onClose={() => setShowModal(false)}
          onSave={async (data) => {
            try {
              if (editingItem) {
                await api.put(`/admin/knowledge-base/${activeTab}/${editingItem.id}`, data);
                showToast.success('更新成功');
              } else {
                await api.post(`/admin/knowledge-base/${activeTab}`, data);
                showToast.success('创建成功');
              }
              setShowModal(false);
              fetchData();
            } catch (error: any) {
              showToast.error(error.response?.data?.detail || '操作失败');
            }
          }}
        />
      )}

      {showImportModal && (
        <ImportModal type={activeTab} onClose={() => setShowImportModal(false)} onImport={handleImport} />
      )}
    </div>
  );
};

const HouseTypesTable: React.FC<{ data: HouseType[]; onEdit: (item: HouseType) => void; onDelete: (id: string) => void }> = ({ data, onEdit, onDelete }) => (
  <table className="w-full text-sm">
    <thead className="bg-gray-50 dark:bg-gray-700">
      <tr>
        <th className="px-4 py-3 text-left font-medium">户型</th>
        <th className="px-4 py-3 text-left font-medium">城市</th>
        <th className="px-4 py-3 text-right font-medium">最小面积</th>
        <th className="px-4 py-3 text-right font-medium">最大面积</th>
        <th className="px-4 py-3 text-right font-medium">平均面积</th>
        <th className="px-4 py-3 text-left font-medium">常见面积</th>
        <th className="px-4 py-3 text-left font-medium">来源</th>
        <th className="px-4 py-3 text-right font-medium">操作</th>
      </tr>
    </thead>
    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
      {data.map((item) => (
        <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
          <td className="px-4 py-3 font-medium">{item.type}</td>
          <td className="px-4 py-3">{item.city || '通用'}</td>
          <td className="px-4 py-3 text-right">{item.min_area}㎡</td>
          <td className="px-4 py-3 text-right">{item.max_area}㎡</td>
          <td className="px-4 py-3 text-right">{item.avg_area}㎡</td>
          <td className="px-4 py-3">{item.common_areas?.join(', ')}㎡</td>
          <td className="px-4 py-3 text-gray-500">{item.source || '-'}</td>
          <td className="px-4 py-3 text-right">
            <button onClick={() => onEdit(item)} className="p-1 text-blue-600 hover:bg-blue-50 rounded"><PencilIcon className="w-4 h-4" /></button>
            <button onClick={() => onDelete(item.id)} className="p-1 text-red-600 hover:bg-red-50 rounded ml-1"><TrashIcon className="w-4 h-4" /></button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
);

const DistrictPricesTable: React.FC<{ data: DistrictPrice[]; onEdit: (item: DistrictPrice) => void; onDelete: (id: string) => void }> = ({ data, onEdit, onDelete }) => (
  <table className="w-full text-sm">
    <thead className="bg-gray-50 dark:bg-gray-700">
      <tr>
        <th className="px-4 py-3 text-left font-medium">城市</th>
        <th className="px-4 py-3 text-left font-medium">区域</th>
        <th className="px-4 py-3 text-right font-medium">均价</th>
        <th className="px-4 py-3 text-right font-medium">最低价</th>
        <th className="px-4 py-3 text-right font-medium">最高价</th>
        <th className="px-4 py-3 text-left font-medium">更新日期</th>
        <th className="px-4 py-3 text-left font-medium">来源</th>
        <th className="px-4 py-3 text-right font-medium">操作</th>
      </tr>
    </thead>
    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
      {data.map((item) => (
        <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
          <td className="px-4 py-3 font-medium">{item.city}</td>
          <td className="px-4 py-3">{item.district}</td>
          <td className="px-4 py-3 text-right">{item.avg_price_per_sqm?.toLocaleString()}元/㎡</td>
          <td className="px-4 py-3 text-right">{item.min_price_per_sqm?.toLocaleString()}元/㎡</td>
          <td className="px-4 py-3 text-right">{item.max_price_per_sqm?.toLocaleString()}元/㎡</td>
          <td className="px-4 py-3">{item.date}</td>
          <td className="px-4 py-3 text-gray-500">{item.source || '-'}</td>
          <td className="px-4 py-3 text-right">
            <button onClick={() => onEdit(item)} className="p-1 text-blue-600 hover:bg-blue-50 rounded"><PencilIcon className="w-4 h-4" /></button>
            <button onClick={() => onDelete(item.id)} className="p-1 text-red-600 hover:bg-red-50 rounded ml-1"><TrashIcon className="w-4 h-4" /></button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
);

const DistrictInfoTable: React.FC<{ data: DistrictInfo[]; onEdit: (item: DistrictInfo) => void; onDelete: (id: string) => void }> = ({ data, onEdit, onDelete }) => (
  <table className="w-full text-sm">
    <thead className="bg-gray-50 dark:bg-gray-700">
      <tr>
        <th className="px-4 py-3 text-left font-medium">城市</th>
        <th className="px-4 py-3 text-left font-medium">区域</th>
        <th className="px-4 py-3 text-left font-medium">简介</th>
        <th className="px-4 py-3 text-left font-medium">优势</th>
        <th className="px-4 py-3 text-left font-medium">劣势</th>
        <th className="px-4 py-3 text-right font-medium">操作</th>
      </tr>
    </thead>
    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
      {data.map((item) => (
        <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
          <td className="px-4 py-3 font-medium">{item.city}</td>
          <td className="px-4 py-3">{item.district}</td>
          <td className="px-4 py-3 max-w-xs truncate">{item.introduction || '-'}</td>
          <td className="px-4 py-3">{item.pros?.slice(0, 2).join('、')}{item.pros?.length > 2 ? '...' : ''}</td>
          <td className="px-4 py-3">{item.cons?.slice(0, 2).join('、')}{item.cons?.length > 2 ? '...' : ''}</td>
          <td className="px-4 py-3 text-right">
            <button onClick={() => onEdit(item)} className="p-1 text-blue-600 hover:bg-blue-50 rounded"><PencilIcon className="w-4 h-4" /></button>
            <button onClick={() => onDelete(item.id)} className="p-1 text-red-600 hover:bg-red-50 rounded ml-1"><TrashIcon className="w-4 h-4" /></button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
);

const EditModal: React.FC<{ type: TabType; item: any; cities: string[]; onClose: () => void; onSave: (data: any) => void }> = ({ type, item, cities, onClose, onSave }) => {
  const [formData, setFormData] = useState<any>(item || {});
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    await onSave(formData);
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">{item ? '编辑' : '新增'}记录</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded"><XMarkIcon className="w-5 h-5" /></button>
        </div>
        
        {type === 'house-types' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">户型 *</label>
              <input type="text" value={formData.type || ''} onChange={(e) => setFormData({ ...formData, type: e.target.value })} className="w-full px-3 py-2 border rounded-lg" placeholder="如: 3室2厅" />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">最小面积 *</label>
                <input type="number" value={formData.min_area || ''} onChange={(e) => setFormData({ ...formData, min_area: parseFloat(e.target.value) })} className="w-full px-3 py-2 border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">最大面积 *</label>
                <input type="number" value={formData.max_area || ''} onChange={(e) => setFormData({ ...formData, max_area: parseFloat(e.target.value) })} className="w-full px-3 py-2 border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">平均面积 *</label>
                <input type="number" value={formData.avg_area || ''} onChange={(e) => setFormData({ ...formData, avg_area: parseFloat(e.target.value) })} className="w-full px-3 py-2 border rounded-lg" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">城市</label>
              <select value={formData.city || ''} onChange={(e) => setFormData({ ...formData, city: e.target.value || null })} className="w-full px-3 py-2 border rounded-lg">
                <option value="">通用（不限城市）</option>
                {cities.map((city) => <option key={city} value={city}>{city}</option>)}
              </select>
            </div>
          </div>
        )}

        {type === 'district-prices' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">城市 *</label>
              <input type="text" value={formData.city || ''} onChange={(e) => setFormData({ ...formData, city: e.target.value })} className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">区域 *</label>
              <input type="text" value={formData.district || ''} onChange={(e) => setFormData({ ...formData, district: e.target.value })} className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">均价（元/㎡）*</label>
              <input type="number" value={formData.avg_price_per_sqm || ''} onChange={(e) => setFormData({ ...formData, avg_price_per_sqm: parseFloat(e.target.value) })} className="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>
        )}

        {type === 'district-info' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">城市 *</label>
                <input type="text" value={formData.city || ''} onChange={(e) => setFormData({ ...formData, city: e.target.value })} className="w-full px-3 py-2 border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">区域 *</label>
                <input type="text" value={formData.district || ''} onChange={(e) => setFormData({ ...formData, district: e.target.value })} className="w-full px-3 py-2 border rounded-lg" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">区域介绍</label>
              <textarea value={formData.introduction || ''} onChange={(e) => setFormData({ ...formData, introduction: e.target.value })} className="w-full px-3 py-2 border rounded-lg" rows={3} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">交通情况</label>
              <textarea value={formData.transportation || ''} onChange={(e) => setFormData({ ...formData, transportation: e.target.value })} className="w-full px-3 py-2 border rounded-lg" rows={2} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">教育资源</label>
              <textarea value={formData.education || ''} onChange={(e) => setFormData({ ...formData, education: e.target.value })} className="w-full px-3 py-2 border rounded-lg" rows={2} />
            </div>
          </div>
        )}

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 px-4 py-2 border border-gray-300 rounded-lg">取消</button>
          <button onClick={handleSubmit} disabled={saving} className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50">
            {saving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  );
};

const ImportModal: React.FC<{ type: TabType; onClose: () => void; onImport: (file: File) => void }> = ({ type, onClose, onImport }) => {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onImport(file);
  };

  const templates = {
    'house-types': ['type', 'min_area', 'max_area', 'avg_area', 'common_areas', 'city', 'source'],
    'district-prices': ['city', 'district', 'avg_price_per_sqm', 'min_price_per_sqm', 'max_price_per_sqm', 'source'],
    'district-info': ['city', 'district', 'introduction', 'transportation', 'education', 'commercial', 'future_plan', 'pros', 'cons'],
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">导入 CSV 文件</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded"><XMarkIcon className="w-5 h-5" /></button>
        </div>
        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-2">CSV 文件需包含以下列：</p>
          <code className="block p-2 bg-gray-100 rounded text-xs">{templates[type].join(', ')}</code>
        </div>
        <input type="file" accept=".csv" onChange={handleFileChange} className="w-full" />
      </div>
    </div>
  );
};

export default KnowledgeBasePage;
