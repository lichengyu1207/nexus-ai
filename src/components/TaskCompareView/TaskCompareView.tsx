import React, { useState, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TaskSelector } from './TaskSelector';
import { CompareTable, generateDifferenceAnalysis } from './CompareTable';
import { RadarChartComponent } from './RadarChart';
import { PDFExport } from './PDFExport';
import { fetchCompareData } from './api';
import { CompareTask, AvailableTask, DifferenceAnalysis } from './types';

interface TaskCompareViewProps {
  availableTasks?: AvailableTask[];
  onBack?: () => void;
}

export const TaskCompareView: React.FC<TaskCompareViewProps> = ({
  availableTasks = [],
  onBack,
}) => {
  const [selectedTaskIds, setSelectedTaskIds] = useState<string[]>([]);
  const [compareTasks, setCompareTasks] = useState<CompareTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reportRef = useRef<HTMLDivElement>(null);

  const handleCompare = async (ids: string[]) => {
    setSelectedTaskIds(ids);
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCompareData(ids);
      setCompareTasks(data.tasks);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '获取对比数据失败';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setSelectedTaskIds([]);
    setCompareTasks([]);
    setError(null);
    onBack?.();
  };

  const differenceAnalysis = useMemo(() => {
    if (compareTasks.length < 2) return [];
    return generateDifferenceAnalysis(compareTasks);
  }, [compareTasks]);

  const significantDifferences = useMemo(
    () => differenceAnalysis.filter((d) => d.isSignificant),
    [differenceAnalysis]
  );

  if (selectedTaskIds.length === 0) {
    return (
      <TaskSelector
        tasks={availableTasks}
        onCompare={handleCompare}
        onCancel={onBack}
      />
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-text-secondary">加载对比数据...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <div className="text-red-400 mb-4">{error}</div>
        <button onClick={handleBack} className="text-primary hover:underline">
          返回选择
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <motion.button
          whileHover={{ x: -4 }}
          onClick={handleBack}
          className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回选择
        </motion.button>
        <PDFExport containerRef={reportRef} fileName="任务对比报告" />
      </div>

      <div ref={reportRef} className="bg-bg-secondary rounded-xl p-6 space-y-6 border border-border-light">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-text-primary">任务对比报告</h2>
          <span className="text-sm text-text-secondary">
            生成时间: {new Date().toLocaleString('zh-CN')}
          </span>
        </div>

        <CompareTable tasks={compareTasks} />

        <div className="pt-4">
          <h3 className="text-lg font-semibold text-text-primary mb-4">多维度对比</h3>
          <RadarChartComponent tasks={compareTasks} />
        </div>

        <div className="pt-4">
          <h3 className="text-lg font-semibold text-text-primary mb-3">差异分析</h3>
          <div className="bg-bg-tertiary rounded-lg p-4 space-y-3">
            <AnimatePresence>
              {significantDifferences.length > 0 ? (
                significantDifferences.map((diff, index) => (
                  <motion.div
                    key={diff.metric}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-2 text-sm"
                  >
                    <span className="text-yellow-400 mt-0.5">⚠</span>
                    <span className="text-text-primary">
                      <strong>{diff.metric}</strong> 差异较大：{diff.maxTask} 比 {diff.minTask}{' '}
                      高出 <span className="text-yellow-400 font-bold">{diff.diffPercent.toFixed(1)}%</span>
                    </span>
                  </motion.div>
                ))
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-2 text-sm text-text-secondary"
                >
                  <span className="text-green-400">✓</span>
                  各任务指标差异在合理范围内（差异均小于10%）
                </motion.div>
              )}
            </AnimatePresence>

            {differenceAnalysis.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border-light">
                <h4 className="text-sm font-medium text-text-secondary mb-2">详细数据</h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                  {differenceAnalysis.map((diff) => (
                    <div key={diff.metric} className="bg-bg-secondary rounded p-2">
                      <div className="text-text-secondary">{diff.metric}</div>
                      <div className="text-text-primary font-medium">
                        差异 {diff.diffPercent.toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskCompareView;
