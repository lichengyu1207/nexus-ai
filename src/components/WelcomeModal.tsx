import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { XMarkIcon, GiftIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { userSourceApi, SourceInfo } from '@/services/userSourceApi';
import Mascot from '@/components/mascot/Mascot';

interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  username?: string;
}

const WelcomeModal: React.FC<WelcomeModalProps> = ({ isOpen, onClose, username }) => {
  const { data: sourceInfo } = useQuery({
    queryKey: ['userSource'],
    queryFn: userSourceApi.getSourceInfo,
    enabled: isOpen,
  });

  if (!isOpen) return null;

  const getMascotEmotion = (emotion: string): 'default' | 'happy' | 'thinking' | 'confused' | 'surprised' | 'comforting' => {
    const mapping: Record<string, 'default' | 'happy' | 'thinking' | 'confused' | 'surprised' | 'comforting'> = {
      happy: 'happy',
      curious: 'surprised',
      thinking: 'thinking',
      professional: 'default',
      default: 'default',
    };
    return mapping[emotion] || 'default';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden">
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-primary-500 to-primary-700 p-6 text-white text-center relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-full transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
          
          <div className="flex justify-center mb-4">
            <Mascot
              emotion={getMascotEmotion(sourceInfo?.mascot_emotion || 'happy')}
              size="lg"
              animate
            />
          </div>
          
          <h2 className="text-2xl font-bold">
            {sourceInfo?.welcome_message || '欢迎来到房都督AI！'}
          </h2>
          
          {username && (
            <p className="text-primary-100 mt-1">{username}</p>
          )}
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Mascot message */}
          <div className="bg-gray-50 rounded-xl p-4 mb-4">
            <p className="text-gray-700 text-center">
              {sourceInfo?.mascot_message || '开始你的房产分析之旅吧！'}
            </p>
          </div>

          {/* Bonus info */}
          {sourceInfo?.bonus_label && (
            <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-xl p-4 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center">
                  <GiftIcon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{sourceInfo.bonus_label}</p>
                  <p className="text-sm text-gray-600">
                    您已获得 {sourceInfo.free_integral} 次免费分析机会
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Features */}
          <div className="space-y-3 mb-6">
            <div className="flex items-center gap-3">
              <SparklesIcon className="w-5 h-5 text-primary-600" />
              <span className="text-gray-700">AI智能分析房产价值</span>
            </div>
            <div className="flex items-center gap-3">
              <SparklesIcon className="w-5 h-5 text-primary-600" />
              <span className="text-gray-700">周边配套一键查询</span>
            </div>
            <div className="flex items-center gap-3">
              <SparklesIcon className="w-5 h-5 text-primary-600" />
              <span className="text-gray-700">专业投资建议</span>
            </div>
          </div>

          {/* Action button */}
          <button
            onClick={onClose}
            className="w-full py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
          >
            开始分析
          </button>
        </div>
      </div>
    </div>
  );
};

export default WelcomeModal;
