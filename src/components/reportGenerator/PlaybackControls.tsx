import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

interface PlaybackControlsProps {
  isPlaying: boolean;
  speed: number;
  progress: number;
  totalDuration: number;
  currentTime: number;
  onPlayPause: () => void;
  onSpeedChange: (speed: number) => void;
  onProgressChange: (progress: number) => void;
  onReplay: () => void;
  onComplete?: boolean;
}

const SPEED_OPTIONS = [0.5, 1, 1.5, 2, 3];

const PlaybackControls: React.FC<PlaybackControlsProps> = ({
  isPlaying,
  speed,
  progress,
  totalDuration,
  currentTime,
  onPlayPause,
  onSpeedChange,
  onProgressChange,
  onReplay,
  onComplete = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const progressRef = useRef<HTMLDivElement>(null);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);

  const formatTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressRef.current) return;
    const rect = progressRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    onProgressChange(percentage);
  };

  const handleProgressDrag = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging || !progressRef.current) return;
    const rect = progressRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    onProgressChange(percentage);
  };

  useEffect(() => {
    const handleMouseUp = () => setIsDragging(false);
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !progressRef.current) return;
      const rect = progressRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
      onProgressChange(percentage);
    };

    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, [isDragging, onProgressChange]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
      padding: '16px',
      background: 'rgba(255, 255, 255, 0.03)',
      borderRadius: '12px',
      border: '1px solid rgba(255, 255, 255, 0.05)',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <h4 style={{
          color: 'rgba(255, 255, 255, 0.9)',
          margin: 0,
          fontSize: '14px',
          fontWeight: 600,
        }}>
          播放控制
        </h4>
        {onComplete && (
          <motion.span
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              background: 'rgba(16, 185, 129, 0.1)',
              borderRadius: '4px',
              color: '#10B981',
              fontSize: '12px',
            }}
          >
            <span>✓</span>
            <span>已完成</span>
          </motion.span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <motion.button
          onClick={onPlayPause}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            border: 'none',
            background: isPlaying 
              ? 'rgba(239, 68, 68, 0.2)'
              : 'rgba(59, 130, 246, 0.2)',
            color: isPlaying ? '#EF4444' : '#3B82F6',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '16px',
          }}
        >
          {isPlaying ? '⏸' : '▶'}
        </motion.button>

        <motion.button
          onClick={onReplay}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            border: 'none',
            background: 'rgba(255, 255, 255, 0.05)',
            color: 'rgba(255, 255, 255, 0.7)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px',
          }}
        >
          ↺
        </motion.button>

        <div style={{ position: 'relative' }}>
          <motion.button
            onClick={() => setShowSpeedMenu(!showSpeedMenu)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: 'none',
              background: 'rgba(255, 255, 255, 0.05)',
              color: 'rgba(255, 255, 255, 0.7)',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 500,
            }}
          >
            {speed}x
          </motion.button>

          {showSpeedMenu && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                marginTop: '4px',
                background: 'rgba(0, 0, 0, 0.9)',
                borderRadius: '8px',
                padding: '4px',
                zIndex: 100,
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              {SPEED_OPTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => {
                    onSpeedChange(s);
                    setShowSpeedMenu(false);
                  }}
                  style={{
                    display: 'block',
                    width: '100%',
                    padding: '8px 16px',
                    border: 'none',
                    background: s === speed ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                    color: s === speed ? '#3B82F6' : 'rgba(255, 255, 255, 0.7)',
                    cursor: 'pointer',
                    fontSize: '12px',
                    textAlign: 'left',
                    borderRadius: '4px',
                  }}
                >
                  {s}x
                </button>
              ))}
            </motion.div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div
          ref={progressRef}
          onClick={handleProgressClick}
          onMouseDown={() => setIsDragging(true)}
          style={{
            position: 'relative',
            height: '8px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '4px',
            cursor: 'pointer',
            overflow: 'hidden',
          }}
        >
          <motion.div
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              height: '100%',
              background: 'linear-gradient(90deg, #3B82F6, #8B5CF6)',
              borderRadius: '4px',
            }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.1 }}
          />
          
          <motion.div
            style={{
              position: 'absolute',
              top: '50%',
              transform: 'translate(-50%, -50%)',
              width: '16px',
              height: '16px',
              background: '#fff',
              borderRadius: '50%',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
            }}
            animate={{ left: `${progress}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '11px',
          color: 'rgba(255, 255, 255, 0.4)',
        }}>
          <span>{formatTime(currentTime)}</span>
          <span>{progress.toFixed(1)}%</span>
          <span>{formatTime(totalDuration)}</span>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '8px',
        marginTop: '8px',
      }}>
        {[
          { icon: '⏮', label: '开始', action: () => onProgressChange(0) },
          { icon: '⏭', label: '结束', action: () => onProgressChange(100) },
          { icon: '⏪', label: '-10%', action: () => onProgressChange(Math.max(0, progress - 10)) },
          { icon: '⏩', label: '+10%', action: () => onProgressChange(Math.min(100, progress + 10)) },
        ].map((item, index) => (
          <motion.button
            key={index}
            onClick={item.action}
            whileHover={{ scale: 1.05, background: 'rgba(255, 255, 255, 0.1)' }}
            whileTap={{ scale: 0.95 }}
            style={{
              padding: '8px',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              background: 'rgba(255, 255, 255, 0.03)',
              color: 'rgba(255, 255, 255, 0.6)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '2px',
            }}
          >
            <span style={{ fontSize: '14px' }}>{item.icon}</span>
            <span style={{ fontSize: '10px' }}>{item.label}</span>
          </motion.button>
        ))}
      </div>
    </div>
  );
};

export default PlaybackControls;
