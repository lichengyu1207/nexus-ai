import { useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import type { AlertEvent } from '../types';
import { SEVERITY_COLORS, SEVERITY_LABELS } from '../types';

interface AlertHistoryListProps {
  alerts: AlertEvent[];
  isLoading: boolean;
  onViewDetail: (alert: AlertEvent) => void;
}

const SeverityIcon = {
  critical: ExclamationCircleIcon,
  warning: ExclamationTriangleIcon,
  info: InformationCircleIcon,
};

export function AlertHistoryList({
  alerts,
  isLoading,
  onViewDetail,
}: AlertHistoryListProps) {
  const Row = useCallback(
    ({ index, style }: { index: number; style: React.CSSProperties }) => {
      const alert = alerts[index];
      const Icon = SeverityIcon[alert.severity];

      return (
        <div style={style} className="px-2">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.02 }}
            onClick={() => onViewDetail(alert)}
            className={`
              flex items-center gap-4 p-3 rounded-lg cursor-pointer
              border transition-colors hover:bg-slate-700/30
              ${SEVERITY_COLORS[alert.severity]}
            `}
          >
            <div className="flex-shrink-0">
              <Icon className="w-5 h-5" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white truncate">
                  {alert.ruleName}
                </span>
                <span className={`px-2 py-0.5 text-xs rounded border ${SEVERITY_COLORS[alert.severity]}`}>
                  {SEVERITY_LABELS[alert.severity]}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                触发值: {alert.value.toFixed(2)} / 阈值: {alert.threshold}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-xs text-slate-400">
                  {new Date(alert.triggeredAt).toLocaleString('zh-CN')}
                </p>
                <div className="flex items-center gap-1 mt-0.5">
                  {alert.status === 'firing' ? (
                    <span className="text-xs text-red-400">触发中</span>
                  ) : (
                    <>
                      <CheckCircleIcon className="w-3 h-3 text-green-400" />
                      <span className="text-xs text-green-400">已恢复</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      );
    },
    [alerts, onViewDetail]
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl overflow-hidden">
      <AnimatePresence>
        {alerts.length > 0 ? (
          <List
            height={400}
            itemCount={alerts.length}
            itemSize={80}
            width="100%"
          >
            {Row}
          </List>
        ) : (
          <div className="flex flex-col items-center justify-center py-12">
            <CheckCircleIcon className="w-12 h-12 text-green-400 mb-4" />
            <p className="text-slate-400">暂无告警历史</p>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default AlertHistoryList;
