import React from 'react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { useHealthData } from '../hooks/useDashboardData';

interface DashboardHeaderProps {
  userName?: string;
}

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 6) return '夜深了';
  if (hour < 12) return '早上好';
  if (hour < 14) return '中午好';
  if (hour < 18) return '下午好';
  return '晚上好';
};

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ userName = '用户' }) => {
  const { health, isLoading } = useHealthData();

  const healthData = [
    { name: '健康度', value: health },
    { name: '剩余', value: 100 - health },
  ];

  const getHealthColor = (value: number) => {
    if (value >= 80) return '#10B981';
    if (value >= 60) return '#FFD966';
    return '#EF4444';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center justify-between p-6 bg-bg-secondary rounded-xl"
    >
      <div>
        <h1 className="text-2xl font-bold text-text-primary">
          {getGreeting()}，{userName}
        </h1>
        <p className="text-text-secondary mt-1">
          欢迎回到房都督平台，今日已为您完成 {isLoading ? '...' : `${health}%`} 系统健康检查
        </p>
      </div>

      <div className="relative w-32 h-32">
        {isLoading ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={healthData}
                cx="50%"
                cy="50%"
                innerRadius={35}
                outerRadius={50}
                paddingAngle={0}
                dataKey="value"
              >
                <Cell fill={getHealthColor(health)} />
                <Cell fill="#374151" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        )}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold text-text-primary">{health}%</span>
        </div>
      </div>
    </motion.div>
  );
};

export default DashboardHeader;
