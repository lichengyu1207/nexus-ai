import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ArrowRightIcon,
  UserGroupIcon,
  CheckCircleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { relationApi, RecommendedTeam } from '@/api/relationApi';
import { useAppContextStore } from '@/store/appContextStore';
import { eventBus, EventTypes } from '@/services/eventBus';
import showToast from '@/utils/toast';

interface ConsultToTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  consultResult: {
    id: string;
    query: string;
    summary: string;
    keywords?: string[];
  };
}

const ConsultToTaskModal: React.FC<ConsultToTaskModalProps> = ({
  isOpen,
  onClose,
  consultResult,
}) => {
  const navigate = useNavigate();
  const { setCurrentTask, setCurrentTeam } = useAppContextStore();
  
  const [step, setStep] = useState<'select' | 'creating' | 'success'>('select');
  const [recommendedTeams, setRecommendedTeams] = useState<RecommendedTeam[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<RecommendedTeam | null>(null);
  const [taskTitle, setTaskTitle] = useState(consultResult.query.slice(0, 50));
  const [isLoading, setIsLoading] = useState(false);
  const [createdTaskId, setCreatedTaskId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && consultResult.keywords?.length) {
      loadRecommendedTeams();
    }
  }, [isOpen, consultResult.keywords]);

  useEffect(() => {
    setTaskTitle(consultResult.query.slice(0, 50));
  }, [consultResult.query]);

  const loadRecommendedTeams = async () => {
    setIsLoading(true);
    try {
      const teams = await relationApi.getRecommendedTeams(
        consultResult.keywords || [],
        consultResult.query
      );
      setRecommendedTeams(teams);
      if (teams.length > 0) {
        setSelectedTeam(teams[0]);
      }
    } catch (error) {
      console.error('Failed to load recommended teams:', error);
      showToast.error('获取推荐团队失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTask = async () => {
    if (!selectedTeam) {
      showToast.warning('请先选择一个团队');
      return;
    }

    setStep('creating');
    try {
      const result = await relationApi.createTaskFromConsult({
        consultResultId: consultResult.id,
        teamId: selectedTeam.id,
        title: taskTitle,
      });
      
      setCreatedTaskId(result.task.id);
      setCurrentTask({
        id: result.task.id,
        title: result.task.title,
        status: result.task.status,
        teamId: selectedTeam.id,
      });
      setCurrentTeam({
        id: selectedTeam.id,
        name: selectedTeam.name,
        skills: selectedTeam.skills,
        memberCount: selectedTeam.memberCount,
      });
      
      eventBus.emit(EventTypes.TASK_CREATED, result.task);
      
      setStep('success');
      showToast.success('任务创建成功！');
    } catch (error) {
      console.error('Failed to create task:', error);
      showToast.error('创建任务失败');
      setStep('select');
    }
  };

  const handleGoToTask = () => {
    if (createdTaskId) {
      onClose();
      navigate(`/tasks/${createdTaskId}`);
    }
  };

  const handleGoToTeam = () => {
    if (selectedTeam) {
      onClose();
      navigate(`/teams/${selectedTeam.id}`);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/50"
          onClick={onClose}
        />
        
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden"
        >
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <SparklesIcon className="w-6 h-6 text-primary-500" />
                转化为任务
              </h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {step === 'select' && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    任务标题
                  </label>
                  <input
                    type="text"
                    value={taskTitle}
                    onChange={(e) => setTaskTitle(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    placeholder="输入任务标题"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    原咨询内容
                  </label>
                  <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-sm text-gray-600 dark:text-gray-400">
                    {consultResult.summary}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    推荐团队
                    {consultResult.keywords && (
                      <span className="ml-2 text-xs text-gray-400">
                        (基于关键词: {consultResult.keywords.join(', ')})
                      </span>
                    )}
                  </label>
                  
                  {isLoading ? (
                    <div className="py-8 text-center text-gray-500">
                      正在匹配最佳团队...
                    </div>
                  ) : recommendedTeams.length === 0 ? (
                    <div className="py-8 text-center">
                      <UserGroupIcon className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                      <p className="text-gray-500">暂无匹配的团队</p>
                      <button
                        onClick={() => navigate('/teams')}
                        className="mt-2 text-sm text-primary-600 hover:text-primary-700"
                      >
                        创建新团队
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[200px] overflow-y-auto">
                      {recommendedTeams.map((team) => (
                        <button
                          key={team.id}
                          onClick={() => setSelectedTeam(team)}
                          className={`w-full p-3 rounded-lg border-2 text-left transition-all ${
                            selectedTeam?.id === team.id
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-gray-900 dark:text-white">
                                {team.name}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                {team.memberCount} 成员 · {team.recentTasks} 近期任务
                              </p>
                            </div>
                            <div className="text-right">
                              <span className="text-lg font-bold text-primary-600">
                                {team.matchScore}%
                              </span>
                              <p className="text-xs text-gray-400">匹配度</p>
                            </div>
                          </div>
                          {team.skills.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {team.skills.slice(0, 4).map((skill) => (
                                <span
                                  key={skill}
                                  className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs rounded"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={onClose}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleCreateTask}
                    disabled={!selectedTeam || !taskTitle.trim()}
                    className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    创建任务
                    <ArrowRightIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {step === 'creating' && (
              <div className="py-12 text-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4"
                />
                <p className="text-gray-600 dark:text-gray-400">正在创建任务...</p>
              </div>
            )}

            {step === 'success' && (
              <div className="py-8 text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4"
                >
                  <CheckCircleIcon className="w-10 h-10 text-green-500" />
                </motion.div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  任务创建成功！
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  已分配到团队「{selectedTeam?.name}」
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={handleGoToTeam}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    查看团队
                  </button>
                  <button
                    onClick={handleGoToTask}
                    className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    前往任务
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <ArrowRightIcon className="w-4 h-4" />
              <span>
                下一步：在团队管理中发布招募，或直接分配任务给成员
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default ConsultToTaskModal;
