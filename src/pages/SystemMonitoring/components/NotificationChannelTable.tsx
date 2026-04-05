import { motion } from 'framer-motion';
import {
  PencilIcon,
  TrashIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import type { NotificationChannel } from '../types';
import { NOTIFICATION_TYPE_LABELS } from '../types';

interface NotificationChannelTableProps {
  channels: NotificationChannel[];
  onAdd: () => void;
  onEdit: (channel: NotificationChannel) => void;
  onDelete: (id: string) => void;
  onTest: (id: string) => void;
  isTesting?: boolean;
}

export function NotificationChannelTable({
  channels,
  onAdd,
  onEdit,
  onDelete,
  onTest,
  isTesting,
}: NotificationChannelTableProps) {
  const getConfigSummary = (channel: NotificationChannel) => {
    switch (channel.type) {
      case 'email':
        return channel.config.recipients?.join(', ') || '未配置';
      case 'webhook':
        return channel.config.webhookUrl || '未配置';
      case 'dingtalk':
      case 'wecom':
        return '已配置';
      default:
        return '未知';
    }
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
        <h3 className="text-sm font-medium text-white">通知渠道</h3>
        <button
          onClick={onAdd}
          className="px-3 py-1.5 bg-amber-500 text-slate-900 rounded-lg text-sm font-medium hover:bg-amber-400 transition-colors"
        >
          添加渠道
        </button>
      </div>

      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-700/50">
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              名称
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              类型
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              配置
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
              状态
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
              操作
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/30">
          {channels.map((channel, index) => (
            <motion.tr
              key={channel.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="hover:bg-slate-700/20 transition-colors"
            >
              <td className="px-4 py-3">
                <span className="text-sm text-white">{channel.name}</span>
              </td>
              <td className="px-4 py-3">
                <span className="px-2 py-1 text-xs bg-slate-700/50 text-slate-300 rounded">
                  {NOTIFICATION_TYPE_LABELS[channel.type]}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className="text-sm text-slate-400 truncate max-w-xs block">
                  {getConfigSummary(channel)}
                </span>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`px-2 py-1 text-xs rounded ${
                    channel.enabled
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-slate-700/50 text-slate-400'
                  }`}
                >
                  {channel.enabled ? '已启用' : '已禁用'}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onTest(channel.id)}
                    disabled={isTesting}
                    className="p-1.5 text-slate-400 hover:text-green-400 hover:bg-green-500/20 rounded-lg transition-colors disabled:opacity-50"
                    title="测试发送"
                  >
                    <PaperAirplaneIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onEdit(channel)}
                    className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onDelete(channel.id)}
                    className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </td>
            </motion.tr>
          ))}
          {channels.length === 0 && (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                暂无通知渠道
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default NotificationChannelTable;
