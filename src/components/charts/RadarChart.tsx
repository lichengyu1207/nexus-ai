import React from 'react';
import {
  RadarChart as RechartsRadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface DataSeries {
  dataKey: string;
  name: string;
  color?: string;
}

interface RadarChartProps {
  data: Record<string, unknown>[];
  angleKey: string;
  series: DataSeries[];
  height?: number;
  showLegend?: boolean;
  showTooltip?: boolean;
}

const defaultColors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

const RadarChart: React.FC<RadarChartProps> = ({
  data,
  angleKey,
  series,
  height = 300,
  showLegend = true,
  showTooltip = true,
}) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsRadarChart data={data}>
        <PolarGrid stroke="#374151" />
        <PolarAngleAxis dataKey={angleKey} stroke="#9CA3AF" fontSize={12} />
        <PolarRadiusAxis stroke="#9CA3AF" fontSize={10} />
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
          <Radar
            key={s.dataKey}
            name={s.name}
            dataKey={s.dataKey}
            stroke={s.color || defaultColors[index % defaultColors.length]}
            fill={s.color || defaultColors[index % defaultColors.length]}
            fillOpacity={0.3}
          />
        ))}
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
};

export default RadarChart;
