import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type LivenessStatus = 'verified' | 'pending' | 'unverified' | 'warning';

interface LivenessRecord {
  id: string;
  timestamp: Date;
  type: 'face' | 'voice' | 'behavior';
  confidence: number;
  status: 'pass' | 'fail';
}

interface LivenessFloatingBallProps {
  onStatusChange?: (status: LivenessStatus) => void;
}

const LivenessFloatingBall: React.FC<LivenessFloatingBallProps> = ({ onStatusChange }) => {
  const [status, setStatus] = useState<LivenessStatus>('pending');
  const [showPanel, setShowPanel] = useState(false);
  const [records, setRecords] = useState<LivenessRecord[]>([]);
  const [isVerifying, setIsVerifying] = useState(false);

  useEffect(() => {
    const mockRecords: LivenessRecord[] = [
      { id: '1', timestamp: new Date(Date.now() - 3600000), type: 'face', confidence: 0.98, status: 'pass' },
      { id: '2', timestamp: new Date(Date.now() - 7200000), type: 'behavior', confidence: 0.92, status: 'pass' },
      { id: '3', timestamp: new Date(Date.now() - 86400000), type: 'voice', confidence: 0.85, status: 'pass' },
    ];
    setRecords(mockRecords);
    
    setTimeout(() => {
      setStatus('verified');
      onStatusChange?.('verified');
    }, 2000);
  }, [onStatusChange]);

  const getStatusColor = () => {
    switch (status) {
      case 'verified': return '#22C55E';
      case 'pending': return '#F59E0B';
      case 'unverified': return '#6B7280';
      case 'warning': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'verified': return '已验证';
      case 'pending': return '验证中';
      case 'unverified': return '未验证';
      case 'warning': return '警告';
      default: return '未知';
    }
  };

  const runVerification = () => {
    setIsVerifying(true);
    setStatus('pending');
    
    setTimeout(() => {
      const newRecord: LivenessRecord = {
        id: Date.now().toString(),
        timestamp: new Date(),
        type: 'face',
        confidence: 0.95 + Math.random() * 0.04,
        status: 'pass',
      };
      setRecords(prev => [newRecord, ...prev.slice(0, 9)]);
      setStatus('verified');
      setIsVerifying(false);
      onStatusChange?.('verified');
    }, 3000);
  };

  return (
    <>
      <motion.div
        style={{
          ...styles.ball,
          borderColor: getStatusColor(),
          boxShadow: `0 0 20px ${getStatusColor()}40`,
        }}
        onClick={() => setShowPanel(!showPanel)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        animate={{
          boxShadow: [
            `0 0 20px ${getStatusColor()}40`,
            `0 0 30px ${getStatusColor()}60`,
            `0 0 20px ${getStatusColor()}40`,
          ],
        }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <motion.div
          style={{
            ...styles.innerCircle,
            background: `radial-gradient(circle, ${getStatusColor()}40, transparent)`,
          }}
          animate={status === 'pending' ? { rotate: 360 } : {}}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        >
          <span style={styles.icon}>
            {status === 'verified' ? '✓' : status === 'pending' ? '⟳' : status === 'warning' ? '!' : '?'}
          </span>
        </motion.div>
        
        <div style={styles.label}>{getStatusText()}</div>
      </motion.div>

      <AnimatePresence>
        {showPanel && (
          <motion.div
            initial={{ opacity: 0, x: 20, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 20, scale: 0.9 }}
            style={styles.panel}
          >
            <div style={styles.panelHeader}>
              <span style={styles.panelTitle}>活体检测记录</span>
              <button style={styles.closeBtn} onClick={() => setShowPanel(false)}>✕</button>
            </div>

            <div style={styles.currentStatus}>
              <div style={{ ...styles.statusDot, background: getStatusColor() }} />
              <span>当前状态: {getStatusText()}</span>
            </div>

            <div style={styles.recordsList}>
              {records.map((record) => (
                <div key={record.id} style={styles.recordItem}>
                  <div style={styles.recordIcon}>
                    {record.type === 'face' ? '👤' : record.type === 'voice' ? '🎤' : '🎯'}
                  </div>
                  <div style={styles.recordInfo}>
                    <span style={styles.recordType}>
                      {record.type === 'face' ? '人脸识别' : record.type === 'voice' ? '声纹验证' : '行为分析'}
                    </span>
                    <span style={styles.recordTime}>
                      {record.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={styles.recordConfidence}>
                    <div style={styles.confidenceBar}>
                      <div 
                        style={{ 
                          ...styles.confidenceFill, 
                          width: `${record.confidence * 100}%`,
                          background: record.confidence > 0.9 ? '#22C55E' : '#F59E0B',
                        }} 
                      />
                    </div>
                    <span style={styles.confidenceText}>{Math.round(record.confidence * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>

            <motion.button
              style={styles.verifyButton}
              onClick={runVerification}
              disabled={isVerifying}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isVerifying ? '验证中...' : '重新验证'}
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

const styles: Record<string, React.CSSProperties> = {
  ball: {
    position: 'fixed',
    bottom: '100px',
    right: '24px',
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    border: '3px solid',
    background: 'rgba(10, 35, 66, 0.9)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    zIndex: 1000,
  },
  innerCircle: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: '18px',
    color: '#fff',
    fontWeight: 'bold',
  },
  label: {
    position: 'absolute',
    bottom: '-20px',
    fontSize: '10px',
    color: 'rgba(255, 255, 255, 0.7)',
    whiteSpace: 'nowrap',
  },
  panel: {
    position: 'fixed',
    bottom: '100px',
    right: '100px',
    width: '280px',
    background: 'rgba(10, 35, 66, 0.95)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    padding: '16px',
    zIndex: 1000,
    backdropFilter: 'blur(10px)',
  },
  panelHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
    paddingBottom: '12px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  panelTitle: {
    color: '#D4AF37',
    fontSize: '14px',
    fontWeight: 'bold',
  },
  closeBtn: {
    background: 'transparent',
    border: 'none',
    color: 'rgba(255, 255, 255, 0.5)',
    cursor: 'pointer',
    fontSize: '16px',
  },
  currentStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '8px',
    marginBottom: '12px',
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.8)',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  recordsList: {
    maxHeight: '200px',
    overflowY: 'auto',
    marginBottom: '12px',
  },
  recordItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '8px',
    marginBottom: '8px',
  },
  recordIcon: {
    fontSize: '20px',
  },
  recordInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  recordType: {
    fontSize: '12px',
    color: '#fff',
  },
  recordTime: {
    fontSize: '10px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  recordConfidence: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '4px',
  },
  confidenceBar: {
    width: '50px',
    height: '4px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    borderRadius: '2px',
  },
  confidenceText: {
    fontSize: '10px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  verifyButton: {
    width: '100%',
    padding: '12px',
    background: 'linear-gradient(135deg, #22C55E, #16A34A)',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
};

export default LivenessFloatingBall;
export type { LivenessStatus, LivenessRecord };
