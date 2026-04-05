import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend,
  Label
} from 'recharts';
import { ChartData, ChartPoint, getAgentInfo } from './types/reportStream';

interface ProgressiveChartProps {
  chartData: ChartData;
  progress?: number;
  isPlaying?: boolean;
  animationDuration?: number;
  showAgentTooltip?: boolean;
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
}

export interface ProgressiveChartRef {
  addPoint: (point: ChartPoint) => void;
  setProgress: (progress: number) => void;
  reset: () => void;
  skipToEnd: () => void;
  getCurrentData: () => ChartPoint[];
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

const ProgressiveChart = forwardRef<ProgressiveChartRef, ProgressiveChartProps>(({
  chartData,
  progress: externalProgress,
  isPlaying = true,
  animationDuration = 300,
  showAgentTooltip = true,
  onProgress,
  onComplete,
}, ref) => {
  const [internalProgress, setInternalProgress] = useState(0);
  const [visiblePoints, setVisiblePoints] = useState<ChartPoint[]>([]);
  const [animatingBars, setAnimatingBars] = useState<Set<number>>(new Set());
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);
  
  const progress = externalProgress !== undefined ? externalProgress : internalProgress;
  const totalPoints = chartData.data.length;
  const visiblePointCount = Math.floor((progress / 100) * totalPoints);

  useEffect(() => {
    if (externalProgress === undefined && isPlaying) {
      startTimeRef.current = performance.now();
      
      const animate = (currentTime: number) => {
        const elapsed = currentTime - startTimeRef.current;
        const newProgress = Math.min((elapsed / animationDuration) * 100, 100);
        setInternalProgress(newProgress);
        onProgress?.(newProgress);
        
        if (newProgress < 100) {
          animationRef.current = requestAnimationFrame(animate);
        } else {
          onComplete?.();
        }
      };
      
      animationRef.current = requestAnimationFrame(animate);
    }
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, animationDuration, externalProgress, onProgress, onComplete]);

  useEffect(() => {
    const points = chartData.data.slice(0, visiblePointCount);
    setVisiblePoints(points);
    
    if (chartData.chartType === 'bar') {
      const newAnimating = new Set<number>();
      points.forEach((_, index) => {
        if (!animatingBars.has(index)) {
          newAnimating.add(index);
        }
      });
      if (newAnimating.size > 0) {
        setAnimatingBars(prev => new Set([...prev, ...newAnimating]));
        setTimeout(() => {
          setAnimatingBars(prev => {
            const next = new Set(prev);
            newAnimating.forEach(i => next.delete(i));
            return next;
          });
        }, 500);
      }
    }
  }, [visiblePointCount, chartData.data, chartData.chartType]);

  const addPoint = (point: ChartPoint) => {
    setVisiblePoints(prev => [...prev, point]);
    const newProgress = ((visiblePoints.length + 1) / totalPoints) * 100;
    setInternalProgress(newProgress);
    onProgress?.(newProgress);
    
    if (newProgress >= 100) {
      onComplete?.();
    }
  };

  const setProgressExternal = (newProgress: number) => {
    setInternalProgress(newProgress);
    onProgress?.(newProgress);
  };

  const reset = () => {
    setInternalProgress(0);
    setVisiblePoints([]);
    setAnimatingBars(new Set());
  };

  const skipToEnd = () => {
    setInternalProgress(100);
    setVisiblePoints(chartData.data);
    onProgress?.(100);
    onComplete?.();
  };

  useImperativeHandle(ref, () => ({
    addPoint,
    setProgress: setProgressExternal,
    reset,
    skipToEnd,
    getCurrentData: () => visiblePoints,
  }), [visiblePoints, totalPoints, onProgress, onComplete]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const agent = payload[0].payload.agent;
      const agentInfo = agent ? getAgentInfo(agent) : null;
      
      return (
        <div style={{
          background: 'rgba(0, 0, 0, 0.9)',
          padding: '12px 16px',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        }}>
          <p style={{ color: '#fff', margin: 0, fontWeight: 'bold' }}>
            {label}
          </p>
          <p style={{ color: '#3B82F6', margin: '4px 0 0 0' }}>
            {chartData.yAxisLabel || '值'}: {payload[0].value}
          </p>
          {showAgentTooltip && agentInfo && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '4px', 
              marginTop: '8px',
              color: agentInfo.color,
              fontSize: '12px',
            }}>
              <span>{agentInfo.icon}</span>
              <span>数据来源: {agentInfo.name}</span>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  const renderLineChart = () => (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={visiblePoints} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
        <XAxis 
          dataKey="x" 
          stroke="rgba(255, 255, 255, 0.5)"
          tick={{ fill: 'rgba(255, 255, 255, 0.7)', fontSize: 12 }}
        >
          {chartData.xAxisLabel && (
            <Label value={chartData.xAxisLabel} position="bottom" fill="rgba(255, 255, 255, 0.7)" />
          )}
        </XAxis>
        <YAxis 
          stroke="rgba(255, 255, 255, 0.5)"
          tick={{ fill: 'rgba(255, 255, 255, 0.7)', fontSize: 12 }}
        >
          {chartData.yAxisLabel && (
            <Label value={chartData.yAxisLabel} angle={-90} position="left" fill="rgba(255, 255, 255, 0.7)" />
          )}
        </YAxis>
        <Tooltip content={<CustomTooltip />} />
        <Line 
          type="monotone" 
          dataKey="y" 
          stroke={chartData.colors?.[0] || COLORS[0]}
          strokeWidth={3}
          dot={{ 
            fill: chartData.colors?.[0] || COLORS[0], 
            strokeWidth: 2,
            r: 4,
          }}
          activeDot={{ 
            r: 6, 
            fill: chartData.colors?.[0] || COLORS[0],
            stroke: '#fff',
            strokeWidth: 2,
          }}
          animationDuration={300}
        />
      </LineChart>
    </ResponsiveContainer>
  );

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={visiblePoints} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
        <XAxis 
          dataKey="x" 
          stroke="rgba(255, 255, 255, 0.5)"
          tick={{ fill: 'rgba(255, 255, 255, 0.7)', fontSize: 12 }}
        />
        <YAxis 
          stroke="rgba(255, 255, 255, 0.5)"
          tick={{ fill: 'rgba(255, 255, 255, 0.7)', fontSize: 12 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar 
          dataKey="y" 
          fill={chartData.colors?.[0] || COLORS[0]}
          radius={[4, 4, 0, 0]}
          animationDuration={500}
        >
          {visiblePoints.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={chartData.colors?.[index % (chartData.colors?.length || 1)] || COLORS[index % COLORS.length]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );

  const renderPieChart = () => {
    const pieProgress = progress / 100;
    const endAngle = 360 * pieProgress;
    
    return (
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={visiblePoints}
            dataKey="y"
            nameKey="x"
            cx="50%"
            cy="50%"
            outerRadius={80}
            innerRadius={40}
            startAngle={0}
            endAngle={endAngle}
            animationDuration={0}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            labelLine={{ stroke: 'rgba(255, 255, 255, 0.3)' }}
          >
            {visiblePoints.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={chartData.colors?.[index % (chartData.colors?.length || 1)] || COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="bottom" 
            height={36}
            formatter={(value) => <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        background: 'rgba(255, 255, 255, 0.03)',
        borderRadius: '12px',
        padding: '16px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '12px',
      }}>
        <h4 style={{ 
          color: '#fff', 
          margin: 0, 
          fontSize: '16px',
          fontWeight: 600,
        }}>
          {chartData.title}
        </h4>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <span style={{
            fontSize: '12px',
            color: 'rgba(255, 255, 255, 0.5)',
          }}>
            {visiblePointCount}/{totalPoints} 数据点
          </span>
          <div style={{
            width: '60px',
            height: '4px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '2px',
            overflow: 'hidden',
          }}>
            <motion.div
              style={{
                height: '100%',
                background: chartData.colors?.[0] || COLORS[0],
                borderRadius: '2px',
              }}
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      </div>
      
      {chartData.chartType === 'line' && renderLineChart()}
      {chartData.chartType === 'bar' && renderBarChart()}
      {chartData.chartType === 'pie' && renderPieChart()}
    </motion.div>
  );
});

ProgressiveChart.displayName = 'ProgressiveChart';

export default ProgressiveChart;
