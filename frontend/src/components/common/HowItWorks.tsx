import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface Step {
  icon: string;
  title: string;
  description: string;
}

interface HowItWorksProps {
  steps?: Step[];
  className?: string;
}

const defaultSteps: Step[] = [
  {
    icon: '📝',
    title: '输入地址',
    description: '输入您想了解的房产地址或区域',
  },
  {
    icon: '🤖',
    title: 'AI分析',
    description: '多智能体协同工作，深度分析房产',
  },
  {
    icon: '📊',
    title: '生成报告',
    description: '生成详细的分析报告和建议',
  },
  {
    icon: '💡',
    title: '决策参考',
    description: '为您的购房决策提供专业参考',
  },
];

const HowItWorks: React.FC<HowItWorksProps> = ({
  steps = defaultSteps,
  className = '',
}) => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % steps.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [steps.length]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className={`py-12 ${className}`}>
      <h2 className="text-2xl md:text-3xl font-bold text-center mb-12">
        工作流程
      </h2>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="relative max-w-5xl mx-auto px-4"
      >
        <div className="hidden md:block absolute top-12 left-0 right-0 h-1 bg-gray-200">
          <motion.div
            className="h-full bg-primary"
            initial={{ width: '0%' }}
            whileInView={{ width: '100%' }}
            viewport={{ once: true }}
            transition={{ duration: 2, ease: 'easeInOut' }}
          />
        </div>

        <div className="flex flex-col md:flex-row justify-between items-start md:items-start gap-8 md:gap-0">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              className="flex flex-col items-center text-center flex-1 relative"
            >
              <div className="relative z-10">
                <motion.div
                  className={`w-24 h-24 rounded-full flex items-center justify-center text-4xl mb-4 transition-all duration-300 ${
                    activeStep === index
                      ? 'bg-primary text-white shadow-lg scale-110'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                  animate={activeStep === index ? { scale: [1, 1.1, 1] } : {}}
                  transition={{ duration: 0.5 }}
                >
                  {step.icon}
                </motion.div>

                {activeStep === index && (
                  <motion.div
                    className="absolute inset-0 rounded-full bg-primary/20"
                    initial={{ scale: 1, opacity: 0 }}
                    animate={{ scale: 1.5, opacity: 0 }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                )}
              </div>

              <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
              <p className="text-gray-600 text-sm max-w-[150px]">
                {step.description}
              </p>

              <div className="md:hidden flex items-center justify-center w-full my-4">
                {index < steps.length - 1 && (
                  <motion.div
                    className="w-1 h-8 bg-gray-200"
                    initial={{ height: 0 }}
                    whileInView={{ height: 32 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.2 }}
                  />
                )}
              </div>
            </motion.div>
          ))}
        </div>

        <div className="mt-12 flex justify-center">
          <div className="flex gap-2">
            {steps.map((_, index) => (
              <button
                key={index}
                onClick={() => setActiveStep(index)}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  activeStep === index
                    ? 'bg-primary w-6'
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
              />
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
};

interface FlowingDotsProps {
  className?: string;
}

const FlowingDots: React.FC<FlowingDotsProps> = ({ className = '' }) => {
  return (
    <div className={`relative h-2 w-full overflow-hidden ${className}`}>
      <motion.div
        className="absolute left-0 top-0 h-full w-4 bg-primary rounded-full"
        animate={{
          x: ['0%', '2400%'],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'linear',
        }}
      />
    </div>
  );
};

interface AnimatedLineProps {
  className?: string;
}

const AnimatedLine: React.FC<AnimatedLineProps> = ({ className = '' }) => {
  return (
    <div className={`relative h-1 bg-gray-200 rounded-full overflow-hidden ${className}`}>
      <motion.div
        className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary to-purple-500 rounded-full"
        initial={{ width: '0%' }}
        whileInView={{ width: '100%' }}
        viewport={{ once: true }}
        transition={{ duration: 1.5, ease: 'easeInOut' }}
      />
    </div>
  );
};

interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
  className?: string;
}

const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  totalSteps,
  className = '',
}) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {Array.from({ length: totalSteps }).map((_, index) => (
        <React.Fragment key={index}>
          <motion.div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
              index < currentStep
                ? 'bg-primary text-white'
                : index === currentStep
                ? 'bg-primary text-white ring-4 ring-primary/20'
                : 'bg-gray-200 text-gray-500'
            }`}
            animate={index === currentStep ? { scale: [1, 1.1, 1] } : {}}
            transition={{ duration: 0.5, repeat: index === currentStep ? Infinity : 0, repeatDelay: 1 }}
          >
            {index < currentStep ? '✓' : index + 1}
          </motion.div>
          {index < totalSteps - 1 && (
            <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary"
                initial={{ width: '0%' }}
                animate={{ width: index < currentStep ? '100%' : '0%' }}
                transition={{ duration: 0.3 }}
              />
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export { HowItWorks, FlowingDots, AnimatedLine, StepIndicator };
export default HowItWorks;
