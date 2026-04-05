import { motion } from 'framer-motion';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';


interface MetricCardProps {
  title: string;
  value: number;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  status?: 'normal' | 'warning' | 'critical';
  threshold?: number;
  icon?: React.ReactNode;
}

export function MetricCard({
  title,
  value,
  unit,
  trend = 'stable',
  trendValue = 0,
  status = 'normal',
  threshold,
  icon,
}: MetricCardProps) {
  const statusColors = {
    normal: 'border-slate-700/50',
    warning: 'border-orange-500/50 bg-orange-500/5',
    critical: 'border-red-500/50 bg-red-500/5',
  };

  const trendColors = {
    up: status === 'critical' ? 'text-red-400' : status === 'warning' ? 'text-orange-400' : 'text-green-400',
    down: status === 'critical' ? 'text-green-400' : 'text-blue-400',
    stable: 'text-slate-400',
  };

  const TrendIcon = trend === 'up' ? ArrowUpIcon : trend === 'down' ? ArrowDownIcon : MinusIcon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        relative p-4 rounded-xl border backdrop-blur-sm
        bg-slate-800/50 ${statusColors[status]}
      `}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-sm text-slate-400">{title}</span>
        {icon && <div className="text-slate-500">{icon}</div>}
      </div>

      <div className="flex items-end gap-2">
        <span className="text-3xl font-bold text-white">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </span>
        <span className="text-sm text-slate-400 mb-1">{unit}</span>
      </div>

      <div className="flex items-center justify-between mt-2">
        <div className={`flex items-center gap-1 text-xs ${trendColors[trend]}`}>
          <TrendIcon className="w-3 h-3" />
          <span>{trendValue > 0 ? `${trendValue.toFixed(1)}%` : '稳定'}</span>
        </div>

        {threshold !== undefined && (
          <div className="text-xs text-slate-500">
            阈值: {threshold}{unit}
          </div>
        )}
      </div>

      {status !== 'normal' && (
        <div className="absolute top-2 right-2">
          <ExclamationTriangleIcon className={`w-4 h-4 ${status === 'critical' ? 'text-red-400' : 'text-orange-400'}`} />
        </div>
      )}
    </motion.div>
  );
}

export default MetricCard;
