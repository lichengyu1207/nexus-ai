import React, { useState } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { motion } from 'framer-motion';

interface PDFExportProps {
  containerRef: React.RefObject<HTMLDivElement>;
  fileName?: string;
  onBeforeGenerate?: () => void;
  onAfterGenerate?: () => void;
  onError?: (error: Error) => void;
}

export const PDFExport: React.FC<PDFExportProps> = ({
  containerRef,
  fileName = '任务对比报告',
  onBeforeGenerate,
  onAfterGenerate,
  onError,
}) => {
  const [isGenerating, setIsGenerating] = useState(false);

  const generatePDF = async () => {
    if (!containerRef.current) {
      onError?.(new Error('找不到报告容器'));
      return;
    }

    setIsGenerating(true);
    onBeforeGenerate?.();

    try {
      const canvas = await html2canvas(containerRef.current, {
        scale: 2,
        backgroundColor: '#0A0F1A',
        logging: false,
        useCORS: true,
        allowTaint: true,
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
        format: 'a4',
      });

      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth - 20;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      if (imgHeight > pageHeight - 20) {
        const scaledHeight = pageHeight - 20;
        const scaledWidth = (canvas.width * scaledHeight) / canvas.height;
        pdf.addImage(imgData, 'PNG', (pageWidth - scaledWidth) / 2, 10, scaledWidth, scaledHeight);
      } else {
        pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
      }

      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
      pdf.save(`${fileName}_${timestamp}.pdf`);
    } catch (error) {
      console.error('PDF生成失败', error);
      onError?.(error as Error);
    } finally {
      setIsGenerating(false);
      onAfterGenerate?.();
    }
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={generatePDF}
      disabled={isGenerating}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
        isGenerating
          ? 'bg-bg-tertiary text-text-disabled cursor-not-allowed'
          : 'bg-primary text-gray-900 hover:bg-primary-dark'
      }`}
    >
      {isGenerating ? (
        <>
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 0114.707"
            />
          </svg>
          生成中...
        </>
      ) : (
        <>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          导出 PDF
        </>
      )}
    </motion.button>
  );
};

export default PDFExport;
