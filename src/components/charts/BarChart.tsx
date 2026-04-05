import React from 'react';
import {
  BarChart as RechartsBarChart,
  Bar,
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

interface BarChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  series: DataSeries[];
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  horizontal?: boolean;
  stacked?: boolean;
}

const defaultColors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

const BarChart: React.FC<BarChartProps> = ({
  data,
  xKey,
  series,
  height = 300,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  horizontal = false,
  stacked = false,
}) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart
        data={data}
        layout={horizontal ? 'vertical' : 'horizontal'}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#374151" />}
        {horizontal ? (
          <>
            <XAxis type="number" stroke="#9CA3AF" fontSize={12} />
            <YAxis type="category" dataKey={xKey} stroke="#9CA3AF" fontSize={12} width={100} />
          </>
        ) : (
          <>
            <XAxis dataKey={xKey} stroke="#9CA3AF" fontSize={12} />
            <YAxis stroke="#9CA3AF" fontSize={12} />
          </>
        )}
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
          <Bar
            key={s.dataKey}
            dataKey={s.dataKey}
            name={s.name}
            fill={s.color || defaultColors[index % defaultColors.length]}
            radius={[4, 4, 0, 0]}
            stackId={stacked ? 'stack' : undefined}
          />
        ))}
      </RechartsBarChart>
    </ResponsiveContainer>
  );
};

export default BarChart;
