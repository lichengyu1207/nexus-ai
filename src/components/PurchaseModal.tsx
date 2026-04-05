import React, { useState, useEffect } from 'react';
import { XMarkIcon, QrCodeIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface Plan {
  id: string;
  name: string;
  final_price: number;
  original_price: number;
  discount_reason: string | null;
  credits: number | null;
}

interface PurchaseModalProps {
  plan: Plan;
  onClose: () => void;
  onSuccess: () => void;
}

const PurchaseModal: React.FC<PurchaseModalProps> = ({ plan, onClose, onSuccess }) => {
  const [paymentMethod, setPaymentMethod] = useState<'wechat' | 'alipay'>('wechat');
  const [orderId, setOrderId] = useState<string | null>(null);
  const [qrCodeUrl, setQrCodeUrl] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [isPaid, setIsPaid] = useState(false);

  useEffect(() => {
    createOrder();
  }, []);

  useEffect(() => {
    if (!isPolling || !orderId || isPaid) return;

    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/orders/${orderId}/status`);
        if (response.data.status === 'paid') {
          setIsPaid(true);
          setIsPolling(false);
          showToast.success('支付成功！');
          setTimeout(() => {
            onSuccess();
          }, 1500);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isPolling, orderId, isPaid, onSuccess]);

  const createOrder = async () => {
    try {
      const response = await api.post('/orders/create', {
        plan_id: plan.id,
        payment_method: paymentMethod,
      });
      setOrderId(response.data.id);
      setQrCodeUrl(response.data.qr_code_url);
      setIsPolling(true);
    } catch (error) {
      showToast.error('创建订单失败');
    }
  };

  const handleSimulatePay = async () => {
    if (!orderId) return;
    
    try {
      await api.post(`/orders/${orderId}/simulate-pay`);
      setIsPaid(true);
      setIsPolling(false);
      showToast.success('支付成功！');
      setTimeout(() => {
        onSuccess();
      }, 1500);
    } catch (error) {
      showToast.error('支付失败');
    }
  };

  const formatPrice = (price: number) => {
    return (price / 100).toFixed(2);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />
        
        <div className="relative bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>

          {isPaid ? (
            <div className="text-center py-8">
              <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-gray-900 mb-2">支付成功</h3>
              <p className="text-gray-600">
                {plan.credits ? `已获得 ${plan.credits} 次分析` : '会员已开通'}
              </p>
            </div>
          ) : (
            <>
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                购买 {plan.name}
              </h3>

              <div className="bg-gray-50 rounded-xl p-4 mb-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">套餐</span>
                  <span className="font-medium">{plan.name}</span>
                </div>
                <div className="flex justify-between items-center mt-2">
                  <span className="text-gray-600">金额</span>
                  <div>
                    {plan.discount_reason && (
                      <span className="text-sm text-gray-400 line-through mr-2">
                        ¥{formatPrice(plan.original_price)}
                      </span>
                    )}
                    <span className="font-bold text-primary-600">
                      ¥{formatPrice(plan.final_price)}
                    </span>
                  </div>
                </div>
                {plan.discount_reason && (
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-gray-600">优惠</span>
                    <span className="text-red-500 text-sm">{plan.discount_reason}</span>
                  </div>
                )}
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">支付方式</p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setPaymentMethod('wechat')}
                    className={`flex-1 py-2 rounded-lg border ${
                      paymentMethod === 'wechat'
                        ? 'border-green-500 bg-green-50 text-green-600'
                        : 'border-gray-200'
                    }`}
                  >
                    微信支付
                  </button>
                  <button
                    onClick={() => setPaymentMethod('alipay')}
                    className={`flex-1 py-2 rounded-lg border ${
                      paymentMethod === 'alipay'
                        ? 'border-blue-500 bg-blue-50 text-blue-600'
                        : 'border-gray-200'
                    }`}
                  >
                    支付宝
                  </button>
                </div>
              </div>

              {qrCodeUrl && (
                <div className="text-center mb-4">
                  <div className="bg-white p-4 rounded-xl inline-block border">
                    <img src={qrCodeUrl} alt="支付二维码" className="w-48 h-48" />
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    请使用{paymentMethod === 'wechat' ? '微信' : '支付宝'}扫码支付
                  </p>
                  {orderId && (
                    <p className="text-xs text-gray-400 mt-1">
                      订单号: {orderId}
                    </p>
                  )}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={onClose}
                  className="flex-1 py-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleSimulatePay}
                  className="flex-1 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  我已支付
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PurchaseModal;
