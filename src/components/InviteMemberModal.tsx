import React, { useState } from 'react';
import {
  XMarkIcon,
  LinkIcon,
  ClipboardDocumentIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface InviteMemberModalProps {
  isOpen: boolean;
  onClose: () => void;
  teamId: string;
  teamName: string;
}

const InviteMemberModal: React.FC<InviteMemberModalProps> = ({
  isOpen,
  onClose,
  teamId,
  teamName,
}) => {
  const [inviteCode, setInviteCode] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const loadInviteCode = async () => {
    setIsLoading(true);
    try {
      const response = await api.post(`/teams/${teamId}/invite`);
      setInviteCode(response.data.invite_code);
    } catch {
      showToast.error('获取邀请链接失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      const response = await api.post(`/teams/${teamId}/invite/regenerate`);
      setInviteCode(response.data.invite_code);
      showToast.success('邀请链接已更新');
    } catch {
      showToast.error('更新邀请链接失败');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleCopyLink = () => {
    const link = `${window.location.origin}/teams/join/${inviteCode}`;
    navigator.clipboard.writeText(link);
    showToast.success('邀请链接已复制');
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(inviteCode);
    showToast.success('邀请码已复制');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />
      
      <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            邀请成员加入 {teamName}
          </h3>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6">
          {!inviteCode && !isLoading && (
            <div className="text-center">
              <LinkIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                生成邀请链接分享给团队成员
              </p>
              <button
                onClick={loadInviteCode}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                生成邀请链接
              </button>
            </div>
          )}
          
          {isLoading && (
            <div className="text-center py-8">
              <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">加载中...</p>
            </div>
          )}
          
          {inviteCode && !isLoading && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  邀请链接
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={`${window.location.origin}/teams/join/${inviteCode}`}
                    readOnly
                    className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-600 dark:text-gray-300"
                  />
                  <button
                    onClick={handleCopyLink}
                    className="px-3 py-2 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                    title="复制链接"
                  >
                    <ClipboardDocumentIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  邀请码
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={inviteCode}
                    readOnly
                    className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-lg font-mono text-center text-gray-900 dark:text-white tracking-wider"
                  />
                  <button
                    onClick={handleCopyCode}
                    className="px-3 py-2 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                    title="复制邀请码"
                  >
                    <ClipboardDocumentIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                  </button>
                </div>
              </div>
              
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={handleRegenerate}
                  disabled={isRegenerating}
                  className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >
                  <ArrowPathIcon className={`w-4 h-4 ${isRegenerating ? 'animate-spin' : ''}`} />
                  {isRegenerating ? '更新中...' : '重新生成邀请链接'}
                </button>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  重新生成后，旧链接将失效
                </p>
              </div>
            </div>
          )}
        </div>
        
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-500"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default InviteMemberModal;
