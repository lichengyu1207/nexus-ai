import React, { useState } from 'react';
import { XMarkIcon, ClipboardDocumentIcon, CheckIcon } from '@heroicons/react/24/outline';

interface ContactModalProps {
  onClose: () => void;
}

const ContactModal: React.FC<ContactModalProps> = ({ onClose }) => {
  const [copied, setCopied] = useState(false);

  const wechatId = 'svip6763';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(wechatId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Copy failed:', error);
    }
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

          <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">
            联系销售
          </h3>

          <div className="text-center">
            <div className="bg-gray-50 rounded-xl p-6 mb-4">
              <div className="w-48 h-48 bg-white rounded-lg mx-auto mb-4 flex items-center justify-center border">
                <img 
                  src="/wechat-qr.png" 
                  alt="微信二维码" 
                  className="w-40 h-40"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https://u.wechat.com/EEXAMPLE';
                  }}
                />
              </div>
              <p className="text-sm text-gray-600 mb-2">扫描二维码添加客服微信</p>
            </div>

            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-sm text-gray-600 mb-2">或复制微信号</p>
              <div className="flex items-center justify-center gap-2">
                <span className="font-mono text-lg font-medium">{wechatId}</span>
                <button
                  onClick={handleCopy}
                  className="p-2 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  {copied ? (
                    <CheckIcon className="w-5 h-5 text-green-500" />
                  ) : (
                    <ClipboardDocumentIcon className="w-5 h-5 text-gray-500" />
                  )}
                </button>
              </div>
            </div>

            <p className="text-sm text-gray-500 mt-4">
              工作时间：周一至周五 9:00-18:00
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-full mt-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContactModal;
