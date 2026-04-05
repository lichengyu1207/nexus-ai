import React from 'react';
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  PlusCircleIcon,
  MinusCircleIcon,
  ArrowsRightLeftIcon,
} from '@heroicons/react/24/outline';
import { ReportContent } from '@/services/reports';

interface DiffResult {
  sections: Record<string, {
    status: 'added' | 'removed' | 'modified';
    current: unknown;
    compare: unknown;
  }>;
  summary: {
    status: 'modified';
    current: unknown;
    compare: unknown;
  } | null;
  added: string[];
  removed: string[];
  modified: string[];
}

interface ReportCompareProps {
  currentContent: ReportContent;
  compareContent: ReportContent;
  currentVersion: number;
  compareVersion: number;
  diff: DiffResult;
}

const sectionLabels: Record<string, string> = {
  summary: '执行摘要',
  key_findings: '核心发现',
  detailed_analysis: '详细分析',
  investment_advice: '投资建议',
  risk_warning: '风险提示',
  data_sources: '数据来源',
};

const ReportCompare: React.FC<ReportCompareProps> = ({
  currentContent,
  compareContent,
  currentVersion,
  compareVersion,
  diff,
}) => {
  const getSectionStatusBadge = (section: string) => {
    const sectionDiff = diff.sections[section];
    if (!sectionDiff) return null;

    const configs = {
      added: {
        icon: <PlusCircleIcon className="w-4 h-4" />,
        text: '新增',
        bg: 'bg-green-100',
        color: 'text-green-700',
      },
      removed: {
        icon: <MinusCircleIcon className="w-4 h-4" />,
        text: '删除',
        bg: 'bg-red-100',
        color: 'text-red-700',
      },
      modified: {
        icon: <ArrowsRightLeftIcon className="w-4 h-4" />,
        text: '修改',
        bg: 'bg-yellow-100',
        color: 'text-yellow-700',
      },
    };

    const config = configs[sectionDiff.status];
    if (!config) return null;

    return (
      <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.color}`}>
        {config.icon}
        {config.text}
      </span>
    );
  };

  const renderSectionDiff = (sectionKey: string) => {
    const sectionDiff = diff.sections[sectionKey];
    const currentSection = currentContent?.sections?.[sectionKey as keyof typeof currentContent.sections];
    const compareSection = compareContent?.sections?.[sectionKey as keyof typeof compareContent.sections];

    if (!sectionDiff && !currentSection && !compareSection) return null;

    return (
      <div key={sectionKey} className="border-b border-gray-100 last:border-b-0">
        <div className="flex items-center justify-between p-4 bg-gray-50">
          <h4 className="font-medium text-gray-900">
            {sectionLabels[sectionKey] || sectionKey}
          </h4>
          {getSectionStatusBadge(sectionKey)}
        </div>

        <div className="grid grid-cols-2 divide-x divide-gray-100">
          {/* Current Version */}
          <div className={`p-4 ${sectionDiff?.status === 'added' ? 'bg-green-50' : ''}`}>
            <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
              <span className="font-medium">版本 {currentVersion}</span>
              {sectionDiff?.status === 'added' && (
                <span className="text-green-600">(新增)</span>
              )}
            </div>
            {currentSection ? (
              <div className="text-sm text-gray-700">
                {renderSectionContent(sectionKey, currentSection)}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">无内容</p>
            )}
          </div>

          {/* Compare Version */}
          <div className={`p-4 ${sectionDiff?.status === 'removed' ? 'bg-red-50' : ''}`}>
            <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
              <span className="font-medium">版本 {compareVersion}</span>
              {sectionDiff?.status === 'removed' && (
                <span className="text-red-600">(已删除)</span>
              )}
            </div>
            {compareSection ? (
              <div className="text-sm text-gray-700">
                {renderSectionContent(sectionKey, compareSection)}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">无内容</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderSectionContent = (sectionKey: string, content: unknown) => {
    if (!content) return <span className="text-gray-400">-</span>;

    switch (sectionKey) {
      case 'summary':
        const summary = content as { text?: string };
        return <p>{summary?.text || '-'}</p>;

      case 'key_findings':
        const findings = content as Array<{ title: string; description: string }>;
        if (Array.isArray(findings)) {
          return (
            <ul className="space-y-1">
              {findings.map((f, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="font-medium text-gray-900">{f.title}:</span>
                  <span className="text-gray-600">{f.description}</span>
                </li>
              ))}
            </ul>
          );
        }
        return <span>{JSON.stringify(content)}</span>;

      case 'risk_warning':
        const warnings = content as string[];
        if (Array.isArray(warnings)) {
          return (
            <ul className="space-y-1">
              {warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          );
        }
        return <span>{JSON.stringify(content)}</span>;

      case 'detailed_analysis':
      case 'investment_advice':
      case 'data_sources':
        return (
          <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
            {JSON.stringify(content, null, 2)}
          </pre>
        );

      default:
        return <span>{JSON.stringify(content)}</span>;
    }
  };

  const allSections = Object.keys(sectionLabels);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h3 className="font-semibold text-gray-900">版本对比</h3>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded">
                版本 {currentVersion}
              </span>
              <ArrowRightIcon className="w-4 h-4" />
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                版本 {compareVersion}
              </span>
            </div>
          </div>
          
          {/* Diff Summary */}
          <div className="flex items-center gap-3 text-xs">
            {diff.added.length > 0 && (
              <span className="flex items-center gap-1 text-green-600">
                <PlusCircleIcon className="w-3 h-3" />
                {diff.added.length} 新增
              </span>
            )}
            {diff.removed.length > 0 && (
              <span className="flex items-center gap-1 text-red-600">
                <MinusCircleIcon className="w-3 h-3" />
                {diff.removed.length} 删除
              </span>
            )}
            {diff.modified.length > 0 && (
              <span className="flex items-center gap-1 text-yellow-600">
                <ArrowsRightLeftIcon className="w-3 h-3" />
                {diff.modified.length} 修改
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Column Headers */}
        <div className="grid grid-cols-2 divide-x divide-gray-100 bg-gray-50 border-b border-gray-100">
          <div className="p-3 text-center">
            <span className="font-medium text-gray-900">版本 {currentVersion}</span>
            <span className="text-xs text-gray-500 ml-2">(当前)</span>
          </div>
          <div className="p-3 text-center">
            <span className="font-medium text-gray-900">版本 {compareVersion}</span>
            <span className="text-xs text-gray-500 ml-2">(对比)</span>
          </div>
        </div>

        {/* Sections */}
        <div className="divide-y divide-gray-100">
          {allSections.map(renderSectionDiff)}
        </div>
      </div>
    </div>
  );
};

export default ReportCompare;
