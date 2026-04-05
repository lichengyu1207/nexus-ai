import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import type { QualityStats, QualityMetric, QualityTrend } from '../types';
import { useQualityStats, useAssetQuality } from '../hooks/useQualityStats';

export interface QualityDashboardProps {
  assetId?: string;
}

const COLORS = {
  excellent: '#22c55e',
  good: '#84cc16',
  fair: '#eab308',
  poor: '#ef4444',
};

const getScoreColor = (score: number): string => {
  if (score >= 90) return COLORS.excellent;
  if (score >= 70) return COLORS.good;
  if (score >= 50) return COLORS.fair;
  return COLORS.poor;
};

const getScoreLabel = (score: number): string => {
  if (score >= 90) return '优秀';
  if (score >= 70) return '良好';
  if (score >= 50) return '一般';
  return '较差';
};

const QualityGauge = ({ score }: { score: number }) => {
  const data = [
    { value: score, color: getScoreColor(score) },
    { value: 100 - score, color: '#374151' },
  ];

  return (
    <div className="relative w-32 h-32">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={45}
            outerRadius={55}
            dataKey="value"
            startAngle={90}
            endAngle={-270}
            stroke="none"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white">{score}</span>
        <span className="text-xs text-gray-400">{getScoreLabel(score)}</span>
      </div>
    </div>
  );
};

const MetricBar = ({ label, value }: { label: string; value: number }) => (
  <div className="space-y-1">
    <div className="flex justify-between text-sm">
      <span className="text-gray-400">{label}</span>
      <span className="text-white">{value}%</span>
    </div>
    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="h-full rounded-full"
        style={{ backgroundColor: getScoreColor(value) }}
      />
    </div>
  </div>
);

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: QualityTrend }>;
}) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-gray-800 border border-white/10 rounded-lg p-2 shadow-lg">
        <p className="text-xs text-gray-400">{data.date}</p>
        <p className="text-sm text-white">评分: {data.score}</p>
      </div>
    );
  }
  return null;
};

export function QualityDashboard({ assetId }: QualityDashboardProps) {
  const { stats, isLoading: statsLoading } = useQualityStats();
  const { metric, trend, isLoadingMetric, isLoadingTrend } = useAssetQuality({
    assetId: assetId ?? null,
  });

  const overallScore = useMemo(() => {
    if (!stats) return 0;
    return Math.round(
      (stats.byType.datasource * 0.3 +
        stats.byType.dataset * 0.5 +
        stats.byType.knowledgebase * 0.2)
    );
  }, [stats]);

  const trendData = useMemo(() => {
    return trend.map((t) => ({
      ...t,
      date: new Date(t.date).toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
      }),
    }));
  }, [trend]);

  if (assetId) {
    if (isLoadingMetric || isLoadingTrend) {
      return (
        <div className="flex items-center justify-center h-32">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full"
          />
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center">
          <QualityGauge score={metric?.overall ?? 0} />
        </div>

        <div className="space-y-3">
          <MetricBar label="完整性" value={metric?.completeness ?? 0} />
          <MetricBar label="准确性" value={metric?.accuracy ?? 0} />
          <MetricBar label="时效性" value={metric?.timeliness ?? 0} />
        </div>

        {trend.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">质量趋势</h3>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#6b7280" fontSize={10} />
                  <YAxis stroke="#6b7280" fontSize={10} domain={[0, 100]} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    dot={{ fill: '#f59e0b', r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-center">
        <div className="text-center">
          <QualityGauge score={overallScore} />
          <p className="text-sm text-gray-400 mt-2">整体健康度</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {stats?.byType && (
          <>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <span className="text-2xl">🗄️</span>
              <p className="text-lg font-bold text-blue-400 mt-1">
                {stats.byType.datasource}
              </p>
              <p className="text-xs text-gray-500">数据源</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <span className="text-2xl">📊</span>
              <p className="text-lg font-bold text-green-400 mt-1">
                {stats.byType.dataset}
              </p>
              <p className="text-xs text-gray-500">数据集</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <span className="text-2xl">📚</span>
              <p className="text-lg font-bold text-amber-400 mt-1">
                {stats.byType.knowledgebase}
              </p>
              <p className="text-xs text-gray-500">知识库</p>
            </div>
          </>
        )}
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-400 mb-3">低质量资产</h3>
        <div className="space-y-2">
          {stats?.lowQualityAssets.slice(0, 5).map((asset) => (
            <div
              key={asset.id}
              className="flex items-center justify-between p-2 bg-white/5 rounded-lg"
            >
              <span className="text-sm text-white truncate">{asset.name}</span>
              <span
                className="text-xs px-2 py-0.5 rounded"
                style={{
                  backgroundColor: `${getScoreColor(asset.score)}20`,
                  color: getScoreColor(asset.score),
                }}
              >
                {asset.score}%
              </span>
            </div>
          ))}
          {(!stats?.lowQualityAssets || stats.lowQualityAssets.length === 0) && (
            <p className="text-sm text-gray-500 text-center py-2">暂无低质量资产</p>
          )}
        </div>
      </div>
    </div>
  );
}
