import React, { useState, useRef, useEffect, useCallback } from 'react';

interface SliderCaptchaProps {
  onSuccess: () => void;
  onFail?: () => void;
  width?: number;
  height?: number;
  sliderWidth?: number;
}

const SliderCaptcha: React.FC<SliderCaptchaProps> = ({
  onSuccess,
  onFail,
  width = 300,
  height = 40,
  sliderWidth = 50,
}) => {
  const [sliderLeft, setSliderLeft] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const [targetPosition, setTargetPosition] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const startXRef = useRef(0);

  const generateTarget = useCallback(() => {
    const maxPosition = width - sliderWidth - 10;
    const newPosition = Math.floor(Math.random() * maxPosition) + 5;
    setTargetPosition(newPosition);
    setSliderLeft(0);
    setIsVerified(false);
  }, [width, sliderWidth]);

  useEffect(() => {
    generateTarget();
  }, [refreshKey, generateTarget]);

  const handleStart = (clientX: number) => {
    if (isVerified) return;
    setIsDragging(true);
    startXRef.current = clientX - sliderLeft;
  };

  const handleMove = useCallback((clientX: number) => {
    if (!isDragging || isVerified) return;
    
    const container = containerRef.current;
    if (!container) return;
    
    let newLeft = clientX - startXRef.current;
    
    const maxLeft = width - sliderWidth;
    newLeft = Math.max(0, Math.min(newLeft, maxLeft));
    
    setSliderLeft(newLeft);
  }, [isDragging, isVerified, width, sliderWidth]);

  const handleEnd = useCallback(() => {
    if (!isDragging || isVerified) return;
    setIsDragging(false);
    
    const tolerance = 5;
    if (Math.abs(sliderLeft - targetPosition) <= tolerance) {
      setIsVerified(true);
      onSuccess();
    } else {
      onFail?.();
      setTimeout(() => {
        setRefreshKey(prev => prev + 1);
      }, 500);
    }
  }, [isDragging, isVerified, sliderLeft, targetPosition, onSuccess, onFail]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    handleStart(e.clientX);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault();
    if (e.touches.length > 0) {
      handleStart(e.touches[0].clientX);
    }
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    handleMove(e.clientX);
  }, [handleMove]);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (e.touches.length > 0) {
      handleMove(e.touches[0].clientX);
    }
  }, [handleMove]);

  const handleMouseUp = useCallback(() => {
    handleEnd();
  }, [handleEnd]);

  const handleTouchEnd = useCallback(() => {
    handleEnd();
  }, [handleEnd]);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.addEventListener('touchmove', handleTouchMove, { passive: false });
      document.addEventListener('touchend', handleTouchEnd);
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [isDragging, handleMouseMove, handleMouseUp, handleTouchMove, handleTouchEnd]);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const progress = (sliderLeft / (width - sliderWidth)) * 100;

  return (
    <div className="slider-captcha-container">
      <div
        ref={containerRef}
        className="relative bg-gray-100 rounded-lg overflow-hidden select-none touch-none"
        style={{ width, height, touchAction: 'none' }}
      >
        <div
          className="absolute top-0 left-0 h-full bg-green-200 transition-all duration-100"
          style={{ width: `${progress}%` }}
        />
        
        <div
          className="absolute top-0 h-full flex items-center justify-center text-xs text-gray-400"
          style={{ left: targetPosition, width: sliderWidth }}
        >
          <div className="w-1 h-6 bg-gray-400 rounded" />
        </div>
        
        <div
          className={`absolute top-0 h-full flex items-center justify-center cursor-pointer rounded transition-colors ${
            isVerified 
              ? 'bg-green-500 text-white' 
              : 'bg-white border-2 border-gray-300 hover:border-primary-500 active:bg-gray-50'
          }`}
          style={{ left: sliderLeft, width: sliderWidth, touchAction: 'none' }}
          onMouseDown={handleMouseDown}
          onTouchStart={handleTouchStart}
        >
          {isVerified ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          )}
        </div>
        
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <span className={`text-sm ${isVerified ? 'text-white' : 'text-gray-400'}`}>
            {isVerified ? '验证成功' : '向右拖动滑块到指定位置'}
          </span>
        </div>
      </div>
      
      <button
        onClick={handleRefresh}
        className="mt-2 text-sm text-gray-500 hover:text-primary-600 flex items-center gap-1"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新验证
      </button>
    </div>
  );
};

export default SliderCaptcha;
