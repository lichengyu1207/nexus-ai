import React from 'react';
import { Button } from './Button';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

/**
 * 极简主义空状态组件
 * @param title 标题
 * @param description 描述
 * @param action 操作按钮文本
 * @param onAction 操作按钮点击回调
 * @param icon 自定义图标
 */
export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  action,
  onAction,
  icon = '📭'
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="text-text-secondary mb-2 text-4xl">{icon}</div>
      <h3 className="text-base font-medium">{title}</h3>
      <p className="text-sm text-text-secondary mt-1">{description}</p>
      {action && onAction && (
        <Button variant="primary" size="sm" className="mt-4" onClick={onAction}>
          {action}
        </Button>
      )}
    </div>
  );
};
