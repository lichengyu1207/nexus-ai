import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  SparklesIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  TagIcon,
  CheckCircleIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import { relationApi, RecommendedTalent } from '@/api/relationApi';
import { useAppContextStore } from '@/store/appContextStore';
import { eventBus, EventTypes } from '@/services/eventBus';
import showToast from '@/utils/toast';

interface RecruitmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  teamId: string;
  teamName: string;
  teamSkills?: string[];
  taskId?: string;
}

const RecruitmentModal: React.FC<RecruitmentModalProps> = ({
  isOpen,
  onClose,
  teamId,
  teamName,
  teamSkills = [],
  taskId,
}) => {
  const { setCurrentRecruitment } = useAppContextStore();
  
  const [step, setStep] = useState<'form' | 'talents' | 'success'>('form');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [requiredSkills, setRequiredSkills] = useState<string[]>(teamSkills?.slice(0, 3) || []);
  const [budget, setBudget] = useState(1000);
  const [deadline, setDeadline] = useState('');
  const [newSkill, setNewSkill] = useState('');
  
  const [recommendedTalents, setRecommendedTalents] = useState<RecommendedTalent[]>([]);
  const [selectedTalents, setSelectedTalents] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [createdRecruitmentId, setCreatedRecruitmentId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      const date = new Date();
      date.setDate(date.getDate() + 14);
      setDeadline(date.toISOString().split('T')[0]);
    }
  }, [isOpen]);

  const handleAddSkill = () => {
    if (newSkill.trim() && !requiredSkills.includes(newSkill.trim())) {
      setRequiredSkills([...requiredSkills, newSkill.trim()]);
      setNewSkill('');
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setRequiredSkills(requiredSkills.filter((s) => s !== skill));
  };

  const handleSubmit = async () => {
    if (!title.trim() || requiredSkills.length === 0) {
      showToast.error('请填写标题并选择至少一个技能');
      return;
    }

    setIsLoading(true);
    try {
      const recruitment = await relationApi.createRecruitment({
        teamId,
        title,
        description,
        requiredSkills,
        budget,
        deadline,
      });
      
      setCreatedRecruitmentId(recruitment.id);
      setCurrentRecruitment({
        id: recruitment.id,
        teamId,
        title,
        requiredSkills,
      });
      
      const talents = await relationApi.getRecommendedTalents({ skills: requiredSkills, teamId });
      setRecommendedTalents(talents);
      setStep('talents');
      
      eventBus.emit(EventTypes.RECRUITMENT_CREATED, { recruitmentId: recruitment.id, teamId });
      showToast.success('招募发布成功！');
    } catch (error) {
      showToast.error('发布招募失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInviteTalent = async (talentId: string) => {
    try {
      await relationApi.inviteTalent(talentId, teamId);
      setSelectedTalents(new Set(selectedTalents).add(talentId));
      showToast.success('邀请已发送');
      eventBus.emit(EventTypes.TALENT_INVITED, { talentId, teamId });
    } catch (error) {
      showToast.error('邀请失败');
    }
  };

  const handleFinish = () => {
    onClose();
    setStep('form');
    setTitle('');
    setDescription('');
    setRequiredSkills(teamSkills?.slice(0, 3) || []);
    setBudget(1000);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                <UserGroupIcon className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  发布招募
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {teamName} · 寻找人才
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <XMarkIcon className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {step === 'form' && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    招募标题
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="例如：寻找数据分析师"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    任务描述
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="描述任务内容、要求、交付物等..."
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 resize-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <TagIcon className="w-4 h-4 inline mr-1" />
                    所需技能
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {requiredSkills.map((skill) => (
                      <span
                        key={skill}
                        className="px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm flex items-center gap-1"
                      >
                        {skill}
                        <button
                          onClick={() => handleRemoveSkill(skill)}
                          className="hover:text-red-500"
                        >
                          <XMarkIcon className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newSkill}
                      onChange={(e) => setNewSkill(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddSkill()}
                      placeholder="输入技能标签"
                      className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                    />
                    <button
                      onClick={handleAddSkill}
                      className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                    >
                      <PlusIcon className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      <CurrencyDollarIcon className="w-4 h-4 inline mr-1" />
                      预算 (元)
                    </label>
                    <input
                      type="number"
                      value={budget}
                      onChange={(e) => setBudget(Number(e.target.value))}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      <CalendarIcon className="w-4 h-4 inline mr-1" />
                      截止日期
                    </label>
                    <input
                      type="date"
                      value={deadline}
                      onChange={(e) => setDeadline(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 'talents' && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    推荐人才
                  </h3>
                  <span className="text-sm text-gray-500">
                    {recommendedTalents.length} 位匹配
                  </span>
                </div>

                {recommendedTalents.length === 0 ? (
                  <div className="text-center py-12">
                    <UserGroupIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-500 dark:text-gray-400">暂无匹配的人才</p>
                    <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                      您可以在人才市场主动寻找
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {recommendedTalents.map((talent) => (
                      <div
                        key={talent.id}
                        className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-bold">
                            {talent.name.charAt(0)}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {talent.name}
                            </p>
                            <div className="flex items-center gap-2 text-sm text-gray-500">
                              <span className="text-green-600 font-medium">
                                {talent.matchScore}% 匹配
                              </span>
                              <span>·</span>
                              <span>{talent.completedTasks} 个任务</span>
                            </div>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {talent.skills.slice(0, 3).map((skill) => (
                                <span
                                  key={skill}
                                  className="px-2 py-0.5 bg-white dark:bg-gray-600 text-gray-600 dark:text-gray-300 text-xs rounded"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => handleInviteTalent(talent.id)}
                          disabled={selectedTalents.has(talent.id)}
                          className={`px-4 py-2 rounded-lg text-sm font-medium ${
                            selectedTalents.has(talent.id)
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-600'
                              : 'bg-primary-600 text-white hover:bg-primary-700'
                          }`}
                        >
                          {selectedTalents.has(talent.id) ? '已邀请' : '邀请'}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {step === 'success' && (
              <div className="text-center py-8">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-6"
                >
                  <CheckCircleIcon className="w-12 h-12 text-green-500" />
                </motion.div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  招募发布成功！
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  已向 {selectedTalents.size} 位人才发送邀请
                </p>
                <div className="flex gap-3 justify-center">
                  <button
                    onClick={handleFinish}
                    className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    完成
                  </button>
                  <button
                    onClick={() => window.location.href = `/talent-market`}
                    className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    去人才市场
                  </button>
                </div>
              </div>
            )}
          </div>

          {step !== 'success' && (
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700 flex justify-between">
              <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <SparklesIcon className="w-4 h-4" />
                发布后系统会自动推荐匹配的人才
              </p>
              <div className="flex gap-3">
                {step === 'talents' && (
                  <button
                    onClick={() => setStep('success')}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    完成
                  </button>
                )}
                {step === 'form' && (
                  <button
                    onClick={handleSubmit}
                    disabled={isLoading || !title.trim()}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {isLoading ? '发布中...' : '发布招募'}
                  </button>
                )}
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default RecruitmentModal;
