import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { mockShowcaseData } from '../showcaseData';
import SixMinistriesGrid, { MINISTRIES } from '../SixMinistriesGrid';

const DemandDetail: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(true);
  const [showLiveness, setShowLiveness] = useState(false);
  const [livenessProgress, setLivenessProgress] = useState(0);
  const [livenessPassed, setLivenessPassed] = useState(false);
  const [showLightBeams, setShowLightBeams] = useState(false);
  const [activeMinistries, setActiveMinistries] = useState<string[]>([]);
  const [tasks, setTasks] = useState<typeof mockShowcaseData.demand.parsedTasks>([]);
  const [dataFlows, setDataFlows] = useState<{ from: string; to: string }[]>([]);

  const fullText = mockShowcaseData.demand.exampleInput;

  useEffect(() => {
    if (isTyping) {
      let index = 0;
      const interval = setInterval(() => {
        if (index < fullText.length) {
          setInputText(fullText.substring(0, index + 1));
          index++;
        } else {
          clearInterval(interval);
          setIsTyping(false);
          setShowLiveness(true);
        }
      }, 50);
      return () => clearInterval(interval);
    }
  }, [isTyping, fullText]);

  useEffect(() => {
    if (showLiveness && !livenessPassed) {
      const interval = setInterval(() => {
        setLivenessProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            setLivenessPassed(true);
            setTimeout(() => {
              setShowLiveness(false);
              setShowLightBeams(true);
            }, 500);
            return 100;
          }
          return prev + 5;
        });
      }, 50);
      return () => clearInterval(interval);
    }
  }, [showLiveness, livenessPassed]);

  useEffect(() => {
    if (showLightBeams) {
      setActiveMinistries(['li_guan']);
      setTimeout(() => {
        setActiveMinistries(['li_guan', 'hu', 'bing']);
        setDataFlows([
          { from: 'li_guan', to: 'hu' },
          { from: 'li_guan', to: 'bing' },
        ]);
      }, 500);

      mockShowcaseData.demand.parsedTasks.forEach((task, index) => {
        setTimeout(() => {
          setTasks(prev => [...prev, task]);
        }, (index + 1) * 600);
      });
    }
  }, [showLightBeams]);

  return (
    <div style={styles.container}>
      <div style={styles.inputSection}>
        <div style={styles.inputBox}>
          <div style={styles.terminalHeader}>
            <span style={styles.dot} />
            <span style={{ ...styles.dot, background: '#fbbf24' }} />
            <span style={{ ...styles.dot, background: '#22c55e' }} />
            <span style={styles.terminalTitle}>智能分析终端</span>
          </div>
          <div style={styles.inputContent}>
            <span style={styles.prompt}>$ </span>
            <span style={styles.inputText}>{inputText}</span>
            {isTyping && <span style={styles.cursor}>▋</span>}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showLiveness && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            style={styles.livenessOverlay}
          >
            <div style={styles.livenessCard}>
              <motion.div
                style={styles.livenessIcon}
                animate={{ rotate: livenessProgress < 100 ? 360 : 0 }}
                transition={{ duration: 2, repeat: livenessProgress < 100 ? Infinity : 0, ease: 'linear' }}
              >
                {livenessPassed ? '✓' : '🔍'}
              </motion.div>
              <span style={styles.livenessText}>
                {livenessPassed ? '活体验证通过' : '正在进行活体验证...'}
              </span>
              <div style={styles.livenessBar}>
                <motion.div
                  style={{ ...styles.livenessFill, width: `${livenessProgress}%` }}
                />
              </div>
              <span style={styles.livenessPercent}>{livenessProgress}%</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {showLightBeams && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={styles.flowSection}
        >
          <h4 style={styles.sectionTitle}>任务分配流程</h4>
          <SixMinistriesGrid
            activeMinistries={activeMinistries}
            dataFlows={dataFlows}
            showLabels={true}
            showDataFlow={true}
          />
        </motion.div>
      )}

      <div style={styles.tasksSection}>
        <h4 style={styles.sectionTitle}>任务拆解结果</h4>
        <div style={styles.taskList}>
          {tasks.map((task, index) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              style={styles.taskItem}
            >
              <span style={styles.taskNumber}>{task.id}</span>
              <div style={styles.taskContent}>
                <span style={styles.taskName}>{task.task}</span>
                <span style={styles.taskAgent}>→ {task.agent}</span>
              </div>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                style={styles.taskCheck}
              >
                ✓
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>

      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: tasks.length === 3 ? 1 : 0 }}
        style={styles.startButton}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        开始分析 →
      </motion.button>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  inputSection: {
    display: 'flex',
    justifyContent: 'center',
  },
  inputBox: {
    width: '100%',
    maxWidth: '500px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    overflow: 'hidden',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  terminalHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 16px',
    background: 'rgba(0, 0, 0, 0.3)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  dot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    background: '#ef4444',
  },
  terminalTitle: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: '12px',
    marginLeft: '8px',
  },
  inputContent: {
    padding: '16px',
    fontFamily: 'monospace',
    fontSize: '16px',
    color: '#fff',
  },
  prompt: {
    color: '#D4AF37',
  },
  inputText: {
    color: '#fff',
  },
  cursor: {
    color: '#D4AF37',
    animation: 'blink 1s infinite',
  },
  livenessOverlay: {
    display: 'flex',
    justifyContent: 'center',
    padding: '20px',
  },
  livenessCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
    padding: '24px 40px',
    background: 'rgba(16, 185, 129, 0.1)',
    borderRadius: '16px',
    border: '1px solid rgba(16, 185, 129, 0.3)',
  },
  livenessIcon: {
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #22C55E, #16A34A)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '28px',
    color: '#fff',
  },
  livenessText: {
    color: '#22C55E',
    fontSize: '14px',
    fontWeight: 'bold',
  },
  livenessBar: {
    width: '200px',
    height: '6px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  livenessFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #22C55E, #16A34A)',
    borderRadius: '3px',
  },
  livenessPercent: {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  flowSection: {
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '12px',
    padding: '16px',
  },
  sectionTitle: {
    color: '#D4AF37',
    fontSize: '14px',
    margin: '0 0 12px 0',
  },
  tasksSection: {
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '12px',
    padding: '16px',
  },
  taskList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  taskItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '8px',
  },
  taskNumber: {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    background: '#D4AF37',
    color: '#0A2342',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  taskContent: {
    flex: 1,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  taskName: {
    color: '#fff',
    fontSize: '14px',
  },
  taskAgent: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: '12px',
  },
  taskCheck: {
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    background: '#22C55E',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontSize: '12px',
  },
  startButton: {
    padding: '14px 32px',
    background: 'linear-gradient(135deg, #D4AF37, #B8962E)',
    border: 'none',
    borderRadius: '8px',
    color: '#0A2342',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    alignSelf: 'center',
  },
};

export default DemandDetail;
