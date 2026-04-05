import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ShieldCheckIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import showToast from '@/utils/toast';
import { useAuth } from '@/contexts/AuthContext';

interface RealnameStatus {
  verified: boolean;
  real_name: string | null;
  id_number_masked: string | null;
  verified_at: string | null;
  verify_method: string | null;
}

const RealnamePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [status, setStatus] = useState<RealnameStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [realName, setRealName] = useState('');
  const [idNumber, setIdNumber] = useState('');

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auth/realname/status', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!realName.trim() || realName.length < 2) {
      showToast.error('请输入正确的姓名');
      return;
    }
    
    if (!idNumber.trim() || idNumber.length !== 18) {
      showToast.error('请输入正确的18位身份证号');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      
      const initResponse = await fetch('/api/auth/realname/init', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ real_name: realName, id_number: idNumber }),
      });

      if (!initResponse.ok) {
        const error = await initResponse.json();
        throw new Error(error.detail || '初始化失败');
      }

      const { certify_id } = await initResponse.json();

      const verifyResponse = await fetch(`/api/auth/realname/verify?certify_id=${certify_id}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!verifyResponse.ok) {
        const error = await verifyResponse.json();
        throw new Error(error.detail || '认证失败');
      }

      showToast.success('实名认证成功！');
      fetchStatus();
    } catch (error: any) {
      showToast.error(error.message || '认证失败，请重试');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-500 px-6 py-8 text-white">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                <ShieldCheckIcon className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">实名认证</h1>
                <p className="text-blue-100">完成实名认证，解锁更多功能</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {status?.verified ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-8"
              >
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircleIcon className="w-10 h-10 text-green-600" />
                </div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">已完成实名认证</h2>
                <div className="space-y-2 text-gray-600">
                  <p>姓名：{status.real_name}</p>
                  <p>身份证号：{status.id_number_masked}</p>
                  <p>认证时间：{status.verified_at ? new Date(status.verified_at).toLocaleString() : '-'}</p>
                </div>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  返回首页
                </button>
              </motion.div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="bg-blue-50 rounded-xl p-4 flex items-start gap-3">
                  <ExclamationCircleIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">认证须知</p>
                    <ul className="list-disc list-inside space-y-1 text-blue-700">
                      <li>请确保填写的信息与身份证一致</li>
                      <li>您的身份信息将被加密存储</li>
                      <li>每个身份证号只能认证一个账户</li>
                    </ul>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    真实姓名
                  </label>
                  <input
                    type="text"
                    value={realName}
                    onChange={(e) => setRealName(e.target.value)}
                    placeholder="请输入身份证上的姓名"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    身份证号
                  </label>
                  <input
                    type="text"
                    value={idNumber}
                    onChange={(e) => setIdNumber(e.target.value.toUpperCase())}
                    placeholder="请输入18位身份证号"
                    maxLength={18}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {submitting ? (
                    <>
                      <ArrowPathIcon className="w-5 h-5 animate-spin" />
                      认证中...
                    </>
                  ) : (
                    <>
                      <ShieldCheckIcon className="w-5 h-5" />
                      提交认证
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </motion.div>

        {/* Benefits */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-8 bg-white rounded-2xl shadow-lg p-6"
        >
          <h3 className="text-lg font-bold text-gray-900 mb-4">认证权益</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { title: '等级提升', desc: '认证后自动升级为L1用户' },
              { title: '更多功能', desc: '解锁高级分析功能' },
              { title: '安全保障', desc: '账户安全更有保障' },
              { title: '优先支持', desc: '享受优先客服支持' },
            ].map((benefit, idx) => (
              <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <CheckCircleIcon className="w-5 h-5 text-green-500" />
                <div>
                  <p className="font-medium text-gray-900">{benefit.title}</p>
                  <p className="text-sm text-gray-500">{benefit.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default RealnamePage;
