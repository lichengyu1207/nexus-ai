import React, { useState, useEffect } from 'react';

interface AreaStat {
  id: string;
  city: string;
  district: string;
  layout_type: string;
  avg_area: number;
  sample_count: number;
  created_at: string;
}

interface PriceStat {
  id: string;
  city: string;
  district: string;
  avg_price: number;
  price_per_sqm: number;
  sample_count: number;
  month: string;
}

interface DistrictInfo {
  id: string;
  city: string;
  district: string;
  description: string;
  highlights: string;
  facilities: string;
  transport: string;
  education: string;
}

const AdminKnowledgePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('area');
  const [areaStats, setAreaStats] = useState<AreaStat[]>([]);
  const [priceStats, setPriceStats] = useState<PriceStat[]>([]);
  const [districtInfos, setDistrictInfos] = useState<DistrictInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      if (activeTab === 'area') {
        const res = await fetch('http://localhost:8000/api/admin/knowledge/area-stats', { headers });
        if (res.ok) {
          const data = await res.json();
          setAreaStats(data.items || []);
        }
      } else if (activeTab === 'price') {
        const res = await fetch('http://localhost:8000/api/admin/knowledge/price-stats', { headers });
        if (res.ok) {
          const data = await res.json();
          setPriceStats(data.items || []);
        }
      } else if (activeTab === 'district') {
        const res = await fetch('http://localhost:8000/api/admin/knowledge/district-info', { headers });
        if (res.ok) {
          const data = await res.json();
          setDistrictInfos(data.items || []);
        }
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (data: any) => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const url = editingItem
        ? `http://localhost:8000/api/admin/knowledge/${activeTab}/${editingItem.id}`
        : `http://localhost:8000/api/admin/knowledge/${activeTab}`;
      const method = editingItem ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        setShowModal(false);
        setEditingItem(null);
        fetchData();
      } else {
        const error = await response.json();
        alert(error.detail || '保存失败');
      }
    } catch (error) {
      console.error('Failed to save:', error);
      alert('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除此记录吗？')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/knowledge/${activeTab}/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        fetchData();
      } else {
        alert('删除失败');
      }
    } catch (error) {
      console.error('Failed to delete:', error);
      alert('删除失败');
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">知识库管理</h1>
        <button
          onClick={() => {
            setEditingItem(null);
            setShowModal(true);
          }}
          className="bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark"
        >
          添加数据
        </button>
      </div>

      <div className="flex gap-2 mb-6">
        {[
          { key: 'area', label: '户型面积统计' },
          { key: 'price', label: '区域房价统计' },
          { key: 'district', label: '区域介绍' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded ${
              activeTab === tab.key ? 'bg-primary text-white' : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-10">加载中...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {activeTab === 'area' && (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">城市</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">区域</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">户型</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">平均面积</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">样本数</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {areaStats.map((item) => (
                  <tr key={item.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.city}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.district}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.layout_type}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.avg_area} ㎡</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.sample_count}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => {
                          setEditingItem(item);
                          setShowModal(true);
                        }}
                        className="text-primary hover:underline mr-3"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="text-red-600 hover:underline"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'price' && (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">城市</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">区域</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">平均总价</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">单价</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">月份</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {priceStats.map((item) => (
                  <tr key={item.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.city}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.district}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.avg_price} 万</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.price_per_sqm} 元/㎡</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.month}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => {
                          setEditingItem(item);
                          setShowModal(true);
                        }}
                        className="text-primary hover:underline mr-3"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="text-red-600 hover:underline"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === 'district' && (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">城市</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">区域</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">简介</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {districtInfos.map((item) => (
                  <tr key={item.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.city}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{item.district}</td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">
                      {item.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => {
                          setEditingItem(item);
                          setShowModal(true);
                        }}
                        className="text-primary hover:underline mr-3"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="text-red-600 hover:underline"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold mb-4">
              {editingItem ? '编辑' : '添加'}数据
            </h3>
            <KnowledgeForm
              type={activeTab}
              initialData={editingItem}
              onSave={handleSave}
              onCancel={() => {
                setShowModal(false);
                setEditingItem(null);
              }}
              saving={saving}
            />
          </div>
        </div>
      )}
    </div>
  );
};

const KnowledgeForm: React.FC<{
  type: string;
  initialData: any;
  onSave: (data: any) => void;
  onCancel: () => void;
  saving: boolean;
}> = ({ type, initialData, onSave, onCancel, saving }) => {
  const [formData, setFormData] = useState(initialData || {});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {type === 'area' && (
        <>
          <div>
            <label className="block text-sm font-medium mb-1">城市</label>
            <input
              name="city"
              value={formData.city || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">区域</label>
            <input
              name="district"
              value={formData.district || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">户型</label>
            <input
              name="layout_type"
              value={formData.layout_type || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              placeholder="如：三室两厅"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">平均面积（㎡）</label>
            <input
              name="avg_area"
              type="number"
              value={formData.avg_area || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">样本数</label>
            <input
              name="sample_count"
              type="number"
              value={formData.sample_count || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </>
      )}

      {type === 'price' && (
        <>
          <div>
            <label className="block text-sm font-medium mb-1">城市</label>
            <input
              name="city"
              value={formData.city || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">区域</label>
            <input
              name="district"
              value={formData.district || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">平均总价（万）</label>
            <input
              name="avg_price"
              type="number"
              value={formData.avg_price || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">单价（元/㎡）</label>
            <input
              name="price_per_sqm"
              type="number"
              value={formData.price_per_sqm || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">月份</label>
            <input
              name="month"
              value={formData.month || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              placeholder="如：2024-01"
              required
            />
          </div>
        </>
      )}

      {type === 'district' && (
        <>
          <div>
            <label className="block text-sm font-medium mb-1">城市</label>
            <input
              name="city"
              value={formData.city || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">区域</label>
            <input
              name="district"
              value={formData.district || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">简介</label>
            <textarea
              name="description"
              value={formData.description || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              rows={3}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">亮点</label>
            <textarea
              name="highlights"
              value={formData.highlights || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              rows={2}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">配套设施</label>
            <textarea
              name="facilities"
              value={formData.facilities || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              rows={2}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">交通</label>
            <textarea
              name="transport"
              value={formData.transport || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              rows={2}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">教育</label>
            <textarea
              name="education"
              value={formData.education || ''}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              rows={2}
            />
          </div>
        </>
      )}

      <div className="flex justify-end gap-2 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded hover:bg-gray-50"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-primary text-white rounded hover:bg-primaryDark disabled:opacity-50"
        >
          {saving ? '保存中...' : '保存'}
        </button>
      </div>
    </form>
  );
};

export default AdminKnowledgePage;
