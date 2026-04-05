import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  InformationCircleIcon,
  ShareIcon,
  ClockIcon,
  ChartBarIcon,
  LockClosedIcon,
  ArrowPathIcon,
  TrashIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { formatDistanceToNow, format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import type { AssetDetail, AssetVersion, Permission } from '../types';
import { ASSET_TYPE_CONFIG, ACCESS_LEVEL_CONFIG } from '../types';
import { useAssetDetail } from '../hooks/useAssetDetail';
import { LineageGraph } from './LineageGraph';
import { QualityDashboard } from './QualityDashboard';

export interface AssetDetailDrawerProps {
  assetId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: (asset: AssetDetail) => void;
  onDelete?: (asset: AssetDetail) => void;
}

type TabKey = 'overview' | 'lineage' | 'versions' | 'quality' | 'permissions';

const TABS: { key: TabKey; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { key: 'overview', label: '概览', icon: InformationCircleIcon },
  { key: 'lineage', label: '血缘', icon: ShareIcon },
  { key: 'versions', label: '版本', icon: ClockIcon },
  { key: 'quality', label: '质量', icon: ChartBarIcon },
  { key: 'permissions', label: '权限', icon: LockClosedIcon },
];

const QualityStars = ({ score }: { score?: number }) => {
  if (score === undefined) return <span className="text-gray-500">-</span>;
  const fullStars = Math.floor(score / 20);
  const hasHalf = score % 20 >= 10;

  return (
    <div className="flex items-center gap-0.5">
      {[...Array(5)].map((_, i) => (
        <span
          key={i}
          className={`text-sm ${
            i < fullStars
              ? 'text-amber-400'
              : i === fullStars && hasHalf
                ? 'text-amber-400/50'
                : 'text-gray-600'
          }`}
        >
          ★
        </span>
      ))}
      <span className="ml-1 text-xs text-gray-400">{score}%</span>
    </div>
  );
};

export function AssetDetailDrawer({
  assetId,
  isOpen,
  onClose,
  onEdit,
  onDelete,
}: AssetDetailDrawerProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const {
    detail,
    versions,
    permissions,
    isLoading,
    restoreVersion,
    isRestoring,
  } = useAssetDetail(assetId);

  const handleRestoreVersion = useCallback(
    (version: number) => {
      if (assetId) {
        restoreVersion({ assetId, version });
      }
    },
    [assetId, restoreVersion]
  );

  const handleEdit = useCallback(() => {
    if (detail && onEdit) {
      onEdit(detail);
    }
  }, [detail, onEdit]);

  const handleDelete = useCallback(() => {
    if (detail && onDelete) {
      onDelete(detail);
      setShowDeleteConfirm(false);
      onClose();
    }
  }, [detail, onDelete, onClose]);

  const handleExport = useCallback(() => {
    if (detail) {
      console.log('Exporting asset:', detail.id);
    }
  }, [detail]);

  if (!assetId) return null;

  const config = detail ? ASSET_TYPE_CONFIG[detail.type] : null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-[500px] bg-gray-900 border-l border-white/10 shadow-2xl z-50 flex flex-col"
          >
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                {config && (
                  <span className={`text-2xl ${config.color}`}>
                    {config.icon === 'DatabaseIcon' && '🗄️'}
                    {config.icon === 'TableCellsIcon' && '📊'}
                    {config.icon === 'BookOpenIcon' && '📚'}
                  </span>
                )}
                <div>
                  <h2 className="text-lg font-semibold text-white">
                    {isLoading ? '加载中...' : detail?.name ?? '资产详情'}
                  </h2>
                  {config && (
                    <span className={`text-xs ${config.color}`}>{config.label}</span>
                  )}
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <div className="flex border-b border-white/10 overflow-x-auto">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`
                    flex items-center gap-1.5 px-4 py-3 text-sm font-medium whitespace-nowrap
                    transition-colors relative
                    ${activeTab === tab.key ? 'text-amber-400' : 'text-gray-400 hover:text-white'}
                  `}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                  {activeTab === tab.key && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400"
                    />
                  )}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {isLoading ? (
                <div className="flex items-center justify-center h-32">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"
                  />
                </div>
              ) : detail ? (
                <>
                  {activeTab === 'overview' && (
                    <div className="space-y-6">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-white/5 rounded-lg p-3">
                          <span className="text-xs text-gray-500">创建时间</span>
                          <p className="text-sm text-white mt-1">
                            {format(new Date(detail.createdAt), 'yyyy-MM-dd HH:mm', {
                              locale: zhCN,
                            })}
                          </p>
                        </div>
                        <div className="bg-white/5 rounded-lg p-3">
                          <span className="text-xs text-gray-500">最后更新</span>
                          <p className="text-sm text-white mt-1">
                            {formatDistanceToNow(new Date(detail.updatedAt), {
                              addSuffix: true,
                              locale: zhCN,
                            })}
                          </p>
                        </div>
                        <div className="bg-white/5 rounded-lg p-3">
                          <span className="text-xs text-gray-500">所有者</span>
                          <p className="text-sm text-white mt-1">{detail.owner}</p>
                        </div>
                        <div className="bg-white/5 rounded-lg p-3">
                          <span className="text-xs text-gray-500">当前版本</span>
                          <p className="text-sm text-white mt-1">v{detail.version}</p>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-sm font-medium text-gray-400 mb-2">描述</h3>
                        <p className="text-sm text-white bg-white/5 rounded-lg p-3">
                          {detail.description || '暂无描述'}
                        </p>
                      </div>

                      <div>
                        <h3 className="text-sm font-medium text-gray-400 mb-2">标签</h3>
                        <div className="flex flex-wrap gap-2">
                          {detail.tags.length > 0 ? (
                            detail.tags.map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-1 text-xs bg-amber-500/20 text-amber-400 rounded"
                              >
                                {tag}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-gray-500">暂无标签</span>
                          )}
                        </div>
                      </div>

                      <div>
                        <h3 className="text-sm font-medium text-gray-400 mb-2">质量评分</h3>
                        <QualityStars score={detail.qualityScore} />
                      </div>

                      {detail.previewData && detail.previewData.length > 0 && (
                        <div>
                          <h3 className="text-sm font-medium text-gray-400 mb-2">数据预览</h3>
                          <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="border-b border-white/10">
                                  {Object.keys(detail.previewData[0]).map((key) => (
                                    <th
                                      key={key}
                                      className="px-2 py-1 text-left text-gray-400 font-medium"
                                    >
                                      {key}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {detail.previewData.slice(0, 5).map((row, i) => (
                                  <tr key={i} className="border-b border-white/5">
                                    {Object.values(row).map((value, j) => (
                                      <td key={j} className="px-2 py-1 text-gray-300">
                                        {String(value).slice(0, 30)}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'lineage' && (
                    <LineageGraph assetId={assetId} height={400} />
                  )}

                  {activeTab === 'versions' && (
                    <div className="space-y-3">
                      {versions.map((version) => (
                        <motion.div
                          key={version.version}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={`
                            p-3 rounded-lg border transition-colors
                            ${
                              version.version === detail.version
                                ? 'bg-amber-500/10 border-amber-500/30'
                                : 'bg-white/5 border-white/10 hover:border-white/20'
                            }
                          `}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-white">
                              v{version.version}
                              {version.version === detail.version && (
                                <span className="ml-2 text-xs text-amber-400">(当前)</span>
                              )}
                            </span>
                            <span className="text-xs text-gray-500">
                              {format(new Date(version.createdAt), 'yyyy-MM-dd HH:mm', {
                                locale: zhCN,
                              })}
                            </span>
                          </div>
                          <p className="text-xs text-gray-400 mb-2">
                            {version.changeSummary}
                          </p>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500">
                              by {version.createdBy}
                            </span>
                            {version.version !== detail.version && (
                              <button
                                onClick={() => handleRestoreVersion(version.version)}
                                disabled={isRestoring}
                                className="flex items-center gap-1 px-2 py-1 text-xs text-amber-400 hover:bg-amber-500/10 rounded transition-colors disabled:opacity-50"
                              >
                                <ArrowPathIcon className="w-3 h-3" />
                                回滚
                              </button>
                            )}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}

                  {activeTab === 'quality' && <QualityDashboard assetId={assetId} />}

                  {activeTab === 'permissions' && (
                    <div className="space-y-3">
                      {permissions.map((permission) => {
                        const accessConfig = ACCESS_LEVEL_CONFIG[permission.accessLevel];
                        return (
                          <div
                            key={permission.id}
                            className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-sm text-white">
                                {permission.principalName}
                              </span>
                              <span className="text-xs text-gray-500">
                                {permission.principalType === 'user' ? '用户' : '智能体'}
                              </span>
                            </div>
                            <span className={`text-xs ${accessConfig.color}`}>
                              {accessConfig.label}
                            </span>
                          </div>
                        );
                      })}
                      <button className="w-full py-2 text-sm text-amber-400 hover:bg-amber-500/10 rounded-lg transition-colors">
                        + 添加权限
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center h-32 text-gray-400">
                  资产不存在或已删除
                </div>
              )}
            </div>

            {detail && (
              <div className="flex items-center gap-2 p-4 border-t border-white/10">
                <button
                  onClick={handleEdit}
                  className="flex-1 py-2 text-sm font-medium bg-amber-500 text-gray-900 rounded-lg hover:bg-amber-400 transition-colors"
                >
                  编辑
                </button>
                <button
                  onClick={handleExport}
                  className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                  title="导出"
                >
                  <ArrowDownTrayIcon className="w-5 h-5 text-gray-400" />
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 transition-colors"
                  title="删除"
                >
                  <TrashIcon className="w-5 h-5 text-red-400" />
                </button>
              </div>
            )}
          </motion.div>

          <AnimatePresence>
            {showDeleteConfirm && (
              <>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 bg-black/50 z-50"
                />
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 bg-gray-800 border border-white/10 rounded-xl shadow-2xl z-50 p-4"
                >
                  <h3 className="text-lg font-semibold text-white mb-2">确认删除</h3>
                  <p className="text-sm text-gray-400 mb-4">
                    确定要删除资产 "{detail?.name}" 吗？此操作不可撤销。
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="flex-1 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                    >
                      取消
                    </button>
                    <button
                      onClick={handleDelete}
                      className="flex-1 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-400 transition-colors"
                    >
                      删除
                    </button>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </>
      )}
    </AnimatePresence>
  );
}
