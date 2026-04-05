import React from 'react';
import {
  XMarkIcon,
  InformationCircleIcon,
  CheckBadgeIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

interface DataSourceInfo {
  name: string;
  type: string;
  label: string;
  icon: string;
  reliability: string;
  description: string;
  confidence: number;
  timestamp?: string;
  url?: string;
}

interface DataSourcesPanelProps {
  sources: DataSourceInfo[];
  summary?: {
    total_sources: number;
    high_confidence_count: number;
    estimated_count: number;
    overall_confidence: number;
  };
  onClose: () => void;
}

const SOURCE_TYPE_CONFIG: Record<string, { color: string; bgColor: string; borderColor: string }> = {
  government: { color: 'text-blue-700', bgColor: 'bg-blue-50', borderColor: 'border-blue-200' },
  market: { color: 'text-green-700', bgColor: 'bg-green-50', borderColor: 'border-green-200' },
  analysis: { color: 'text-purple-700', bgColor: 'bg-purple-50', borderColor: 'border-purple-200' },
  estimate: { color: 'text-amber-700', bgColor: 'bg-amber-50', borderColor: 'border-amber-200' },
  user_input: { color: 'text-gray-700', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' },
  gis: { color: 'text-teal-700', bgColor: 'bg-teal-50', borderColor: 'border-teal-200' },
  default: { color: 'text-gray-700', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' },
};

const DataSourcesPanel: React.FC<DataSourcesPanelProps> = ({ sources, summary, onClose }) => {
  const getTypeConfig = (type: string) => {
    return SOURCE_TYPE_CONFIG[type] || SOURCE_TYPE_CONFIG.default;
  };

  const getReliabilityIcon = (reliability: string) => {
    switch (reliability) {
      case 'high':
        return <CheckBadgeIcon className="w-5 h-5 text-green-600" />;
      case 'medium':
        return <InformationCircleIcon className="w-5 h-5 text-yellow-600" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />;
    }
  };

  const getConfidenceBar = (confidence: number) => {
    const percentage = confidence * 100;
    let barColor = 'bg-green-500';
    if (confidence < 0.7) barColor = 'bg-red-500';
    else if (confidence < 0.9) barColor = 'bg-yellow-500';

    return (
      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
        <div
          className={`${barColor} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  };

  const groupedSources = sources.reduce((acc, source) => {
    const type = source.type || 'default';
    if (!acc[type]) acc[type] = [];
    acc[type].push(source);
    return acc;
  }, {} as Record<string, DataSourceInfo[]>);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      
      <div className="relative w-full max-w-md h-full bg-white shadow-xl overflow-y-auto animate-slide-in-right">
        <div className="sticky top-0 bg-white border-b border-gray-100 p-4 z-10">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <InformationCircleIcon className="w-5 h-5 text-primary-600" />
              数据可信度报告
            </h2>
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <XMarkIcon className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {summary && (
          <div className="p-4 bg-gradient-to-r from-primary-50 to-blue-50 border-b border-gray-100">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                <div className="text-2xl font-bold text-primary-600">
                  {(summary.overall_confidence * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500 mt-1">综合可信度</div>
              </div>
              <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                <div className="text-2xl font-bold text-gray-700">
                  {summary.total_sources}
                </div>
                <div className="text-xs text-gray-500 mt-1">数据来源</div>
              </div>
            </div>
            
            <div className="flex items-center justify-center gap-4 mt-4 text-sm">
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-gray-600">高置信: {summary.high_confidence_count}</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span className="text-gray-600">估算: {summary.estimated_count}</span>
              </div>
            </div>
          </div>
        )}

        <div className="p-4 space-y-6">
          {Object.entries(groupedSources).map(([type, typeSources]) => {
            const config = getTypeConfig(type);
            
            return (
              <div key={type} className="space-y-3">
                <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bgColor} ${config.borderColor} border`}>
                  <span className="text-lg">{typeSources[0]?.icon || '📊'}</span>
                  <span className={`text-sm font-medium ${config.color}`}>
                    {typeSources[0]?.label || type}
                  </span>
                  <span className="text-xs text-gray-500">({typeSources.length})</span>
                </div>

                <div className="space-y-2">
                  {typeSources.map((source, index) => (
                    <div
                      key={`${type}-${index}`}
                      className="p-4 bg-gray-50 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium text-gray-900">{source.name}</h4>
                            {getReliabilityIcon(source.reliability)}
                          </div>
                          <p className="text-sm text-gray-500 mt-1">{source.description}</p>
                          
                          {source.timestamp && (
                            <div className="flex items-center gap-1 text-xs text-gray-400 mt-2">
                              <ClockIcon className="w-3 h-3" />
                              <span>更新于 {new Date(source.timestamp).toLocaleString('zh-CN')}</span>
                            </div>
                          )}
                        </div>
                        
                        <div className="text-right ml-4">
                          <div className={`text-lg font-bold ${
                            source.confidence >= 0.9 ? 'text-green-600' :
                            source.confidence >= 0.7 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {(source.confidence * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs text-gray-500">置信度</div>
                        </div>
                      </div>
                      
                      {getConfidenceBar(source.confidence)}
                      
                      {source.url && (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 mt-2"
                        >
                          <InformationCircleIcon className="w-3 h-3" />
                          查看原始数据
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        <div className="sticky bottom-0 bg-white border-t border-gray-100 p-4">
          <div className="bg-blue-50 rounded-lg p-3">
            <h4 className="text-sm font-medium text-blue-800 mb-2">可信度说明</h4>
            <div className="space-y-1 text-xs text-blue-700">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-green-500" />
                <span>高 (90%+): 官方数据、市场交易记录</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-yellow-500" />
                <span>中 (70-90%): 智能分析、模型预测</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-red-500" />
                <span>低 (&lt;70%): 估算数据、参考建议</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataSourcesPanel;
