import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface StepSubtitle {
  step: number;
  english: string;
  chinese: string;
}

const SUBTITLES: StepSubtitle[] = [
  {
    step: 1,
    english: "Your voice ignites the spark.",
    chinese: "你的声音，点燃最初的星火。",
  },
  {
    step: 2,
    english: "Countless agents unite in harmony.",
    chinese: "无数智能体，共谱协奏。",
  },
  {
    step: 3,
    english: "Wisdom from the past, retrieved.",
    chinese: "从过往中，唤醒智慧。",
  },
  {
    step: 4,
    english: "Personality evolves with every conversation.",
    chinese: "人格，在对话中进化。",
  },
  {
    step: 5,
    english: "Insights delivered, clarity achieved.",
    chinese: "洞察已至，清晰可循。",
  },
];

const INTRO_TEXT = {
  english: "Hear the resonance of the world. Bridge divides, let communication flow. With technology, we sync.",
  chinese: "听见世界的每一次共鸣，消弭隔阂，让沟通精准直达。以科技，让世界同频。",
};

interface BilingualSubtitleProps {
  currentStep: number;
  showIntro?: boolean;
  highlightProgress?: number;
}

const BilingualSubtitle: React.FC<BilingualSubtitleProps> = ({
  currentStep,
  showIntro = false,
  highlightProgress = 0,
}) => {
  const [displayText, setDisplayText] = useState({ english: '', chinese: '' });
  
  const currentSubtitle = SUBTITLES.find((s) => s.step === currentStep) || SUBTITLES[0];

  useEffect(() => {
    if (showIntro) {
      setDisplayText(INTRO_TEXT);
    } else {
      setDisplayText({
        english: currentSubtitle.english,
        chinese: currentSubtitle.chinese,
      });
    }
  }, [currentStep, showIntro, currentSubtitle]);

  const highlightChars = (text: string, progress: number) => {
    const chars = text.split('');
    const highlightIndex = Math.floor(chars.length * progress);
    
    return chars.map((char, index) => (
      <span
        key={index}
        className={`transition-all duration-100 ${
          index <= highlightIndex
            ? 'text-white'
            : 'text-gray-500'
        }`}
      >
        {char}
      </span>
    ));
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-8 py-12">
      <AnimatePresence mode="wait">
        <motion.div
          key={showIntro ? 'intro' : currentStep}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.5 }}
          className="text-center space-y-6"
        >
          {showIntro ? (
            <>
              <motion.p
                className="text-2xl md:text-3xl font-light text-white/90 leading-relaxed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                {highlightChars(displayText.english, highlightProgress)}
              </motion.p>
              <motion.p
                className="text-lg md:text-xl font-light text-gray-400 leading-relaxed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
              >
                {displayText.chinese}
              </motion.p>
            </>
          ) : (
            <>
              <motion.p
                className="text-xl md:text-2xl font-light text-white/90 leading-relaxed tracking-wide"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
              >
                {displayText.english}
              </motion.p>
              <motion.p
                className="text-base md:text-lg font-light text-gray-400 leading-relaxed"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                {displayText.chinese}
              </motion.p>
            </>
          )}
        </motion.div>
      </AnimatePresence>

      <motion.div
        className="mt-8 flex items-center gap-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <span className="text-xs text-gray-500 uppercase tracking-widest">
          Step {currentStep} of 5
        </span>
        <div className="flex gap-1">
          {SUBTITLES.map((s) => (
            <div
              key={s.step}
              className={`w-8 h-0.5 rounded-full transition-all duration-300 ${
                currentStep === s.step
                  ? 'bg-yellow-400'
                  : currentStep > s.step
                  ? 'bg-green-500'
                  : 'bg-gray-700'
              }`}
            />
          ))}
        </div>
      </motion.div>

      <motion.div
        className="mt-6 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.6 }}
      >
        <p className="text-xs text-gray-500 italic">
          "Hearing is seeing, the future in sync."
        </p>
        <p className="text-xs text-gray-600 mt-1">
          "听见是见，同步未来"
        </p>
      </motion.div>
    </div>
  );
};

export default BilingualSubtitle;
