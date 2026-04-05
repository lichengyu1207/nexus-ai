import { motion } from 'framer-motion';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import type { HealthCheck } from '../types';
import { HEALTH_STATUS_COLORS, HEALTH_STATUS_LABELS, COMPONENT_NAMES } from '../types';

interface HealthCheckCardProps {
  check: HealthCheck;
  onManualCheck?: () => void;
  isChecking?: boolean;
}

const StatusIcon = {
  healthy: CheckCircleIcon,
  degraded: ExclamationTriangleIcon,
  down: ExclamationCircleIcon,
};

export function HealthCheckCard({
  check,
  onManualCheck,
  isChecking,
}: HealthCheckCardProps) {
  const Icon = StatusIcon[check.status];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        p-4 rounded-xl border backdrop-blur-sm
        bg-slate-800/50
        ${check.status === 'healthy' ? 'border-green-500/30' :
          check.status === 'degraded' ? 'border-yellow-500/30' :
          'border-red-500/30'}
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`
            p-2 rounded-lg
            ${check.status === 'healthy' ? 'bg-green-500/20' :
              check.status === 'degraded' ? 'bg-yellow-500/20' :
              'bg-red-500/20'}
          `}>
            <Icon className={`w-5 h-5 ${HEALTH_STATUS_COLORS[check.status]}`} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-white">
              {COMPONENT_NAMES[check.component] || check.component}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {HEALTH_STATUS_LABELS[check.status]}
            </p>
          </div>
        </div>

        {onManualCheck && (
          <button
            onClick={onManualCheck}
            disabled={isChecking}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-4 h-4 ${isChecking ? 'animate-spin' : ''}`} />
          </button>
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 text-xs">
        <div>
          <span className="text-slate-500">响应时间</span>
          <p className="text-white mt-0.5">{check.latency}ms</p>
        </div>
        <div>
          <span className="text-slate-500">最后检查</span>
          <p className="text-white mt-0.5">
            {new Date(check.lastCheck).toLocaleTimeString('zh-CN')}
          </p>
        </div>
      </div>

      {check.details && (
        <p className="mt-3 text-xs text-slate-400 border-t border-slate-700/30 pt-3">
          {check.details}
        </p>
      )}
    </motion.div>
  );
}

export default HealthCheckCard;
