import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ReportInsight } from './types';

interface ReportProgressPanelProps {
  progress: number;
  status: string;
  currentStep: string;
  insights: ReportInsight[];
}

const ReportProgressPanel: React.FC<ReportProgressPanelProps> = ({
  progress,
  status,
  currentStep,
  insights,
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'pending':
        return '#6B7280';
      case 'collecting':
        return '#3B82F6';
      case 'analyzing':
        return '#F59E0B';
      case 'rendering':
        return '#8B5CF6';
      case 'completed':
        return '#10B981';
      case 'failed':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'collecting':
        return '📥';
      case 'analyzing':
        return '🔍';
      case 'rendering':
        return '📊';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '⏳';
    }
  };

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div style={styles.container}>
      <div style={styles.progressSection}>
        <div style={styles.progressRing}>
          <svg width="100" height="100" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="rgba(255, 255, 255, 0.1)"
              strokeWidth="6"
            />
            <motion.circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke={getStatusColor()}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              style={{
                transform: 'rotate(-90deg)',
                transformOrigin: 'center',
              }}
            />
          </svg>
          <div style={styles.progressText}>
            <span style={styles.progressValue}>{Math.round(progress)}</span>
            <span style={styles.progressUnit}>%</span>
          </div>
        </div>

        <div style={styles.statusInfo}>
          <div style={styles.statusHeader}>
            <span style={styles.statusIcon}>{getStatusIcon()}</span>
            <span style={{ ...styles.statusText, color: getStatusColor() }}>
              {currentStep}
            </span>
          </div>
          
          <div style={styles.progressBar}>
            <motion.div
              style={{ ...styles.progressFill, background: getStatusColor() }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      </div>

      <div style={styles.insightsSection}>
        <h4 style={styles.insightsTitle}>实时洞察</h4>
        <div style={styles.insightsList}>
          <AnimatePresence>
            {insights.map((insight, index) => (
              <motion.div
                key={insight.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                transition={{ delay: index * 0.1 }}
                style={styles.insightItem}
              >
                <div style={styles.insightContent}>
                  <span style={styles.insightDot}>•</span>
                  <span style={styles.insightText}>{insight.content}</span>
                </div>
                <div style={styles.insightConfidence}>
                  <div style={styles.miniConfidenceBar}>
                    <motion.div
                      style={styles.miniConfidenceFill}
                      initial={{ width: 0 }}
                      animate={{ width: `${insight.confidence * 100}%` }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                    />
                  </div>
                  <span style={styles.confidenceValue}>
                    {Math.round(insight.confidence * 100)}%
                  </span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {insights.length === 0 && (
            <div style={styles.noInsights}>
              <motion.div
                animate={{ opacity: [0.3, 0.6, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                等待洞察生成...
              </motion.div>
            </div>
          )}
        </div>
      </div>

      {status === 'completed' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          style={styles.completedBadge}
        >
          <span style={styles.completedIcon}>🎉</span>
          <span style={styles.completedText}>报告已就绪</span>
        </motion.div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    padding: '16px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  progressSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
  },
  progressRing: {
    position: 'relative',
    width: '100px',
    height: '100px',
    flexShrink: 0,
  },
  progressText: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '2px',
  },
  progressValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#D4AF37',
  },
  progressUnit: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  statusInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  statusHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusIcon: {
    fontSize: '20px',
  },
  statusText: {
    fontSize: '14px',
    fontWeight: 500,
  },
  progressBar: {
    height: '6px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: '3px',
  },
  insightsSection: {
    marginTop: '8px',
  },
  insightsTitle: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.7)',
    margin: '0 0 12px 0',
    paddingBottom: '8px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  insightsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    maxHeight: '200px',
    overflowY: 'auto',
  },
  insightItem: {
    padding: '10px 12px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.05)',
  },
  insightContent: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '8px',
    marginBottom: '8px',
  },
  insightDot: {
    color: '#D4AF37',
    fontSize: '12px',
    marginTop: '2px',
  },
  insightText: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 1.4,
    flex: 1,
  },
  insightConfidence: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    paddingLeft: '16px',
  },
  miniConfidenceBar: {
    flex: 1,
    height: '3px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  miniConfidenceFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #D4AF37, #F59E0B)',
    borderRadius: '2px',
  },
  confidenceValue: {
    fontSize: '11px',
    color: 'rgba(255, 255, 255, 0.5)',
    minWidth: '32px',
    textAlign: 'right',
  },
  noInsights: {
    padding: '20px',
    textAlign: 'center',
    color: 'rgba(255, 255, 255, 0.3)',
    fontSize: '13px',
  },
  completedBadge: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '12px',
    background: 'rgba(16, 185, 129, 0.1)',
    borderRadius: '8px',
    border: '1px solid rgba(16, 185, 129, 0.3)',
  },
  completedIcon: {
    fontSize: '20px',
  },
  completedText: {
    fontSize: '14px',
    color: '#10B981',
    fontWeight: 500,
  },
};

export default ReportProgressPanel;
