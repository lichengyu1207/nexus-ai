import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  UserGroupIcon,
  CubeIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
} from '@heroicons/react/24/outline';
import { TalentList } from './components/TalentList';
import { TalentFilters } from './components/TalentFilters';
import { TalentProfile } from './components/TalentProfile';
import { RecruitmentForm } from './components/RecruitmentForm';
import { BidForm } from './components/BidForm';
import { InviteModal } from './components/InviteModal';
import { RatingModal } from './components/RatingModal';
import { useTalents } from './hooks/useTalents';
import { useRecruitments } from './hooks/useRecruitments';
import { useBids } from './hooks/useBids';
import type { Talent, Recruitment, ViewMode, TalentFilters } from './types';

const NAV_ITEMS: { key: ViewMode; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { key: 'talents', label: '人才库', icon: UserGroupIcon },
  { key: 'skills', label: '技能市场', icon: CubeIcon },
  { key: 'my-recruitments', label: '我的招募', icon: DocumentTextIcon },
  { key: 'my-bids', label: '我的投标', icon: ChatBubbleLeftRightIcon },
];

export default function TalentMarketplace() {
  const [activeView, setActiveView] = useState<ViewMode>('talents');
  const [filters, setFilters] = useState<TalentFilters>({});
  const [selectedTalent, setSelectedTalent] = useState<Talent | null>(null);
  const [selectedRecruitment, setSelectedRecruitment] = useState<Recruitment | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isRecruitmentFormOpen, setIsRecruitmentFormOpen] = useState(false);
  const [isBidFormOpen, setIsBidFormOpen] = useState(false);
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [isRatingModalOpen, setIsRatingModalOpen] = useState(false);

  const {
    talents,
    isLoading: isTalentsLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
  } = useTalents({ filters });

  const {
    recruitments,
    isLoading: isRecruitmentsLoading,
    createRecruitment,
    isCreating,
  } = useRecruitments();

  const { bids, isLoading: isBidsLoading } = useBids();

  const handleTalentClick = useCallback((talent: Talent) => {
    setSelectedTalent(talent);
    setIsProfileOpen(true);
  }, []);

  const handleInvite = useCallback((talent: Talent) => {
    setSelectedTalent(talent);
    setIsInviteModalOpen(true);
  }, []);

  const handleCreateRecruitment = useCallback(
    (data: Partial<Recruitment>) => {
      createRecruitment(data, {
        onSuccess: () => {
          setIsRecruitmentFormOpen(false);
        },
      });
    },
    [createRecruitment]
  );

  const handleViewChange = useCallback((view: ViewMode) => {
    setActiveView(view);
    setFilters({});
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white flex">
      <header className="h-16 bg-gray-900/80 backdrop-blur-sm border-b border-white/10 flex items-center justify-between px-6">
        <h1 className="text-xl font-bold text-white">人才市场</h1>
        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              onClick={() => handleViewChange(item.key)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg transition-colors
                ${
                  activeView === item.key
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }
              `}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-sm font-medium">{item.label}</span>
            </button>
          ))}
        </nav>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {(activeView === 'talents' || activeView === 'skills') && (
          <TalentFilters filters={filters} onFiltersChange={setFilters} />
        )}

        <main className="flex-1 overflow-y-auto p-6">
          {activeView === 'talents' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-gray-400">
                  共 {talents.length} 位人才
                </p>
                <button
                  onClick={() => setIsRecruitmentFormOpen(true)}
                  className="px-4 py-2 text-sm font-medium bg-amber-500 text-gray-900 rounded-lg hover:bg-amber-400 transition-colors"
                >
                  发布招募
                </button>
              </div>
              <TalentList
                talents={talents}
                isLoading={isTalentsLoading}
                isFetchingNextPage={isFetchingNextPage}
                hasMore={hasNextPage}
                onLoadMore={fetchNextPage}
                onTalentClick={handleTalentClick}
                onInvite={handleInvite}
              />
            </div>
          )}

          {activeView === 'skills' && (
            <div className="flex items-center justify-center h-64 text-gray-400">
              <p>技能市场功能开发中...</p>
            </div>
          )}

          {activeView === 'my-recruitments' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">我的招募</h2>
                <button
                  onClick={() => setIsRecruitmentFormOpen(true)}
                  className="px-4 py-2 text-sm font-medium bg-amber-500 text-gray-900 rounded-lg hover:bg-amber-400 transition-colors"
                >
                  新建招募
                </button>
              </div>
              {isRecruitmentsLoading ? (
                <div className="flex justify-center py-8">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"
                  />
                </div>
              ) : recruitments.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <p>暂无招募记录</p>
                  <button
                    onClick={() => setIsRecruitmentFormOpen(true)}
                    className="mt-2 text-amber-400 hover:text-amber-300"
                  >
                    发布第一个招募
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {recruitments.map((recruitment) => (
                    <div
                      key={recruitment.id}
                      className="p-4 bg-white/5 border border-white/10 rounded-lg hover:border-amber-500/30 transition-colors cursor-pointer"
                      onClick={() => {
                        setSelectedRecruitment(recruitment);
                        setIsBidFormOpen(true);
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="text-base font-semibold text-white">{recruitment.title}</h3>
                          <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                            {recruitment.description}
                          </p>
                        </div>
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            recruitment.status === 'open'
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-gray-500/20 text-gray-400'
                          }`}
                        >
                          {recruitment.status === 'open' ? '招募中' : '已关闭'}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                        <span>预算: ¥{recruitment.budget}</span>
                        <span>投标: {recruitment.bids?.length ?? 0} 个</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeView === 'my-bids' && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">我的投标</h2>
              {isBidsLoading ? (
                <div className="flex justify-center py-8">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"
                  />
                </div>
              ) : bids.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <p>暂无投标记录</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {bids.map((bid) => (
                    <div
                      key={bid.id}
                      className="p-4 bg-white/5 border border-white/10 rounded-lg"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="text-base font-semibold text-white">
                            投标 #{bid.recruitmentId.slice(0, 8)}
                          </h3>
                          <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                            {bid.proposal}
                          </p>
                        </div>
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            bid.status === 'pending'
                              ? 'bg-amber-500/20 text-amber-400'
                              : bid.status === 'accepted'
                                ? 'bg-green-500/20 text-green-400'
                                : 'bg-red-500/20 text-red-400'
                          }`}
                        >
                          {bid.status === 'pending' ? '待审核' : bid.status === 'accepted' ? '已接受' : '已拒绝'}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                        <span>报价: ¥{bid.price}</span>
                        <span>预计: {bid.estimatedDays} 天</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      <TalentProfile
        talent={selectedTalent!}
        reviews={[]}
        isOpen={isProfileOpen}
        onClose={() => {
          setIsProfileOpen(false);
          setSelectedTalent(null);
        }}
        onInvite={() => {
          setIsProfileOpen(false);
          setIsInviteModalOpen(true);
        }}
      />

      <RecruitmentForm
        isOpen={isRecruitmentFormOpen}
        onClose={() => setIsRecruitmentFormOpen(false)}
        onSubmit={handleCreateRecruitment}
        isLoading={isCreating}
      />

      <BidForm
        isOpen={isBidFormOpen}
        onClose={() => {
          setIsBidFormOpen(false);
          setSelectedRecruitment(null);
        }}
        onSubmit={() => {}}
        recruitmentId={selectedRecruitment?.id ?? ''}
        recruitmentTitle={selectedRecruitment?.title}
      />

      <InviteModal
        isOpen={isInviteModalOpen}
        onClose={() => {
          setIsInviteModalOpen(false);
          setSelectedTalent(null);
        }}
        onSubmit={() => {
          setIsInviteModalOpen(false);
          setSelectedTalent(null);
        }}
        talent={selectedTalent}
      />

      <RatingModal
        isOpen={isRatingModalOpen}
        onClose={() => setIsRatingModalOpen(false)}
        onSubmit={() => setIsRatingModalOpen(false)}
        talentId={selectedTalent?.id ?? ''}
        talentName={selectedTalent?.name}
      />
    </div>
  );
}
