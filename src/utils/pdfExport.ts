import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

interface ExportOptions {
  taskId: string;
  filename?: string;
  title?: string;
  quality?: number;
}

const generateFilename = (taskId: string): string => {
  const date = new Date();
  const dateStr = date.toISOString().split('T')[0].replace(/-/g, '');
  return `房产分析报告_${taskId.slice(0, 8)}_${dateStr}.pdf`;
};

export const exportToPDF = async (
  element: HTMLElement,
  options: ExportOptions
): Promise<void> => {
  const { taskId, filename, title = '房产分析报告', quality = 2 } = options;
  
  const outputFilename = filename || generateFilename(taskId);
  
  try {
    const canvas = await html2canvas(element, {
      scale: quality,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#ffffff',
      logging: false,
      windowWidth: element.scrollWidth,
      windowHeight: element.scrollHeight,
    });
    
    const imgWidth = 210;
    const pageHeight = 297;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });
    
    const imgData = canvas.toDataURL('image/png', 1.0);
    
    let heightLeft = imgHeight;
    let position = 0;
    
    pdf.setFontSize(16);
    pdf.text(title, 105, 15, { align: 'center' });
    
    position = 25;
    heightLeft -= 25;
    
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;
    
    while (heightLeft > 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }
    
    pdf.save(outputFilename);
    
    return Promise.resolve();
  } catch (error) {
    console.error('PDF export failed:', error);
    return Promise.reject(error);
  }
};

export const exportReportToPDF = async (
  elementId: string,
  taskId: string
): Promise<void> => {
  const element = document.getElementById(elementId);
  
  if (!element) {
    throw new Error(`Element with id "${elementId}" not found`);
  }
  
  return exportToPDF(element, {
    taskId,
    title: '房都督AI - 房产分析报告',
  });
};

export const generateReportText = (report: Record<string, unknown>): string => {
  const lines: string[] = [];
  
  lines.push('=================================');
  lines.push('       房都督AI - 房产分析报告      ');
  lines.push('=================================');
  lines.push('');
  
  lines.push(`查询: ${report.query || '-'}`);
  lines.push(`风格: ${getStyleLabel(report.style as string)}`);
  lines.push(`置信度: ${((report.confidence_score as number || 0) * 100).toFixed(0)}%`);
  lines.push('');
  
  lines.push('【执行摘要】');
  lines.push(report.executive_summary as string || '-');
  lines.push('');
  
  const coreFindings = report.core_findings as Record<string, unknown>;
  if (coreFindings) {
    lines.push('【核心发现】');
    
    const location = coreFindings.location as Record<string, string>;
    if (location) {
      lines.push(`位置: ${location.city || ''} ${location.district || ''} ${location.community || ''}`);
    }
    
    const marketOverview = coreFindings.market_overview as Record<string, unknown>;
    if (marketOverview) {
      lines.push(`在售房源: ${marketOverview.total_properties || 0} 套`);
      lines.push(`均价: ${(marketOverview.average_price as number || 0).toLocaleString()} 元/㎡`);
    }
    
    const priceAnalysis = coreFindings.price_analysis as Record<string, unknown>;
    if (priceAnalysis) {
      lines.push(`价格趋势: ${priceAnalysis.trend || '-'}`);
      lines.push(`同比变化: ${priceAnalysis.year_over_year || 0}%`);
    }
    lines.push('');
  }
  
  const investmentAdvice = report.investment_advice as Record<string, unknown>;
  if (investmentAdvice) {
    lines.push('【投资建议】');
    lines.push(`综合评级: ${investmentAdvice.overall_rating || '-'}`);
    lines.push(`操作建议: ${investmentAdvice.action_recommendation || '-'}`);
    
    const styleAdvice = investmentAdvice.style_specific_advice as Record<string, string>;
    if (styleAdvice) {
      lines.push(`风险偏好: ${styleAdvice.risk_level || '-'}`);
      lines.push(`建议: ${styleAdvice.suggestion || '-'}`);
    }
    lines.push('');
  }
  
  const riskWarnings = report.risk_warnings as string[];
  if (riskWarnings && riskWarnings.length > 0) {
    lines.push('【风险提示】');
    riskWarnings.forEach((warning, index) => {
      lines.push(`${index + 1}. ${warning}`);
    });
    lines.push('');
  }
  
  const dataSources = report.data_sources as Array<Record<string, string>>;
  if (dataSources && dataSources.length > 0) {
    lines.push('【数据来源】');
    dataSources.forEach((source) => {
      lines.push(`- ${source.name}: ${source.type === 'real' ? '真实数据' : '模拟数据'}`);
    });
  }
  
  lines.push('');
  lines.push('=================================');
  lines.push(`报告生成时间: ${new Date(report.created_at as string).toLocaleString('zh-CN')}`);
  lines.push('=================================');
  
  return lines.join('\n');
};

const getStyleLabel = (style: string): string => {
  switch (style) {
    case 'conservative': return '保守型';
    case 'aggressive': return '进取型';
    default: return '平衡型';
  }
};

export default {
  exportToPDF,
  exportReportToPDF,
  generateReportText,
};
