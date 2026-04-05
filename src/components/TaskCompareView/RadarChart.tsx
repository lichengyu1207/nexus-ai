import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { CompareTask } from './types';

interface RadarChartProps {
  tasks: CompareTask[];
  height?: number;
}

const COLORS = ['#FFD966', '#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

const DIMENSION_CONFIG = [
  { key: 'valuation', label: '估价' },
  { key: 'riskScore', label: '风险评分' },
  { key: 'profitExpectation', label: '收益预期' },
  { key: 'stability', label: '稳定性' },
];

export const RadarChartComponent: React.FC<RadarChartProps> = ({ tasks, height = 320 }) => {
  const data = DIMENSION_CONFIG.map(({ key, label }) => {
    const entry: Record<string, string | number> = { dimension: label, fullDimension: label };
    tasks.forEach((task) => {
      const value = task.radarData[key as keyof typeof task.radarData];
      entry[task.name] = typeof value === 'number' ? value : 0;
    });
    return entry;
  });

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 1]}
            tick={{ fill: '#6B7280', fontSize: 10 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#F3F4F6',
            }}
            formatter={(value: number) => [(value * 100).toFixed(1) + '%', '']}
          />
          {tasks.map((task, idx) => (
            <Radar
              key={task.id}
              name={task.name}
              dataKey={task.name}
              stroke={COLORS[idx % COLORS.length]}
              fill={COLORS[idx % COLORS.length]}
              fillOpacity={0.25}
              strokeWidth={2}
            />
          ))}
          <Legend
            wrapperStyle={{ color: '#F3F4F6', paddingTop: '10px' }}
            formatter={(value) => <span className="text-text-primary">{value}</span>}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RadarChartComponent;
