import React, { useState, Suspense, lazy } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { DashboardHeader } from './components/DashboardHeader';
import { QuickActions } from './components/QuickActions';
import { TaskSnapshot } from './components/TaskSnapshot';
import { CrossEndTimeline } from './components/CrossEndTimeline';
import {
  useHealthData,
  useRecentTasks,
  useCrossEndEvents,
  useAgentTopology,
} from './hooks/useDashboardData';
import { TopologyModal } from './components/TopologyModal';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const Dashboard: React.FC = () => {
  const [isTopologyOpen, setIsTopologyOpen] = useState(false);
  const { health, isLoading: healthLoading } = useHealthData();
  const { tasks, isLoading: tasksLoading } = useRecentTasks();
  const { events, isLoading: eventsLoading } = useCrossEndEvents();
  const { topology } = useAgentTopology();

  const isLoading = healthLoading || tasksLoading || eventsLoading;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      <motion.div variants={itemVariants}>
        <DashboardHeader health={health} isLoading={isLoading} />
      </motion.div>

      <motion.div variants={itemVariants}>
        <QuickActions />
      </motion.div>

      <motion.div variants={itemVariants}>
        <TaskSnapshot tasks={tasks} isLoading={tasksLoading} />
      </motion.div>

      <motion.div variants={itemVariants}>
        <CrossEndTimeline events={events} isLoading={eventsLoading} />
      </motion.div>

      <motion.button
        variants={itemVariants}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsTopologyOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-primary rounded-full shadow-lg flex items-center justify-center hover:bg-primary-dark transition-colors z-40"
        aria-label="查看智能体拓扑图"
      >
        <svg
          className="w-6 h-6 text-gray-900"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
      </motion.button>

      <TopologyModal
        topology={topology}
        isOpen={isTopologyOpen}
        onClose={() => setIsTopologyOpen(false)}
      />
    </motion.div>
  );
};

export default Dashboard;
