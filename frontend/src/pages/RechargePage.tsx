import React, { useState, useEffect } from 'react';

interface Plan {
  id: string;
  name: string;
  price: number;
  integral: number;
  description: string;
  popular?: boolean;
}

interface RechargeOrder {
  id: string;
  amount: number;
  integral: number;
  status: string;
  created_at: string;
  payment_proof_url: string | null;
}

const RechargePage: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([
    { id: '1', name: '体验包', price: 19, integral: 10, description: '适合初次体验' },
    { id: '2', name: '标准包', price: 49, integral: 30, description: '最受欢迎', popular: true },
    { id: '3', name: '专业包', price: 99, integral: 70, description: '专业用户首选' },
    { id: '4', name: '企业包', price: 199, integral: 150, description: '团队协作必备' },
  ]);
  
  const [orders, setOrders] = useState<RechargeOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    amount: 0,
    expected_integral: 0,
    wechat_transaction_id: '',
    notes: '',
  });

  useEffect(() => {
    fetchOrders();
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/plans', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.plans && data.plans.length > 0) {
          setPlans(data.plans);
        }
      }
    } catch (error) {
      console.error('Failed to fetch plans:', error);
    }
  };

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/recharge/orders', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setOrders(data.orders || []);
      }
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const openPurchaseModal = (plan: Plan) => {
    setSelectedPlan(plan);
    setFormData({
      amount: plan.price,
      expected_integral: plan.integral,
      wechat_transaction_id: '',
      notes: '',
    });
    setShowModal(true);
  };

  const handleSubmit = async () => {
    if (!formData.wechat_transaction_id) {
      alert('请输入微信转账单号');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/recharge/apply', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        alert('申请已提交，请等待管理员审核');
        setShowModal(false);
        fetchOrders();
      } else {
        const error = await response.json();
        alert(error.detail || '提交失败');
      }
    } catch (error) {
      console.error('Failed to submit:', error);
      alert('提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      approved: 'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const getStatusName = (status: string) => {
    const names: Record<string, string> = {
      pending: '待处理',
      approved: '已完成',
      rejected: '已拒绝',
    };
    return names[status] || status;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">积分充值</h1>
      
      {/* 充值套餐 */}
      <div className="mb-8">
        <h2 className="text-lg font-medium mb-4">选择套餐</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-lg shadow p-6 relative cursor-pointer hover:shadow-lg transition-shadow ${
                plan.popular ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => openPurchaseModal(plan)}
            >
              {plan.popular && (
                <div className="absolute -top-2 left-1/2 -translate-x-1/2 bg-primary text-white text-xs px-3 py-1 rounded-full">
                  推荐
                </div>
              )}
              <h3 className="text-lg font-medium text-center">{plan.name}</h3>
              <div className="text-center my-4">
                <span className="text-3xl font-bold text-primary">¥{plan.price}</span>
              </div>
              <div className="text-center text-gray-500 mb-4">
                {plan.integral} 积分
              </div>
              <p className="text-sm text-gray-400 text-center">{plan.description}</p>
              <button className="w-full mt-4 bg-primary text-white py-2 rounded-lg hover:bg-primaryDark transition-colors">
                立即购买
              </button>
            </div>
          ))}
        </div>
      </div>
      
      {/* 充值说明 */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-medium mb-4">充值说明</h2>
        <div className="space-y-3 text-gray-600">
          <p>1. 选择套餐后，请通过微信转账完成支付</p>
          <p>2. 转账完成后，在弹出的表单中填写转账单号</p>
          <p>3. 管理员审核通过后，积分将自动到账</p>
          <p>4. 如有问题，请联系客服微信：fangtan_ai</p>
        </div>
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-500">收款微信</p>
          <p className="text-lg font-medium">fangtan_ai（房都督AI官方）</p>
        </div>
      </div>
      
      {/* 充值记录 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-lg font-medium">充值记录</h2>
        </div>
        
        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : orders.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无充值记录</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">金额</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">积分</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {orders.map((order) => (
                <tr key={order.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(order.created_at).toLocaleString('zh-CN')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    ¥{order.amount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {order.integral} 积分
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(order.status)}`}>
                      {getStatusName(order.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      
      {/* 购买弹窗 */}
      {showModal && selectedPlan && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">确认购买 - {selectedPlan.name}</h3>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="flex justify-between mb-2">
                <span className="text-gray-500">支付金额</span>
                <span className="font-medium">¥{selectedPlan.price}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">获得积分</span>
                <span className="font-medium text-primary">{selectedPlan.integral} 积分</span>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="bg-blue-50 rounded-lg p-4 text-sm">
                <p className="font-medium text-blue-700 mb-2">请转账至以下微信账号：</p>
                <p className="text-blue-600">微信号：fangtan_ai</p>
                <p className="text-blue-600">金额：¥{selectedPlan.price}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  微信转账单号 *
                </label>
                <input
                  type="text"
                  value={formData.wechat_transaction_id}
                  onChange={(e) => setFormData({ ...formData, wechat_transaction_id: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  placeholder="在微信转账记录中查看"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  备注（可选）
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  rows={2}
                  placeholder="如有特殊要求请备注"
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primaryDark disabled:opacity-50"
              >
                {submitting ? '提交中...' : '确认提交'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RechargePage;
