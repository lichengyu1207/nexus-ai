import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ReportData, ReportChart, ReportInsight } from './types';

interface DynamicReportRendererProps {
  reportData: ReportData | null;
  progress: number;
}

const DynamicReportRenderer: React.FC<DynamicReportRendererProps> = ({
  reportData,
  progress,
}) => {
  const [visibleTitle, setVisibleTitle] = useState('');
  const [visibleCharts, setVisibleCharts] = useState<number[]>([]);
  const [visibleInsights, setVisibleInsights] = useState<number[]>([]);
  const [visibleSummary, setVisibleSummary] = useState(false);

  const titleProgress = useMemo(() => {
    if (!reportData) return 0;
    return Math.min(progress / 20, 100);
  }, [progress, reportData]);

  useEffect(() => {
    if (!reportData) return;

    const titleLength = reportData.title.length;
    const charsToShow = Math.floor((titleLength * titleProgress) / 100);
    setVisibleTitle(reportData.title.substring(0, charsToShow));
  }, [reportData, titleProgress]);

  useEffect(() => {
    if (!reportData) return;

    const chartProgress = ((progress - 20) / 50) * 100;
    if (chartProgress > 0) {
      const numCharts = Math.ceil((chartProgress / 100) * reportData.charts.length);
      setVisibleCharts(Array.from({ length: numCharts }, (_, i) => i));
    }
  }, [progress, reportData]);

  useEffect(() => {
    if (!reportData) return;

    const insightProgress = ((progress - 70) / 20) * 100;
    if (insightProgress > 0) {
      const numInsights = Math.ceil((insightProgress / 100) * reportData.insights.length);
      setVisibleInsights(Array.from({ length: numInsights }, (_, i) => i));
    }
  }, [progress, reportData]);

  useEffect(() => {
    setVisibleSummary(progress >= 90);
  }, [progress]);

  if (!reportData) {
    return (
      <div style={styles.placeholder}>
        <div style={styles.spinner} />
        <p>等待报告数据...</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <motion.h2
          style={styles.title}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {visibleTitle}
          {titleProgress < 100 && <span style={styles.cursor}>▋</span>}
        </motion.h2>
        <div style={styles.meta}>
          <span style={styles.date}>
            {new Date(reportData.createdAt).toLocaleDateString('zh-CN')}
          </span>
        </div>
      </div>

      <div style={styles.content}>
        <div style={styles.chartsSection}>
          <AnimatePresence>
            {visibleCharts.map((index) => {
              const chart = reportData.charts[index];
              if (!chart) return null;
              return (
                <motion.div
                  key={chart.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: index * 0.1 }}
                  style={styles.chartCard}
                >
                  <h4 style={styles.chartTitle}>{chart.title}</h4>
                  <ChartRenderer chart={chart} progress={progress} />
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        <div style={styles.insightsSection}>
          <h3 style={styles.sectionTitle}>核心洞察</h3>
          <AnimatePresence>
            {visibleInsights.map((index) => {
              const insight = reportData.insights[index];
              if (!insight) return null;
              return (
                <motion.div
                  key={insight.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: index * 0.1 }}
                  style={{
                    ...styles.insightCard,
                    borderLeftColor: insight.type === 'positive' 
                      ? '#10B981' 
                      : insight.type === 'negative' 
                      ? '#EF4444' 
                      : '#D4AF37',
                  }}
                >
                  <p style={styles.insightContent}>{insight.content}</p>
                  <div style={styles.insightMeta}>
                    <div style={styles.confidenceBar}>
                      <motion.div
                        style={styles.confidenceFill}
                        initial={{ width: 0 }}
                        animate={{ width: `${insight.confidence * 100}%` }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                      />
                    </div>
                    <span style={styles.confidenceText}>
                      置信度 {Math.round(insight.confidence * 100)}%
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        <AnimatePresence>
          {visibleSummary && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              style={styles.summarySection}
            >
              <h3 style={styles.sectionTitle}>分析摘要</h3>
              <p style={styles.summaryText}>{reportData.summary}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

const ChartRenderer: React.FC<{ chart: ReportChart; progress: number }> = ({ chart, progress }) => {
  const chartProgress = Math.min(((progress - 20) / 50) * 100, 100);

  if (chart.type === 'line') {
    const maxValue = Math.max(...chart.data.map((d: any) => d.price || d.value || 0));
    const minValue = Math.min(...chart.data.map((d: any) => d.price || d.value || 0));
    const range = maxValue - minValue || 1;

    const points = chart.data
      .map((d: any, i: number) => {
        const x = (i / (chart.data.length - 1)) * 280 + 20;
        const value = d.price || d.value || 0;
        const y = 100 - ((value - minValue) / range) * 80;
        return `${x},${y}`;
      })
      .join(' ');

    const visiblePoints = points.split(' ').slice(0, Math.ceil((chartProgress / 100) * chart.data.length)).join(' ');

    return (
      <svg width="100%" height="120" style={styles.chart}>
        <defs>
          <linearGradient id={`gradient-${chart.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#D4AF37" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#D4AF37" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polyline
          fill="none"
          stroke="#D4AF37"
          strokeWidth="2"
          points={visiblePoints}
        />
        {chart.data.slice(0, Math.ceil((chartProgress / 100) * chart.data.length)).map((d: any, i: number) => {
          const x = (i / (chart.data.length - 1)) * 280 + 20;
          const value = d.price || d.value || 0;
          const y = 100 - ((value - minValue) / range) * 80;
          return (
            <circle key={i} cx={x} cy={y} r="4" fill="#D4AF37" />
          );
        })}
      </svg>
    );
  }

  if (chart.type === 'bar') {
    const maxValue = Math.max(...chart.data.map((d: any) => d.price || d.value || 0));

    return (
      <div style={styles.barChart}>
        {chart.data.slice(0, Math.ceil((chartProgress / 100) * chart.data.length)).map((d: any, i: number) => {
          const value = d.price || d.value || 0;
          const height = (value / maxValue) * 80;
          return (
            <motion.div
              key={i}
              style={styles.barItem}
              initial={{ height: 0 }}
              animate={{ height: `${height}px` }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
            >
              <div
                style={{
                  ...styles.bar,
                  background: chart.config?.colors?.[i] || '#D4AF37',
                }}
              />
              <span style={styles.barLabel}>{d.area || d.name}</span>
            </motion.div>
          );
        })}
      </div>
    );
  }

  if (chart.type === 'pie') {
    let currentAngle = -90;
    const total = chart.data.reduce((sum: number, d: any) => sum + (d.value || 0), 0);

    return (
      <svg width="100%" height="120" viewBox="0 0 120 120" style={styles.chart}>
        {chart.data.map((d: any, i: number) => {
          const value = d.value || 0;
          const angle = (value / total) * 360 * (chartProgress / 100);
          const startAngle = currentAngle;
          currentAngle += angle;

          const startRad = (startAngle * Math.PI) / 180;
          const endRad = (currentAngle * Math.PI) / 180;

          const x1 = 60 + 40 * Math.cos(startRad);
          const y1 = 60 + 40 * Math.sin(startRad);
          const x2 = 60 + 40 * Math.cos(endRad);
          const y2 = 60 + 40 * Math.sin(endRad);

          const largeArc = angle > 180 ? 1 : 0;

          return (
            <motion.path
              key={i}
              d={`M 60 60 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
              fill={d.color || chart.config?.colors?.[i] || '#D4AF37'}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: i * 0.1 }}
            />
          );
        })}
      </svg>
    );
  }

  return <div style={styles.chartPlaceholder}>图表类型: {chart.type}</div>;
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    height: '100%',
    overflow: 'auto',
    padding: '20px',
  },
  placeholder: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '3px solid rgba(255, 255, 255, 0.1)',
    borderTopColor: '#D4AF37',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: '16px',
  },
  header: {
    marginBottom: '24px',
    paddingBottom: '16px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  title: {
    fontSize: '24px',
    color: '#D4AF37',
    margin: 0,
    marginBottom: '8px',
  },
  cursor: {
    color: '#D4AF37',
    animation: 'blink 1s infinite',
  },
  meta: {
    display: 'flex',
    gap: '16px',
  },
  date: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  chartsSection: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '16px',
  },
  chartCard: {
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    padding: '16px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  chartTitle: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.8)',
    margin: '0 0 12px 0',
  },
  chart: {
    display: 'block',
  },
  barChart: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '8px',
    height: '100px',
    paddingTop: '20px',
  },
  barItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    flex: 1,
  },
  bar: {
    width: '100%',
    maxWidth: '30px',
    borderRadius: '4px 4px 0 0',
  },
  barLabel: {
    fontSize: '10px',
    color: 'rgba(255, 255, 255, 0.5)',
    marginTop: '4px',
    textAlign: 'center',
  },
  chartPlaceholder: {
    height: '100px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'rgba(255, 255, 255, 0.3)',
    fontSize: '14px',
  },
  insightsSection: {
    marginTop: '16px',
  },
  sectionTitle: {
    fontSize: '16px',
    color: '#D4AF37',
    margin: '0 0 12px 0',
  },
  insightCard: {
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '8px',
    padding: '12px 16px',
    marginBottom: '8px',
    borderLeft: '3px solid',
  },
  insightContent: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.9)',
    margin: '0 0 8px 0',
    lineHeight: 1.5,
  },
  insightMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  confidenceBar: {
    flex: 1,
    height: '4px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #D4AF37, #F59E0B)',
    borderRadius: '2px',
  },
  confidenceText: {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.5)',
    minWidth: '80px',
  },
  summarySection: {
    background: 'rgba(212, 175, 55, 0.1)',
    borderRadius: '12px',
    padding: '16px',
    border: '1px solid rgba(212, 175, 55, 0.3)',
  },
  summaryText: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 1.6,
    margin: 0,
  },
};

export default DynamicReportRenderer;
