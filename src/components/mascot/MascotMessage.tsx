import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Mascot, { MascotEmotion, MascotPose, MascotSize } from './Mascot';

export type MessagePosition = 'top' | 'bottom' | 'left' | 'right';
export type MessageType = 'info' | 'success' | 'warning' | 'error' | 'question';

interface MascotMessageProps {
  message: string;
  emotion?: MascotEmotion;
  pose?: MascotPose;
  size?: MascotSize;
  position?: MessagePosition;
  type?: MessageType;
  autoDismiss?: boolean;
  dismissDelay?: number;
  onDismiss?: () => void;
  onConfirm?: () => void;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
  className?: string;
  showMascot?: boolean;
  animate?: boolean;
}

const typeStyles: Record<MessageType, {
  bgColor: string;
  borderColor: string;
  textColor: string;
}> = {
  info: {
    bgColor: '#EFF6FF',
    borderColor: '#BFDBFE',
    textColor: '#1E40AF',
  },
  success: {
    bgColor: '#ECFDF5',
    borderColor: '#A7F3D0',
    textColor: '#065F46',
  },
  warning: {
    bgColor: '#FFFBEB',
    borderColor: '#FDE68A',
    textColor: '#92400E',
  },
  error: {
    bgColor: '#FEF2F2',
    borderColor: '#FECACA',
    textColor: '#991B1B',
  },
  question: {
    bgColor: '#F5F3FF',
    borderColor: '#DDD6FE',
    textColor: '#5B21B6',
  },
};

