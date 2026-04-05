import React, { useState, useRef, useEffect, ReactNode } from 'react';

type TooltipPlacement = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  placement?: TooltipPlacement;
  delay?: number;
  className?: string;
}

const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  placement = 'top',
  delay = 200,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const calculatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const gap = 8;

    let x = 0;
    let y = 0;

    switch (placement) {
      case 'top':
        x = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
        y = triggerRect.top - tooltipRect.height - gap;
        break;
      case 'bottom':
        x = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
        y = triggerRect.bottom + gap;
        break;
      case 'left':
        x = triggerRect.left - tooltipRect.width - gap;
        y = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
        break;
      case 'right':
        x = triggerRect.right + gap;
        y = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
        break;
    }

    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    if (x < 0) x = gap;
    if (x + tooltipRect.width > viewportWidth) x = viewportWidth - tooltipRect.width - gap;
    if (y < 0) y = gap;
    if (y + tooltipRect.height > viewportHeight) y = viewportHeight - tooltipRect.height - gap;

    setPosition({ x, y });
  };

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  useEffect(() => {
    if (isVisible) {
      calculatePosition();
    }
  }, [isVisible, placement]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const arrowClasses: Record<TooltipPlacement, string> = {
    top: 'bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45',
    bottom: 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 rotate-45',
    left: 'right-0 top-1/2 translate-x-1/2 -translate-y-1/2 rotate-45',
    right: 'left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 rotate-45',
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        className="inline-block"
      >
        {children}
      </div>

      {isVisible && (
        <div
          ref={tooltipRef}
          role="tooltip"
          className={`
            fixed z-[9999] px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg
            animate-fade-in max-w-xs
            ${className}
          `}
          style={{
            left: position.x,
            top: position.y,
          }}
        >
          {content}
          <div
            className={`absolute w-2 h-2 bg-gray-900 ${arrowClasses[placement]}`}
          />
        </div>
      )}
    </>
  );
};

interface InfoTooltipProps {
  content: ReactNode;
  placement?: TooltipPlacement;
  iconClassName?: string;
}

const InfoTooltip: React.FC<InfoTooltipProps> = ({
  content,
  placement = 'top',
  iconClassName = '',
}) => {
  return (
    <Tooltip content={content} placement={placement}>
      <svg
        className={`w-4 h-4 text-gray-400 cursor-help ${iconClassName}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </Tooltip>
  );
};

interface DataSourceTooltipProps {
  source: string;
  confidence?: number;
  updatedAt?: string;
}

const DataSourceTooltip: React.FC<DataSourceTooltipProps> = ({
  source,
  confidence,
  updatedAt,
}) => {
  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return 'text-green-600';
    if (conf >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Tooltip
      content={
        <div className="space-y-1">
          <p className="font-medium">数据来源</p>
          <p>{source}</p>
          {confidence !== undefined && (
            <p className={getConfidenceColor(confidence)}>
              置信度: {(confidence * 100).toFixed(0)}%
            </p>
          )}
          {updatedAt && (
            <p className="text-gray-400 text-xs">
              更新于: {new Date(updatedAt).toLocaleDateString('zh-CN')}
            </p>
          )}
        </div>
      }
      placement="top"
    >
      <span className="inline-flex items-center cursor-help">
        <svg
          className="w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </span>
    </Tooltip>
  );
};

export { Tooltip, InfoTooltip, DataSourceTooltip };
export default Tooltip;
