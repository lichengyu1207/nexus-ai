import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { mockShowcaseData } from '../showcaseData';
import { ReportGenerator } from '../../reportGenerator';

const ReportDetail: React.FC = () => {
  const [progress, setProgress] = useState(0);
  const [showReport, setShowReport] = useState(false);
  const [showGenerator, setShowGenerator] = useState(false);
  const reportData = mockShowcaseData.report;

  useEffect(() => {
    const duration = 3000;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const newProgress = Math.min((elapsed / duration) * 100, 100);
      setProgress(newProgress);

      if (newProgress < 100) {
        requestAnimationFrame(animate);
      } else {
        setTimeout(() => setShowReport(true), 500);
      }
    };

    animate();
  }, []);

  return (
    <div style={styles.container}>
      <AnimatePresence mode="wait">
        {!showGenerator ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={styles.previewContainer}
          >
            <div style={styles.visualizationArea}>
              <div style={styles.dataFlowSide}>
                {[0, 1, 2, 3, 4].map((i) => (
                  <motion.div
                    key={i}
                    style={styles.dataPoint}
                    initial={{ x: -50, opacity: 0 }}
                    animate={{ 
                      x: progress > i * 20 ? 150 : -50, 
                      opacity: progress > i * 20 ? 1 : 0 
                    }}
                    transition={{ duration: 0.5 }}
                  />
                ))}
              </div>

              <div style={styles.reportIcon}>
                <motion.div
                  animate={{ 
                    scale: [1, 1.1, 1],
                    boxShadow: progress < 100 
                      ? '0 0 20px rgba(239, 68, 68, 0.5)' 
                      : '0 0 40px rgba(239, 68, 68, 0.8)',
                  }}
                  transition={{ duration: 1, repeat: Infinity }}
                  style={styles.reportIconInner}
                >
                  📊
                </motion.div>
                <div style={styles.progressLabel}>
                  完成度 {Math.round(progress)}%
                </div>
              </div>
            </div>

            {showReport && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                style={styles.reportCard}
              >
                <h4 style={styles.reportTitle}>{reportData.title}</h4>
                <p style={styles.reportSummary}>{reportData.summary}</p>
                
                <div style={styles.chartTags}>
                  {reportData.charts.map((chart) => (
                    <span key={chart} style={styles.chartTag}>{chart}</span>
                  ))}
                </div>

                <motion.button
                  style={styles.viewButton}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setShowGenerator(true)}
                >
                  🎬 观看动态生成过程
                </motion.button>
              </motion.div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="generator"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={styles.generatorContainer}
          >
            <div style={styles.generatorHeader}>
              <h4 style={styles.generatorTitle}>动态报告生成器</h4>
              <motion.button
                style={styles.backButton}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowGenerator(false)}
              >
                ← 返回预览
              </motion.button>
            </div>
            
            <div style={styles.generatorWrapper}>
              <ReportGenerator 
                autoPlay={true}
                height={500}
                showHeader={false}
                compact={true}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  previewContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  visualizationArea: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '12px',
    minHeight: '150px',
  },
  dataFlowSide: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  dataPoint: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    background: '#EF4444',
    boxShadow: '0 0 10px #EF4444',
  },
  reportIcon: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
  },
  reportIconInner: {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    background: 'rgba(239, 68, 68, 0.2)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '40px',
  },
  progressLabel: {
    fontSize: '14px',
    color: '#EF4444',
    fontWeight: 'bold',
  },
  reportCard: {
    padding: '20px',
    background: 'rgba(239, 68, 68, 0.1)',
    borderRadius: '12px',
    border: '1px solid rgba(239, 68, 68, 0.3)',
  },
  reportTitle: {
    color: '#EF4444',
    fontSize: '18px',
    margin: '0 0 12px 0',
    fontFamily: 'sans-serif',
  },
  reportSummary: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: '14px',
    lineHeight: 1.6,
    margin: '0 0 16px 0',
  },
  chartTags: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
    flexWrap: 'wrap',
  },
  chartTag: {
    padding: '6px 12px',
    background: 'rgba(239, 68, 68, 0.2)',
    borderRadius: '12px',
    fontSize: '12px',
    color: '#EF4444',
  },
  viewButton: {
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #EF4444, #DC2626)',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
    width: '100%',
  },
  generatorContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  generatorHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  generatorTitle: {
    color: '#EF4444',
    fontSize: '16px',
    margin: 0,
    fontWeight: 600,
  },
  backButton: {
    padding: '8px 16px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '6px',
    color: '#EF4444',
    fontSize: '12px',
    cursor: 'pointer',
  },
  generatorWrapper: {
    borderRadius: '12px',
    overflow: 'hidden',
    border: '1px solid rgba(239, 68, 68, 0.2)',
  },
};

export default ReportDetail;
