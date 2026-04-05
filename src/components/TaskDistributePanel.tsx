import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRightIcon,
  BuildingOfficeIcon,
  AcademicCapIcon,
  BuildingLibraryIcon,
  UserGroupIcon,
  GlobeAltIcon,
  CheckCircleIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import { relationApi, DistributionResult } from '@/api/relationApi';
import { eventBus, EventTypes } from '@/services/eventBus';
import showToast from '@/utils/toast';

interface TaskDistributePanelProps {
  taskId: string;
  taskTitle: string;
  taskType?: string;
}

interface Endpoint {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  color: string;
  bgColor: string;
}

const endpoints: Endpoint[] = [
  {
    id: 'enterprise',
    name: '企业端',
    icon: <BuildingOfficeIcon className="w-5 h-5" />,
    description: '推送至企业合作平台',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
  },
  {
    id: 'academic',
    name: '院校端',
    icon: <AcademicCapIcon className="w-5 h-5" />,
    description: '推送至院校实训系统',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
  },
  {
    id: 'government',
    name: '政府端',
    icon: <BuildingLibraryIcon className="w-5 h-5" />,
    description: '推送至政务数据平台',
    color: 'text-red-600',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
  },
  {
    id: 'association',
    name: '协会端',
    icon: <UserGroupIcon className="w-5 h-5" />,
    description: '推送至行业协会平台',
    color: 'text-green-600',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
  },
  {
    id: 'public',
    name: '公众端',
    icon: <GlobeAltIcon className="w-5 h-5" />,
    description: '公开发布展示',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
  },
];

const TaskDistributePanel: React.FC<TaskDistributePanelProps> = ({
  taskId,
  taskTitle,
  taskType,
}) => {
  const [selectedEndpoints, setSelectedEndpoints] = useState<Set<string>>(new Set());
  const [isDistributing, setIsDistributing] = useState(false);
  const [results, setResults] = useState<DistributionResult | null>(null);

  const getDefaultEndpoints = () => {
    switch (taskType) {
      case 'enterprise_report':
        return ['enterprise'];
      case 'academic_training':
        return ['academic'];
      case 'policy_analysis':
        return ['government'];
      default:
        return [];
    }
  };

  React.useEffect(() => {
    const defaults = getDefaultEndpoints();
    if (defaults.length > 0) {
      setSelectedEndpoints(new Set(defaults));
    }
  }, [taskType]);

  const toggleEndpoint = (id: string) => {
    const newSet = new Set(selectedEndpoints);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedEndpoints(newSet);
  };

  const handleDistribute = async () => {
    if (selectedEndpoints.size === 0) {
      showToast.error('请选择至少一个分发端');
      return;
    }

    setIsDistributing(true);
    try {
      const result = await relationApi.distributeTask(taskId, Array.from(selectedEndpoints));
      setResults(result);
      eventBus.emit(EventTypes.DISTRIBUTION_COMPLETED, { taskId, endpoints: Array.from(selectedEndpoints) });
      showToast.success('分发成功！');
    } catch (error) {
      showToast.error('分发失败');
    } finally {
      setIsDistributing(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <PaperAirplaneIcon className="w-5 h-5 text-primary-600" />
          五端分发
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          将成果分发到不同平台
        </p>
      </div>

      <div className="p-4">
        {results ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-6"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="w-14 h-14 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4"
            >
              <CheckCircleIcon className="w-8 h-8 text-green-500" />
            </motion.div>
            <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
              分发完成
            </h4>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              已分发到 {results.successCount} 个端
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {results.distributedTo.map((ep) => (
                <span
                  key={ep}
                  className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm"
                >
                  {endpoints.find((e) => e.id === ep)?.name || ep}
                </span>
              ))}
            </div>
          </motion.div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
              {endpoints.map((endpoint) => (
                <button
                  key={endpoint.id}
                  onClick={() => toggleEndpoint(endpoint.id)}
                  className={`p-3 rounded-xl text-left transition-all ${
                    selectedEndpoints.has(endpoint.id)
                      ? `${endpoint.bgColor} ring-2 ring-offset-1 ring-${endpoint.color.replace('text-', '')}`
                      : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`${endpoint.color}`}>
                      {endpoint.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`font-medium ${endpoint.color}`}>
                        {endpoint.name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {endpoint.description}
                      </p>
                    </div>
                    {selectedEndpoints.has(endpoint.id) && (
                      <CheckCircleIcon className={`w-5 h-5 ${endpoint.color}`} />
                    )}
                  </div>
                </button>
              ))}
            </div>

            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-400">
                已选择 {selectedEndpoints.size} 个端
              </p>
              <button
                onClick={handleDistribute}
                disabled={isDistributing || selectedEndpoints.size === 0}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm"
              >
                {isDistributing ? (
                  '分发中...'
                ) : (
                  <>
                    <ArrowRightIcon className="w-4 h-4" />
                    立即分发
                  </>
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default TaskDistributePanel;
