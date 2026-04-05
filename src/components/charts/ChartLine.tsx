import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface LineChartConfig {
  xAxis: { dataKey: string; label?: string };
  yAxis: { label?: string };
  lines: Array<{
    dataKey: string;
    name: string;
    color: string;
  }>;
}

interface ChartLineProps {
  title: string;
  config: LineChartConfig;
  data: Record<string, unknown>[];
}

const ChartLine: React.FC<ChartLineProps> = ({ title, config, data }) => {
  return (
    <div className="bg-white rounded-lg p-4">
      <h4 className="text-sm font-medium text-gray-700 mb-4">{title}</h4>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey={config.xAxis.dataKey}
            tick={{ fontSize: 12, fill: '#6b7280' }}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#6b7280' }}
            axisLine={{ stroke: '#e5e7eb' }}
            label={
              config.yAxis.label
                ? { value: config.yAxis.label, angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280' } }
                : undefined
            }
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {config.lines.map((line, index) => (
            <Line
              key={index}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={line.color}
              strokeWidth={2}
              dot={{ r: 4, fill: line.color }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ChartLine;
