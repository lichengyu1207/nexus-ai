import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, ChevronRightIcon, ChevronLeftIcon } from '@heroicons/react/24/outline';
import Mascot from './Mascot';

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  message: string;
  targetSelector?: string;
  emotion?: 'default' | 'thinking' | 'happy' | 'confused' | 'surprised' | 'comforting';
  pose?: 'standing' | 'sitting' | 'waving' | 'pointing';
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
}

const defaultSteps: OnboardingStep[] = [
  {
    id: 'welcome',
    title: '欢迎来到房都督AI',
    description: '让我带你熟悉一下平台的核心功能',
    message: '欢迎来到房小智！我来带你熟悉一下～',
    emotion: 'happy',
    pose: 'waving',
    position: 'center',
  },
  {
    id: 'start-analysis',
    title: '开始分析',
    description: '在这里输入你的房产需求，开始智能分析',
    message: '点击这里输入你的房产需求，我会帮你分析～',
    targetSelector: '[data-onboarding="start-analysis"]',
    emotion: 'default',
    pose: 'pointing',
    position: 'right',
  },
  {
    id: 'task-list',
    title: '任务列表',
    description: '所有历史分析任务都会在这里显示',
    message: '所有历史任务都会在这里，随时可以查看～',
    targetSelector: '[data-onboarding="task-list"]',
    emotion: 'default',
    pose: 'pointing',
    position: 'right',
  },
  {
    id: 'help-center',
    title: '帮助中心',
    description: '有任何问题可以随时查看帮助文档',
    message: '有任何问题可以随时查看帮助哦～',
    targetSelector: '[data-onboarding="help-center"]',
    emotion: 'thinking',
    position: 'left',
  },
];

interface OnboardingTourProps {
  steps?: OnboardingStep[];
  onComplete: () => void;
  onSkip: () => void;
  isOpen: boolean;
}

const OnboardingTour: React.FC<OnboardingTourProps> = ({
  steps = defaultSteps,
  onComplete,
  onSkip,
  isOpen,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  const currentStep = steps[currentStepIndex];
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === steps.length - 1;

  const updateTargetPosition = useCallback(() => {
    if (currentStep.targetSelector) {
      const target = document.querySelector(currentStep.targetSelector);
      if (target) {
        setTargetRect(target.getBoundingClientRect());
      }
    } else {
      setTargetRect(null);
    }
  }, [currentStep.targetSelector]);

  useEffect(() => {
    if (isOpen) {
      updateTargetPosition();
      window.addEventListener('resize', updateTargetPosition);
      window.addEventListener('scroll', updateTargetPosition, true);
      return () => {
        window.removeEventListener('resize', updateTargetPosition);
        window.removeEventListener('scroll', updateTargetPosition, true);
      };
    }
  }, [isOpen, updateTargetPosition]);

  const handleNext = () => {
    if (isLastStep) {
      onComplete();
    } else {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirstStep) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const getTooltipPosition = (): React.CSSProperties => {
    if (!targetRect) {
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    }

    const padding = 20;
    const tooltipWidth = 320;
    const tooltipHeight = 200;

    switch (currentStep.position) {
      case 'top':
        return {
          top: targetRect.top - tooltipHeight - padding,
          left: targetRect.left + targetRect.width / 2 - tooltipWidth / 2,
        };
      case 'bottom':
        return {
          top: targetRect.bottom + padding,
          left: targetRect.left + targetRect.width / 2 - tooltipWidth / 2,
        };
      case 'left':
        return {
          top: targetRect.top + targetRect.height / 2 - tooltipHeight / 2,
          left: targetRect.left - tooltipWidth - padding,
        };
      case 'right':
        return {
          top: targetRect.top + targetRect.height / 2 - tooltipHeight / 2,
          left: targetRect.right + padding,
        };
      default:
        return {
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
        };
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[9999]">
        <motion.div
          className="absolute inset-0 bg-black/50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onSkip}
        />

        {targetRect && (
          <motion.div
            className="absolute rounded-lg ring-2 ring-primary-500 ring-offset-2 ring-offset-black/50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              top: targetRect.top - 4,
              left: targetRect.left - 4,
              width: targetRect.width + 8,
              height: targetRect.height + 8,
            }}
          />
        )}

        <motion.div
          className="absolute w-80"
          style={getTooltipPosition()}
          initial={{ opacity: 0, scale: 0.9, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 10 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        >
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="p-4">
              <div className="flex items-start gap-3">
                <motion.div
                  animate={{ y: [0, -4, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                >
                  <Mascot
                    emotion={currentStep.emotion || 'happy'}
                    pose={currentStep.pose}
                    size="lg"
                    animate
                  />
                </motion.div>

                <div className="flex-1">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-xl px-3 py-2 relative">
                    <div className="absolute left-0 top-1/2 -translate-x-2 -translate-y-1/2 w-0 h-0 border-t-6 border-b-6 border-r-8 border-transparent border-r-gray-50 dark:border-r-gray-700" />
                    <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">
                      {currentStep.message}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  {currentStep.title}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {currentStep.description}
                </p>
              </div>
            </div>

            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  {steps.map((_, index) => (
                    <div
                      key={index}
                      className={`w-2 h-2 rounded-full transition-colors ${
                        index === currentStepIndex
                          ? 'bg-primary-600'
                          : index < currentStepIndex
                          ? 'bg-primary-300'
                          : 'bg-gray-300 dark:bg-gray-600'
                      }`}
                    />
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={onSkip}
                    className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    跳过
                  </button>
                  {!isFirstStep && (
                    <button
                      onClick={handlePrev}
                      className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg flex items-center gap-1"
                    >
                      <ChevronLeftIcon className="w-4 h-4" />
                      上一步
                    </button>
                  )}
                  <button
                    onClick={handleNext}
                    className="px-4 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-1"
                  >
                    {isLastStep ? '完成' : '下一步'}
                    {!isLastStep && <ChevronRightIcon className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default OnboardingTour;

interface OnboardingManagerProps {
  children: React.ReactNode;
}

const ONBOARDING_COMPLETED_KEY = 'onboarding_completed';

export const OnboardingManager: React.FC<OnboardingManagerProps> = ({ children }) => {
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const completed = localStorage.getItem(ONBOARDING_COMPLETED_KEY);
    if (!completed) {
      setShowOnboarding(true);
    }
    setIsLoading(false);
  }, []);

  const handleComplete = () => {
    localStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true');
    setShowOnboarding(false);
  };

  const handleSkip = () => {
    localStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true');
    setShowOnboarding(false);
  };

  if (isLoading) {
    return <>{children}</>;
  }

  return (
    <>
      {children}
      <OnboardingTour
        isOpen={showOnboarding}
        onComplete={handleComplete}
        onSkip={handleSkip}
      />
    </>
  );
};

export const useOnboarding = () => {
  const resetOnboarding = () => {
    localStorage.removeItem(ONBOARDING_COMPLETED_KEY);
  };

  const isOnboardingCompleted = () => {
    return localStorage.getItem(ONBOARDING_COMPLETED_KEY) === 'true';
  };

  return {
    resetOnboarding,
    isOnboardingCompleted,
  };
};
