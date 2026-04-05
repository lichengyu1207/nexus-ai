import { motion } from 'framer-motion';
import {
  PencilIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import type { AlertRule } from '../types';
import { AVAILABLE_METRICS } from '../types';

interface AlertRuleTableProps {
  rules: AlertRule[];
  onEdit: (rule: AlertRule) => void;
  onDelete: (id: string) => void;
  onToggle: (id: string, enabled: boolean) => void;
}

export function AlertRuleTable({
  rules,
  onEdit,
  onDelete,
  onToggle,
}: AlertRuleTableProps) {
  const getMetricName = (metricId: string) => {
    const metric = AVAILABLE_METRICS.find((m) => m.id === metricId);
    return metric?.name || metricId;
  };

  const getConditionLabel = (condition: string) => {
    const labels: Record<string, string> = {
      '>': '大于',
      '<': '小于',
      '>=': '大于等于',
      '<=': '小于等于',
    };
    return labels[condition] || condition;
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-700/50">
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              规则名称
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              监控指标
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              条件
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              持续时间
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              状态
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
              操作
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/30">
          {rules.map((rule, index) => (
            <motion.tr
              key={rule.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="hover:bg-slate-700/20 transition-colors"
            >
              <td className="px-4 py-3">
                <span className="text-sm text-white">{rule.name}</span>
              </td>
              <td className="px-4 py-3">
                <span className="text-sm text-slate-300">{getMetricName(rule.metric)}</span>
              </td>
              <td className="px-4 py-3">
                <span className="text-sm text-slate-300">
                  {getConditionLabel(rule.condition)} {rule.threshold}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className="text-sm text-slate-300">{rule.duration}秒</span>
              </td>
              <td className="px-4 py-3">
                <button
                  onClick={() => onToggle(rule.id, !rule.enabled)}
                  className={`
                    relative inline-flex h-5 w-9 items-center rounded-full transition-colors
                    ${rule.enabled ? 'bg-amber-500' : 'bg-slate-600'}
                  `}
                >
                  <span
                    className={`
                      inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                      ${rule.enabled ? 'translate-x-4' : 'translate-x-0.5'}
                    `}
                  />
                </button>
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onEdit(rule)}
                    className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onDelete(rule.id)}
                    className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </td>
            </motion.tr>
          ))}
          {rules.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                暂无告警规则
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default AlertRuleTable;
