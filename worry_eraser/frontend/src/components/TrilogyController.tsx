import React, { useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import ConfessionAnimation from './ConfessionAnimation';
import MemoryRipple from './MemoryRipple';
import CareReportAnimation from './CareReportAnimation';
import { Report } from '../types';

interface TrilogyControllerProps {
  userInput: string;
  reportData: Report | null;
  memoryContent?: string;
  memoryId?: string;
  agentEmoji?: string;
  onComplete: () => void;
}

const TrilogyController: React.FC<TrilogyControllerProps> = ({
  userInput,
  reportData,
  memoryContent,
  memoryId,
  agentEmoji = '🎵',
  onComplete,
}) => {
  const [step, setStep] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [hasPlayed, setHasPlayed] = useState<Set<number>>(new Set());

  const steps = [
    { id: 1, title: '倾诉回响', icon: '✨' },
    { id: 2, title: '记忆涟漪', icon: '💭' },
    { id: 3, title: '慰藉成章', icon: '📖' },
  ];

  const startTrilogy = useCallback(() => {
    setStep(1);
    setHasPlayed(new Set());
  }, []);

  const handleConfessionComplete = useCallback(() => {
    setHasPlayed(prev => new Set(prev).add(1));
    if (!isPaused) {
      setStep(2);
    }
  }, [isPaused]);

  const handleMemoryComplete = useCallback(() => {
    setHasPlayed(prev => new Set(prev).add(2));
    if (!isPaused) {
      setStep(3);
    }
  }, [isPaused]);

  const handleReportComplete = useCallback(() => {
    setHasPlayed(prev => new Set(prev).add(3));
    setStep(0);
    onComplete();
  }, [onComplete]);

  const handleReplay = useCallback((stepNumber: number) => {
    setStep(stepNumber);
    setHasPlayed(prev => {
      const newSet = new Set(prev);
      newSet.delete(stepNumber);
      return newSet;
    });
  }, []);

  const handlePause = useCallback(() => {
    setIsPaused(prev => !prev);
  }, []);

  const handleSkip = useCallback(() => {
    setStep(0);
    onComplete();
  }, [onComplete]);

  if (step === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 9999,
          textAlign: 'center',
        }}
      >
        <motion.button
          onClick={startTrilogy}
          style={{
            padding: '20px 40px',
            fontSize: '18px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            border: 'none',
            borderRadius: '30px',
            cursor: 'pointer',
            boxShadow: '0 10px 30px rgba(102, 126, 234, 0.4)',
          }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          ✨ 体验烦恼橡皮擦三部曲
        </motion.button>
      </motion.div>
    );
  }

  return (
    <>
      {/* Step Indicator */}
      <motion.div
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          position: 'fixed',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 10000,
          display: 'flex',
          gap: '20px',
          background: 'rgba(255, 255, 255, 0.95)',
          padding: '16px 24px',
          borderRadius: '30px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)',
        }}
      >
        {steps.map((s, index) => (
          <motion.div
            key={s.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              opacity: step === s.id ? 1 : 0.5,
            }}
            animate={{
              scale: step === s.id ? 1.1 : 1,
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: step === s.id
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  : hasPlayed.has(s.id)
                  ? '#4CAF50'
                  : '#e0e0e0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '16px',
              }}
            >
              {hasPlayed.has(s.id) ? '✓' : s.icon}
            </div>
            <span
              style={{
                fontSize: '14px',
                fontWeight: step === s.id ? 'bold' : 'normal',
                color: step === s.id ? '#667eea' : '#666',
              }}
            >
              {s.title}
            </span>
            {index < steps.length - 1 && (
              <div
                style={{
                  width: '20px',
                  height: '2px',
                  background: hasPlayed.has(s.id) ? '#4CAF50' : '#e0e0e0',
                }}
              />
            )}
          </motion.div>
        ))}
      </motion.div>

      {/* Control Buttons */}
      <motion.div
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        style={{
          position: 'fixed',
          right: '20px',
          top: '50%',
          transform: 'translateY(-50%)',
          zIndex: 10000,
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <motion.button
          onClick={handlePause}
          style={{
            width: '50px',
            height: '50px',
            borderRadius: '50%',
            border: 'none',
            background: 'rgba(255, 255, 255, 0.95)',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
            cursor: 'pointer',
            fontSize: '20px',
          }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          {isPaused ? '▶️' : '⏸️'}
        </motion.button>

        <motion.button
          onClick={handleSkip}
          style={{
            width: '50px',
            height: '50px',
            borderRadius: '50%',
            border: 'none',
            background: 'rgba(255, 255, 255, 0.95)',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
            cursor: 'pointer',
            fontSize: '20px',
          }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          ⏭️
        </motion.button>

        {steps.map(s => (
          hasPlayed.has(s.id) && (
            <motion.button
              key={s.id}
              onClick={() => handleReplay(s.id)}
              style={{
                width: '50px',
                height: '50px',
                borderRadius: '50%',
                border: 'none',
                background: 'rgba(255, 255, 255, 0.95)',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
                cursor: 'pointer',
                fontSize: '16px',
              }}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              {s.icon}
            </motion.button>
          )
        ))}
      </motion.div>

      {/* Animation Components */}
      <AnimatePresence mode="wait">
        {step === 1 && (
          <ConfessionAnimation
            key="confession"
            text={userInput}
            agentEmoji={agentEmoji}
            onComplete={handleConfessionComplete}
          />
        )}
        {step === 2 && memoryContent && (
          <MemoryRipple
            key="memory"
            memoryContent={memoryContent}
            memoryId={memoryId}
            onComplete={handleMemoryComplete}
          />
        )}
        {step === 3 && reportData && (
          <CareReportAnimation
            key="report"
            reportData={reportData}
            onComplete={handleReportComplete}
          />
        )}
      </AnimatePresence>
    </>
  );
};

export default TrilogyController;
