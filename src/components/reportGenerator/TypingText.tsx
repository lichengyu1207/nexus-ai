import React, { useState, useEffect, useRef, useCallback, forwardRef, useImperativeHandle } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TypingTextProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
  className?: string;
  isPlaying?: boolean;
  startDelay?: number;
  showCursor?: boolean;
  cursorChar?: string;
}

export interface TypingTextRef {
  pause: () => void;
  resume: () => void;
  reset: () => void;
  skipToEnd: () => void;
  getCurrentIndex: () => number;
  setCurrentIndex: (index: number) => void;
}

const TypingText = forwardRef<TypingTextRef, TypingTextProps>(({
  text,
  speed = 50,
  onComplete,
  className = '',
  isPlaying: externalIsPlaying,
  startDelay = 0,
  showCursor = true,
  cursorChar = '|',
}, ref) => {
  const [displayedIndex, setDisplayedIndex] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [internalIsPlaying, setInternalIsPlaying] = useState(true);
  const animationRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);
  const accumulatorRef = useRef<number>(0);
  const startedRef = useRef<boolean>(false);
  const startDelayRef = useRef<number>(startDelay);
  const startTimeRef = useRef<number>(0);

  const isPlaying = externalIsPlaying !== undefined ? externalIsPlaying : internalIsPlaying;

  const clearAnimation = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  }, []);

  const skipToEnd = useCallback(() => {
    clearAnimation();
    setDisplayedIndex(text.length);
    setIsComplete(true);
    onComplete?.();
  }, [text.length, onComplete, clearAnimation]);

  const reset = useCallback(() => {
    clearAnimation();
    setDisplayedIndex(0);
    setIsComplete(false);
    startedRef.current = false;
    accumulatorRef.current = 0;
  }, [clearAnimation]);

  const setCurrentIndex = useCallback((index: number) => {
    const clampedIndex = Math.max(0, Math.min(index, text.length));
    setDisplayedIndex(clampedIndex);
    setIsComplete(clampedIndex >= text.length);
    if (clampedIndex >= text.length) {
      onComplete?.();
    }
  }, [text.length, onComplete]);

  useImperativeHandle(ref, () => ({
    pause: () => setInternalIsPlaying(false),
    resume: () => setInternalIsPlaying(true),
    reset,
    skipToEnd,
    getCurrentIndex: () => displayedIndex,
    setCurrentIndex,
  }), [reset, skipToEnd, setCurrentIndex, displayedIndex]);

  useEffect(() => {
    if (!isPlaying || isComplete) {
      clearAnimation();
      return;
    }

    if (!startedRef.current) {
      startTimeRef.current = performance.now();
      startedRef.current = true;
    }

    const animate = (currentTime: number) => {
      if (!lastTimeRef.current) {
        lastTimeRef.current = currentTime;
      }

      const elapsed = currentTime - startTimeRef.current;
      
      if (elapsed < startDelayRef.current) {
        animationRef.current = requestAnimationFrame(animate);
        return;
      }

      const deltaTime = currentTime - lastTimeRef.current;
      lastTimeRef.current = currentTime;
      accumulatorRef.current += deltaTime;

      while (accumulatorRef.current >= speed && displayedIndex < text.length) {
        setDisplayedIndex(prev => {
          const newIndex = prev + 1;
          if (newIndex >= text.length) {
            setIsComplete(true);
            onComplete?.();
          }
          return newIndex;
        });
        accumulatorRef.current -= speed;
      }

      if (displayedIndex < text.length) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return clearAnimation;
  }, [isPlaying, isComplete, speed, text.length, onComplete, clearAnimation, displayedIndex, startDelay]);

  useEffect(() => {
    reset();
  }, [text, reset]);

  const displayedText = text.slice(0, displayedIndex);

  return (
    <span className={className} style={{ position: 'relative' }}>
      <span>{displayedText}</span>
      <AnimatePresence>
        {showCursor && !isComplete && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 1, 1, 0] }}
            transition={{ 
              duration: 0.8, 
              repeat: Infinity, 
              ease: 'linear' 
            }}
            style={{
              display: 'inline-block',
              marginLeft: '1px',
              color: 'inherit',
              fontWeight: 'bold',
            }}
            aria-hidden="true"
          >
            {cursorChar}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
});

TypingText.displayName = 'TypingText';

export default TypingText;
