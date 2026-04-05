import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PlusIcon, EyeIcon, PencilIcon, TrashIcon, ClockIcon } from '@heroicons/react/24/outline';
import { useRecruitments } from '../hooks/useRecruitments';
import { RecruitmentForm } from '../components/RecruitmentForm';
import { BidList } from '../components/BidList';
import type { Recruitment } from '../types';
import { RECRUITMENT_STATUS_CONFIG, BUDGET_TYPE_CONFIG } from '../types';

export function MyRecruitments() {
  const [showForm, setShowForm] = useState(false);
  const [selectedRecruitment, setSelectedRecruitment] = useState<Recruitment | null>(null);
  const [viewingBids, setViewingBids] = useState<string | null>(null);
  
  const { recruitments, isLoading, createRecruitment, updateRecruitment, deleteRecruitment, acceptBid, rejectBid, isCreating } = useRecruitments();

  const handleCreate = (data: Partial<Recruitment>) => {
    createRecruitment(data);
    setShowForm(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('确定要删除这个招募吗？')) {
      deleteRecruitment(id);
    }
  };

  const handleClose = (id: string) => {
    updateRecruitment({ id, status: 'closed' });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const isExpired = (deadline: string) => new Date(deadline) < new Date();

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">我的招募</h2>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-slate-900 font-semibold rounded-xl hover:bg-amber-400 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          发布招募
        </motion.button>
      </div>

      {recruitments.length === 0 ? (
        <div className="text-center py-12 bg-slate-800/30 rounded-xl border border-slate-700/50">
          <p className="text-slate-400 mb-4">还没有发布任何招募</p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowForm(true)}
            className="px-6 py-2 bg-amber-500/20 text-amber-400 rounded-xl hover:bg-amber-500/30 transition-colors"
          >
            发布第一个招募
          </motion.button>
        </div>
      ) : (
        <div className="space-y-4">
          <AnimatePresence mode="popLayout">
            {recruitments.map((recruitment, index) => (
              <motion.div
                key={recruitment.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -100 }}
                transition={{ delay: index * 0.05 }}
                className={`
                  bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border
                  ${recruitment.status === 'closed' 
                    ? 'border-slate-600/30 opacity-60' 
                    : isExpired(recruitment.deadline)
                    ? 'border-red-500/30'
                    : 'border-slate-700/50 hover:border-amber-500/30'
                  }
                  transition-colors duration-200
                `}
              >
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">{recruitment.title}</h3>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${RECRUITMENT_STATUS_CONFIG[recruitment.status].color} bg-slate-700/50`}>
                        {RECRUITMENT_STATUS_CONFIG[recruitment.status].label}
                      </span>
                      {isExpired(recruitment.deadline) && recruitment.status === 'open' && (
                        <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded-full">
                          已过期
                        </span>
                      )}
                    </div>
                    <p className="text-slate-400 text-sm line-clamp-2 mb-3">
                      {recruitment.description}
                    </p>
                    <div className="flex items-center gap-4 text-sm text-slate-400">
                      <span className="text-amber-400 font-medium">
                        ¥{recruitment.budget.toLocaleString()} {BUDGET_TYPE_CONFIG[recruitment.budgetType].label}
                      </span>
                      <span className="flex items-center gap-1">
                        <ClockIcon className="w-4 h-4" />
                        截止: {formatDate(recruitment.deadline)}
                      </span>
                      <span>{recruitment.bids.length} 个投标</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setViewingBids(recruitment.id)}
                      className="p-2 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-700/50 transition-colors"
                      title="查看投标"
                    >
                      <EyeIcon className="w-5 h-5" />
                    </motion.button>
                    {recruitment.status === 'open' && (
                      <>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => setSelectedRecruitment(recruitment)}
                          className="p-2 rounded-lg text-slate-400 hover:text-blue-400 hover:bg-slate-700/50 transition-colors"
                          title="编辑"
                        >
                          <PencilIcon className="w-5 h-5" />
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handleClose(recruitment.id)}
                          className="p-2 rounded-lg text-slate-400 hover:text-green-400 hover:bg-slate-700/50 transition-colors"
                          title="关闭招募"
                        >
                          <span className="text-xs">关闭</span>
                        </motion.button>
                      </>
                    )}
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleDelete(recruitment.id)}
                      className="p-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-700/50 transition-colors"
                      title="删除"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </motion.button>
                  </div>
                </div>

                {recruitment.requiredSkills.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {recruitment.requiredSkills.map((skill) => (
                      <span
                        key={skill}
                        className="px-2 py-1 text-xs bg-amber-500/10 text-amber-400 rounded-full"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      <RecruitmentForm
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleCreate}
        isLoading={isCreating}
      />

      <RecruitmentForm
        isOpen={!!selectedRecruitment}
        recruitment={selectedRecruitment ?? undefined}
        onClose={() => setSelectedRecruitment(null)}
        onSubmit={(data) => {
          if (selectedRecruitment) {
            updateRecruitment({ ...data, id: selectedRecruitment.id });
            setSelectedRecruitment(null);
          }
        }}
        isLoading={false}
      />

      <AnimatePresence>
        {viewingBids && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setViewingBids(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-2xl max-h-[80vh] overflow-y-auto bg-slate-900 rounded-2xl border border-slate-700/50 p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">投标列表</h3>
                <button
                  onClick={() => setViewingBids(null)}
                  className="text-slate-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              <BidList
                bids={recruitments.find((r) => r.id === viewingBids)?.bids ?? []}
                isOwner
                onAccept={(bidId) => {
                  acceptBid({ bidId, recruitmentId: viewingBids });
                }}
                onReject={(bidId) => {
                  rejectBid({ bidId, recruitmentId: viewingBids });
                }}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
