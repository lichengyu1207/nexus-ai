import React from 'react';
import LineChart from './LineChart';
import BarChart from './BarChart';
import RadarChart from './RadarChart';
import PieChart from './PieChart';

export interface ChartConfig {
  id: string;
  type: 'line' | 'bar' | 'radar' | 'pie';
  title: string;
  data: Record<string, unknown>[];
  xKey?: string;
  dataKeys?: string[];
  height?: number;
}

interface ChartRendererProps {
  chart: ChartConfig;
}

const ChartRenderer: React.FC<ChartRendererProps> = ({ chart }) => {
  const { type, title, data, xKey, dataKeys, height = 300 } = chart;

  const series = (dataKeys || []).map((key) => ({
    dataKey: key,
    name: key,
  }));

  const pieData = data.map((item) => ({
    name: String(item[xKey || 'name'] || ''),
    value: Number(item[dataKeys?.[0] || 'value'] || 0),
  }));

  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <LineChart
            data={data}
            xKey={xKey || 'name'}
            series={series}
            height={height}
          />
        );
      case 'bar':
        return (
          <BarChart
            data={data}
            xKey={xKey || 'name'}
            series={series}
            height={height}
          />
        );
      case 'radar':
        return (
          <RadarChart
            data={data}
            angleKey={xKey || 'name'}
            series={series}
            height={height}
          />
        );
      case 'pie':
        return (
          <PieChart
            data={pieData}
            height={height}
          />
        );
      default:
        return <div>Unknown chart type: {type}</div>;
    }
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
      {title && (
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
          {title}
        </h4>
      )}
      {renderChart()}
    </div>
  );
};

export default ChartRenderer;
