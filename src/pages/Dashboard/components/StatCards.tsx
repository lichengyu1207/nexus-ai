import { motion } from 'framer-motion';
import { 
  ClipboardDocumentListIcon, 
  PlayIcon, 
  CpuChipIcon, 
  ArrowPathIcon 
} from '@heroicons/react/24/outline';
import type { DashboardStats } from '../types';

interface StatCardsProps {
  stats: DashboardStats;
  onTaskClick?: () => void;
  onAgentClick?: () => void;
  onEventClick?: () => void;
}

export function StatCards({ stats, onTaskClick, onAgentClick, onEventClick }: StatCardsProps) {
  const cards = [
    {
      key: 'totalTasks',
      label: '总任务数',
      value: stats.totalTasks,
      subValue: `今日 ${stats.todayTasks}`,
      icon: ClipboardDocumentListIcon,
      color: 'from-amber-500 to-orange-600',
      onClick: onTaskClick,
    },
    {
      key: 'activeTasks',
      label: '进行中任务',
      value: stats.activeTasks,
      subValue: `${((stats.activeTasks / stats.totalTasks) * 100).toFixed(0)}% 占比`,
      icon: PlayIcon,
      color: 'from-green-500 to-emerald-600',
      onClick: onTaskClick,
    },
    {
      key: 'totalAgents',
      label: '智能体总数',
      value: stats.totalAgents,
      subValue: `${stats.healthyAgents} 健康 / ${stats.busyAgents} 繁忙`,
      icon: CpuChipIcon,
      color: 'from-blue-500 to-indigo-600',
      onClick: onAgentClick,
    },
    {
      key: 'crossEndEvents',
      label: '五端协同事件',
      value: stats.crossEndEventsToday,
      subValue: '今日',
      icon: ArrowPathIcon,
      color: 'from-purple-500 to-pink-600',
      onClick: onEventClick,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <motion.div
          key={card.key}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          whileHover={{ y: -2, boxShadow: '0 8px 30px rgba(0,0,0,0.3)' }}
          onClick={card.onClick}
          className={`
            bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-5
            cursor-pointer transition-all duration-200
            hover:border-amber-500/30
          `}
        >
          <div className="flex items-start justify-between mb-3">
            <div className={`p-2 rounded-lg bg-gradient-to-br ${card.color}`}>
              <card.icon className="w-5 h-5 text-white" />
            </div>
          </div>
          
          <div>
            <p className="text-slate-400 text-sm mb-1">{card.label}</p>
            <p className="text-3xl font-bold text-white mb-1">
              {card.value.toLocaleString()}
            </p>
            <p className="text-xs text-slate-500">{card.subValue}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
