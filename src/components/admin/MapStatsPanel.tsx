import React from 'react';
import {
  MapPinIcon,
  UserIcon,
  DocumentTextIcon,
  HeartIcon,
  SparklesIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { MapStats } from '@/api/admin/map';

interface MapStatsPanelProps {
  stats: MapStats | null;
  onSourceFilter: (source: string | null) => void;
  activeSource: string | null;
}

const SOURCE_CONFIG: Record<string, { label: string; icon: React.FC<{ className?: string }>; color: string }> = {
  registration: { label: '注册地址', icon: UserIcon, color: 'bg-blue-500' },
  interest: { label: '兴趣地址', icon: HeartIcon, color: 'bg-pink-500' },
  report: { label: '报告地址', icon: DocumentTextIcon, color: 'bg-green-500' },
};

const MapStatsPanel: React.FC<MapStatsPanelProps> = ({ stats, onSourceFilter, activeSource }) => {
  if (!stats) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
        </div>
      </div>
    );
  }

  const totalBySource = Object.values(stats.by_source).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-4">
      {/* Total Stats */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <div className="flex items-center gap-2 mb-3">
          <MapPinIcon className="w-5 h-5 text-primary-500" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">位置统计</h3>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.total_locations.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">总位置数</p>
          </div>
          
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.geocoded_locations.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">已编码</p>
          </div>
        </div>
        
        <div className="mt-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 flex items-center gap-2">
          <SparklesIcon className="w-5 h-5 text-yellow-500" />
          <div>
            <p className="text-lg font-bold text-yellow-700 dark:text-yellow-400">
              {stats.new_communities_last_30d}
            </p>
            <p className="text-xs text-yellow-600 dark:text-yellow-500">近30天新小区</p>
          </div>
        </div>
      </div>

      {/* By Source */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <div className="flex items-center gap-2 mb-3">
          <ChartBarIcon className="w-5 h-5 text-primary-500" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">按来源分布</h3>
        </div>
        
        <div className="space-y-2">
          {Object.entries(stats.by_source).map(([source, count]) => {
            const config = SOURCE_CONFIG[source] || { 
              label: source, 
              icon: MapPinIcon, 
              color: 'bg-gray-500' 
            };
            const percentage = totalBySource > 0 ? (count / totalBySource) * 100 : 0;
            const isActive = activeSource === source;
            
            return (
              <button
                key={source}
                onClick={() => onSourceFilter(isActive ? null : source)}
                className={`w-full text-left p-2 rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-primary-50 dark:bg-primary-900/30 ring-2 ring-primary-500' 
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${config.color}`} />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {config.label}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {count.toLocaleString()}
                  </span>
                </div>
                
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${config.color} transition-all`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  {percentage.toFixed(1)}%
                </p>
              </button>
            );
          })}
        </div>
        
        {activeSource && (
          <button
            onClick={() => onSourceFilter(null)}
            className="w-full mt-2 text-sm text-primary-600 dark:text-primary-400 hover:underline"
          >
            清除筛选
          </button>
        )}
      </div>

      {/* Top Cities */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Top 10 城市
        </h3>
        
        <div className="space-y-2">
          {stats.top_cities.map((city, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400 dark:text-gray-500 w-4">
                  {index + 1}
                </span>
                <span className="text-sm text-gray-900 dark:text-white">
                  {city.name}
                </span>
              </div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {city.count.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Provinces */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Top 10 省份
        </h3>
        
        <div className="space-y-2">
          {stats.top_provinces.map((province, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400 dark:text-gray-500 w-4">
                  {index + 1}
                </span>
                <span className="text-sm text-gray-900 dark:text-white">
                  {province.name}
                </span>
              </div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {province.count.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MapStatsPanel;
