import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useEndStats } from '../hooks/useEndStats';
import type { EndName } from '../types';

interface EndStatisticsCardsProps {
  endId: EndName;
}

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.3 },
  }),
};

const statIcons: Record<string, string> = {
  taskCount: '📋',
  activeUsers: '👥',
  messageCount: '💬',
};

const statLabels: Record<string, string> = {
  taskCount: '任务数',
  activeUsers: '活跃用户',
  messageCount: '消息数',
};

export function EndStatisticsCards({ endId }: EndStatisticsCardsProps) {
  const navigate = useNavigate();
  const { data: stats, isLoading, error } = useEndStats(endId);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-24 rounded-xl bg-slate-800/50 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="col-span-3 p-4 rounded-xl bg-red-500/10 text-red-400 text-center">
          加载统计数据失败
        </div>
      </div>
    );
  }

  const statItems = [
    { key: 'taskCount', value: stats.taskCount, route: '/tasks' },
    { key: 'activeUsers', value: stats.activeUsers, route: '/users' },
    { key: 'messageCount', value: stats.messageCount, route: '/messages' },
  ];

  const handleCardClick = (route: string) => {
    navigate(`${route}?end=${endId}`);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {statItems.map((item, index) => (
        <motion.button
          key={item.key}
          custom={index}
          variants={cardVariants}
          initial="hidden"
          animate="visible"
          onClick={() => handleCardClick(item.route)}
          className="
            relative p-5 rounded-xl cursor-pointer
            bg-gradient-to-br from-slate-800/80 to-slate-900/80
            backdrop-blur-md border border-amber-500/20
            hover:border-amber-400/40 hover:shadow-lg hover:shadow-amber-500/10
            transition-all duration-300 group
          "
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{statIcons[item.key]}</span>
              <span className="text-gray-400 text-sm">{statLabels[item.key]}</span>
            </div>
            <motion.span
              className="text-3xl font-bold text-white group-hover:text-amber-400 transition-colors"
              whileHover={{ scale: 1.05 }}
            >
              {item.value.toLocaleString()}
            </motion.span>
          </div>
          <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
        </motion.button>
      ))}
    </div>
  );
}
