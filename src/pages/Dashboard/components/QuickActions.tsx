import { motion } from 'framer-motion';
import { PlusIcon, CpuChipIcon, BrainIcon } from '@heroicons/react/24/outline';

interface QuickActionsProps {
  onNewTask: () => void;
  onAgentWorkshop: () => void;
  onMemorySystem: () => void;
}

export function QuickActions({ onNewTask, onAgentWorkshop, onMemorySystem }: QuickActionsProps) {
  const actions = [
    {
      key: 'newTask',
      label: '新建任务',
      description: '创建新的智能体任务',
      icon: PlusIcon,
      onClick: onNewTask,
      gradient: 'from-amber-500 to-orange-600',
    },
    {
      key: 'agentWorkshop',
      label: '智能体工坊',
      description: '管理和配置智能体',
      icon: CpuChipIcon,
      onClick: onAgentWorkshop,
      gradient: 'from-blue-500 to-indigo-600',
    },
    {
      key: 'memorySystem',
      label: '记忆系统',
      description: '查看和管理记忆库',
      icon: BrainIcon,
      onClick: onMemorySystem,
      gradient: 'from-purple-500 to-pink-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {actions.map((action, index) => (
        <motion.button
          key={action.key}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          whileHover={{ scale: 1.02, y: -2 }}
          whileTap={{ scale: 0.98 }}
          onClick={action.onClick}
          className="
            relative overflow-hidden
            bg-slate-800/50 backdrop-blur-sm rounded-xl 
            border border-slate-700/50 p-6 text-left
            hover:border-amber-500/30 transition-all duration-200
            group
          "
        >
          <div className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-10 transition-opacity`} />
          
          <div className="relative">
            <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${action.gradient} mb-4`}>
              <action.icon className="w-6 h-6 text-white" />
            </div>
            
            <h4 className="text-lg font-semibold text-white mb-1">{action.label}</h4>
            <p className="text-sm text-slate-400">{action.description}</p>
          </div>
        </motion.button>
      ))}
    </div>
  );
}
