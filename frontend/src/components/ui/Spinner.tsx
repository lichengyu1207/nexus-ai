import React from 'react';

type SpinnerSize = 'sm' | 'md' | 'lg' | 'xl';
type SpinnerVariant = 'primary' | 'white' | 'gray';

interface SpinnerProps {
  size?: SpinnerSize;
  variant?: SpinnerVariant;
  className?: string;
}

const sizeClasses: Record<SpinnerSize, string> = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-3',
  xl: 'w-12 h-12 border-4',
};

const variantClasses: Record<SpinnerVariant, string> = {
  primary: 'border-primary border-t-transparent',
  white: 'border-white border-t-transparent',
  gray: 'border-gray-400 border-t-transparent',
};

const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  className = '',
}) => {
  return (
    <div
      className={`
        inline-block rounded-full animate-spin
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
      role="status"
      aria-label="加载中"
    >
      <span className="sr-only">加载中...</span>
    </div>
  );
};

interface DotsSpinnerProps {
  size?: SpinnerSize;
  className?: string;
}

const DotsSpinner: React.FC<DotsSpinnerProps> = ({
  size = 'md',
  className = '',
}) => {
  const dotSizes: Record<SpinnerSize, string> = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
    xl: 'w-3 h-3',
  };

  return (
    <div className={`inline-flex items-center gap-1 ${className}`} role="status">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={`
            ${dotSizes[size]}
            bg-primary rounded-full
            animate-bounce
          `}
          style={{
            animationDelay: `${i * 0.15}s`,
            animationDuration: '0.6s',
          }}
        />
      ))}
      <span className="sr-only">加载中...</span>
    </div>
  );
};

interface PulseSpinnerProps {
  size?: SpinnerSize;
  className?: string;
}

const PulseSpinner: React.FC<PulseSpinnerProps> = ({
  size = 'md',
  className = '',
}) => {
  const pulseSizes: Record<SpinnerSize, string> = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  return (
    <div className={`relative ${pulseSizes[size]} ${className}`} role="status">
      <div className="absolute inset-0 bg-primary/30 rounded-full animate-ping" />
      <div className="absolute inset-1 bg-primary/50 rounded-full animate-ping" style={{ animationDelay: '0.2s' }} />
      <div className="absolute inset-2 bg-primary rounded-full" />
      <span className="sr-only">加载中...</span>
    </div>
  );
};

interface BarsSpinnerProps {
  size?: SpinnerSize;
  className?: string;
}

const BarsSpinner: React.FC<BarsSpinnerProps> = ({
  size = 'md',
  className = '',
}) => {
  const barHeights: Record<SpinnerSize, string> = {
    sm: 'h-3',
    md: 'h-5',
    lg: 'h-7',
    xl: 'h-9',
  };

  const barWidths: Record<SpinnerSize, string> = {
    sm: 'w-0.5',
    md: 'w-1',
    lg: 'w-1',
    xl: 'w-1.5',
  };

  return (
    <div className={`inline-flex items-end gap-0.5 ${className}`} role="status">
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className={`
            ${barHeights[size]}
            ${barWidths[size]}
            bg-primary rounded-full
            animate-pulse
          `}
          style={{
            animationDelay: `${i * 0.1}s`,
            animationDuration: '0.5s',
          }}
        />
      ))}
      <span className="sr-only">加载中...</span>
    </div>
  );
};

interface RingSpinnerProps {
  size?: SpinnerSize;
  className?: string;
}

const RingSpinner: React.FC<RingSpinnerProps> = ({
  size = 'md',
  className = '',
}) => {
  const ringSizes: Record<SpinnerSize, string> = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-14 h-14',
    xl: 'w-18 h-18',
  };

  return (
    <div className={`relative ${ringSizes[size]} ${className}`} role="status">
      <div className="absolute inset-0 border-2 border-primary/20 rounded-full" />
      <div className="absolute inset-0 border-2 border-transparent border-t-primary rounded-full animate-spin" />
      <span className="sr-only">加载中...</span>
    </div>
  );
};

interface LoadingOverlayProps {
  visible: boolean;
  text?: string;
  className?: string;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  visible,
  text = '加载中...',
  className = '',
}) => {
  if (!visible) return null;

  return (
    <div className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 ${className}`}>
      <div className="bg-white rounded-lg p-6 flex flex-col items-center gap-4">
        <Spinner size="lg" />
        <p className="text-gray-600">{text}</p>
      </div>
    </div>
  );
};

interface InlineLoadingProps {
  text?: string;
  className?: string;
}

const InlineLoading: React.FC<InlineLoadingProps> = ({
  text = '加载中',
  className = '',
}) => {
  return (
    <div className={`inline-flex items-center gap-2 text-gray-500 ${className}`}>
      <Spinner size="sm" />
      <span>{text}</span>
    </div>
  );
};

export {
  Spinner,
  DotsSpinner,
  PulseSpinner,
  BarsSpinner,
  RingSpinner,
  LoadingOverlay,
  InlineLoading,
};

export default Spinner;
