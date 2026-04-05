import React from 'react';
import { motion } from 'framer-motion';
import ClusterHealth from '@/components/cluster/ClusterHealth';

const ClusterMonitorPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            集群健康监控
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            实时监控智能体节点状态、蜂群通信拓扑、活体检测记录
          </p>
        </motion.div>

        <ClusterHealth showTopology />
      </div>
    </div>
  );
};

export default ClusterMonitorPage;