const MascotMessage: React.FC<MascotMessageProps> = ({
  message,
  emotion = 'default',
  pose,
  size = 'md',
  position = 'bottom',
  type = 'info',
  autoDismiss = false,
  dismissDelay = 3000,
  onDismiss,
  onConfirm,
  onCancel,
  confirmText,
  cancelText,
  className = '',
  showMascot = true,
  animate = true,
}) => {
  const [visible, setVisible] = useState(true);
  const styles = typeStyles[type];

  useEffect(() => {
    if (autoDismiss && dismissDelay > 0) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, dismissDelay);
      return () => clearTimeout(timer);
    }
  }, [autoDismiss, dismissDelay]);

  const handleDismiss = useCallback(() => {
    setVisible(false);
    setTimeout(() => {
      onDismiss?.();
    }, 300);
  }, [onDismiss]);

  const handleConfirm = useCallback(() => {
    onConfirm?.();
    handleDismiss();
  }, [onConfirm, handleDismiss]);

  const handleCancel = useCallback(() => {
    onCancel?.();
    handleDismiss();
  }, [onCancel, handleDismiss]);

  const getLayoutDirection = () => {
    switch (position) {
      case 'left':
        return 'row-reverse';
      case 'right':
        return 'row';
      case 'top':
        return 'column-reverse';
      case 'bottom':
      default:
        return 'column';
    }
  };

  const getBubbleStyle = (): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      backgroundColor: styles.bgColor,
      border: `1px solid ${styles.borderColor}`,
      borderRadius: '12px',
      padding: '12px 16px',
      maxWidth: position === 'left' || position === 'right' ? '240px' : '320px',
      position: 'relative',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    };

    return baseStyle;
  };

  const getArrowStyle = (): React.CSSProperties => {
    const arrowSize = 8;
    const arrowColor = styles.borderColor;
    const arrowBgColor = styles.bgColor;

    const baseStyle: React.CSSProperties = {
      position: 'absolute',
      width: 0,
      height: 0,
    };

    switch (position) {
      case 'top':
        return {
          ...baseStyle,
          bottom: -arrowSize,
          left: '50%',
          transform: 'translateX(-50%)',
          borderLeft: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid transparent`,
          borderTop: `${arrowSize}px solid ${arrowBgColor}`,
        };
      case 'bottom':
        return {
          ...baseStyle,
          top: -arrowSize,
          left: '50%',
          transform: 'translateX(-50%)',
          borderLeft: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid transparent`,
          borderBottom: `${arrowSize}px solid ${arrowBgColor}`,
        };
      case 'left':
        return {
          ...baseStyle,
          right: -arrowSize,
          top: '50%',
          transform: 'translateY(-50%)',
          borderTop: `${arrowSize}px solid transparent`,
          borderBottom: `${arrowSize}px solid transparent`,
          borderLeft: `${arrowSize}px solid ${arrowBgColor}`,
        };
      case 'right':
        return {
          ...baseStyle,
          left: -arrowSize,
          top: '50%',
          transform: 'translateY(-50%)',
          borderTop: `${arrowSize}px solid transparent`,
          borderBottom: `${arrowSize}px solid transparent`,
          borderRight: `${arrowSize}px solid ${arrowBgColor}`,
        };
      default:
        return baseStyle;
    }
  };

  const containerVariants = {
    hidden: {
      opacity: 0,
      scale: 0.9,
      y: position === 'top' ? 10 : position === 'bottom' ? -10 : 0,
      x: position === 'left' ? 10 : position === 'right' ? -10 : 0,
    },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      x: 0,
    },
    exit: {
      opacity: 0,
      scale: 0.9,
      y: position === 'top' ? 10 : position === 'bottom' ? -10 : 0,
      x: position === 'left' ? 10 : position === 'right' ? -10 : 0,
    },
  };

  const bubbleVariants = {
    hidden: { opacity: 0, scale: 0.8 },
    visible: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.8 },
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className={`mascot-message-container ${className}`}
          style={{
            display: 'inline-flex',
            flexDirection: getLayoutDirection(),
            alignItems: 'center',
            gap: position === 'left' || position === 'right' ? '16px' : '12px',
          }}
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        >
          {showMascot && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
            >
              <Mascot
                emotion={emotion}
                pose={pose}
                size={size}
                animate={animate}
              />
            </motion.div>
          )}

          <motion.div
            style={getBubbleStyle()}
            variants={bubbleVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ delay: 0.15 }}
          >
            <div style={getArrowStyle()} />
            
            <motion.p
              style={{
                margin: 0,
                fontSize: '14px',
                color: styles.textColor,
                lineHeight: 1.5,
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              {message}
            </motion.p>

            {(confirmText || cancelText) && (
              <motion.div
                style={{
                  display: 'flex',
                  gap: '8px',
                  marginTop: '12px',
                  justifyContent: 'flex-end',
                }}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                {cancelText && (
                  <motion.button
                    onClick={handleCancel}
                    style={{
                      padding: '6px 12px',
                      fontSize: '13px',
                      border: '1px solid #D1D5DB',
                      borderRadius: '6px',
                      backgroundColor: 'white',
                      color: '#374151',
                      cursor: 'pointer',
                    }}
                    whileHover={{ backgroundColor: '#F3F4F6' }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {cancelText}
                  </motion.button>
                )}
                {confirmText && (
                  <motion.button
                    onClick={handleConfirm}
                    style={{
                      padding: '6px 12px',
                      fontSize: '13px',
                      border: 'none',
                      borderRadius: '6px',
                      backgroundColor: '#1D4ED8',
                      color: 'white',
                      cursor: 'pointer',
                    }}
                    whileHover={{ backgroundColor: '#1E40AF' }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {confirmText}
                  </motion.button>
                )}
              </motion.div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default MascotMessage;

interface MascotChatBubbleProps {
  messages: string[];
  emotion?: MascotEmotion;
  size?: MascotSize;
  typingSpeed?: number;
  onComplete?: () => void;
  showMascot?: boolean;
}

export const MascotChatBubble: React.FC<MascotChatBubbleProps> = ({
  messages,
  emotion = 'default',
  size = 'md',
  typingSpeed = 50,
  onComplete,
  showMascot = true,
}) => {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(true);
  const [isComplete, setIsComplete] = useState(false);

  const currentMessage = messages[currentMessageIndex] || '';

  useEffect(() => {
    if (currentMessageIndex >= messages.length) {
      setIsComplete(true);
      onComplete?.();
      return;
    }

    setDisplayedText('');
    setIsTyping(true);

    let charIndex = 0;
    const interval = setInterval(() => {
      if (charIndex < currentMessage.length) {
        setDisplayedText(currentMessage.slice(0, charIndex + 1));
        charIndex++;
      } else {
        setIsTyping(false);
        clearInterval(interval);

        if (currentMessageIndex < messages.length - 1) {
          setTimeout(() => {
            setCurrentMessageIndex((prev) => prev + 1);
          }, 1500);
        } else {
          setIsComplete(true);
          onComplete?.();
        }
      }
    }, typingSpeed);

    return () => clearInterval(interval);
  }, [currentMessageIndex, currentMessage, typingSpeed, messages.length, onComplete]);

  if (isComplete && messages.length === 0) return null;

  return (
    <motion.div
      style={{
        display: 'inline-flex',
        alignItems: 'flex-start',
        gap: '12px',
      }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {showMascot && (
        <Mascot
          emotion={isTyping ? 'thinking' : emotion}
          size={size}
          animate
        />
      )}

      <motion.div
        style={{
          backgroundColor: 'white',
          border: '1px solid #E5E7EB',
          borderRadius: '12px',
          padding: '12px 16px',
          maxWidth: '280px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
        }}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <p style={{ margin: 0, fontSize: '14px', color: '#374151', lineHeight: 1.5 }}>
          {displayedText}
          {isTyping && (
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.5, repeat: Infinity }}
              style={{ marginLeft: '2px' }}
            >
              |
            </motion.span>
          )}
        </p>

        {messages.length > 1 && (
          <motion.div
            style={{
              display: 'flex',
              gap: '4px',
              marginTop: '8px',
              justifyContent: 'center',
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {messages.map((_, index) => (
              <motion.div
                key={index}
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  backgroundColor: index === currentMessageIndex ? '#1D4ED8' : '#D1D5DB',
                }}
                animate={index === currentMessageIndex ? { scale: [1, 1.2, 1] } : {}}
                transition={{ duration: 0.3 }}
              />
            ))}
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
};

interface MascotTooltipProps {
  content: string;
  emotion?: MascotEmotion;
  size?: MascotSize;
  position?: MessagePosition;
  children: React.ReactNode;
}

export const MascotTooltip: React.FC<MascotTooltipProps> = ({
  content,
  emotion = 'default',
  size = 'sm',
  position = 'top',
  children,
}) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      style={{ position: 'relative', display: 'inline-block' }}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            style={{
              position: 'absolute',
              zIndex: 50,
              ...(position === 'top' && { bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '8px' }),
              ...(position === 'bottom' && { top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: '8px' }),
              ...(position === 'left' && { right: '100%', top: '50%', transform: 'translateY(-50%)', marginRight: '8px' }),
              ...(position === 'right' && { left: '100%', top: '50%', transform: 'translateY(-50%)', marginLeft: '8px' }),
            }}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.2 }}
          >
            <MascotMessage
              message={content}
              emotion={emotion}
              size={size}
              position={position}
              showMascot={false}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
