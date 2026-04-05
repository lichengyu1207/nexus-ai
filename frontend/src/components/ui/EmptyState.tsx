import React from 'react';

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon = '📭',
  title,
  description,
  action,
  className = '',
}) => {
  return (
    <div className={`text-center py-12 ${className}`}>
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      {description && (
        <p className="text-gray-500 mb-4 max-w-sm mx-auto">{description}</p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-primaryDark transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};

export const NoDataState: React.FC<{ message?: string }> = ({ message = '暂无数据' }) => (
  <EmptyState icon="📊" title={message} />
);

export const NoResultsState: React.FC<{ query?: string; onReset?: () => void }> = ({
  query,
  onReset,
}) => (
  <EmptyState
    icon="🔍"
    title="未找到结果"
    description={query ? `没有找到与"${query}"相关的内容` : '没有找到匹配的内容'}
    action={onReset ? { label: '清除筛选', onClick: onReset } : undefined}
  />
);

export const ErrorState: React.FC<{ message?: string; onRetry?: () => void }> = ({
  message = '加载失败，请稍后重试',
  onRetry,
}) => (
  <EmptyState
    icon="❌"
    title="出错了"
    description={message}
    action={onRetry ? { label: '重试', onClick: onRetry } : undefined}
  />
);

export const NoPermissionState: React.FC = () => (
  <EmptyState
    icon="🔒"
    title="没有权限"
    description="您没有权限访问此内容"
  />
);

export const ComingSoonState: React.FC = () => (
  <EmptyState
    icon="🚧"
    title="即将推出"
    description="此功能正在开发中，敬请期待"
  />
);

export default EmptyState;
