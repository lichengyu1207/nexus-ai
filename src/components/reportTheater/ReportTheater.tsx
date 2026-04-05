import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import DataFlowToReport from './DataFlowToReport';
import ReportProgressPanel from './ReportProgressPanel';
import { ReportGenerator, useReportGeneratorStore } from '../reportGenerator';

interface ReportTheaterProps {
  isOpen: boolean;
  onClose: () => void;
  taskId?: string;
  autoPlay?: boolean;
}

const ReportTheater: React.FC<ReportTheaterProps> = ({
  isOpen,
  onClose,
  taskId,
  autoPlay = true,
}) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('pending');
  const [currentStep, setCurrentStep] = useState('准备生成报告...');
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [showGenerator, setShowGenerator] = useState(false);

  const { 
    insights, 
    isComplete, 
    isPlaying,
    initStreamPlayer, 
    play, 
    pause, 
    reset,
    setSpeed,
    progress: reportProgress 
  } = useReportGeneratorStore();

  useEffect(() => {
    if (isOpen && autoPlay) {
      startReportGeneration();
    }
  }, [isOpen, autoPlay]);

  useEffect(() => {
    if (isPlaying) {
      setProgress(reportProgress);
      setStatus(reportProgress < 100 ? 'generating' : 'completed');
      
      if (reportProgress < 20) {
        setCurrentStep('解析需求...');
      } else if (reportProgress < 40) {
        setCurrentStep('数据采集...');
      } else if (reportProgress < 60) {
        setCurrentStep('智能分析...');
      } else if (reportProgress < 80) {
        setCurrentStep('生成洞察...');
      } else if (reportProgress < 100) {
        setCurrentStep('渲染报告...');
      } else {
        setCurrentStep('报告生成完成');
        setStatus('completed');
      }
    }
  }, [isPlaying, reportProgress]);

  const startReportGeneration = useCallback(() => {
    setProgress(0);
    setStatus('pending');
    setCurrentStep('准备生成报告...');
    setShowGenerator(true);
    
    reset();
    setTimeout(() => {
      initStreamPlayer();
      setTimeout(() => play(), 300);
    }, 100);
  }, [reset, initStreamPlayer, play]);

  const handleReplay = useCallback(() => {
    startReportGeneration();
  }, [startReportGeneration]);

  const handleSpeedChange = useCallback((newSpeed: number) => {
    setPlaybackSpeed(newSpeed);
    setSpeed(newSpeed);
  }, [setSpeed]);

  const handlePlayPause = useCallback(() => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }, [isPlaying, play, pause]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={styles.overlay}
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 50 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 50 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          style={styles.container}
          onClick={e => e.stopPropagation()}
        >
          <div style={styles.header}>
            <div style={styles.headerLeft}>
              <h2 style={styles.title}>📊 动态报告生成器</h2>
              <span style={styles.subtitle}>见证报告从数据中"生长"出来</span>
            </div>
            <button style={styles.closeButton} onClick={onClose}>
              ✕
            </button>
          </div>

          <div style={styles.content}>
            <div style={styles.leftPanel}>
              <div style={styles.panelTitle}>数据汇聚</div>
              <DataFlowToReport
                isActive={status !== 'completed' && status !== 'pending'}
                progress={progress}
              />
              
              <div style={styles.panelTitle} className="mt-4">生成进度</div>
              <ReportProgressPanel
                progress={progress}
                status={status}
                currentStep={currentStep}
                insights={insights}
              />
            </div>

            <div style={styles.centerPanel}>
              <div style={styles.panelTitle}>报告预览</div>
              <div style={styles.reportContainer}>
                {showGenerator ? (
                  <ReportGenerator 
                    autoPlay={false}
                    height="100%"
                    showHeader={false}
                    compact={true}
                  />
                ) : (
                  <div style={styles.emptyState}>
                    <span style={styles.emptyIcon}>📝</span>
                    <p>点击"开始生成"按钮</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div style={styles.controls}>
            <div style={styles.controlsLeft}>
              <button
                style={styles.controlButton}
                onClick={handleReplay}
                title="重播"
              >
                🔄 重播
              </button>
              
              <button
                style={{
                  ...styles.controlButton,
                  background: isPlaying ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                  borderColor: isPlaying ? '#EF4444' : '#10B981',
                }}
                onClick={handlePlayPause}
                title={isPlaying ? '暂停' : '播放'}
              >
                {isPlaying ? '⏸ 暂停' : '▶ 播放'}
              </button>
              
              <div style={styles.speedControl}>
                <span style={styles.speedLabel}>速度:</span>
                {[0.5, 1, 1.5, 2, 3].map(speed => (
                  <button
                    key={speed}
                    style={{
                      ...styles.speedButton,
                      background: playbackSpeed === speed 
                        ? 'rgba(212, 175, 55, 0.3)' 
                        : 'rgba(255, 255, 255, 0.1)',
                      borderColor: playbackSpeed === speed 
                        ? '#D4AF37' 
                        : 'rgba(255, 255, 255, 0.2)',
                    }}
                    onClick={() => handleSpeedChange(speed)}
                  >
                    {speed}x
                  </button>
                ))}
              </div>
            </div>

            <div style={styles.controlsRight}>
              <button
                style={styles.controlButton}
                onClick={() => setIsMuted(!isMuted)}
                title={isMuted ? '开启音效' : '静音'}
              >
                {isMuted ? '🔇' : '🔊'}
              </button>

              {status === 'completed' && (
                <motion.button
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  style={styles.viewReportButton}
                  onClick={() => {
                    console.log('查看完整报告');
                  }}
                >
                  查看完整报告 →
                </motion.button>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.85)',
    backdropFilter: 'blur(12px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
    padding: '20px',
  },
  container: {
    width: '100%',
    maxWidth: '1400px',
    height: '90vh',
    background: 'linear-gradient(180deg, #0A2342, #061224)',
    borderRadius: '20px',
    border: '1px solid rgba(212, 175, 55, 0.3)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    background: 'rgba(0, 0, 0, 0.2)',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '12px',
  },
  title: {
    fontSize: '24px',
    color: '#D4AF37',
    margin: 0,
    fontFamily: 'sans-serif',
  },
  subtitle: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  closeButton: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    background: 'rgba(255, 255, 255, 0.1)',
    color: '#fff',
    fontSize: '16px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flex: 1,
    display: 'grid',
    gridTemplateColumns: '300px 1fr',
    gap: '20px',
    padding: '20px',
    overflow: 'hidden',
  },
  leftPanel: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  centerPanel: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    overflow: 'hidden',
  },
  panelTitle: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
    paddingBottom: '8px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  reportContainer: {
    flex: 1,
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: '12px',
    overflow: 'hidden',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: 'rgba(255, 255, 255, 0.4)',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  controls: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 24px',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
    background: 'rgba(0, 0, 0, 0.2)',
  },
  controlsLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  controlsRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  controlButton: {
    padding: '8px 16px',
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '14px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  speedControl: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  speedLabel: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  speedButton: {
    padding: '6px 12px',
    borderRadius: '6px',
    border: '1px solid',
    color: '#fff',
    fontSize: '12px',
    cursor: 'pointer',
  },
  viewReportButton: {
    padding: '10px 24px',
    background: 'linear-gradient(135deg, #D4AF37, #B8962E)',
    border: 'none',
    borderRadius: '8px',
    color: '#0A2342',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
};

export default ReportTheater;
