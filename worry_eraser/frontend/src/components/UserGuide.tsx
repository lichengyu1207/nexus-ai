import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Step {
  target: string;
  title: string;
  content: string;
  position: 'top' | 'bottom' | 'left' | 'right';
}

const steps: Step[] = [
  {
    target: '.header',
    title: '欢迎使用烦恼橡皮擦',
    content: '在这里，你可以向智能体倾诉你的烦恼，获得温暖的回应和建议。',
    position: 'bottom',
  },
  {
    target: '.agent-selector',
    title: '选择智能体',
    content: '点击切换不同的智能体：周瑜（豪迈豁达）或陆逊（沉稳细腻）。',
    position: 'bottom',
  },
  {
    target: '.chat-input',
    title: '倾诉你的烦恼',
    content: '在这里输入你的烦恼，按回车或点击发送按钮。',
    position: 'top',
  },
  {
    target: '.report-section',
    title: '查看分析报告',
    content: '发送消息后，点击"生成报告"按钮查看详细的烦恼分析。',
    position: 'left',
  },
];

interface UserGuideProps {
  onComplete: () => void;
}

const UserGuide: React.FC<UserGuideProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    const hasSeenGuide = localStorage.getItem('worry_eraser_guide_completed');
    if (!hasSeenGuide) {
      setTimeout(() => setIsVisible(true), 500);
    }
  }, []);

  useEffect(() => {
    if (isVisible && currentStep < steps.length) {
      const targetElement = document.querySelector(steps[currentStep].target);
      if (targetElement) {
        const rect = targetElement.getBoundingClientRect();
        setTargetRect(rect);
      }
    }
  }, [isVisible, currentStep]);

  const handleNext = useCallback(() => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      handleComplete();
    }
  }, [currentStep]);

  const handlePrevious = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  }, [currentStep]);

  const handleComplete = useCallback(() => {
    setIsVisible(false);
    localStorage.setItem('worry_eraser_guide_completed', 'true');
    onComplete();
  }, [onComplete]);

  const handleSkip = useCallback(() => {
    handleComplete();
  }, [handleComplete]);

  if (!isVisible || !targetRect) return null;

  const step = steps[currentStep];
  const tooltipStyle = getTooltipStyle(step.position, targetRect);

  return (
    <AnimatePresence>
      <motion.div
        className="user-guide-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <div
          className="user-guide-highlight"
          style={{
            top: targetRect.top - 5,
            left: targetRect.left - 5,
            width: targetRect.width + 10,
            height: targetRect.height + 10,
          }}
        />
        
        <motion.div
          className="user-guide-tooltip"
          style={tooltipStyle}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
        >
          <h3>{step.title}</h3>
          <p>{step.content}</p>
          
          <div className="user-guide-progress">
            {currentStep + 1} / {steps.length}
          </div>
          
          <div className="user-guide-actions">
            <button onClick={handleSkip} className="skip-btn">
              跳过
            </button>
            <div className="nav-buttons">
              {currentStep > 0 && (
                <button onClick={handlePrevious} className="prev-btn">
                  上一步
                </button>
              )}
              <button onClick={handleNext} className="next-btn">
                {currentStep === steps.length - 1 ? '完成' : '下一步'}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

function getTooltipStyle(
  position: Step['position'],
  targetRect: DOMRect
): React.CSSProperties {
  const offset = 15;
  
  switch (position) {
    case 'top':
      return {
        bottom: window.innerHeight - targetRect.top + offset,
        left: targetRect.left + targetRect.width / 2,
        transform: 'translateX(-50%)',
      };
    case 'bottom':
      return {
        top: targetRect.bottom + offset,
        left: targetRect.left + targetRect.width / 2,
        transform: 'translateX(-50%)',
      };
    case 'left':
      return {
        right: window.innerWidth - targetRect.left + offset,
        top: targetRect.top + targetRect.height / 2,
        transform: 'translateY(-50%)',
      };
    case 'right':
      return {
        left: targetRect.right + offset,
        top: targetRect.top + targetRect.height / 2,
        transform: 'translateY(-50%)',
      };
    default:
      return {};
  }
}

export default UserGuide;
