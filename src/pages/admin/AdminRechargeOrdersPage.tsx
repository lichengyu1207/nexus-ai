import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, CheckCircle, XCircle, AlertTriangle, Eye, ChevronLeft, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';
import OrderDetailModal from '../../components/OrderDetailModal';

interface Order {
  id: string;
  order_no: string;
  user_id: string;
  email: string;
  full_name: string;
  amount: number;
  integral: number;
  actual_integral: number | null;
  status: string;
  risk_level: string;
  payment_method: string;
  proof_image: string | null;
  user_notes: string | null;
  admin_notes: string | null;
  submitted_at: string;
  processed_at: string | null;
  user_integral: number;
}

interface Stats {
  today: { count: number; amount: number };
  month: { count: number; amount: number };
  total: { count: number; amount: number };
  pending_count: number;
  avg_process_time_hours: number;
}

export default function AdminRechargeOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedOrders, setSelectedOrders] = useState<string[]>([]);
  const [showDetail, setShowDetail] = useState<string | null>(null);
  const [reviewModal, setReviewModal] = useState<{ order: Order; action: string } | null>(null);
  
  const [filters, setFilters] = useState({
    status: '',
    risk_level: '',
    min_amount: '',
    max_amount: '',
    start_date: '',
    end_date: '',
    search: ''
  });
  
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0
  });

  const token = localStorage.getItem('token');

  const fetchOrders = async () => {
    if (!token) return;
    setLoading(true);
    
    try {
      const params = new URLSearchParams();
      params.append('page', pagination.page.toString());
      params.append('limit', pagination.limit.toString());
      
      if (filters.status) params.append('status', filters.status);
      if (filters.risk_level) params.append('risk_level', filters.risk_level);
      if (filters.min_amount) params.append('min_amount', filters.min_amount);
      if (filters.max_amount) params.append('max_amount', filters.max_amount);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);

      const res = await fetch(`/api/admin/recharge/orders?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setOrders(data.orders);
        setPagination(prev => ({ ...prev, total: data.total }));
      }
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    if (!token) return;
    
    try {
      const res = await fetch('/api/admin/recharge/stats/overview', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    fetchOrders();
    fetchStats();
  }, [pagination.page, filters]);

  const handleReview = async (orderId: string, action: string, actualIntegral?: number, adminNotes?: string) => {
    if (!token) return;
    
    try {
      const res = await fetch(`/api/admin/recharge/orders/${orderId}/review`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action,
          actual_integral: actualIntegral,
          admin_notes: adminNotes,
          notify_user: true
        })
      });
      
      if (res.ok) {
        toast.success(`订单已${action === 'approve' ? '通过' : action === 'reject' ? '拒绝' : '标记可疑'}`);
        fetchOrders();
        fetchStats();
        setReviewModal(null);
      } else {
        const data = await res.json();
        toast.error(data.detail || '操作失败');
      }
    } catch (error) {
      toast.error('操作失败');
    }
  };

  const handleBatchReview = async (action: string) => {
    if (selectedOrders.length === 0) {
      toast.error('请选择订单');
      return;
    }
    
    if (!confirm(`确定要批量${action === 'approve' ? '通过' : '拒绝'} ${selectedOrders.length} 个订单吗？`)) {
      return;
    }
    
    if (!token) return;
    
    try {
      const res = await fetch('/api/admin/recharge/orders/batch-review', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          order_ids: selectedOrders,
          action
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`成功处理 ${data.success} 个订单`);
        setSelectedOrders([]);
        fetchOrders();
        fetchStats();
      }
    } catch (error) {
      toast.error('批量操作失败');
    }
  };

  const handleExport = async () => {
    if (!token) return;
    
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.risk_level) params.append('risk_level', filters.risk_level);
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    
    window.open(`/api/admin/recharge/orders/export?${params}&token=${token}`, '_blank');
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      suspicious: 'bg-orange-100 text-orange-800'
    };
    const labels: Record<string, string> = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已拒绝',
      suspicious: '可疑'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getRiskBadge = (riskLevel: string) => {
    const styles: Record<string, string> = {
      low: 'bg-green-50 text-green-600 border-green-200',
      medium: 'bg-yellow-50 text-yellow-600 border-yellow-200',
      high: 'bg-red-50 text-red-600 border-red-200'
    };
    const labels: Record<string, string> = {
      low: '低风险',
      medium: '中风险',
      high: '高风险'
    };
    return (
      <span className={`px-2 py-1 rounded border text-xs ${styles[riskLevel] || 'bg-gray-50 text-gray-600'}`}>
        {labels[riskLevel] || riskLevel}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">充值订单管理</h1>
          <p className="text-gray-500 mt-1">管理用户充值申请，审核并发放积分</p>
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="text-sm text-gray-500">今日充值</div>
              <div className="text-2xl font-bold text-gray-900">¥{stats.today.amount.toFixed(2)}</div>
              <div className="text-xs text-gray-400">{stats.today.count} 笔</div>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="text-sm text-gray-500">本月充值</div>
              <div className="text-2xl font-bold text-gray-900">¥{stats.month.amount.toFixed(2)}</div>
              <div className="text-xs text-gray-400">{stats.month.count} 笔</div>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="text-sm text-gray-500">累计充值</div>
              <div className="text-2xl font-bold text-gray-900">¥{stats.total.amount.toFixed(2)}</div>
              <div className="text-xs text-gray-400">{stats.total.count} 笔</div>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="text-sm text-gray-500">待处理</div>
              <div className="text-2xl font-bold text-orange-500">{stats.pending_count}</div>
              <div className="text-xs text-gray-400">平均处理 {stats.avg_process_time_hours}h</div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="p-4 border-b">
            <div className="flex flex-wrap gap-4">
              <select
                value={filters.status}
                onChange={e => setFilters({ ...filters, status: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm"
              >
                <option value="">全部状态</option>
                <option value="pending">待审核</option>
                <option value="approved">已通过</option>
                <option value="rejected">已拒绝</option>
                <option value="suspicious">可疑</option>
              </select>
              
              <select
                value={filters.risk_level}
                onChange={e => setFilters({ ...filters, risk_level: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm"
              >
                <option value="">全部风险</option>
                <option value="low">低风险</option>
                <option value="medium">中风险</option>
                <option value="high">高风险</option>
              </select>
              
              <input
                type="date"
                value={filters.start_date}
                onChange={e => setFilters({ ...filters, start_date: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm"
                placeholder="开始日期"
              />
              
              <input
                type="date"
                value={filters.end_date}
                onChange={e => setFilters({ ...filters, end_date: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm"
                placeholder="结束日期"
              />
              
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 text-sm"
              >
                <Download className="w-4 h-4" />
                导出
              </button>
            </div>
          </div>

          {selectedOrders.length > 0 && (
            <div className="px-4 py-2 bg-blue-50 border-b flex items-center gap-4">
              <span className="text-sm text-blue-700">已选择 {selectedOrders.length} 个订单</span>
              <button
                onClick={() => handleBatchReview('approve')}
                className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
              >
                批量通过
              </button>
              <button
                onClick={() => handleBatchReview('reject')}
                className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
              >
                批量拒绝
              </button>
              <button
                onClick={() => setSelectedOrders([])}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                取消选择
              </button>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">
                    <input
                      type="checkbox"
                      checked={selectedOrders.length === orders.length && orders.length > 0}
                      onChange={e => {
                        if (e.target.checked) {
                          setSelectedOrders(orders.filter(o => o.status === 'pending').map(o => o.id));
                        } else {
                          setSelectedOrders([]);
                        }
                      }}
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">订单号</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">用户</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">金额</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">积分</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">状态</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">风险</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">提交时间</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {loading ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-gray-500">加载中...</td>
                  </tr>
                ) : orders.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-gray-500">暂无订单</td>
                  </tr>
                ) : (
                  orders.map(order => (
                    <tr key={order.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        {order.status === 'pending' && (
                          <input
                            type="checkbox"
                            checked={selectedOrders.includes(order.id)}
                            onChange={e => {
                              if (e.target.checked) {
                                setSelectedOrders([...selectedOrders, order.id]);
                              } else {
                                setSelectedOrders(selectedOrders.filter(id => id !== order.id));
                              }
                            }}
                          />
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm font-mono">{order.order_no}</td>
                      <td className="px-4 py-3">
                        <div className="text-sm">{order.email}</div>
                        <div className="text-xs text-gray-500">{order.full_name}</div>
                      </td>
                      <td className="px-4 py-3 text-sm font-medium">¥{order.amount.toFixed(2)}</td>
                      <td className="px-4 py-3 text-sm">{order.integral}</td>
                      <td className="px-4 py-3">{getStatusBadge(order.status)}</td>
                      <td className="px-4 py-3">{getRiskBadge(order.risk_level)}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {new Date(order.submitted_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setShowDetail(order.id)}
                            className="p-1 hover:bg-gray-100 rounded"
                            title="查看详情"
                          >
                            <Eye className="w-4 h-4 text-gray-500" />
                          </button>
                          {order.status === 'pending' && (
                            <>
                              <button
                                onClick={() => setReviewModal({ order, action: 'approve' })}
                                className="p-1 hover:bg-green-50 rounded"
                                title="通过"
                              >
                                <CheckCircle className="w-4 h-4 text-green-500" />
                              </button>
                              <button
                                onClick={() => setReviewModal({ order, action: 'reject' })}
                                className="p-1 hover:bg-red-50 rounded"
                                title="拒绝"
                              >
                                <XCircle className="w-4 h-4 text-red-500" />
                              </button>
                              <button
                                onClick={() => setReviewModal({ order, action: 'mark_suspicious' })}
                                className="p-1 hover:bg-orange-50 rounded"
                                title="标记可疑"
                              >
                                <AlertTriangle className="w-4 h-4 text-orange-500" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="px-4 py-3 border-t flex items-center justify-between">
            <div className="text-sm text-gray-500">
              共 {pagination.total} 条记录
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={pagination.page === 1}
                className="p-2 border rounded hover:bg-gray-50 disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm">
                第 {pagination.page} / {Math.ceil(pagination.total / pagination.limit)} 页
              </span>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={pagination.page >= Math.ceil(pagination.total / pagination.limit)}
                className="p-2 border rounded hover:bg-gray-50 disabled:opacity-50"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {reviewModal && (
        <ReviewModal
          order={reviewModal.order}
          action={reviewModal.action}
          onConfirm={(actualIntegral, adminNotes) => handleReview(reviewModal.order.id, reviewModal.action, actualIntegral, adminNotes)}
          onClose={() => setReviewModal(null)}
        />
      )}

      {showDetail && (
        <OrderDetailModal
          orderId={showDetail}
          onClose={() => setShowDetail(null)}
          onRefresh={() => { fetchOrders(); fetchStats(); }}
        />
      )}
    </div>
  );
}

function ReviewModal({ order, action, onConfirm, onClose }: {
  order: Order;
  action: string;
  onConfirm: (actualIntegral?: number, adminNotes?: string) => void;
  onClose: () => void;
}) {
  const [actualIntegral, setActualIntegral] = useState(order.integral);
  const [adminNotes, setAdminNotes] = useState('');

  const actionLabels: Record<string, string> = {
    approve: '通过',
    reject: '拒绝',
    mark_suspicious: '标记可疑'
  };

  const actionColors: Record<string, string> = {
    approve: 'bg-green-500 hover:bg-green-600',
    reject: 'bg-red-500 hover:bg-red-600',
    mark_suspicious: 'bg-orange-500 hover:bg-orange-600'
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-start justify-center z-50 p-4 overflow-y-auto" style={{ minHeight: '100vh' }}>
      <div className="bg-white rounded-xl max-w-md w-full my-8 flex flex-col" style={{ maxHeight: 'calc(100vh - 4rem)' }}>
        <div className="p-6 overflow-y-auto flex-1">
          <h3 className="text-lg font-bold mb-4">
            {actionLabels[action]}订单
          </h3>
          
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-sm text-gray-500">订单号</div>
              <div className="font-mono">{order.order_no}</div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-sm text-gray-500">用户</div>
              <div>{order.email}</div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-500">充值金额</div>
                <div className="font-bold">¥{order.amount.toFixed(2)}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-500">应得积分</div>
                <div className="font-bold">{order.integral}</div>
              </div>
            </div>
            
            {action === 'approve' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  实际发放积分
                </label>
                <input
                  type="number"
                  value={actualIntegral}
                  onChange={e => setActualIntegral(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                备注
              </label>
              <textarea
                value={adminNotes}
                onChange={e => setAdminNotes(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                rows={3}
                placeholder="请输入审核备注..."
              />
            </div>
          </div>
        </div>
        
        <div className="flex gap-3 p-6 pt-4 border-t bg-white rounded-b-xl">
          <button
            onClick={onClose}
            className="flex-1 py-3 border rounded-lg hover:bg-gray-50 text-base"
          >
            取消
          </button>
          <button
            onClick={() => onConfirm(action === 'approve' ? actualIntegral : undefined, adminNotes || undefined)}
            className={`flex-1 py-3 text-white rounded-lg text-base ${actionColors[action]}`}
          >
            确认{actionLabels[action]}
          </button>
        </div>
      </div>
    </div>
  );
}
