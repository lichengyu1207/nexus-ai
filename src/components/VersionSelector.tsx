import React from 'react';
import {
  ChevronDownIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

export interface ReportVersion {
  id: string;
  version: number;
  status: string;
  summary: string | null;
  created_at: string | null;
  completed_at: string | null;
  parent_version_id: string | null;
}

interface VersionSelectorProps {
  versions: ReportVersion[];
  currentVersion: number;
  compareVersion: number | null;
  onVersionChange: (version: number) => void;
  onCompareChange: (version: number | null) => void;
  isComparing: boolean;
  onToggleCompare: () => void;
}

const VersionSelector: React.FC<VersionSelectorProps> = ({
  versions,
  currentVersion,
  compareVersion,
  onVersionChange,
  onCompareChange,
  isComparing,
  onToggleCompare,
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <ExclamationCircleIcon className="w-4 h-4 text-red-500" />;
      case 'generating':
        return <ArrowPathIcon className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (versions.length <= 1) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Current Version Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">当前版本:</label>
            <div className="relative">
              <select
                value={currentVersion}
                onChange={(e) => onVersionChange(Number(e.target.value))}
                className="appearance-none bg-gray-50 border border-gray-200 rounded-lg px-4 py-2 pr-8 text-sm font-medium focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {versions.map((v) => (
                  <option key={v.id} value={v.version}>
                    版本 {v.version}
                  </option>
                ))}
              </select>
              <ChevronDownIcon className="w-4 h-4 text-gray-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            {versions.find((v) => v.version === currentVersion) && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                {getStatusIcon(versions.find((v) => v.version === currentVersion)!.status)}
                <span>{formatDate(versions.find((v) => v.version === currentVersion)!.created_at)}</span>
              </div>
            )}
          </div>

          {/* Compare Toggle */}
          {isComparing && (
            <div className="flex items-center gap-2">
              <span className="text-gray-400">vs</span>
              <div className="relative">
                <select
                  value={compareVersion || ''}
                  onChange={(e) => onCompareChange(e.target.value ? Number(e.target.value) : null)}
                  className="appearance-none bg-gray-50 border border-gray-200 rounded-lg px-4 py-2 pr-8 text-sm font-medium focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">选择版本</option>
                  {versions
                    .filter((v) => v.version !== currentVersion)
                    .map((v) => (
                      <option key={v.id} value={v.version}>
                        版本 {v.version}
                      </option>
                    ))}
                </select>
                <ChevronDownIcon className="w-4 h-4 text-gray-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>
          )}
        </div>

        {/* Compare Button */}
        <button
          onClick={onToggleCompare}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            isComparing
              ? 'bg-primary-100 text-primary-700 hover:bg-primary-200'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <ArrowPathIcon className="w-4 h-4" />
          {isComparing ? '取消对比' : '版本对比'}
        </button>
      </div>

      {/* Version History */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <p className="text-xs text-gray-500 mb-2">版本历史</p>
        <div className="flex flex-wrap gap-2">
          {versions.map((v) => (
            <button
              key={v.id}
              onClick={() => onVersionChange(v.version)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                v.version === currentVersion
                  ? 'bg-primary-100 text-primary-700 ring-2 ring-primary-500'
                  : v.version === compareVersion
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
              }`}
            >
              {getStatusIcon(v.status)}
              <span>V{v.version}</span>
              <span className="text-gray-400">{formatDate(v.created_at)}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default VersionSelector;
