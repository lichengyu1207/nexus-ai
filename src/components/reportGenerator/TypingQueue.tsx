import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TypingQueueItem {
  id: string;
  text: string;
  type: 'title' | 'section-title' | 'paragraph' | 'summary' | 'insight' | 'other';
  speed?: number;
  metadata?: Record<string, unknown>;
}

interface TypingQueueProps {
  items: TypingQueueItem[];
  isPlaying: boolean;
  speed: number;
  onProgress?: (currentIndex: number, totalItems: number) => void;
  onComplete?: () => void;
  renderTitle?: (text: string, isTyping: boolean) => React.ReactNode;
  renderSectionTitle?: (text: string, isTyping: boolean) => React.ReactNode;
  renderParagraph?: (text: string, isTyping: boolean, metadata?: Record<string, unknown>) => React.ReactNode;
  renderSummary?: (text: string, isTyping: boolean) => React.ReactNode;
  renderInsight?: (text: string, isTyping: boolean, metadata?: Record<string, unknown>) => React.ReactNode;
  renderOther?: (item: TypingQueueItem, isTyping: boolean) => React.ReactNode;
}

const TypingQueue: React.FC<TypingQueueProps> = ({
  items,
  isPlaying,
  speed,
  onProgress,
  onComplete,
  renderTitle,
  renderSectionTitle,
  renderParagraph,
  renderSummary,
  renderInsight,
  renderOther,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const animationRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);
  const charIndexRef = useRef(0);
  const accumulatorRef = useRef(0);

  const currentItem = items[currentIndex];
  const typingSpeed = (currentItem?.speed || 30) / speed;

  const clearAnimation = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  }, []);

  const moveToNext = useCallback(() => {
    if (currentIndex < items.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setDisplayedText('');
      charIndexRef.current = 0;
      accumulatorRef.current = 0;
      onProgress?.(currentIndex + 1, items.length);
    } else {
      setIsTyping(false);
      onComplete?.();
    }
  }, [currentIndex, items.length, onProgress, onComplete]);

  useEffect(() => {
    if (!isPlaying || !currentItem) {
      clearAnimation();
      return;
    }

    setIsTyping(true);
    const text = currentItem.text;
    const itemSpeed = typingSpeed;

    const animate = (currentTime: number) => {
      if (!lastTimeRef.current) {
        lastTimeRef.current = currentTime;
      }

      const deltaTime = currentTime - lastTimeRef.current;
      lastTimeRef.current = currentTime;
      accumulatorRef.current += deltaTime;

      while (accumulatorRef.current >= itemSpeed && charIndexRef.current < text.length) {
        charIndexRef.current++;
        setDisplayedText(text.slice(0, charIndexRef.current));
        accumulatorRef.current -= itemSpeed;
      }

      if (charIndexRef.current < text.length) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        setTimeout(() => {
          moveToNext();
        }, 100);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return clearAnimation;
  }, [isPlaying, currentItem, typingSpeed, moveToNext, clearAnimation]);

  useEffect(() => {
    setCurrentIndex(0);
    setDisplayedText('');
    charIndexRef.current = 0;
    accumulatorRef.current = 0;
    lastTimeRef.current = 0;
  }, [items]);

  useEffect(() => {
    if (!isPlaying) {
      clearAnimation();
    }
  }, [isPlaying, clearAnimation]);

  const renderCompletedItems = () => {
    return items.slice(0, currentIndex).map((item, index) => {
      const key = `completed-${item.id}-${index}`;
      
      switch (item.type) {
        case 'title':
          return renderTitle ? (
            <React.Fragment key={key}>{renderTitle(item.text, false)}</React.Fragment>
          ) : (
            <div key={key} style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff', marginBottom: '16px' }}>
              {item.text}
            </div>
          );
        case 'section-title':
          return renderSectionTitle ? (
            <React.Fragment key={key}>{renderSectionTitle(item.text, false)}</React.Fragment>
          ) : (
            <h2 key={key} style={{ fontSize: '18px', fontWeight: 600, color: '#fff', marginTop: '24px', marginBottom: '12px' }}>
              {item.text}
            </h2>
          );
        case 'paragraph':
          return renderParagraph ? (
            <React.Fragment key={key}>{renderParagraph(item.text, false, item.metadata)}</React.Fragment>
          ) : (
            <p key={key} style={{ fontSize: '14px', lineHeight: 1.8, color: 'rgba(255,255,255,0.8)', marginBottom: '12px', textIndent: '2em' }}>
              {item.text}
            </p>
          );
        case 'summary':
          return renderSummary ? (
            <React.Fragment key={key}>{renderSummary(item.text, false)}</React.Fragment>
          ) : (
            <div key={key} style={{ fontSize: '14px', lineHeight: 1.6, color: 'rgba(255,255,255,0.7)', marginBottom: '16px' }}>
              {item.text}
            </div>
          );
        case 'insight':
          return renderInsight ? (
            <React.Fragment key={key}>{renderInsight(item.text, false, item.metadata)}</React.Fragment>
          ) : (
            <div key={key} style={{ fontSize: '13px', color: '#F59E0B', marginBottom: '8px', paddingLeft: '12px', borderLeft: '2px solid #F59E0B' }}>
              {item.text}
            </div>
          );
        default:
          return renderOther ? (
            <React.Fragment key={key}>{renderOther(item, false)}</React.Fragment>
          ) : (
            <div key={key}>{item.text}</div>
          );
      }
    });
  };

  const renderCurrentItem = () => {
    if (!currentItem) return null;
    
    const textWithCursor = (
      <>
        {displayedText}
        <motion.span
          animate={{ opacity: [0, 1, 1, 0] }}
          transition={{ duration: 0.6, repeat: Infinity, ease: 'linear' }}
          style={{ 
            display: 'inline-block', 
            marginLeft: '1px',
            color: 'inherit',
            fontWeight: 'bold',
          }}
        >
          |
        </motion.span>
      </>
    );

    switch (currentItem.type) {
      case 'title':
        return renderTitle ? renderTitle(displayedText, true) : (
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff', marginBottom: '16px' }}>
            {textWithCursor}
          </div>
        );
      case 'section-title':
        return renderSectionTitle ? renderSectionTitle(displayedText, true) : (
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#fff', marginTop: '24px', marginBottom: '12px' }}>
            {textWithCursor}
          </h2>
        );
      case 'paragraph':
        return renderParagraph ? renderParagraph(displayedText, true, currentItem.metadata) : (
          <p style={{ fontSize: '14px', lineHeight: 1.8, color: 'rgba(255,255,255,0.8)', marginBottom: '12px', textIndent: '2em' }}>
            {textWithCursor}
          </p>
        );
      case 'summary':
        return renderSummary ? renderSummary(displayedText, true) : (
          <div style={{ fontSize: '14px', lineHeight: 1.6, color: 'rgba(255,255,255,0.7)', marginBottom: '16px' }}>
            {textWithCursor}
          </div>
        );
      case 'insight':
        return renderInsight ? renderInsight(displayedText, true, currentItem.metadata) : (
          <div style={{ fontSize: '13px', color: '#F59E0B', marginBottom: '8px', paddingLeft: '12px', borderLeft: '2px solid #F59E0B' }}>
            {textWithCursor}
          </div>
        );
      default:
        return renderOther ? renderOther(currentItem, true) : (
          <div>{textWithCursor}</div>
        );
    }
  };

  return (
    <div>
      <AnimatePresence>
        {renderCompletedItems()}
      </AnimatePresence>
      {renderCurrentItem()}
    </div>
  );
};

export default TypingQueue;
