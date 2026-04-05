import React from 'react';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface DataSeries {
  dataKey: string;
  name: string;
  color?: string;
}

interface LineChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  series: DataSeries[];
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  showDots?: boolean;
  curved?: boolean;
}

const defaultColors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

const LineChart: React.FC<LineChartProps> = ({
  data,
  xKey,
  series,
  height = 300,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  showDots = true,
  curved = true,
}) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#374151" />}
        <XAxis dataKey={xKey} stroke="#9CA3AF" fontSize={12} />
        <YAxis stroke="#9CA3AF" fontSize={12} />
        {showTooltip && (
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#F9FAFB' }}
          />
        )}
        {showLegend && <Legend />}
        {series.map((s, index) => (
          <Line
            key={s.dataKey}
            type={curved ? 'monotone' : 'linear'}
            dataKey={s.dataKey}
            name={s.name}
            stroke={s.color || defaultColors[index % defaultColors.length]}
            strokeWidth={2}
            dot={showDots ? { fill: s.color || defaultColors[index % defaultColors.length], r: 4 } : false}
            activeDot={{ r: 6 }}
          />
        ))}
      </RechartsLineChart>
    </ResponsiveContainer>
  );
};

export default LineChart;
