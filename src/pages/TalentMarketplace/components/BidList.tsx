import { motion, AnimatePresence } from 'framer-motion';
import { CheckIcon, XMarkIcon, ClockIcon, UserIcon } from '@heroicons/react/24/outline';
import type { Bid } from '../types';
import { BID_STATUS_CONFIG } from '../types';

interface BidListProps {
  bids: Bid[];
  onAccept?: (bidId: string) => void;
  onReject?: (bidId: string) => void;
  isOwner?: boolean;
  loading?: boolean;
}

export function BidList({ bids, onAccept, onReject, isOwner = false, loading = false }: BidListProps) {
  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="animate-pulse bg-slate-800/50 rounded-xl p-4 border border-slate-700/50"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-slate-700 rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-slate-700 rounded w-1/4" />
                <div className="h-3 bg-slate-700 rounded w-1/2" />
                <div className="h-3 bg-slate-700 rounded w-3/4" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (bids.length === 0) {
    return (
      <div className="text-center py-12">
        <UserIcon className="w-12 h-12 mx-auto text-slate-600 mb-4" />
        <p className="text-slate-400">暂无投标</p>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-4">
      <AnimatePresence mode="popLayout">
        {bids.map((bid, index) => (
          <motion.div
            key={bid.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -100 }}
            transition={{ delay: index * 0.05 }}
            className={`
              bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border
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
              <div className="flex items-start gap-4 flex-1">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-bold">
                  {bid.talentId.slice(0, 2).toUpperCase()}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-white font-medium">
                      人才 #{bid.talentId.slice(0, 8)}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${BID_STATUS_CONFIG[bid.status].color} bg-slate-700/50`}>
                      {BID_STATUS_CONFIG[bid.status].label}
                    </span>
                  </div>
                  
                  <p className="text-slate-300 text-sm mb-2 line-clamp-2">
                    {bid.proposal}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <span className="text-amber-400 font-medium">¥{bid.price.toLocaleString()}</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <ClockIcon className="w-3.5 h-3.5" />
                      {bid.estimatedDays} 天
                    </span>
                    <span>{formatDate(bid.createdAt)}</span>
                  </div>
                </div>
              </div>
              
              {isOwner && bid.status === 'pending' && (
                <div className="flex items-center gap-2">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onAccept?.(bid.id)}
                    className="p-2 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors"
                    title="接受投标"
                  >
                    <CheckIcon className="w-5 h-5" />
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onReject?.(bid.id)}
                    className="p-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
                    title="拒绝投标"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </motion.button>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
