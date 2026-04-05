import React, { useState, useEffect } from 'react';
import { X, CheckCircle, XCircle, AlertTriangle, User, Clock, FileText, Image, History } from 'lucide-react';
import toast from 'react-hot-toast';

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
  user_created_at: string | null;
  user_recharge_count: number;
  user_total_recharge: number;
  processor_email: string | null;
  processor_name: string | null;
  operation_logs: OperationLog[];
}

interface OperationLog {
  id: string;
  admin_id: string;
  operation_type: string;
  before_data: string | null;
  after_data: string | null;
  created_at: string;
}

interface OrderDetailModalProps {
  orderId: string | null;
  onClose: () => void;
  onRefresh: () => void;
}

export default function OrderDetailModal({ orderId, onClose, onRefresh }: OrderDetailModalProps) {
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState<'approve' | 'reject' | 'suspicious' | null>(null);
  const [adminNotes, setAdminNotes] = useState('');
  const [actualIntegral, setActualIntegral] = useState(0);
  const [notifyUser, setNotifyUser] = useState(true);
  const [userCurrentIntegral, setUserCurrentIntegral] = useState(0);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [successData, setSuccessData] = useState({ integral: 0, total: 0 });

  const token = localStorage.getItem('token');

  useEffect(() => {
    if (orderId) {
      fetchOrderDetail();
    }
  }, [orderId]);

  const fetchOrderDetail = async () => {
    if (!token || !orderId) return;
    setLoading(true);
    
    try {
      const res = await fetch(`/api/admin/recharge/orders/${orderId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setOrder(data);
        setActualIntegral(data.integral);
        setUserCurrentIntegral(data.user_integral);
      } else {
        toast.error('获取订单详情失败');
        onClose();
      }
    } catch (error) {
      console.error('Failed to fetch order detail:', error);
      toast.error('获取订单详情失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchUserIntegral = async (userId: string) => {
    if (!token) return;
    
    try {
      const res = await fetch(`/api/admin/users/${userId}/integral`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setUserCurrentIntegral(data.integral);
        return data.integral;
      }
    } catch (error) {
      console.error('Failed to fetch user integral:', error);
    }
    return null;
  };

  const handleReview = async (action: string) => {
    if (!token || !order) return;
    
    setProcessing(true);
    
    try {
      const res = await fetch(`/api/admin/recharge/orders/${order.id}/review`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action,
          actual_integral: action === 'approve' ? actualIntegral : undefined,
          admin_notes: adminNotes || undefined,
          notify_user: notifyUser
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        
        if (action === 'approve') {
          const newIntegral = await fetchUserIntegral(order.user_id);
          setSuccessData({
            integral: actualIntegral,
            total: newIntegral || userCurrentIntegral + actualIntegral
          });
          setShowSuccessModal(true);
        } else {
          toast.success(`订单已${action === 'reject' ? '拒绝' : '标记可疑'}`);
        }
        
        fetchOrderDetail();
        onRefresh();
        setShowConfirmModal(null);
        setAdminNotes('');
      } else {
        const data = await res.json();
        toast.error(data.detail || '操作失败');
      }
    } catch (error) {
      toast.error('操作失败');
    } finally {
      setProcessing(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      approved: 'bg-green-100 text-green-800 border-green-200',
      rejected: 'bg-red-100 text-red-800 border-red-200',
      suspicious: 'bg-orange-100 text-orange-800 border-orange-200'
    };
    const labels: Record<string, string> = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已拒绝',
      suspicious: '可疑'
    };
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium border ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
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

  const getOperationLabel = (type: string) => {
    const labels: Record<string, string> = {
      recharge_approve: '审核通过',
      recharge_reject: '审核拒绝',
      recharge_mark_suspicious: '标记可疑'
    };
    return labels[type] || type;
  };

  if (!orderId) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold">订单详情</h2>
              {order && getStatusBadge(order.status)}
            </div>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-gray-500">加载中...</div>
            </div>
          ) : order ? (
            <div className="flex-1 overflow-y-auto p-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      订单信息
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">订单号</span>
                        <span className="font-mono">{order.order_no}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">充值金额</span>
                        <span className="font-bold text-lg">¥{order.amount.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">应得积分</span>
                        <span className="font-bold text-lg text-blue-600">{order.integral}</span>
                      </div>
                      {order.actual_integral && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">实际发放</span>
                          <span className="font-bold text-lg text-green-600">{order.actual_integral}</span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-gray-500">风险等级</span>
                        {getRiskBadge(order.risk_level)}
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">支付方式</span>
                        <span>{order.payment_method || '银行转账'}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <User className="w-4 h-4" />
                      用户信息
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">邮箱</span>
                        <span>{order.email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">姓名</span>
                        <span>{order.full_name || '-'}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-500">当前积分</span>
                        <span className="font-bold text-lg text-blue-600">{userCurrentIntegral}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">充值次数</span>
                        <span>{order.user_recharge_count} 次</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">累计充值</span>
                        <span>¥{order.user_total_recharge.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      时间信息
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">提交时间</span>
                        <span>{new Date(order.submitted_at).toLocaleString()}</span>
                      </div>
                      {order.processed_at && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">处理时间</span>
                          <span>{new Date(order.processed_at).toLocaleString()}</span>
                        </div>
                      )}
                      {order.processor_email && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">处理人</span>
                          <span>{order.processor_name || order.processor_email}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  {order.proof_image && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                        <Image className="w-4 h-4" />
                        转账凭证
                      </h3>
                      <div className="relative">
                        <img
                          src={order.proof_image}
                          alt="转账凭证"
                          className="w-full rounded-lg border cursor-pointer hover:opacity-90"
                          onClick={() => window.open(order.proof_image!, '_blank')}
                        />
                        <div className="absolute bottom-2 right-2">
                          <button
                            onClick={() => window.open(order.proof_image!, '_blank')}
                            className="px-2 py-1 bg-black/50 text-white text-xs rounded"
                          >
                            查看大图
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {order.user_notes && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-medium text-gray-900 mb-2">用户备注</h3>
                      <p className="text-sm text-gray-600">{order.user_notes}</p>
                    </div>
                  )}
                  
                  {order.admin_notes && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-medium text-gray-900 mb-2">管理员备注</h3>
                      <p className="text-sm text-gray-600">{order.admin_notes}</p>
                    </div>
                  )}
                  
                  {order.operation_logs && order.operation_logs.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                        <History className="w-4 h-4" />
                        操作日志
                      </h3>
                      <div className="space-y-2">
                        {order.operation_logs.map((log) => (
                          <div key={log.id} className="text-sm border-b border-gray-200 pb-2 last:border-0">
                            <div className="flex justify-between">
                              <span className="font-medium">{getOperationLabel(log.operation_type)}</span>
                              <span className="text-gray-500 text-xs">
                                {new Date(log.created_at).toLocaleString()}
                              </span>
                            </div>
                            {log.before_data && log.after_data && (
                              <div className="text-xs text-gray-500 mt-1">
                                {JSON.parse(log.before_data).status} → {JSON.parse(log.after_data).status}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              {order.status === 'pending' && (
                <div className="border-t mt-6 pt-4">
                  <h3 className="text-lg font-medium mb-4">审核操作</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        管理员备注
                      </label>
                      <textarea
                        value={adminNotes}
                        onChange={(e) => setAdminNotes(e.target.value)}
                        placeholder="填写备注信息（如拒绝原因）"
                        rows={3}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="notifyUser"
                        checked={notifyUser}
                        onChange={(e) => setNotifyUser(e.target.checked)}
                        className="rounded"
                      />
                      <label htmlFor="notifyUser" className="text-sm text-gray-600">
                        通知用户处理结果
                      </label>
                    </div>
                    
                    <div className="flex gap-3">
                      <button
                        onClick={() => setShowConfirmModal('approve')}
                        disabled={processing}
                        className="flex-1 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        <CheckCircle className="w-4 h-4" />
                        通过并发放积分
                      </button>
                      <button
                        onClick={() => setShowConfirmModal('reject')}
                        disabled={processing}
                        className="flex-1 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        <XCircle className="w-4 h-4" />
                        拒绝申请
                      </button>
                      <button
                        onClick={() => setShowConfirmModal('suspicious')}
                        disabled={processing}
                        className="flex-1 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        <AlertTriangle className="w-4 h-4" />
                        标记可疑
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {order.status !== 'pending' && (
                <div className="border-t mt-6 pt-4">
                  <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500">
                    订单已 {order.status === 'approved' ? '通过' : order.status === 'rejected' ? '拒绝' : '标记可疑'}
                    {order.processed_at && (
                      <span className="ml-2">· 处理时间：{new Date(order.processed_at).toLocaleString()}</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
      
      {showConfirmModal && order && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
          <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] flex flex-col">
            <div className="p-6 overflow-y-auto flex-1">
              <h3 className="text-lg font-bold mb-4">
                {showConfirmModal === 'approve' ? '确认通过该充值申请？' : 
                 showConfirmModal === 'reject' ? '确认拒绝该充值申请？' : 
                 '确认标记该订单为可疑？'}
              </h3>
              
              <div className="space-y-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-500">用户</div>
                  <div className="font-medium">{order.email}</div>
                </div>
                
                {showConfirmModal === 'approve' && (
                  <>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        实际发放积分
                      </label>
                      <input
                        type="number"
                        value={actualIntegral}
                        onChange={(e) => setActualIntegral(parseFloat(e.target.value) || 0)}
                        className="w-full px-3 py-2 border rounded-lg"
                      />
                    </div>
                    
                    <div className="bg-blue-50 rounded-lg p-3">
                      <div className="text-sm text-blue-600">
                        发放后用户积分：<span className="font-bold">{userCurrentIntegral} + {actualIntegral} = {userCurrentIntegral + actualIntegral}</span>
                      </div>
                    </div>
                  </>
                )}
                
                {showConfirmModal === 'reject' && (
                  <div className="bg-red-50 rounded-lg p-3">
                    <div className="text-sm text-red-600">
                      拒绝后用户将收到通知，积分不会发生变化
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <div className="p-4 border-t flex gap-3 bg-white rounded-b-xl">
              <button
                onClick={() => setShowConfirmModal(null)}
                className="flex-1 py-2 border rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={() => handleReview(showConfirmModal === 'suspicious' ? 'mark_suspicious' : showConfirmModal)}
                disabled={processing}
                className={`flex-1 py-2 text-white rounded-lg disabled:opacity-50 ${
                  showConfirmModal === 'approve' ? 'bg-green-500 hover:bg-green-600' :
                  showConfirmModal === 'reject' ? 'bg-red-500 hover:bg-red-600' :
                  'bg-orange-500 hover:bg-orange-600'
                }`}
              >
                {processing ? '处理中...' : '确认'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {showSuccessModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
          <div className="bg-white rounded-xl max-w-sm w-full p-6 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">积分发放成功</h3>
            <div className="space-y-2 mb-6">
              <div className="text-sm text-gray-500">
                用户：<span className="text-gray-900">{order?.email}</span>
              </div>
              <div className="text-sm text-gray-500">
                发放积分：<span className="text-green-600 font-bold text-lg">{successData.integral}</span>
              </div>
              <div className="text-sm text-gray-500">
                当前总积分：<span className="text-blue-600 font-bold text-lg">{successData.total}</span>
              </div>
            </div>
            <button
              onClick={() => {
                setShowSuccessModal(false);
                onClose();
              }}
              className="w-full py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              确定
            </button>
          </div>
        </div>
      )}
    </>
  );
}
