import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  XMarkIcon,
  ClockIcon,
  CurrencyDollarIcon,
  UserCircleIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { relationApi, Recruitment, Bid } from '@/api/relationApi';
import { useAppContextStore } from '@/store/appContextStore';
import { eventBus, EventTypes } from '@/services/eventBus';
import showToast from '@/utils/toast';

const RecruitmentBidsPage: React.FC = () => {
  const { recruitmentId } = useParams<{ recruitmentId: string }>();
  const navigate = useNavigate();
  const { currentTeam } = useAppContextStore();
  
  const [recruitment, setRecruitment] = useState<Recruitment | null>(null);
  const [bids, setBids] = useState<Bid[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [acceptingBidId, setAcceptingBidId] = useState<string | null>(null);
  const [rejectingBidId, setRejectingBidId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);

  useEffect(() => {
    loadRecruitmentAndBids();
  }, [recruitmentId]);

  const loadRecruitmentAndBids = async () => {
    setIsLoading(true);
    try {
      const recruitmentData = await relationApi.getRecruitment(recruitmentId);
      setRecruitment(recruitmentData);
      
      const bidsData = await relationApi.getRecruitmentBids(recruitmentId);
      setBids(bidsData);
    } catch (error) {
      showToast.error('加载招募信息失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptBid = async (bid: Bid) => {
    setAcceptingBidId(bid.id);
    try {
      const result = await relationApi.acceptBid(bid.id);
      
      setBids(bids.map((b) =>
        b.id === bid.id ? { ...b, status: 'accepted' } : b
      ));
      
      eventBus.emit(EventTypes.RECRUITMENT_BID_ACCEPTED, {
        bidId: bid.id,
        taskId: result.task.id,
        recruitmentId
      });
      
      showToast.success('投标已接受，任务已创建');
      
      setTimeout(() => {
        navigate(`/tasks/${result.task.id}`);
      }, 1500);
    } catch (error) {
      showToast.error('接受投标失败');
    } finally {
      setAcceptingBidId(null);
    }
  };

  const handleRejectBid = async () => {
    if (!rejectReason.trim()) {
      showToast.warning('请填写拒绝原因');
      return;
    }
    
    setRejectingBidId(showRejectModal);
    try {
      await relationApi.rejectBid(showRejectModal, rejectReason);
      
      setBids(bids.map((b) =>
        b.id === showRejectModal ? { ...b, status: 'rejected' } : b
      ));
      
      showToast.success('已拒绝该投标');
      setShowRejectModal(false);
      setRejectReason('');
    } catch (error) {
      showToast.error('拒绝投标失败');
    } finally {
      setRejectingBidId(null);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { bg: string; text: string; label: string }> = {
      pending: { bg: 'bg-yellow-100 text-yellow-700', label: '待处理' },
      accepted: { bg: 'bg-green-100 text-green-700', label: '已接受' },
      rejected: { bg: 'bg-red-100 text-red-700', label: '已拒绝' },
    };
    const config = configs[status] || configs.pending;
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${config.bg}`}>
        {config.label}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-10 h-10 border-4 border-primary-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (!recruitment) {
    return (
      <div className="text-center py-12">
        <DocumentTextIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500">招募不存在</p>
        <button
          onClick={() => navigate('/teams')}
          className="mt-4 text-primary-600 hover:text-primary-700"
        >
          返回团队列表
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
        >
          <ArrowLeftIcon className="w-5 h-5 text-gray-500" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">
            {recruitment.title}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {recruitment.teamName} · 发布于 {formatDate(recruitment.createdAt)}
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {bids.filter((b) => b.status === 'pending').length}
            </p>
            <p className="text-xs text-gray-500">待处理</p>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <p className="text-2xl font-bold text-green-600">
              {bids.filter((b) => b.status === 'accepted').length}
            </p>
            <p className="text-xs text-gray-500">已接受</p>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">
              {bids.filter((b) => b.status === 'rejected').length}
            </p>
            <p className="text-xs text-gray-500">已拒绝</p>
          </div>
        </div>

        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">招募详情</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">预算：</span>{' '}
              <span className="font-medium text-gray-900 dark:text-white">
                ¥{recruitment.budget.toLocaleString()}
              </span>
            </div>
            <div>
              <span className="text-gray-500">截止：</span>{' '}
              <span className="font-medium text-gray-900 dark:text-white">
                {formatDate(recruitment.deadline)}
              </span>
            </div>
          </div>
          <div className="mt-2">
            <span className="text-gray-500">所需技能：</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {recruitment.requiredSkills.map((skill) => (
                <span
                  key={skill}
                  className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs rounded"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="font-semibold text-gray-900 dark:text-white">
            投标列表 ({bids.length})
          </h2>
        </div>

        {bids.length === 0 ? (
          <div className="p-8 text-center">
            <UserCircleIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">暂无投标</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {bids.map((bid) => (
              <motion.div
                key={bid.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`p-4 ${
                  bid.status === 'accepted' ? 'bg-green-50 dark:bg-green-900/20' :
                  bid.status === 'rejected' ? 'bg-red-50 dark:bg-red-900/20' : ''
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-bold">
                      {bid.talentName.charAt(0)}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium text-gray-900 dark:text-white">
                        {bid.talentName}
                      </p>
                      {getStatusBadge(bid.status)}
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm mb-3">
                      <div>
                        <span className="text-gray-500">报价：</span>{' '}
                        <span className="font-medium text-gray-900 dark:text-white">
                          ¥{bid.price.toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">工期：</span>{' '}
                        <span className="font-medium text-gray-900 dark:text-white">
                          {bid.estimatedDays} 天
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">时间：</span>{' '}
                        <span className="text-gray-600 dark:text-gray-400">
                          {formatDate(bid.createdAt)}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {bid.proposal}
                    </p>
                    {bid.status === 'pending' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAcceptBid(bid)}
                          disabled={acceptingBidId === bid.id}
                          className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm"
                        >
                          {acceptingBidId === bid.id ? '处理中...' : '接受'}
                        </button>
                        <button
                          onClick={() => setShowRejectModal(bid.id)}
                          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
                        >
                          拒绝
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {showRejectModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowRejectModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                拒绝投标
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                请填写拒绝原因（可选）
              </p>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="例如：技能不匹配、报价过高..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
              />
              <div className="flex gap-3 mt-4">
                <button
                  onClick={() => {
                    setShowRejectModal(false);
                    setRejectReason('');
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  取消
                </button>
                <button
                  onClick={handleRejectBid}
                  disabled={rejectingBidId === showRejectModal}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  {rejectingBidId === showRejectModal ? '处理中...' : '确认拒绝'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RecruitmentBidsPage;
