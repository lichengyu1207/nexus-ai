import React, { useState, useEffect } from 'react';
import { PencilIcon, TrashIcon, PlusIcon, CheckIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface Plan {
  id: string;
  name: string;
  type: string;
  price_regular: number;
  price_member: number | null;
  price_laohai: number | null;
  price_new_user: number | null;
  credits: number | null;
  duration_days: number;
  features: string[];
  is_active: number;
  sort_order: number;
}

const typeLabels: Record<string, string> = {
  free: '免费版',
  integral: '积分包',
  professional: '专业版',
  enterprise: '企业版',
};

const AdminPlansPage: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    type: 'integral',
    price_regular: 0,
    price_member: 0,
    price_laohai: 0,
    price_new_user: 0,
    credits: 0,
    duration_days: 0,
    features: '',
    is_active: true,
  });

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const response = await api.get('/plans/admin');
      setPlans(response.data || []);
    } catch (error) {
      showToast.error('加载套餐失败');
    } finally {
      setIsLoading(false);
    }
  };

  const formatPrice = (price: number | null) => {
    if (price === null || price === undefined) return '-';
    return `¥${(price / 100).toFixed(2)}`;
  };

  const handleEdit = (plan: Plan) => {
    setEditingPlan(plan);
    setFormData({
      name: plan.name,
      type: plan.type,
      price_regular: plan.price_regular,
      price_member: plan.price_member || 0,
      price_laohai: plan.price_laohai || 0,
      price_new_user: plan.price_new_user || 0,
      credits: plan.credits || 0,
      duration_days: plan.duration_days,
      features: plan.features?.join('\n') || '',
      is_active: plan.is_active === 1,
    });
    setShowModal(true);
  };

  const handleCreate = () => {
    setEditingPlan(null);
    setFormData({
      name: '',
      type: 'integral',
      price_regular: 0,
      price_member: 0,
      price_laohai: 0,
      price_new_user: 0,
      credits: 0,
      duration_days: 0,
      features: '',
      is_active: true,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const features = formData.features
      .split('\n')
      .map(f => f.trim())
      .filter(f => f.length > 0);

    const payload = {
      name: formData.name,
      type: formData.type,
      price_regular: Math.round(formData.price_regular * 100),
      price_member: formData.price_member ? Math.round(formData.price_member * 100) : null,
      price_laohai: formData.price_laohai ? Math.round(formData.price_laohai * 100) : null,
      price_new_user: formData.price_new_user ? Math.round(formData.price_new_user * 100) : null,
      credits: formData.type === 'integral' ? formData.credits : null,
      duration_days: formData.duration_days,
      features,
      is_active: formData.is_active,
    };

    try {
      if (editingPlan) {
        await api.put(`/plans/admin/${editingPlan.id}`, payload);
        showToast.success('套餐更新成功');
      } else {
        await api.post('/plans/admin', payload);
        showToast.success('套餐创建成功');
      }
      setShowModal(false);
      loadPlans();
    } catch (error) {
      showToast.error('操作失败');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">套餐管理</h1>
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          新增套餐
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                套餐名称
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                类型
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                标准价
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                会员价
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                粉丝价
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                新用户价
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                积分/天数
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                状态
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {plans.map((plan) => (
              <tr key={plan.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="font-medium text-gray-900 dark:text-white">{plan.name}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                    {typeLabels[plan.type] || plan.type}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-900 dark:text-white">
                  {formatPrice(plan.price_regular)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                  {formatPrice(plan.price_member)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                  {formatPrice(plan.price_laohai)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                  {formatPrice(plan.price_new_user)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                  {plan.type === 'integral' ? `${plan.credits}次` : 
                   plan.duration_days > 0 ? `${plan.duration_days}天` : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {plan.is_active ? (
                    <span className="px-2 py-1 text-xs rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
                      启用
                    </span>
                  ) : (
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                      禁用
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <button
                    onClick={() => handleEdit(plan)}
                    className="p-1 text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400"
                  >
                    <PencilIcon className="w-5 h-5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {editingPlan ? '编辑套餐' : '新增套餐'}
              </h2>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  套餐名称
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  套餐类型
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="integral">积分包</option>
                  <option value="professional">专业版</option>
                  <option value="enterprise">企业版</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    标准价格 (元)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price_regular}
                    onChange={(e) => setFormData({ ...formData, price_regular: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    会员价格 (元)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price_member}
                    onChange={(e) => setFormData({ ...formData, price_member: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    粉丝专属价 (元)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price_laohai}
                    onChange={(e) => setFormData({ ...formData, price_laohai: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    新用户首单价 (元)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price_new_user}
                    onChange={(e) => setFormData({ ...formData, price_new_user: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>

              {formData.type === 'integral' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    积分数量
                  </label>
                  <input
                    type="number"
                    value={formData.credits}
                    onChange={(e) => setFormData({ ...formData, credits: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              )}

              {(formData.type === 'professional' || formData.type === 'enterprise') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    有效天数
                  </label>
                  <input
                    type="number"
                    value={formData.duration_days}
                    onChange={(e) => setFormData({ ...formData, duration_days: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  权益列表 (每行一条)
                </label>
                <textarea
                  value={formData.features}
                  onChange={(e) => setFormData({ ...formData, features: e.target.value })}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="无限次分析&#10;PDF导出&#10;批量分析"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 text-primary-600 rounded border-gray-300"
                />
                <label htmlFor="is_active" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  启用此套餐
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  {editingPlan ? '保存' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPlansPage;
