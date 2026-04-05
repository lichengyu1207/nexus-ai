import React from 'react';
import { motion } from 'framer-motion';

type EmptyStateType = 'no-data' | 'no-tasks' | 'no-reports' | 'no-messages';
type LoadingType = 'default' | 'analysis' | 'report' | 'search';

interface EmptyStateProps {
  type?: EmptyStateType;
  title?: string;
  message?: string;
  actionText?: string;
  onAction?: () => void;
}

interface LoadingStateProps {
  type?: LoadingType;
  message?: string;
}

interface NotFoundStateProps {
  onGoHome?: () => void;
}

const EMPTY_CONFIGS = {
  'no-data': {
    title: '还没有数据哦',
    message: '主公快来创建任务吧',
    duduAction: 'confused',
  },
  'no-tasks': {
    title: '暂无分析任务',
    message: '点击下方按钮开始您的第一次房产分析',
    duduAction: 'wave',
  },
  'no-reports': {
    title: '暂无报告记录',
    message: '完成分析后，报告将显示在这里',
    duduAction: 'think',
  },
  'no-messages': {
    title: '暂无消息',
    message: '与都督的对话将显示在这里',
    duduAction: 'wave',
  },
};

const LOADING_CONFIGS = {
  default: {
    message: '都督正在推演中...',
    duduAction: 'think',
  },
  analysis: {
    message: '正在分析房产数据...',
    duduAction: 'think',
  },
  report: {
    message: '正在生成报告...',
    duduAction: 'think',
  },
  search: {
    message: '正在搜索房源信息...',
    duduAction: 'think',
  },
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  type = 'no-data',
  title,
  message,
  actionText,
  onAction,
}) => {
  const config = EMPTY_CONFIGS[type];

  return (
    <motion.div
      className="flex flex-col items-center justify-center py-12 px-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* 嘟嘟形象 */}
      <motion.div
        className="relative mb-6"
        animate={{
          y: [0, -10, 0],
          rotate: [0, -5, 5, 0],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          repeatType: 'reverse',
        }}
      >
        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg">
          <span className="text-5xl">🐼</span>
        </div>
        
        <motion.div
          className="absolute -top-2 -right-2 text-2xl"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          {config.duduAction === 'confused' ? '😵' : '🤔'}
        </motion.div>
      </motion.div>

      {/* 文字 */}
      <h3 className="text-lg font-medium text-gray-700 mb-2">
        {title || config.title}
      </h3>
      <p className="text-sm text-gray-500 text-center max-w-xs mb-4">
        {message || config.message}
      </p>

      {/* 操作按钮 */}
      {actionText && onAction && (
        <motion.button
          onClick={onAction}
          className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {actionText}
        </motion.button>
      )}
    </motion.div>
  );
};

export const LoadingState: React.FC<LoadingStateProps> = ({
  type = 'default',
  message,
}) => {
  const config = LOADING_CONFIGS[type];

  return (
    <motion.div
      className="flex flex-col items-center justify-center py-12 px-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {/* 嘟嘟旋转动画 */}
      <motion.div
        className="relative mb-6"
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      >
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg">
          <span className="text-4xl">🐼</span>
        </div>
      </motion.div>

      {/* 加载点 */}
      <div className="flex space-x-1 mb-4">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 rounded-full bg-amber-500"
            animate={{ scale: [1, 1.5, 1] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.2,
            }}
          />
        ))}
      </div>

      {/* 文字 */}
      <p className="text-sm text-gray-500">{message || config.message}</p>
    </motion.div>
  );
};

export const NotFoundState: React.FC<NotFoundStateProps> = ({ onGoHome }) => {
  return (
    <motion.div
      className="flex flex-col items-center justify-center min-h-[60vh] px-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {/* 404 数字 */}
      <motion.div
        className="text-8xl font-bold text-gray-200 mb-4"
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        404
      </motion.div>

      {/* 嘟嘟迷路形象 */}
      <motion.div
        className="relative mb-6"
        animate={{ rotate: [-5, 5, -5] }}
        transition={{ duration: 1, repeat: Infinity }}
      >
        <div className="w-32 h-32 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg">
          <span className="text-6xl">🐼</span>
        </div>
        
        <motion.div
          className="absolute top-0 right-0 text-3xl"
          animate={{ rotate: [0, 20, 0] }}
          transition={{ duration: 0.5, repeat: Infinity }}
        >
          🗺️
        </motion.div>
      </motion.div>

      {/* 气泡消息 */}
      <motion.div
        className="bg-white rounded-xl shadow-lg px-6 py-4 mb-6 relative"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.3 }}
      >
        <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-4 h-4 bg-white rotate-45" />
        <p className="text-gray-700 text-center">
          主公，嘟嘟找不到这个页面了...
        </p>
        <p className="text-gray-400 text-sm text-center mt-1">
          可能是迷路了，要不要回家看看？
        </p>
      </motion.div>

      {/* 返回按钮 */}
      <motion.button
        onClick={onGoHome || (() => window.location.href = '/')}
        className="px-6 py-3 bg-primary-600 text-white rounded-xl font-medium shadow-lg"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        🏠 返回首页
      </motion.button>
    </motion.div>
  );
};

export default EmptyState;
