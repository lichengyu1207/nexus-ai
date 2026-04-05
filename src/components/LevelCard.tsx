import React, { useEffect, useState } from 'react';
import { TrophyIcon, ChevronRightIcon, StarIcon, BriefcaseIcon, UsersIcon } from '@heroicons/react/24/outline';
import { userLevelApi, UserLevelInfo, LevelInfo } from '@/api/userLevel';

interface LevelCardProps {
  completedTasks: number;
}

const LevelCard: React.FC<LevelCardProps> = ({ completedTasks }) => {
  const [levelInfo, setLevelInfo] = useState<UserLevelInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadLevelInfo();
  }, [completedTasks]);

  const loadLevelInfo = async () => {
    setIsLoading(true);
    try {
      const info = await userLevelApi.getUserLevelInfo(completedTasks);
      setLevelInfo(info);
    } catch (error) {
      console.error('Failed to load level info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getLevelColor = (level: number) => {
    if (level >= 10) return 'bg-purple-600';
    if (level >= 7) return 'bg-orange-500';
    if (level >= 4) return 'bg-blue-500';
    return 'bg-green-500';
  };

  const getLevelBadgeColor = (level: number) => {
    if (level >= 10) return 'bg-purple-100 text-purple-800';
    if (level >= 7) return 'bg-orange-100 text-orange-800';
    if (level >= 4) return 'bg-blue-100 text-blue-800';
    return 'bg-green-100 text-green-800';
  };

  const renderLevelSection = (levelData: LevelInfo, title: string, icon: React.ReactNode) => (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getLevelBadgeColor(levelData.current_level)}`}>
              {levelData.level_name}
            </span>
            <h4 className="text-lg font-bold text-gray-900">{levelData.level_title}</h4>
          </div>
          <p className="text-gray-500 mt-1">
            已完成 {levelData.completed_tasks} 个任务
          </p>
        </div>
        <div className={`w-14 h-14 rounded-full ${getLevelColor(levelData.current_level)} flex items-center justify-center text-white font-bold text-lg`}>
          {levelData.current_level}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">升级进度</span>
          <span className="text-sm font-medium text-gray-900">
            {levelData.progress}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full ${getLevelColor(levelData.current_level)}`}
            style={{ width: `${levelData.progress}%` }}
          ></div>
        </div>
      </div>

      {/* Next Level */}
      {levelData.next_level && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">下一等级</p>
              <p className="text-sm text-gray-500">
                {levelData.next_level_name} - 需要 {levelData.next_level} 级
              </p>
            </div>
            <ChevronRightIcon className="w-4 h-4 text-gray-400" />
          </div>
        </div>
      )}

      {/* Benefits */}
      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-2">当前等级权益</h4>
        <div className="space-y-1">
          {levelData.权益.slice(0, 2).map((benefit) => (
            <div key={benefit.id} className="flex items-center gap-2 text-sm">
              <StarIcon className="w-3 h-3 text-yellow-500" />
              <span className="text-gray-700">{benefit.name}</span>
            </div>
          ))}
          {levelData.权益.length > 2 && (
            <div className="text-sm text-gray-500">
              还有 {levelData.权益.length - 2} 项权益
            </div>
          )}
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <TrophyIcon className="w-5 h-5 text-primary-600" />
            用户等级体系
          </h2>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!levelInfo) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-6 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <TrophyIcon className="w-5 h-5 text-primary-600" />
          用户等级体系
        </h2>
        <p className="text-sm text-gray-500 mt-1">双序列发展通道：技术与管理</p>
      </div>
      <div className="p-6">
        {/* 技术序列 */}
        {renderLevelSection(
          levelInfo.technical, 
          '技术序列 (P)', 
          <BriefcaseIcon className="w-5 h-5 text-blue-500" />
        )}
        
        <div className="border-t border-gray-200 my-6"></div>
        
        {/* 管理序列 */}
        {renderLevelSection(
          levelInfo.management, 
          '管理序列 (M)', 
          <UsersIcon className="w-5 h-5 text-green-500" />
        )}
      </div>
    </div>
  );
};

export default LevelCard;