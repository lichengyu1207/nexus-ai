import React from 'react';
import { motion } from 'framer-motion';

interface Step {
  step_name: string;
  status: string;
  comment: string;
}

interface Progress {
  status: string;
  current_step: string;
  steps: Step[];
  step_comment: string;
}

interface ProgressCampProps {
  progress: Progress | null;
  persona: 'zhouyu' | 'luxun';
}

const STEPS = [
  { id: 'requirement', label: '需求解析', icon: '🎯' },
  { id: 'collection', label: '数据采集', icon: '📊' },
  { id: 'analysis', label: '市场分析', icon: '🧠' },
  { id: 'report', label: '报告生成', icon: '📄' },
];

const PERSONA_COMMENTS = {
  zhouyu: {
    requirement: '需求官正解读主公意图，片刻便知。',
    collection: '采集使正在探查各处数据，主公莫急。',
    analysis: '分析将正在推演，很快便有结果。',
    report: '报告已成，请主公过目。',
  },
  luxun: {
    requirement: '需求已明，可图下一步。',
    collection: '数据正在收集中，稍待片刻。',
    analysis: '正在分析，不可轻动。',
    report: '报告已备，请主公查验。',
  },
};

export const ProgressCamp: React.FC<ProgressCampProps> = ({
  progress,
  persona,
}) => {
  const currentStep = progress?.current_step || 'requirement';
  const currentIndex = STEPS.findIndex((s) => s.id === currentStep);
  const personaComments = PERSONA_COMMENTS[persona];

  return (
    <div className="relative py-8">
      {/* 连接线 */}
      <div className="absolute top-1/2 left-0 w-full h-1 bg-gray-200 -translate-y-1/2 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-primary-500"
          initial={{ width: '0%' }}
          animate={{ width: `${((currentIndex + 1) / STEPS.length) * 100}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      <div className="flex justify-between relative">
        {STEPS.map((step, index) => {
          const isActive = index <= currentIndex;
          const isCurrent = index === currentIndex;
          const comment = progress?.steps?.find((s) => s.step_name === step.id)?.comment || 
                         personaComments[step.id as keyof typeof personaComments];

          return (
            <div
              key={step.id}
              className="flex flex-col items-center relative z-10"
            >
              <motion.div
                className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl ${
                  isActive
                    ? 'bg-primary-100 text-primary-600'
                    : 'bg-gray-100 text-gray-400'
                } border-4 ${
                  isCurrent ? 'border-primary-500' : 'border-transparent'
                }`}
                animate={
                  isCurrent
                    ? { scale: [1, 1.1, 1], boxShadow: ['0 0 0 0 rgba(59, 130, 246, 0.5)', '0 0 0 10px rgba(59, 130, 246, 0)', '0 0 0 0 rgba(59, 130, 246, 0)'] }
                    : {}
                }
                transition={{ repeat: Infinity, duration: 1.5 }}
              >
                {step.icon}
              </motion.div>
              <span
                className={`mt-2 font-medium ${
                  isActive ? 'text-primary-600' : 'text-gray-400'
                }`}
              >
                {step.label}
              </span>
              
              {isCurrent && comment && (
                <motion.div
                  className="absolute top-24 bg-white border border-primary-200 rounded-lg p-3 text-sm text-gray-600 w-48 text-center shadow-lg"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <span className="text-lg">
                      {persona === 'zhouyu' ? '🪭' : '⚔️'}
                    </span>
                    <span className="font-semibold">
                      {persona === 'zhouyu' ? '周瑜' : '陆逊'}
                    </span>
                  </div>
                  {comment}
                </motion.div>
              )}
            </div>
          );
        })}
      </div>

      {/* 嘟嘟移动动画 */}
      <motion.div
        className="absolute -bottom-8"
        animate={{
          left: `${(currentIndex / (STEPS.length - 1)) * 100}%`,
        }}
        transition={{ duration: 0.5, ease: 'easeInOut' }}
        style={{ left: '0%' }}
      >
        <div className="w-10 h-10 rounded-full bg-amber-400 flex items-center justify-center text-xl shadow-lg">
          🐼
        </div>
      </motion.div>
    </div>
  );
};

export default ProgressCamp;
