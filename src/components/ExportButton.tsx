import React, { useState } from 'react';
import { ArrowDownTrayIcon, DocumentArrowDownIcon, TableCellsIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

type ExportFormat = 'csv' | 'excel';
type ExportType = 'tasks' | 'report';

interface ExportButtonProps {
  type: ExportType;
  reportId?: string;
  filters?: Record<string, string>;
  className?: string;
}

const ExportButton: React.FC<ExportButtonProps> = ({
  type,
  reportId,
  filters = {},
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(true);
    setIsOpen(false);

    try {
      let url = `/export/${type}`;
      const params = new URLSearchParams({ format });

      if (type === 'report' && reportId) {
        url = `/export/report/${reportId}`;
      } else if (type === 'tasks') {
        Object.entries(filters).forEach(([key, value]) => {
          if (value) params.append(key, value);
        });
      }

      const response = await api.get(url, {
        params,
        responseType: 'blob',
      });

      const contentDisposition = response.headers['content-disposition'];
      let filename = `export_${Date.now()}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?(.+)"?/);
        if (match) filename = match[1];
      }

      const blob = new Blob([response.data], {
        type: response.headers['content-type'],
      });

      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      showToast.success('导出成功');
    } catch {
      showToast.error('导出失败');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className={`relative ${className}`}>
      <div className="flex">
        <button
          onClick={() => handleExport('csv')}
          disabled={isExporting}
          className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-l-lg text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
        >
          {isExporting ? (
            <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
          ) : (
            <ArrowDownTrayIcon className="w-4 h-4" />
          )}
          导出
        </button>
        <button
          onClick={() => setIsOpen(!isOpen)}
          disabled={isExporting}
          className="px-2 py-2 bg-white dark:bg-gray-700 border border-l-0 border-gray-300 dark:border-gray-600 rounded-r-lg text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
        >
          <ChevronDownIcon className="w-4 h-4" />
        </button>
      </div>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-40 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-20">
            <button
              onClick={() => handleExport('csv')}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <TableCellsIcon className="w-4 h-4 text-gray-400" />
              CSV 格式
            </button>
            <button
              onClick={() => handleExport('excel')}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <DocumentArrowDownIcon className="w-4 h-4 text-green-500" />
              Excel 格式
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ExportButton;
