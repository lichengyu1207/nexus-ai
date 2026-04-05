import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Link } from 'react-router-dom';
import { CheckIcon, SparklesIcon, ChatBubbleLeftRightIcon, DocumentDuplicateIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';
import PurchaseModal from '@/components/PurchaseModal';
import ContactModal from '@/components/ContactModal';
import { SkeletonCard } from '@/components/Skeleton';

interface Plan {
  id: string;
  name: string;
  type: string;
  original_price: number;
  final_price: number;
  discount_reason: string | null;
  credits: number | null;
  duration_days: number;
  features: string[];
  is_popular: boolean;
}

interface RechargeOrder {
  id: string;
  amount: number;
  credits: number | null;
  status: string;
  user_notes: string | null;
  admin_notes: string | null;
  created_at: string;
  completed_at: string | null;
}

const RechargePage: React.FC = () => {
  const { user } = useAuth();
  const [integralPlans, setIntegralPlans] = useState<Plan[]>([]);
  const [memberPlans, setMemberPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [showPurchase, setShowPurchase] = useState(false);
  const [showContact, setShowContact] = useState(false);
  const [showManualRecharge, setShowManualRecharge] = useState(false);
  const [myOrders, setMyOrders] = useState<RechargeOrder[]>([]);
  const [manualForm, setManualForm] = useState({
    amount: '',
    credits: '',
    notes: ''
  });

  useEffect(() => {
    loadPlans();
    loadMyOrders();
  }, []);

  const loadPlans = async () => {
    try {
      const response = await api.get('/plans');
      const plans = response.data;
      setIntegralPlans(plans.filter((p: Plan) => p.type === 'integral'));
      setMemberPlans(plans.filter((p: Plan) => ['professional', 'enterprise'].includes(p.type)));
    } catch (error) {
      showToast.error('加载套餐失败');
    } finally {
      setIsLoading(false);
    }
  };

  const loadMyOrders = async () => {
    try {
      const response = await api.get('/recharge/my-orders');
      setMyOrders(response.data);
    } catch (error) {
      console.error('Failed to load orders:', error);
    }
  };

  const handlePurchase = (plan: Plan) => {
    setSelectedPlan(plan);
    setShowPurchase(true);
  };

  const handleContact = () => {
    setShowContact(true);
  };

  const handleCopyWechat = () => {
    navigator.clipboard.writeText('svip6763');
    showToast.success('微信号已复制');
  };

  const handleSubmitManualRecharge = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!manualForm.amount || parseFloat(manualForm.amount) <= 0) {
      showToast.error('请输入正确的转账金额');
      return;
    }

    try {
      await api.post('/recharge/apply', {
        amount: parseFloat(manualForm.amount),
        credits: manualForm.credits ? parseInt(manualForm.credits) : null,
        notes: manualForm.notes || null
      });
      
      showToast.success('充值申请已提交，管理员将在24小时内处理');
      setShowManualRecharge(false);
      setManualForm({ amount: '', credits: '', notes: '' });
      loadMyOrders();
    } catch (error) {
      showToast.error('提交失败，请稍后重试');
    }
  };

  const formatPrice = (price: number) => {
    return (price / 100).toFixed(2);
  };

  const getUnitPrice = (plan: Plan) => {
    if (plan.credits) {
      return (plan.final_price / 100 / plan.credits).toFixed(2);
    }
    return null;
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      pending: '待处理',
      completed: '已完成',
      rejected: '已拒绝'
    };
    return statusMap[status] || status;
  };

  const getStatusColor = (status: string) => {
    const colorMap: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      completed: 'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700'
    };
    return colorMap[status] || 'bg-gray-100 text-gray-700';
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <SkeletonCard className="mb-8" />
        <div className="grid md:grid-cols-3 gap-6">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Current Status */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-500 rounded-2xl p-6 text-white mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">充值中心</h1>
            <p className="opacity-90">
              当前积分：<span className="font-bold text-2xl">{user?.integral || 0}</span> 次
            </p>
            {user?.membership_level && user.membership_level !== 'free' && (
              <p className="opacity-90 mt-1">
                会员等级：<span className="font-medium">{user.membership_level === 'professional' ? '专业版' : '企业版'}</span>
              </p>
            )}
          </div>
          <SparklesIcon className="w-16 h-16 opacity-50" />
        </div>
      </div>

      {/* Integral Plans */}
      <section className="mb-12">
        <h2 className="text-xl font-bold text-gray-900 mb-6">积分充值</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {integralPlans.map((plan) => (
            <div
              key={plan.id}
              className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow"
            >
              <div className="text-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
                <div className="mt-2">
                  {plan.discount_reason && (
                    <span className="text-sm text-gray-400 line-through mr-2">
                      ¥{formatPrice(plan.original_price)}
                    </span>
                  )}
                  <span className="text-3xl font-bold text-primary-600">
                    ¥{formatPrice(plan.final_price)}
                  </span>
                </div>
                {plan.discount_reason && (
                  <span className="inline-block mt-2 px-2 py-1 bg-red-100 text-red-600 text-xs rounded-full">
                    {plan.discount_reason}
                  </span>
                )}
                {getUnitPrice(plan) && (
                  <p className="text-sm text-gray-500 mt-1">
                    约 {getUnitPrice(plan)} 元/次
                  </p>
                )}
              </div>

              <ul className="space-y-2 mb-6">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm text-gray-600">
                    <CheckIcon className="w-4 h-4 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handlePurchase(plan)}
                className="w-full py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                立即购买
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Member Plans */}
      <section className="mb-12">
        <h2 className="text-xl font-bold text-gray-900 mb-6">开通会员</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {memberPlans.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl shadow-lg p-6 ${
                plan.is_popular ? 'ring-2 ring-primary-500' : ''
              }`}
            >
              {plan.is_popular && (
                <div className="text-center -mt-8 mb-4">
                  <span className="bg-primary-600 text-white px-4 py-1 rounded-full text-sm">
                    最受欢迎
                  </span>
                </div>
              )}

              <div className="text-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
                <div className="mt-2">
                  {plan.discount_reason && (
                    <span className="text-sm text-gray-400 line-through mr-2">
                      ¥{formatPrice(plan.original_price)}/月
                    </span>
                  )}
                  <span className="text-3xl font-bold text-primary-600">
                    ¥{formatPrice(plan.final_price)}
                  </span>
                  <span className="text-gray-500">/月</span>
                </div>
                {plan.discount_reason && (
                  <span className="inline-block mt-2 px-2 py-1 bg-red-100 text-red-600 text-xs rounded-full">
                    {plan.discount_reason}
                  </span>
                )}
                <p className="text-sm text-gray-500 mt-1">
                  约 {(plan.final_price / 100 / 30).toFixed(1)} 元/天
                </p>
              </div>

              <ul className="space-y-2 mb-6">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm text-gray-600">
                    <CheckIcon className="w-4 h-4 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={handleContact}
                className={`w-full py-2 rounded-lg transition-colors ${
                  plan.is_popular
                    ? 'bg-primary-600 text-white hover:bg-primary-700'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                }`}
              >
                联系销售
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Manual Recharge Section */}
      <section className="mb-12">
        <h2 className="text-xl font-bold text-gray-900 mb-6">人工充值</h2>
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* WeChat QR Code */}
            <div className="flex-shrink-0 text-center">
              <div className="w-48 h-48 bg-gray-100 rounded-xl flex items-center justify-center mb-3 mx-auto">
                <div className="text-gray-400 text-sm text-center">
                  <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto mb-2" />
                  微信二维码
                </div>
              </div>
              <div className="flex items-center justify-center gap-2">
                <span className="text-gray-600">微信号：</span>
                <span className="font-medium text-primary-600">svip6763</span>
                <button
                  onClick={handleCopyWechat}
                  className="p-1 hover:bg-gray-100 rounded"
                  title="复制微信号"
                >
                  <DocumentDuplicateIcon className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            </div>

            {/* Instructions */}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-3">充值说明</h3>
              <ol className="space-y-2 text-gray-600 text-sm">
                <li className="flex gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs">1</span>
                  添加上方微信，转账您想要充值的金额
                </li>
                <li className="flex gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs">2</span>
                  点击下方"提交充值申请"按钮，填写转账信息
                </li>
                <li className="flex gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs">3</span>
                  管理员核实后将在24小时内为您增加积分
                </li>
              </ol>
              
              <button
                onClick={() => setShowManualRecharge(true)}
                className="mt-4 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                提交充值申请
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* My Recharge Orders */}
      {myOrders.length > 0 && (
        <section className="mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-6">我的充值记录</h2>
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">申请时间</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">金额</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">积分</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">备注</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {myOrders.map((order) => (
                  <tr key={order.id}>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {new Date(order.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      ¥{order.amount}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {order.credits || '-'}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(order.status)}`}>
                        {getStatusText(order.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {order.admin_notes || order.user_notes || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Purchase Modal */}
      {showPurchase && selectedPlan && (
        <PurchaseModal
          plan={selectedPlan}
          onClose={() => setShowPurchase(false)}
          onSuccess={() => {
            setShowPurchase(false);
            loadPlans();
          }}
        />
      )}

      {/* Contact Modal */}
      {showContact && (
        <ContactModal onClose={() => setShowContact(false)} />
      )}

      {/* Manual Recharge Modal */}
      {showManualRecharge && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">提交充值申请</h3>
            
            <form onSubmit={handleSubmitManualRecharge} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  转账金额 (元) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={manualForm.amount}
                  onChange={(e) => setManualForm({ ...manualForm, amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="请输入转账金额"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  期望获得积分
                </label>
                <input
                  type="number"
                  value={manualForm.credits}
                  onChange={(e) => setManualForm({ ...manualForm, credits: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="可选，由管理员确认"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  备注
                </label>
                <textarea
                  value={manualForm.notes}
                  onChange={(e) => setManualForm({ ...manualForm, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  rows={3}
                  placeholder="如有特殊说明请填写"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowManualRecharge(false)}
                  className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  提交申请
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default RechargePage;
