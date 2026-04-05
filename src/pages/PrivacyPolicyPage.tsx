import React, { useState, useEffect } from 'react';
import { ShieldCheckIcon, CheckIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface PrivacyPolicy {
  id: string;
  version: string;
  title: string;
  content: string;
  effective_date: string;
  is_current: boolean;
}

const PrivacyPolicyPage: React.FC = () => {
  const { user } = useAuth();
  const [policy, setPolicy] = useState<PrivacyPolicy | null>(null);
  const [agreed, setAgreed] = useState(false);
  const [hasAgreedLatest, setHasAgreedLatest] = useState(false);
  const [loading, setLoading] = useState(true);
  const [agreeing, setAgreeing] = useState(false);

  useEffect(() => {
    loadPolicy();
  }, []);

  useEffect(() => {
    if (user && policy) {
      checkPrivacyStatus();
    }
  }, [user, policy]);

  const loadPolicy = async () => {
    try {
      const response = await api.get('privacy/current');
      setPolicy(response.data);
    } catch (error) {
      console.error('Failed to load privacy policy:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkPrivacyStatus = async () => {
    try {
      const response = await api.get('privacy/status');
      setHasAgreedLatest(response.data.agreed_latest);
    } catch (error) {
      console.error('Failed to check privacy status:', error);
    }
  };

  const handleAgree = async () => {
    if (!agreed) {
      showToast.error('请先阅读并同意隐私政策');
      return;
    }

    setAgreeing(true);
    try {
      await api.post('privacy/consent', {
        policy_version: policy?.version,
        policy_title: policy?.title,
      });
      showToast.success('已同意隐私政策');
      setHasAgreedLatest(true);
    } catch (error) {
      showToast.error('操作失败');
    } finally {
      setAgreeing(false);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-8 text-white">
          <div className="flex items-center gap-3">
            <ShieldCheckIcon className="w-10 h-10" />
            <div>
              <h1 className="text-2xl font-bold">{policy?.title || '房都督AI 隐私政策'}</h1>
              <p className="text-primary-100 mt-1">
                版本 {policy?.version || '1.0.0'} 
                {policy?.effective_date && ` · 生效日期：${formatDate(policy.effective_date)}`}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6 prose dark:prose-invert max-w-none">
          {policy?.content ? (
            <ReactMarkdown>{policy.content}</ReactMarkdown>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <DocumentTextIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>隐私政策内容加载失败</p>
            </div>
          )}
        </div>

        {user && !loading && policy && (
          <div className="border-t border-gray-200 dark:border-gray-700 p-6">
            {hasAgreedLatest ? (
              <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <CheckIcon className="w-5 h-5" />
                <span>您已同意当前版本隐私政策</span>
              </div>
            ) : (
              <div className="space-y-4">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={agreed}
                    onChange={(e) => setAgreed(e.target.checked)}
                    className="mt-1 w-4 h-4 text-primary-600 rounded"
                  />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    我已阅读并同意《{policy.title || '房都督AI隐私政策'}》，了解平台如何收集、使用、存储和保护我的个人信息
                  </span>
                </label>
                <button
                  onClick={handleAgree}
                  disabled={!agreed || agreeing}
                  className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {agreeing ? '处理中...' : '同意隐私政策'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PrivacyPolicyPage;
