import { motion, memo } from 'framer-motion';
import {
  ClipboardDocumentCheckIcon,
  BellAlertIcon,
  UserGroupIcon,
  MegaphoneIcon,
  KeyIcon,
  CheckIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import type { Notification, NotificationType } from './types';
import { NOTIFICATION_TYPE_CONFIG } from './types';

export interface NotificationItemProps {
  notification: Notification;
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
  onClick?: (notification: Notification) => void;
}

const IconMap: Record<NotificationType, React.ComponentType<{ className?: string }>> = {
  task_status: ClipboardDocumentCheckIcon,
  agent_alert: BellAlertIcon,
  collaboration: UserGroupIcon,
  system_announce: MegaphoneIcon,
  permission_change: KeyIcon,
};

const NotificationItemComponent = ({ notification, onMarkRead, onDelete, onClick }: NotificationItemProps) {
  const config = NOTIFICATION_TYPE_CONFIG[notification.type];
  const Icon = IconMap[notification.type];

  const timeAgo = formatDistanceToNow(new Date(notification.createdAt), {
    addSuffix: true,
    locale: zhCN,
  });

  const handleClick = () => {
    if (!notification.read) {
      onMarkRead(notification.id);
    }
    onClick?.(notification);
  };

  const handleMarkRead = (e: React.MouseEvent) => {
    e.stopPropagation();
    onMarkRead(notification.id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(notification.id);
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -100 }}
      className={`
        group relative flex items-start gap-3 p-3 rounded-lg cursor-pointer
        transition-colors hover:bg-white/5
        ${!notification.read ? 'bg-white/5' : ''}
      `}
      onClick={handleClick}
      role="listitem"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          handleClick();
        }
      }}
    >
      {!notification.read && (
        <span className="absolute left-1 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-amber-400" />
      )}

      <div className={`p-2 rounded-lg ${config.bgColor}`}>
        <Icon className={`w-5 h-5 ${config.color}`} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4
            className={`text-sm truncate ${!notification.read ? 'font-semibold text-white' : 'text-gray-300'}`}
          >
            {notification.title}
          </h4>
          <span className="text-xs text-gray-500 shrink-0">{timeAgo}</span>
        </div>

        <p className="text-xs text-gray-400 mt-1 line-clamp-2">{notification.content}</p>

        <span
          className={`inline-block mt-1 text-xs px-2 py-0.5 rounded ${config.bgColor} ${config.color}`}
        >
          {config.label}
        </span>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {!notification.read && (
          <button
            onClick={handleMarkRead}
            className="p-1 rounded hover:bg-white/10 transition-colors"
            aria-label="标记已读"
          >
            <CheckIcon className="w-4 h-4 text-gray-400 hover:text-green-400" />
          </button>
        )}
        <button
          onClick={handleDelete}
          className="p-1 rounded hover:bg-white/10 transition-colors"
          aria-label="删除通知"
        >
          <TrashIcon className="w-4 h-4 text-gray-400 hover:text-red-400" />
        </button>
      </div>
    </motion.div>
  );
};

export const NotificationItem = memo(NotificationItemComponent);
