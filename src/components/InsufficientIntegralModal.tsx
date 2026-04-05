import React from 'react';
import { ExclamationTriangleIcon, ShoppingBagIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

interface InsufficientIntegralModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentBalance: number;
  required: number;
}

const InsufficientIntegralModal: React.FC<InsufficientIntegralModalProps> = ({
  isOpen,
  onClose,
  currentBalance,
  required,
}) => {
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleGoToIntegral = () => {
    onClose();
    navigate('/recharge');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
        <div className="flex items-center justify-center w-16 h-16 mx-auto bg-red-100 rounded-full">
          <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
        </div>
        
        <h3 className="text-xl font-bold text-center text-gray-900 mt-4">
          积分不足
        </h3>
        
        <p className="text-center text-gray-600 mt-2">
          您的积分余额为 <span className="font-bold text-primary-600">{currentBalance}</span>，
          创建分析任务需要 <span className="font-bold">{required}</span> 积分
        </p>

        <div className="bg-gray-50 rounded-lg p-4 mt-4">
          <p className="text-sm text-gray-600">
            您可以：
          </p>
          <ul className="text-sm text-gray-600 mt-2 space-y-1">
            <li>• 购买积分包，继续使用按次计费</li>
            <li>• 升级会员，享受无限次分析</li>
          </ul>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleGoToIntegral}
            className="flex-1 py-2.5 px-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
          >
            <ShoppingBagIcon className="w-5 h-5" />
            获取积分
          </button>
        </div>
      </div>
    </div>
  );
};

export default InsufficientIntegralModal;
