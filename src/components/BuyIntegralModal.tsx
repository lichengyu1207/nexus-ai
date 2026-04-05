import React from 'react';
import { XMarkIcon, CheckIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline';

interface IntegralPackage {
  id: string;
  name: string;
  integral: number;
  price: number;
  unit_price: number;
  description: string;
  is_popular: boolean;
}

interface MembershipPlan {
  id: string;
  name: string;
  price: number;
  duration_months: number;
  description: string;
  features: string[];
}

interface BuyIntegralModalProps {
  packages: IntegralPackage[];
  membershipPlans: MembershipPlan[];
  contactWechat: string;
  onClose: () => void;
}

const BuyIntegralModal: React.FC<BuyIntegralModalProps> = ({
  packages,
  membershipPlans,
  contactWechat,
  onClose,
}) => {
  const [copied, setCopied] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState<'integral' | 'membership'>('integral');

  const handleCopyWechat = async () => {
    await navigator.clipboard.writeText(contactWechat);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-900">获取积分</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-100">
          <button
            onClick={() => setActiveTab('integral')}
            className={`flex-1 py-3 text-center font-medium transition-colors ${
              activeTab === 'integral'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            购买积分
          </button>
          <button
            onClick={() => setActiveTab('membership')}
            className={`flex-1 py-3 text-center font-medium transition-colors ${
              activeTab === 'membership'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            升级会员
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {activeTab === 'integral' ? (
            <div className="space-y-4">
              <p className="text-gray-600 text-sm">
                选择适合您的积分套餐，添加客服微信完成充值
              </p>
              
              <div className="grid grid-cols-2 gap-3">
                {packages.map((pkg) => (
                  <div
                    key={pkg.id}
                    className={`relative rounded-xl border-2 p-4 transition-all ${
                      pkg.is_popular
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-primary-300'
                    }`}
                  >
                    {pkg.is_popular && (
                      <div className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-primary-500 text-white text-xs rounded-full">
                        推荐
                      </div>
                    )}
                    <h3 className="font-semibold text-gray-900">{pkg.name}</h3>
                    <p className="text-2xl font-bold text-primary-600 mt-2">
                      ¥{pkg.price}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      {pkg.integral} 积分
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      约 {pkg.unit_price.toFixed(2)} 元/次
                    </p>
                    <p className="text-xs text-gray-500 mt-2">{pkg.description}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-gray-600 text-sm">
                升级会员，享受无限次房产分析服务
              </p>
              
              <div className="space-y-3">
                {membershipPlans.map((plan) => (
                  <div
                    key={plan.id}
                    className="rounded-xl border-2 border-gray-200 p-4 hover:border-primary-300 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900">{plan.name}</h3>
                        <p className="text-sm text-gray-500 mt-1">{plan.description}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-primary-600">
                          ¥{plan.price}
                        </p>
                        <p className="text-xs text-gray-400">/月</p>
                      </div>
                    </div>
                    <ul className="mt-3 space-y-1">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-center gap-2 text-sm text-gray-600">
                          <CheckIcon className="w-4 h-4 text-green-500" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Contact Section */}
        <div className="p-4 bg-gray-50 border-t border-gray-100">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-3">
              添加客服微信，转账后为您充值
            </p>
            <div className="flex items-center justify-center gap-2">
              <span className="text-lg font-bold text-gray-900">{contactWechat}</span>
              <button
                onClick={handleCopyWechat}
                className="flex items-center gap-1 px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors"
              >
                {copied ? (
                  <>
                    <CheckIcon className="w-4 h-4" />
                    已复制
                  </>
                ) : (
                  <>
                    <ClipboardDocumentIcon className="w-4 h-4" />
                    复制微信号
                  </>
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              工作时间: 周一至周五 9:00-18:00
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BuyIntegralModal;
