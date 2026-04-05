import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronLeftIcon,
  MegaphoneIcon,
  TasksIcon,
  BookmarkIcon,
  SendIcon,
  DocumentTextIcon,
  UserPlusIcon,
  StarIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';
import { useAppContextStore } from '@/store/appContextStore';
import showToast from '@/utils/toast';

interface Recommendation {
  type: 'team' | 'task' | 'talent';
  title: string;
  icon: React.ReactNode;
  actions: Array<{ label: string; icon: React.ReactNode; action: string }>;
}

const RelationSidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentTeam, currentTask } = useAppContextStore();
  const [isExpanded, setIsExpanded] = useState(true);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  const getRecommendations = (): Recommendation[] => {
    const path = location.pathname;
    
    if (path.startsWith('/teams')) {
      return [
        {
          type: 'team',
          title: '团队操作',
          icon: <UsersIcon className="w-5 h-5" />,
          actions: [
            { label: '发布招募', icon: <MegaphoneIcon className="w-4 h-4" />, action: 'openRecruitment' },
            { label: '分配任务', icon: <TasksIcon className="w-4 h-4" />, action: 'assignTask' },
            { label: '查看成员', icon: <UsersIcon className="w-4 h-4" />, action: 'viewMembers' },
          ],
        },
      ];
    }
    
    if (path.startsWith('/tasks/')) {
      return [
        {
          type: 'task',
          title: '任务操作',
          icon: <TasksIcon className="w-5 h-5" />,
          actions: [
            { label: '存入记忆', icon: <BookmarkIcon className="w-4 h-4" />, action: 'saveMemory' },
            { label: '分发成果', icon: <SendIcon className="w-4 h-4" />, action: 'distribute' },
            { label: '查看报告', icon: <DocumentTextIcon className="w-4 h-4" />, action: 'viewReport' },
          ],
        },
      ];
    }
    
    if (path.startsWith('/talent-market') || path.startsWith('/recruit')) {
      return [
        {
          type: 'talent',
          title: '人才操作',
          icon: <UserPlusIcon className="w-5 h-5" />,
          actions: [
            { label: '邀请到团队', icon: <UserPlusIcon className="w-4 h-4" />, action: 'inviteToTeam' },
            { label: '查看技能', icon: <StarIcon className="w-4 h-4" />, action: 'viewSkills' },
          ],
        },
      ];
    }
    
    return [];
  };

  const handleAction = (action: string) => {
    switch (action) {
      case 'openRecruitment':
        if (currentTeam) {
          window.location.href = `/teams/${currentTeam.id}?action=recruit`;
        } else {
          showToast.warning('请先选择一个团队');
        }
        break;
      case 'assignTask':
        showToast.info('分配任务功能开发中...');
        break;
      case 'viewMembers':
        if (currentTeam) {
          window.location.href = `/teams/${currentTeam.id}`;
        }
        break;
      case 'saveMemory':
        if (currentTask) {
          showToast.info('保存记忆功能开发中...');
        }
        break;
      case 'distribute':
        if (currentTask) {
          showToast.info('分发功能开发中...');
        }
        break;
      case 'viewReport':
        if (currentTask) {
          window.location.href = `/tasks/${currentTask.id}/report`;
        }
        break;
      case 'inviteToTeam':
        showToast.info('邀请功能开发中...');
        break;
      case 'viewSkills':
        showToast.info('技能详情功能开发中...');
        break;
    }
  };

  if (!isExpanded) return null;

  return (
    <motion.div
      initial={{ x: 0, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="fixed right-4 top-24 z-40 w-80"
    >
      <button
        onClick={() => setIsExpanded(false)}
        className="absolute -left-2 top-2 p-1 bg-white dark:bg-gray-700 rounded-lg shadow-sm hover:bg-gray-50 dark:hover:bg-gray-600"
      >
        <ChevronLeftIcon className="w-5 h-5 text-gray-500" />
      </button>
      
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ x: 80, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="w-80 bg-white dark:bg-gray-800 rounded-l shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <div className="p-3 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white text-sm">
                快捷操作
              </h3>
            </div>
            
            <div className="p-3 space-y-1 max-h-[60vh] overflow-y-auto">
              {recommendations.map((rec, index) => (
                <motion.button
                  key={index}
                  initial={{ x: 20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  onClick={() => handleAction(rec.action)}
                  className={`w-full p-3 rounded-lg text-left flex items-center gap-3 transition-colors ${
                    rec.type === 'team'
                      ? 'bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/30'
                      : rec.type === 'task'
                      ? 'bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30'
                      : 'bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${rec.type === 'team' ? 'bg-primary-100 dark:bg-primary-800' : rec.icon === 'task' ? 'bg-blue-100 dark:bg-blue-800' : 'bg-green-100 dark:bg-green-800'}`}>
                    {rec.icon}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white text-sm">
                      {rec.title}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {rec.actions.map((a, i) => (
                        <span key={i} className="text-primary-600 dark:text-primary-400">
                          {a.label}
                        </span>
                      )).join(' · ')}
                    </p>
                  </div>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default RelationSidebar;
