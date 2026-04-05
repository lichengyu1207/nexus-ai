import React, { useState } from 'react';
import { pointsApi } from '../../api/points';

interface RegisterSuccessModalProps {
  bonus: number;
  onClose: () => void;
}

export const RegisterSuccessModal: React.FC<RegisterSuccessModalProps> = ({
  bonus,
  onClose,
}) => {
  const [wechatAdded, setWechatAdded] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleWechatAdded = async () => {
    setLoading(true);
    try {
      await pointsApi.markWechatAdded();
      setWechatAdded(true);
    } catch (error) {
      console.error('Failed to mark wechat added:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyWechat = () => {
    navigator.clipboard.writeText('svip6763');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
        <div className="bg-gradient-to-r from-blue-500 to-purple-500 p-6 text-white text-center">
          <div className="text-5xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold mb-2">注册成功！</h2>
          <p className="opacity-90">欢迎加入房都督</p>
        </div>

        <div className="p-6">
          <div className="bg-blue-50 rounded-xl p-4 mb-6 text-center">
            <p className="text-gray-600 mb-2">恭喜您获得</p>
            <div className="text-4xl font-bold text-blue-600 mb-1">{bonus} 积分</div>
            <p className="text-sm text-gray-500">可兑换 {bonus * 100} Token</p>
          </div>

          {!wechatAdded ? (
            <div className="mb-6">
              <div className="text-center mb-4">
                <h3 className="font-bold text-gray-800 mb-1">添加创始人微信</h3>
                <p className="text-sm text-gray-500">获取更多福利和专属服务</p>
              </div>

              <div className="flex justify-center mb-4">
                <div className="bg-gray-100 p-4 rounded-xl">
                  <div className="w-32 h-32 bg-white rounded-lg flex items-center justify-center text-gray-400">
                    <div className="text-center">
                      <div className="text-4xl mb-2">📱</div>
                      <div className="text-xs">扫码添加</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center gap-2 mb-4">
                <span className="text-gray-600">微信号：</span>
                <span className="font-bold text-lg">svip6763</span>
                <button
                  onClick={handleCopyWechat}
                  className="px-2 py-1 text-xs bg-gray-100 rounded hover:bg-gray-200"
                >
                  复制
                </button>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleWechatAdded}
                  disabled={loading}
                  className="flex-1 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50"
                >
                  {loading ? '处理中...' : '我已添加'}
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200"
                >
                  稍后提醒
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center mb-6">
              <div className="text-4xl mb-2">✅</div>
              <p className="text-green-600 font-medium">感谢添加！我们将为您提供更好的服务</p>
            </div>
          )}

          <button
            onClick={onClose}
            className="w-full py-3 text-gray-500 hover:text-gray-700"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default RegisterSuccessModal;
