import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import WorkflowAnimation, { WorkflowAnimationRef } from './WorkflowAnimation';
import BilingualSubtitle from './BilingualSubtitle';

const TOTAL_STEPS = 5;
const STEP_DURATION = 12000;
const INTRO_DURATION = 5000;

type PlaybackState = 'idle' | 'intro' | 'playing' | 'paused' | 'completed';

interface InternationalShowcaseProps {
  autoPlay?: boolean;
  onExplore?: () => void;
}

const InternationalShowcase: React.FC<InternationalShowcaseProps> = ({
  autoPlay = true,
  onExplore,
}) => {
  const [playbackState, setPlaybackState] = useState<PlaybackState>('idle');
  const [currentStep, setCurrentStep] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [showControls, setShowControls] = useState(true);
  
  const animationRef = useRef<WorkflowAnimationRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const startPlayback = useCallback(() => {
    setPlaybackState('intro');
    setCurrentStep(1);
    
    timeoutRef.current = setTimeout(() => {
      setPlaybackState('playing');
    }, INTRO_DURATION);
  }, []);

  const pausePlayback = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setPlaybackState('paused');
  }, []);

  const resumePlayback = useCallback(() => {
    setPlaybackState('playing');
  }, []);

  const resetPlayback = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setCurrentStep(1);
    setPlaybackState('idle');
    animationRef.current?.reset();
  }, []);

  const handleStepComplete = useCallback((step: number) => {
    if (step < TOTAL_STEPS) {
      setCurrentStep(step + 1);
    } else {
      setPlaybackState('completed');
    }
  }, []);

  useEffect(() => {
    if (autoPlay) {
      const timer = setTimeout(() => {
        startPlayback();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [autoPlay, startPlayback]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case ' ':
          e.preventDefault();
          if (playbackState === 'playing') {
            pausePlayback();
          } else if (playbackState === 'paused' || playbackState === 'idle') {
            if (playbackState === 'idle') {
              startPlayback();
            } else {
              resumePlayback();
            }
          }
          break;
        case 'r':
        case 'R':
          resetPlayback();
          break;
        case 'm':
        case 'M':
          setIsMuted((prev) => !prev);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [playbackState, pausePlayback, resumePlayback, resetPlayback, startPlayback]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting && playbackState === 'playing') {
            pausePlayback();
          }
        });
      },
      { threshold: 0.3 }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, [playbackState, pausePlayback]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && playbackState === 'playing') {
        pausePlayback();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [playbackState, pausePlayback]);

  const isPlaying = playbackState === 'playing' || playbackState === 'intro';

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[600px] md:h-[500px] overflow-hidden bg-gradient-to-br from-[#0a0f1e] via-[#1a1a2e] to-[#0f0f23]"
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(false)}
    >
      <div className="absolute inset-0 flex">
        <div className="hidden md:flex w-[30%] border-r border-white/10">
          <BilingualSubtitle
            currentStep={currentStep}
            showIntro={playbackState === 'intro'}
            highlightProgress={
              playbackState === 'intro'
                ? Math.min(1, (Date.now() % INTRO_DURATION) / INTRO_DURATION)
                : 0
            }
          />
        </div>

        <div className="flex-1 relative">
          <WorkflowAnimation
            ref={animationRef}
            currentStep={currentStep}
            isPlaying={isPlaying}
            onStepComplete={handleStepComplete}
          />

          <div className="md:hidden absolute top-4 left-4 right-4">
            <BilingualSubtitle
              currentStep={currentStep}
              showIntro={playbackState === 'intro'}
            />
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showControls && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute top-4 right-4 flex items-center gap-2"
          >
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
              title={isMuted ? '取消静音 (M)' : '静音 (M)'}
            >
              {isMuted ? (
                <SpeakerXMarkIcon className="w-5 h-5 text-white" />
              ) : (
                <SpeakerWaveIcon className="w-5 h-5 text-white" />
              )}
            </button>

            {playbackState !== 'idle' && playbackState !== 'completed' && (
              <button
                onClick={playbackState === 'playing' ? pausePlayback : resumePlayback}
                className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                title={playbackState === 'playing' ? '暂停 (空格)' : '播放 (空格)'}
              >
                {playbackState === 'playing' ? (
                  <PauseIcon className="w-5 h-5 text-white" />
                ) : (
                  <PlayIcon className="w-5 h-5 text-white" />
                )}
              </button>
            )}

            <button
              onClick={resetPlayback}
              className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
              title="重播 (R)"
            >
              <ArrowPathIcon className="w-5 h-5 text-white" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {playbackState === 'completed' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          >
            <div className="text-center space-y-6">
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', bounce: 0.5 }}
              >
                <h2 className="text-3xl md:text-4xl font-bold text-white mb-2">
                  Hearing is seeing
                </h2>
                <p className="text-xl text-gray-300">
                  听见是见，同步未来
                </p>
              </motion.div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={onExplore || (() => window.scrollTo({ top: 0, behavior: 'smooth' }))}
                  className="px-8 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white font-semibold rounded-full hover:shadow-lg hover:shadow-yellow-500/30 transition-all flex items-center gap-2"
                >
                  探索平台
                  <ChevronRightIcon className="w-5 h-5" />
                </button>

                <button
                  onClick={resetPlayback}
                  className="px-8 py-3 bg-white/10 text-white font-semibold rounded-full hover:bg-white/20 transition-all flex items-center gap-2"
                >
                  <ArrowPathIcon className="w-5 h-5" />
                  重播
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {playbackState === 'idle' && (
        <div className="absolute inset-0 flex items-center justify-center">
          <button
            onClick={startPlayback}
            className="group relative"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full blur-xl opacity-50 group-hover:opacity-75 transition-opacity" />
            <div className="relative w-20 h-20 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full flex items-center justify-center shadow-lg">
              <PlayIcon className="w-10 h-10 text-white ml-1" />
            </div>
          </button>
        </div>
      )}

      <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
        <motion.div
          className="h-full bg-gradient-to-r from-yellow-500 to-orange-500"
          initial={{ width: 0 }}
          animate={{
            width: playbackState === 'completed'
              ? '100%'
              : `${((currentStep - 1) / TOTAL_STEPS) * 100}%`,
          }}
          transition={{ duration: 0.3 }}
        />
      </div>
    </div>
  );
};

export default InternationalShowcase;
