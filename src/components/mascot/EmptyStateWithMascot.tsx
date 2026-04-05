import React from 'react';
import { motion } from 'framer-motion';
import Mascot, { MascotEmotion, MascotPose, MascotSize } from './Mascot';

export type EmptyStateType = 
  | 'welcome' 
  | 'no-tasks' 
  | 'no-results' 
  | 'no-data' 
  | 'error'
  | 'custom';

interface EmptyStateWithMascotProps {
  type?: EmptyStateType;
  title?: string;
  description?: string;
  emotion?: MascotEmotion;
  pose?: MascotPose;
  size?: MascotSize;
  action?: React.ReactNode;
  actionText?: string;
  onAction?: () => void;
  actionHref?: string;
  message?: string;
  showBubble?: boolean;
  className?: string;
}

const defaultConfigs: Record<EmptyStateType, {
  title: string;
  description: string;
  emotion: MascotEmotion;
  pose: MascotPose;
  message: string;
}> = {
  'welcome': {
    title: '欢迎使用房都督AI',
    description: '创建您的第一个房产分析任务，开启智能分析之旅',
    emotion: 'happy',
    pose: 'sitting',
    message: '欢迎！点击"开始分析"创建你的第一个房产报告吧～',
  },
  'no-tasks': {
    title: '暂无分析任务',
    description: '点击下方按钮创建新的分析任务',
    emotion: 'default',
    pose: 'pointing',
    message: '点击"新建任务"开始你的房产分析吧！',
  },
  'no-results': {
    title: '没有找到匹配的结果',
    description: '换个关键词试试，或调整筛选条件',
    emotion: 'confused',
    pose: 'standing',
    message: '没有找到匹配的任务，换个关键词试试？',
  },
  'no-data': {
    title: '暂无数据',
    description: '这里还没有任何内容',
    emotion: 'thinking',
    pose: 'standing',
    message: '这里空空如也～',
  },
  'error': {
    title: '出错了',
    description: '请稍后重试，或联系客服获取帮助',
    emotion: 'comforting',
    pose: 'standing',
    message: '别担心，让我来帮你解决这个问题～',
  },
  'custom': {
    title: '',
    description: '',
    emotion: 'default',
    pose: 'standing',
    message: '',
  },
};

const EmptyStateWithMascot: React.FC<EmptyStateWithMascotProps> = ({
  type = 'no-data',
  title,
  description,
  emotion,
  pose,
  size = 'xl',
  action,
  actionText,
  onAction,
  actionHref,
  message,
  showBubble = true,
  className = '',
}) => {
  const config = defaultConfigs[type];

  const finalTitle = title || config.title;
  const finalDescription = description || config.description;
  const finalEmotion = emotion || config.emotion;
  const finalPose = pose || config.pose;
  const finalMessage = message || config.message;

  const renderAction = () => {
    if (action) return action;

    if (actionText && (onAction || actionHref)) {
      if (actionHref) {
        return (
          <motion.a
            href={actionHref}
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white font-medium rounded-xl hover:bg-primary-700 transition-colors"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {actionText}
          </motion.a>
        );
      }

      return (
        <motion.button
          onClick={onAction}
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white font-medium rounded-xl hover:bg-primary-700 transition-colors"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {actionText}
        </motion.button>
      );
    }

    return null;
  };

  return (
    <motion.div
      className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex flex-col items-center gap-6 max-w-md">
        <div className="relative">
          <motion.div
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          >
            <Mascot
              emotion={finalEmotion}
              pose={finalPose}
              size={size}
              animate
            />
          </motion.div>

          {showBubble && finalMessage && (
            <motion.div
              className="absolute -right-4 top-0 transform translate-x-full -translate-y-2"
              initial={{ opacity: 0, scale: 0.8, x: -10 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.3 }}
            >
              <div className="relative bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-lg max-w-[200px]">
                <div className="absolute left-0 top-1/2 -translate-x-2 -translate-y-1/2 w-0 h-0 border-t-8 border-b-8 border-r-8 border-transparent border-r-white" />
                <div className="absolute left-0 top-1/2 -translate-x-2.5 -translate-y-1/2 w-0 h-0 border-t-8 border-b-8 border-r-8 border-transparent border-r-gray-200" />
                <p className="text-sm text-gray-700 leading-relaxed whitespace-nowrap">
                  {finalMessage}
                </p>
              </div>
            </motion.div>
          )}
        </div>

        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {finalTitle}
          </h3>
          <p className="text-gray-500 text-sm">
            {finalDescription}
          </p>
        </motion.div>

        {renderAction() && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            {renderAction()}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default EmptyStateWithMascot;

interface CompactEmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  mascotEmotion?: MascotEmotion;
  mascotSize?: MascotSize;
}

export const CompactEmptyState: React.FC<CompactEmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  mascotEmotion = 'confused',
  mascotSize = 'lg',
}) => {
  return (
    <motion.div
      className="flex flex-col items-center justify-center py-8 px-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {icon ? (
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          {icon}
        </div>
      ) : (
        <Mascot emotion={mascotEmotion} size={mascotSize} />
      )}
      <p className="text-gray-500 text-lg">{title}</p>
      {description && (
        <p className="text-gray-400 text-sm mt-1">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </motion.div>
  );
};

interface InlineEmptyStateProps {
  message: string;
  emotion?: MascotEmotion;
  size?: MascotSize;
  action?: React.ReactNode;
}

export const InlineEmptyState: React.FC<InlineEmptyStateProps> = ({
  message,
  emotion = 'thinking',
  size = 'md',
  action,
}) => {
  return (
    <motion.div
      className="flex items-center gap-3 py-4 px-4 bg-gray-50 rounded-xl"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <Mascot emotion={emotion} size={size} />
      <div className="flex-1">
        <p className="text-gray-600 text-sm">{message}</p>
      </div>
      {action && <div>{action}</div>}
    </motion.div>
  );
};
