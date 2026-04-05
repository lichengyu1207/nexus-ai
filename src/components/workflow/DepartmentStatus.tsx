import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircleIcon, ClockIcon, PlayIcon } from '@heroicons/react/24/outline';

interface DepartmentStatus {
  name: string;
  nameCn?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  task?: string;
}

interface DepartmentStatusProps {
  departments: DepartmentStatus[];
  activeDepartment?: string;
}

const departmentConfig = {
  LIBU: { name: '吏部', nameCn: '吏部', icon: '👤', color: 'bg-purple-500', description: '教育资源配置' },
  HUBU: { name: '户部', nameCn: '户部', icon: '💰', color: 'bg-green-500', description: '房价数据分析' },
  LIBU_LI: { name: '礼部', nameCn: '礼部', icon: '📝', color: 'bg-blue-500', description: '社区文化分析' },
  BINGBU: { name: '兵部', nameCn: '兵部', icon: '⚔️', color: 'bg-red-500', description: '风险评估预警' },
  XINGBU: { name: '刑部', nameCn: '刑部', icon: '⚖️', color: 'bg-orange-500', description: '法律合规检查' },
  GONGBU: { name: '工部', nameCn: '工部', icon: '🔧', color: 'bg-yellow-500', description: '规划建设分析' },
  // 兼容旧名称
  li: { name: '吏部', nameCn: '吏部', icon: '👤', color: 'bg-purple-500', description: '教育资源配置' },
  hu: { name: '户部', nameCn: '户部', icon: '💰', color: 'bg-green-500', description: '房价数据分析' },
  li_guan: { name: '礼部', nameCn: '礼部', icon: '📝', color: 'bg-blue-500', description: '社区文化分析' },
  bing: { name: '兵部', nameCn: '兵部', icon: '⚔️', color: 'bg-red-500', description: '风险评估预警' },
  xing: { name: '刑部', nameCn: '刑部', icon: '⚖️', color: 'bg-orange-500', description: '法律合规检查' },
  gong: { name: '工部', nameCn: '工部', icon: '🔧', color: 'bg-yellow-500', description: '规划建设分析' },
};

const DepartmentStatus: React.FC<DepartmentStatusProps> = ({
  departments,
  activeDepartment,
}) => {
  const getDepartmentConfig = (name: string) => {
    // 先尝试新名称，再尝试旧名称
    return departmentConfig[name as keyof typeof departmentConfig] || {
      name,
      nameCn: name,
      icon: '📋',
      color: 'bg-gray-500',
      description: '',
    };
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        六部协同执行
      </h3>
      
      <div className="grid grid-cols-3 gap-4">
        {departments.map((dept, index) => {
          const config = getDepartmentConfig(dept.name);
          const isActive = activeDepartment === dept.name || activeDepartment === config.nameCn;
          const isCompleted = dept.status === 'completed';
          const isRunning = dept.status === 'running';
          
          return (
            <motion.div
              key={dept.name}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              className={`p-4 rounded-lg border-2 transition-all ${
                isActive
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : isCompleted
                    ? 'border-green-500/50 bg-green-50 dark:bg-green-900/20'
                    : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg ${
                  isCompleted || isRunning ? config.color : 'bg-gray-200 dark:bg-gray-700'
                }`}>
                  {config.icon}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                    {config.nameCn}
                  </h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {config.description}
                  </p>
                </div>
                <div>
                  {isCompleted && <CheckCircleIcon className="w-5 h-5 text-green-500" />}
                  {isRunning && (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full"
                    />
                  )}
                  {dept.status === 'pending' && <ClockIcon className="w-5 h-5 text-gray-400" />}
                </div>
              </div>
              
              {isRunning && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                    <span>{dept.task || '处理中...'}</span>
                    <span>{dept.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${dept.progress}%` }}
                      className="bg-primary-500 h-1.5 rounded-full"
                    />
                  </div>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default DepartmentStatus;
