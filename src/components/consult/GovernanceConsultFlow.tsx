import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  PaperAirplaneIcon, 
  SparklesIcon,
  DocumentTextIcon,
  ChartBarIcon,
  MapIcon
} from '@heroicons/react/24/outline';
import GovernanceFlow from '@/components/workflow/GovernanceFlow';
import DepartmentStatus from '@/components/workflow/DepartmentStatus';
import { useGovernanceTask } from '@/hooks/useGovernanceTask';

interface GovernanceConsultFlowProps {
  initialQuery?: string;
  onComplete?: (result: any) => void;
}

interface AnalysisResult {
  summary: string;
  findings: string[];
  recommendations: string[];
  charts?: any[];
  maps?: any[];
}

const GovernanceConsultFlow: React.FC<GovernanceConsultFlowProps> = ({
  initialQuery = '',
  onComplete,
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [showResult, setShowResult] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  
  const { 
    createTaskAsync, 
    isCreating, 
    taskData, 
    activeTaskId,
    isLoading 
  } = useGovernanceTask();

  const handleSubmit = async () => {
    if (!query.trim()) return;
    
    try {
      await createTaskAsync({ 
        query, 
        style: 'balanced' 
      });
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  useEffect(() => {
    if (taskData?.status === 'completed' && taskData.result) {
      setAnalysisResult(taskData.result as AnalysisResult);
      setShowResult(true);
      onComplete?.(taskData.result);
    }
  }, [taskData, onComplete]);

  const workflowSteps = taskData?.workflow_steps || [
    { name: 'zhongshu', status: 'pending', progress: 0 },
    { name: 'menxia', status: 'pending', progress: 0 },
    { name: 'shangshu', status: 'pending', progress: 0 },
  ];

  const departments = [
    { name: 'li', status: 'pending', progress: 0 },
    { name: 'hu', status: 'pending', progress: 0 },
    { name: 'li_guan', status: 'pending', progress: 0 },
    { name: 'bing', status: 'pending', progress: 0 },
    { name: 'xing', status: 'pending', progress: 0 },
    { name: 'gong', status: 'pending', progress: 0 },
  ];

  return (
    <div className="space-y-6">
      {/* 输入区域 */}
      {!activeTaskId && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            智能房产分析
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            输入您的房产需求，三省六部制系统将为您提供专业的分析报告
          </p>
          
          <div className="flex gap-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="例如：深圳南山区100平米学区房，预算1000万"
              className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            />
            <button
              onClick={handleSubmit}
              disabled={isCreating || !query.trim()}
              className="px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isCreating ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                />
              ) : (
                <PaperAirplaneIcon className="w-5 h-5" />
              )}
              <span>开始分析</span>
            </button>
          </div>
        </motion.div>
      )}

      {/* 工作流展示 */}
      {activeTaskId && !showResult && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-6"
        >
          {/* 查询显示 */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
              <SparklesIcon className="w-5 h-5" />
              <span className="font-medium">正在分析：</span>
              <span>{query}</span>
            </div>
          </div>

          {/* 三省工作流 */}
          <GovernanceFlow
            currentProvince={taskData?.current_province}
            steps={workflowSteps}
            overallProgress={taskData?.progress || 0}
          />

          {/* 六部状态 */}
          {taskData?.status === 'executing' && (
            <DepartmentStatus
              departments={departments}
              activeDepartment={taskData?.current_department}
            />
          )}

          {/* 状态提示 */}
          <div className="text-center text-gray-500">
            {taskData?.status === 'queued' && '任务已入队列，等待处理...'}
            {taskData?.status === 'planning' && '中书省正在制定分析方案...'}
            {taskData?.status === 'reviewing' && '门下省正在审核方案...'}
            {taskData?.status === 'executing' && '尚书省正在执行分析任务...'}
          </div>
        </motion.div>
      )}

      {/* 分析结果 */}
      <AnimatePresence>
        {showResult && analysisResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* 结果概要 */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <DocumentTextIcon className="w-5 h-5 text-primary-500" />
                分析报告
              </h3>
              <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {analysisResult.summary}
              </p>
            </div>

            {/* 关键发现 */}
            {analysisResult.findings && analysisResult.findings.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartBarIcon className="w-5 h-5 text-green-500" />
                  关键发现
                </h3>
                <ul className="space-y-2">
                  {analysisResult.findings.map((finding, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-300 flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </span>
                      <span className="text-gray-700 dark:text-gray-300">{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 建议 */}
            {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <MapIcon className="w-5 h-5 text-blue-500" />
                  专业建议
                </h3>
                <ul className="space-y-2">
                  {analysisResult.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </span>
                      <span className="text-gray-700 dark:text-gray-300">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 重新分析按钮 */}
            <div className="flex justify-center">
              <button
                onClick={() => {
                  setShowResult(false);
                  setAnalysisResult(null);
                  setQuery('');
                }}
                className="px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                开始新的分析
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default GovernanceConsultFlow;
