import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TypingText, { TypingTextRef } from './TypingText';
import { getAgentInfo } from './types/reportStream';

interface Paragraph {
  text: string;
  agent?: string;
  delay?: number;
  type?: 'title' | 'summary' | 'insight';
}

interface DynamicParagraphProps {
  paragraphs: Paragraph[];
  speed?: number;
  onComplete?: () => void;
  isPlaying?: boolean;
  paragraphDelay?: number;
  showAgentTag?: boolean;
}

export interface DynamicParagraphRef {
  pause: () => void;
  resume: () => void;
  reset: () => void;
  skipToEnd: () => void;
  getCurrentParagraphIndex: () => number;
  setCurrentParagraphIndex: (index: number) => void;
}

const DynamicParagraph = forwardRef<DynamicParagraphRef, DynamicParagraphProps>(({
  paragraphs,
  speed = 50,
  onComplete,
  isPlaying: externalIsPlaying = true,
  paragraphDelay = 300,
  showAgentTag = true,
}, ref) => {
  const [currentParagraphIndex, setCurrentParagraphIndex] = useState(0);
  const [completedParagraphs, setCompletedParagraphs] = useState<Set<number>>(new Set());
  const [allComplete, setAllComplete] = useState(false);
  const typingRefs = useRef<Map<number, TypingTextRef>>(new Map());
  const [internalIsPlaying, setInternalIsPlaying] = useState(true);

  const isPlaying = externalIsPlaying !== undefined ? externalIsPlaying : internalIsPlaying;

  const handleParagraphComplete = (index: number) => {
    setCompletedParagraphs(prev => new Set([...prev, index]));
    
    if (index < paragraphs.length - 1) {
      setTimeout(() => {
        setCurrentParagraphIndex(index + 1);
      }, paragraphDelay);
    } else {
      setAllComplete(true);
      onComplete?.();
    }
  };

  const reset = () => {
    setCurrentParagraphIndex(0);
    setCompletedParagraphs(new Set());
    setAllComplete(false);
    typingRefs.current.forEach(ref => ref?.reset());
  };

  const skipToEnd = () => {
    typingRefs.current.forEach(ref => ref?.skipToEnd());
    setCompletedParagraphs(new Set(paragraphs.map((_, i) => i)));
    setCurrentParagraphIndex(paragraphs.length - 1);
    setAllComplete(true);
    onComplete?.();
  };

  const setCurrentParagraphIndexExternal = (index: number) => {
    const clampedIndex = Math.max(0, Math.min(index, paragraphs.length - 1));
    
    typingRefs.current.forEach((ref, i) => {
      if (i < clampedIndex) {
        ref?.skipToEnd();
      } else if (i > clampedIndex) {
        ref?.reset();
      }
    });
    
    const newCompleted = new Set<number>();
    for (let i = 0; i < clampedIndex; i++) {
      newCompleted.add(i);
    }
    setCompletedParagraphs(newCompleted);
    setCurrentParagraphIndex(clampedIndex);
    setAllComplete(clampedIndex === paragraphs.length - 1);
  };

  useImperativeHandle(ref, () => ({
    pause: () => setInternalIsPlaying(false),
    resume: () => setInternalIsPlaying(true),
    reset,
    skipToEnd,
    getCurrentParagraphIndex: () => currentParagraphIndex,
    setCurrentParagraphIndex: setCurrentParagraphIndexExternal,
  }), [currentParagraphIndex]);

  useEffect(() => {
    if (!isPlaying) {
      typingRefs.current.forEach(ref => ref?.pause?.());
    } else {
      typingRefs.current.forEach(ref => ref?.resume?.());
    }
  }, [isPlaying]);

  const getParagraphStyle = (type?: string): React.CSSProperties => {
    switch (type) {
      case 'title':
        return {
          fontSize: '24px',
          fontWeight: 'bold',
          marginBottom: '16px',
        };
      case 'summary':
        return {
          fontSize: '16px',
          lineHeight: 1.8,
          marginBottom: '12px',
        };
      case 'insight':
        return {
          fontSize: '14px',
          lineHeight: 1.6,
          marginBottom: '8px',
          paddingLeft: '12px',
          borderLeft: '3px solid rgba(59, 130, 246, 0.5)',
        };
      default:
        return {
          fontSize: '14px',
          lineHeight: 1.6,
          marginBottom: '12px',
        };
    }
  };

  return (
    <div style={{ width: '100%' }}>
      <AnimatePresence mode="sync">
        {paragraphs.map((paragraph, index) => {
          const isCurrentOrPast = index <= currentParagraphIndex;
          const agentInfo = paragraph.agent ? getAgentInfo(paragraph.agent) : null;
          
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ 
                opacity: isCurrentOrPast ? 1 : 0,
                y: isCurrentOrPast ? 0 : 10,
              }}
              transition={{ duration: 0.3 }}
              style={{ marginBottom: '8px' }}
            >
              {showAgentTag && agentInfo && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '2px 8px',
                    background: `${agentInfo.color}20`,
                    borderRadius: '4px',
                    marginBottom: '4px',
                    fontSize: '12px',
                  }}
                >
                  <span>{agentInfo.icon}</span>
                  <span style={{ color: agentInfo.color }}>{agentInfo.name}</span>
                </motion.div>
              )}
              
              <div style={getParagraphStyle(paragraph.type)}>
                {isCurrentOrPast && (
                  <TypingText
                    ref={(el) => {
                      if (el) {
                        typingRefs.current.set(index, el);
                      } else {
                        typingRefs.current.delete(index);
                      }
                    }}
                    text={paragraph.text}
                    speed={speed}
                    isPlaying={isPlaying && index === currentParagraphIndex}
                    startDelay={paragraph.delay || 0}
                    showCursor={index === currentParagraphIndex && !completedParagraphs.has(index)}
                    onComplete={() => handleParagraphComplete(index)}
                  />
                )}
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
      
      {allComplete && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            marginTop: '16px',
            padding: '8px 16px',
            background: 'rgba(16, 185, 129, 0.1)',
            borderRadius: '8px',
            color: '#10B981',
            fontSize: '14px',
          }}
        >
          <span>✓</span>
          <span>报告生成完成</span>
        </motion.div>
      )}
    </div>
  );
});

DynamicParagraph.displayName = 'DynamicParagraph';

export default DynamicParagraph;
