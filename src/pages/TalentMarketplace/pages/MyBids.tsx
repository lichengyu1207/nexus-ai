import { motion, AnimatePresence } from 'framer-motion';
import { EyeIcon, CheckIcon, XMarkIcon, ClockIcon } from '@heroicons/react/24/outline';
import { useBids } from '../hooks/useBids';
import type { Bid } from '../types';
import { BID_STATUS_CONFIG } from '../types';

interface MyBidsProps {
  userId?: string;
}

export function MyBids({ userId }: MyBidsProps) {
  const { bids, isLoading, withdrawBid, isUpdating } = useBids(userId ? { talentId: userId } : {});

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
            <div className="h-6 bg-slate-700 rounded w-1/3 mb-4" />
            <div className="h-4 bg-slate-700 rounded w-2/3 mb-2" />
            <div className="h-4 bg-slate-700 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (!bids || bids.length === 0) {
    return (
      <div className="text-center py-12 bg-slate-800/30 rounded-xl border border-slate-700/50">
        <p className="text-slate-400">还没有投过任何标</p>
        <p className="text-slate-500 text-sm mt-2">浏览招募市场找到适合您的项目</p>
      </div>
    );
  }

  const groupedBids = {
    pending: bids.filter((b) => b.status === 'pending'),
    accepted: bids.filter((b) => b.status === 'accepted'),
    rejected: bids.filter((b) => b.status === 'rejected'),
  };

  const renderBidCard = (bid: Bid, index: number) => (
    <motion.div
      key={bid.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -100 }}
      transition={{ delay: index * 0.05 }}
      className={`
        bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border
        ${bid.status === 'accepted' 
          ? 'border-green-500/50 bg-green-500/5' 
          : bid.status === 'rejected'
          ? 'border-red-500/30 bg-red-500/5'
          : 'border-slate-700/50 hover:border-amber-500/30'
        }
        transition-colors duration-200
      `}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-white">
              招募 #{bid.recruitmentId.slice(0, 8)}
            </h3>
            <span className={`px-2 py-0.5 text-xs rounded-full ${BID_STATUS_CONFIG[bid.status].color} bg-slate-700/50`}>
              {BID_STATUS_CONFIG[bid.status].label}
            </span>
          </div>
          
          <p className="text-slate-400 text-sm mb-3 line-clamp-2">
            {bid.proposal}
          </p>
          
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span className="text-amber-400 font-medium">
              报价: ¥{bid.price.toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
              <ClockIcon className="w-4 h-4" />
              {bid.estimatedDays} 天
            </span>
            <span>{formatDate(bid.createdAt)}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="p-2 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-700/50 transition-colors"
            title="查看详情"
          >
            <EyeIcon className="w-5 h-5" />
          </motion.button>
          
          {bid.status === 'pending' && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => withdrawBid(bid.id)}
              disabled={isUpdating}
              className="px-3 py-1.5 text-sm rounded-lg text-red-400 hover:bg-red-500/20 transition-colors disabled:opacity-50"
            >
              撤回
            </motion.button>
          )}
          
          {bid.status === 'accepted' && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-3 py-1.5 text-sm rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 transition-colors"
            >
              开始工作
            </motion.button>
          )}
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">我的投标</h2>
        <div className="flex items-center gap-4 text-sm">
          <span className="flex items-center gap-1 text-amber-400">
            <ClockIcon className="w-4 h-4" />
            {groupedBids.pending.length} 待审核
          </span>
          <span className="flex items-center gap-1 text-green-400">
            <CheckIcon className="w-4 h-4" />
            {groupedBids.accepted.length} 已中标
          </span>
          <span className="flex items-center gap-1 text-red-400">
            <XMarkIcon className="w-4 h-4" />
            {groupedBids.rejected.length} 未中标
          </span>
        </div>
      </div>

      {groupedBids.accepted.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-green-400 mb-3 flex items-center gap-2">
            <CheckIcon className="w-4 h-4" />
            已中标
          </h3>
          <div className="space-y-4">
            <AnimatePresence mode="popLayout">
              {groupedBids.accepted.map((bid, index) => renderBidCard(bid, index))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {groupedBids.pending.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-amber-400 mb-3 flex items-center gap-2">
            <ClockIcon className="w-4 h-4" />
            待审核
          </h3>
          <div className="space-y-4">
            <AnimatePresence mode="popLayout">
              {groupedBids.pending.map((bid, index) => renderBidCard(bid, index))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {groupedBids.rejected.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-red-400 mb-3 flex items-center gap-2">
            <XMarkIcon className="w-4 h-4" />
            未中标
          </h3>
          <div className="space-y-4 opacity-60">
            <AnimatePresence mode="popLayout">
              {groupedBids.rejected.map((bid, index) => renderBidCard(bid, index))}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  );
}
