import React, { useState, useEffect } from 'react';
import { CheckIcon, XMarkIcon, EyeIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface RechargeOrder {
  id: string;
  user_id: string;
  user_email: string;
  user_name: string;
  plan_id: string | null;
  amount: number;
  credits: number | null;
  membership_type: string | null;
  membership_days: number | null;
  status: string;
  admin_notes: string | null;
  user_notes: string | null;
  created_at: string;
  completed_at: string | null;
  completed_by: string | null;
}

const AdminRechargePage: React.FC = () => {
  const [orders, setOrders] = useState<RechargeOrder[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [emailSearch, setEmailSearch] = useState('');
  const [selectedOrder, setSelectedOrder] = useState<RechargeOrder | null>(null);
  const [showProcessModal, setShowProcessModal] = useState(false);
  const [processForm, setProcessForm] = useState({
    action: 'complete',
    admin_notes: '',
    credits: 0,
    membership_type: '',
    membership_days: 0
  });
  const [stats, setStats] = useState({ pending: 0, completed: 0, rejected: 0 });

  useEffect(() => {
    loadOrders();
  }, [statusFilter, emailSearch]);

  const loadOrders = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (emailSearch) params.append('user_email', emailSearch);
      
      const response = await api.get(`/recharge/admin/orders?${params.toString()}`);
      setOrders(response.data.orders || []);
      
      const pending = (response.data.orders || []).filter((o: RechargeOrder) => o.status === 'pending').length;
      const completed = (response.data.orders || []).filter((o: RechargeOrder) => o.status === 'completed').length;
      const rejected = (response.data.orders || []).filter((o: RechargeOrder) => o.status === 'rejected').length;
      setStats({ pending, completed, rejected });
    } catch (error) {
      showToast.error('加载订单失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProcess = async () => {
    if (!selectedOrder) return;
    
    try {
      await api.post(`/recharge/admin/orders/${selectedOrder.id}/process`, {
        action: processForm.action,
        admin_notes: processForm.admin_notes,
        credits: processForm.action === 'complete' ? processForm.credits : null,
        membership_type: processForm.membership_type || null,
        membership_days: processForm.membership_days || null
      });
      
      showToast.success(`订单已${processForm.action === 'complete' ? '完成' : '拒绝'}`);
      setShowProcessModal(false);
      setSelectedOrder(null);
      loadOrders();
    } catch (error) {
      showToast.error('处理失败');
    }
  };

  const openProcessModal = (order: RechargeOrder) => {
    setSelectedOrder(order);
    setProcessForm({
      action: 'complete',
      admin_notes: '',
      credits: order.credits || Math.round(order.amount),
      membership_type: '',
      membership_days: 0
    });
    setShowProcessModal(true);
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      completed: 'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700'
    };
    const labels: Record<string, string> = {
      pending: '待处理',
      completed: '已完成',
      rejected: '已拒绝'
    };
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${styles[status] || 'bg-gray-100 text-gray-700'}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">充值订单管理</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">待处理</p>
          <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">已完成</p>
          <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">已拒绝</p>
          <p className="text-2xl font-bold text-red-600">{stats.rejected}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-4">
        <div className="flex flex-wrap gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              状态筛选
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">全部</option>
              <option value="pending">待处理</option>
              <option value="completed">已完成</option>
              <option value="rejected">已拒绝</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              用户邮箱搜索
            </label>
            <input
              type="text"
              value={emailSearch}
              onChange={(e) => setEmailSearch(e.target.value)}
              placeholder="输入邮箱搜索..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                提交时间
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                用户
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                金额
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                申请积分
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                状态
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                用户备注
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                  加载中...
                </td>
              </tr>
            ) : orders.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                  暂无订单
                </td>
              </tr>
            ) : (
              orders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    {new Date(order.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {order.user_name || '-'}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {order.user_email}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    ¥{order.amount}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    {order.credits || '-'}
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(order.status)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">
                    {order.user_notes || '-'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {order.status === 'pending' ? (
                      <button
                        onClick={() => openProcessModal(order)}
                        className="px-3 py-1 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700"
                      >
                        处理
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          setSelectedOrder(order);
                          setShowProcessModal(true);
                        }}
                        className="p-1 text-gray-500 hover:text-primary-600"
                      >
                        <EyeIcon className="w-5 h-5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Process Modal */}
      {showProcessModal && selectedOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg mx-4 p-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              {selectedOrder.status === 'pending' ? '处理订单' : '订单详情'}
            </h3>

            <div className="space-y-3 mb-6">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">订单ID:</span>
                <span className="text-gray-900 dark:text-white">{selectedOrder.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">用户:</span>
                <span className="text-gray-900 dark:text-white">{selectedOrder.user_name} ({selectedOrder.user_email})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">转账金额:</span>
                <span className="text-gray-900 dark:text-white">¥{selectedOrder.amount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">申请积分:</span>
                <span className="text-gray-900 dark:text-white">{selectedOrder.credits || '未指定'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">用户备注:</span>
                <span className="text-gray-900 dark:text-white">{selectedOrder.user_notes || '无'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">状态:</span>
                {getStatusBadge(selectedOrder.status)}
              </div>
              {selectedOrder.completed_at && (
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">处理时间:</span>
                  <span className="text-gray-900 dark:text-white">
                    {new Date(selectedOrder.completed_at).toLocaleString()}
                  </span>
                </div>
              )}
              {selectedOrder.admin_notes && (
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">管理员备注:</span>
                  <span className="text-gray-900 dark:text-white">{selectedOrder.admin_notes}</span>
                </div>
              )}
            </div>

            {selectedOrder.status === 'pending' && (
              <div className="space-y-4 border-t dark:border-gray-700 pt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    处理结果
                  </label>
                  <select
                    value={processForm.action}
                    onChange={(e) => setProcessForm({ ...processForm, action: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="complete">完成充值</option>
                    <option value="reject">拒绝申请</option>
                  </select>
                </div>

                {processForm.action === 'complete' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        增加积分数量
                      </label>
                      <input
                        type="number"
                        value={processForm.credits}
                        onChange={(e) => setProcessForm({ ...processForm, credits: parseInt(e.target.value) || 0 })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          开通会员类型 (可选)
                        </label>
                        <select
                          value={processForm.membership_type}
                          onChange={(e) => setProcessForm({ ...processForm, membership_type: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="">不开通</option>
                          <option value="professional">专业版</option>
                          <option value="enterprise">企业版</option>
                        </select>
                      </div>
                      {processForm.membership_type && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            会员天数
                          </label>
                          <input
                            type="number"
                            value={processForm.membership_days}
                            onChange={(e) => setProcessForm({ ...processForm, membership_days: parseInt(e.target.value) || 0 })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                      )}
                    </div>
                  </>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    管理员备注
                  </label>
                  <textarea
                    value={processForm.admin_notes}
                    onChange={(e) => setProcessForm({ ...processForm, admin_notes: e.target.value })}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="填写处理说明..."
                  />
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowProcessModal(false);
                  setSelectedOrder(null);
                }}
                className="flex-1 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                {selectedOrder.status === 'pending' ? '取消' : '关闭'}
              </button>
              {selectedOrder.status === 'pending' && (
                <button
                  onClick={handleProcess}
                  className={`flex-1 py-2 text-white rounded-lg ${
                    processForm.action === 'complete'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  {processForm.action === 'complete' ? '确认完成' : '确认拒绝'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminRechargePage;
