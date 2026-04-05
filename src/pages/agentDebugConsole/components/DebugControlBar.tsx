import { motion } from 'framer-motion';
import {
  PlayIcon,
  PauseIcon,
  ForwardIcon,
  ArrowPathIcon,
  StopIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import type { AgentStatus } from '../types';
import { AGENT_STATUS_CONFIG } from '../types';

interface DebugControlBarProps {
  status: AgentStatus;
  isPaused: boolean;
  onPlay: () => void;
  onPause: () => void;
  onStep: () => void;
  onContinue: () => void;
  onRestart: () => void;
  onStop: () => void;
  isConnected?: boolean;
}

export function DebugControlBar({
  status,
  isPaused,
  onPlay,
  onPause,
  onStep,
  onContinue,
  onRestart,
  onStop,
  isConnected = false,
}: DebugControlBarProps) {
  const isRunning = status === 'running';
  const isStopped = status === 'stopped' || status === 'error';

  const controls = [
    {
      key: 'play',
      icon: PlayIcon,
      label: '运行',
      onClick: onPlay,
      disabled: isRunning && !isPaused,
      color: 'text-green-400 hover:bg-green-500/20',
      show: isStopped || isPaused,
    },
    {
      key: 'pause',
      icon: PauseIcon,
      label: '暂停',
      onClick: onPause,
      disabled: !isRunning || isPaused,
      color: 'text-amber-400 hover:bg-amber-500/20',
      show: isRunning && !isPaused,
    },
    {
      key: 'step',
      icon: ChevronRightIcon,
      label: '单步',
      onClick: onStep,
      disabled: !isPaused,
      color: 'text-blue-400 hover:bg-blue-500/20',
      show: true,
    },
    {
      key: 'continue',
      icon: ForwardIcon,
      label: '继续',
      onClick: onContinue,
      disabled: !isPaused,
      color: 'text-purple-400 hover:bg-purple-500/20',
      show: true,
    },
    {
      key: 'restart',
      icon: ArrowPathIcon,
      label: '重启',
      onClick: onRestart,
      disabled: isStopped,
      color: 'text-orange-400 hover:bg-orange-500/20',
      show: true,
    },
    {
      key: 'stop',
      icon: StopIcon,
      label: '停止',
      onClick: onStop,
      disabled: isStopped,
      color: 'text-red-400 hover:bg-red-500/20',
      show: true,
    },
  ];

  return (
    <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl">
      <div className="flex items-center gap-2 mr-4">
        <div
          className={`
            w-3 h-3 rounded-full
            ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}
          `}
        />
        <span className="text-xs text-slate-400">
          {isConnected ? '已连接' : '未连接'}
        </span>
        <span className="text-xs text-slate-600">|</span>
        <span className={`text-xs ${AGENT_STATUS_CONFIG[status].color}`}>
          {AGENT_STATUS_CONFIG[status].label}
        </span>
      </div>

      <div className="flex items-center gap-1">
        {controls
          .filter((c) => c.show)
          .map(({ key, icon: Icon, label, onClick, disabled, color }) => (
            <motion.button
              key={key}
              whileHover={{ scale: disabled ? 1 : 1.05 }}
              whileTap={{ scale: disabled ? 1 : 0.95 }}
              onClick={onClick}
              disabled={disabled}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                transition-colors
                ${disabled ? 'text-slate-600 cursor-not-allowed' : color}
              `}
              title={label}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{label}</span>
            </motion.button>
          ))}
      </div>

      <div className="flex-1" />

      <div className="flex items-center gap-2 text-xs text-slate-500">
        <kbd className="px-1.5 py-0.5 bg-slate-700/50 rounded">F5</kbd>
        <span>运行</span>
        <kbd className="px-1.5 py-0.5 bg-slate-700/50 rounded">F6</kbd>
        <span>暂停</span>
        <kbd className="px-1.5 py-0.5 bg-slate-700/50 rounded">F10</kbd>
        <span>单步</span>
      </div>
    </div>
  );
}
