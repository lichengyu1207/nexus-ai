import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { ArrowsPointingOutIcon, XMarkIcon } from '@heroicons/react/24/outline';
import type { MetricSeries } from '../types';

interface MetricChartProps {
  title: string;
  data: MetricSeries;
  height?: number;
  color?: string;
  showGrid?: boolean;
}

export function MetricChart({
  title,
  data,
  height = 200,
  color = '#f59e0b',
  showGrid = true,
}: MetricChartProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const chartData = data.data.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    }),
    value: point.value,
    timestamp: point.timestamp,
  }));

  const formatValue = useCallback((value: number) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toFixed(1);
  }, []);

  const CustomTooltip = useCallback(({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-700/50 rounded-lg p-3 shadow-xl">
          <p className="text-xs text-slate-400 mb-1">{label}</p>
          <p className="text-sm font-medium text-white">
            {payload[0].value.toFixed(2)} {data.unit}
          </p>
        </div>
      );
    }
    return null;
  }, [data.unit]);

  const ChartContent = () => (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        {showGrid && (
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        )}
        <XAxis
          dataKey="time"
          stroke="#64748b"
          fontSize={10}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#64748b"
          fontSize={10}
          tickLine={false}
          axisLine={false}
          tickFormatter={formatValue}
        />
        <Tooltip content={<CustomTooltip />} />
        <defs>
          <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          fill={`url(#gradient-${title})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  );

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-white">{title}</h3>
          <button
            onClick={() => setIsFullscreen(true)}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
          >
            <ArrowsPointingOutIcon className="w-4 h-4" />
          </button>
        </div>
        <ChartContent />
      </motion.div>

      <AnimatePresence>
        {isFullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-8"
            onClick={() => setIsFullscreen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-slate-800 border border-slate-700/50 rounded-xl p-6 w-full max-w-5xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-medium text-white">{title}</h3>
                <button
                  onClick={() => setIsFullscreen(false)}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} tickFormatter={formatValue} />
                  <Tooltip content={<CustomTooltip />} />
                  <defs>
                    <linearGradient id={`gradient-${title}-fullscreen`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={color} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke={color}
                    strokeWidth={2}
                    fill={`url(#gradient-${title}-fullscreen)`}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default MetricChart;
