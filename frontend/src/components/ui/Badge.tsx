import React, { ReactNode } from 'react';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'primary' | 'secondary';
type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  removable?: boolean;
  onRemove?: () => void;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-gray-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
  primary: 'bg-primary/10 text-primary',
  secondary: 'bg-purple-100 text-purple-700',
};

const dotStyles: Record<BadgeVariant, string> = {
  default: 'bg-gray-500',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  error: 'bg-red-500',
  info: 'bg-blue-500',
  primary: 'bg-primary',
  secondary: 'bg-purple-500',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-base px-3 py-1',
};

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  removable = false,
  onRemove,
  className = '',
}) => {
  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-full
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full mr-1.5 ${dotStyles[variant]}`}
        />
      )}
      {children}
      {removable && (
        <button
          type="button"
          onClick={onRemove}
          className="ml-1 -mr-1 h-4 w-4 rounded-full inline-flex items-center justify-center hover:bg-black/10 transition-colors"
        >
          <svg
            className="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </span>
  );
};

interface StatusBadgeProps {
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  size?: BadgeSize;
  className?: string;
}

const statusConfig: Record<StatusBadgeProps['status'], { label: string; variant: BadgeVariant }> = {
  pending: { label: '等待中', variant: 'default' },
  processing: { label: '处理中', variant: 'info' },
  completed: { label: '已完成', variant: 'success' },
  failed: { label: '失败', variant: 'error' },
  cancelled: { label: '已取消', variant: 'warning' },
};

const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  className = '',
}) => {
  const config = statusConfig[status];
  return (
    <Badge variant={config.variant} size={size} dot className={className}>
      {config.label}
    </Badge>
  );
};

interface MembershipBadgeProps {
  level: 'free' | 'basic' | 'pro' | 'enterprise';
  className?: string;
}

const membershipConfig: Record<MembershipBadgeProps['level'], { label: string; variant: BadgeVariant }> = {
  free: { label: '免费版', variant: 'default' },
  basic: { label: '基础版', variant: 'info' },
  pro: { label: '专业版', variant: 'primary' },
  enterprise: { label: '企业版', variant: 'secondary' },
};

const MembershipBadge: React.FC<MembershipBadgeProps> = ({
  level,
  className = '',
}) => {
  const config = membershipConfig[level];
  return (
    <Badge variant={config.variant} size="sm" className={className}>
      {config.label}
    </Badge>
  );
};

export { Badge, StatusBadge, MembershipBadge };
export default Badge;
