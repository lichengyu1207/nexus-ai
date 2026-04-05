import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { CompareTask, DifferenceAnalysis } from './types';

interface CompareTableProps {
  tasks: CompareTask[];
  highlightThreshold?: number;
}

const formatValuation = (val: number) => `¥ ${val.toLocaleString()}`;
const formatRisk = (score: number) => `${score} 分`;
const formatPercent = (val: number) => `${(val * 100).toFixed(1)}%`;

const getRange = (values: number[]) => {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const diffPercent = min !== 0 ? ((max - min) / min) * 100 : max > 0 ? 100 : 0;
  return { min, max, diffPercent };
};

export const CompareTable: React.FC<CompareTableProps> = ({ tasks, highlightThreshold = 10 }) => {
  const metrics = useMemo(() => {
    const valuations = tasks.map((t) => t.metrics.valuation);
    const riskScores = tasks.map((t) => t.metrics.riskScore);
    const profitExpectations = tasks.map((t) => t.metrics.profitExpectation);
    const confidences = tasks.map((t) => t.metrics.confidence);

    return {
      valuations,
      riskScores,
      profitExpectations,
      confidences,
      valuationRange: getRange(valuations),
      riskRange: getRange(riskScores),
      profitRange: getRange(profitExpectations),
      confidenceRange: getRange(confidences),
    };
  }, [tasks]);

  const isHighlight = (values: number[], current: number) => {
    const range = getRange(values);
    if (range.diffPercent > highlightThreshold) {
      return current === range.max || current === range.min;
    }
    return false;
  };

  const getHighlightClass = (values: number[], current: number) => {
    if (!isHighlight(values, current)) return '';
    const range = getRange(values);
    return current === range.max
      ? 'text-green-400 font-bold bg-green-400/10'
      : 'text-red-400 font-bold bg-red-400/10';
  };

  const rowVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: (i: number) => ({
      opacity: 1,
      x: 0,
      transition: { delay: i * 0.1 },
    }),
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full">
        <thead>
          <tr className="border-b border-border-light">
            <th className="px-4 py-3 text-left text-sm font-medium text-text-secondary bg-bg-tertiary/50">
              指标
            </th>
            {tasks.map((task) => (
              <th
                key={task.id}
                className="px-4 py-3 text-left text-sm font-medium text-primary bg-bg-tertiary/50"
              >
                <div>{task.name}</div>
                <div className="text-xs text-text-secondary font-normal">
                  {new Date(task.completedAt).toLocaleDateString('zh-CN')}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border-light">
          <motion.tr
            custom={0}
            variants={rowVariants}
            initial="hidden"
            animate="visible"
            className="hover:bg-bg-tertiary/30"
          >
            <td className="px-4 py-3 text-sm text-text-primary">估价</td>
            {tasks.map((task) => (
              <td
                key={task.id}
                className={`px-4 py-3 text-sm ${getHighlightClass(
                  metrics.valuations,
                  task.metrics.valuation
                )}`}
              >
                {formatValuation(task.metrics.valuation)}
              </td>
            ))}
          </motion.tr>

          <motion.tr
            custom={1}
            variants={rowVariants}
            initial="hidden"
            animate="visible"
            className="hover:bg-bg-tertiary/30"
          >
            <td className="px-4 py-3 text-sm text-text-primary">风险评分</td>
            {tasks.map((task) => (
              <td
                key={task.id}
                className={`px-4 py-3 text-sm ${getHighlightClass(
                  metrics.riskScores,
                  task.metrics.riskScore
                )}`}
              >
                {formatRisk(task.metrics.riskScore)}
              </td>
            ))}
          </motion.tr>

          <motion.tr
            custom={2}
            variants={rowVariants}
            initial="hidden"
            animate="visible"
            className="hover:bg-bg-tertiary/30"
          >
            <td className="px-4 py-3 text-sm text-text-primary">预期收益</td>
            {tasks.map((task) => (
              <td
                key={task.id}
                className={`px-4 py-3 text-sm ${getHighlightClass(
                  metrics.profitExpectations,
                  task.metrics.profitExpectation
                )}`}
              >
                {formatPercent(task.metrics.profitExpectation)}
              </td>
            ))}
          </motion.tr>

          <motion.tr
            custom={3}
            variants={rowVariants}
            initial="hidden"
            animate="visible"
            className="hover:bg-bg-tertiary/30"
          >
            <td className="px-4 py-3 text-sm text-text-primary">置信度</td>
            {tasks.map((task) => (
              <td
                key={task.id}
                className={`px-4 py-3 text-sm ${getHighlightClass(
                  metrics.confidences,
                  task.metrics.confidence
                )}`}
              >
                {formatPercent(task.metrics.confidence)}
              </td>
            ))}
          </motion.tr>

          <motion.tr
            custom={4}
            variants={rowVariants}
            initial="hidden"
            animate="visible"
            className="hover:bg-bg-tertiary/30"
          >
            <td className="px-4 py-3 text-sm text-text-primary">建议</td>
            {tasks.map((task) => (
              <td key={task.id} className="px-4 py-3 text-sm text-text-primary">
                {task.metrics.suggestion}
              </td>
            ))}
          </motion.tr>
        </tbody>
      </table>
    </div>
  );
};

export const generateDifferenceAnalysis = (tasks: CompareTask[], threshold = 10): DifferenceAnalysis[] => {
  const analyses: DifferenceAnalysis[] = [];
  const metricsConfig = [
    { key: 'valuation', name: '估价' },
    { key: 'riskScore', name: '风险评分' },
    { key: 'profitExpectation', name: '预期收益' },
    { key: 'confidence', name: '置信度' },
  ];

  metricsConfig.forEach(({ key, name }) => {
    const values = tasks.map((t) => t.metrics[key as keyof typeof t.metrics] as number);
    const range = getRange(values);
    const maxTask = tasks.find((t) => t.metrics[key as keyof typeof t.metrics] === range.max);
    const minTask = tasks.find((t) => t.metrics[key as keyof typeof t.metrics] === range.min);

    analyses.push({
      metric: name,
      maxValue: range.max,
      minValue: range.min,
      maxTask: maxTask?.name || '',
      minTask: minTask?.name || '',
      diffPercent: range.diffPercent,
      isSignificant: range.diffPercent > threshold,
    });
  });

  return analyses;
};

export default CompareTable;
