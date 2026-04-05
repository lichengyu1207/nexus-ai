import React from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircleIcon, 
  ClockIcon, 
  ExclamationCircleIcon,
  ArrowRightIcon 
} from '@heroicons/react/24/outline';

interface ProvinceStep {
  name: string;
  nameCn: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  description: string;
  started_at?: string;
  completed_at?: string;
}

interface GovernanceFlowProps {
  currentProvince?: 'zhongshu' | 'menxia' | 'shangshu';
  steps: ProvinceStep[];
  overallProgress: number;
}

const provinceConfig = {
  zhongshu: {
    name: '中书省',
    icon: '📜',
    color: 'bg-purple-500',
    lightColor: 'bg-purple-100',
    textColor: 'text-purple-700',
    description: '决策规划 - 制定分析方案',
  },
  menxia: {
    name: '门下省',
    icon: '⚖️',
    color: 'bg-blue-500',
    lightColor: 'bg-blue-100',
    textColor: 'text-blue-700',
    description: '审核监督 - 合规检查与方案审核',
  },
  shangshu: {
    name: '尚书省',
    icon: '🏛️',
    color: 'bg-green-500',
    lightColor: 'bg-green-100',
    textColor: 'text-green-700',
    description: '执行实施 - 六部协同执行任务',
  },
};

const statusIcons = {
  pending: <ClockIcon className="w-5 h-5 text-gray-400" />,
  running: <motion.div
    animate={{ rotate: 360 }}
    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
    className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full"
  />,
  completed: <CheckCircleIcon className="w-5 h-5 text-green-500" />,
  failed: <ExclamationCircleIcon className="w-5 h-5 text-red-500" />,
};

const GovernanceFlow: React.FC<GovernanceFlowProps> = ({
  currentProvince,
  steps,
  overallProgress,
}) => {
  const provinces = ['zhongshu', 'menxia', 'shangshu'] as const;
  
  const getStepStatus = (province: string): ProvinceStep['status'] => {
    const step = steps.find(s => s.name === province);
    return step?.status || 'pending';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          三省工作流程
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">总体进度</span>
          <span className="text-lg font-bold text-primary-600">{overallProgress}%</span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        {provinces.map((province, index) => {
          const config = provinceConfig[province];
          const status = getStepStatus(province);
          const isActive = currentProvince === province;
          
          return (
            <React.Fragment key={province}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex-1 max-w-[200px] p-4 rounded-xl border-2 transition-all ${
                  isActive 
                    ? 'border-primary-500 shadow-lg shadow-primary-500/20' 
                    : status === 'completed'
                      ? 'border-green-500/50 bg-green-50 dark:bg-green-900/20'
                      : 'border-gray-200 dark:border-gray-700'
                }`}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl ${
                    status === 'completed' ? config.color : 'bg-gray-100 dark:bg-gray-700'
                  }`}>
                    {config.icon}
                  </div>
                  <div>
                    <h4 className={`font-semibold ${
                      isActive ? 'text-primary-600' : 'text-gray-900 dark:text-white'
                    }`}>
                      {config.name}
                    </h4>
                    <div className="flex items-center gap-1">
                      {statusIcons[status]}
                      <span className={`text-xs ${
                        status === 'completed' ? 'text-green-600' :
                        status === 'running' ? 'text-blue-600' :
                        status === 'failed' ? 'text-red-600' : 'text-gray-400'
                      }`}>
                        {status === 'completed' ? '已完成' :
                         status === 'running' ? '处理中' :
                         status === 'failed' ? '失败' : '等待中'}
                      </span>
                    </div>
                  </div>
                </div>
                
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                  {config.description}
                </p>
                
                {status === 'running' && (
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${steps.find(s => s.name === province)?.progress || 0}%` }}
                      className="bg-primary-500 h-2 rounded-full"
                    />
                  </div>
                )}
              </motion.div>
              
              {index < provinces.length - 1 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.1 + 0.05 }}
                  className="mx-2"
                >
                  <ArrowRightIcon className={`w-6 h-6 ${
                    getStepStatus(provinces[index + 1]) !== 'pending' 
                      ? 'text-primary-500' 
                      : 'text-gray-300 dark:text-gray-600'
                  }`} />
                </motion.div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default GovernanceFlow;
