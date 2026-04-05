import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TypewriterText from './TypewriterText';

interface ReportData {
  summary?: string;
  findings?: string[];
  recommendations?: string[];
  report?: string;
  integral_cost?: number;
  steps_count?: number;
}

interface AnalysisReportProps {
  reportData: ReportData;
  taskId?: string;
  onComplete?: () => void;
}

const AnalysisReport: React.FC<AnalysisReportProps> = ({
  reportData,
  taskId,
  onComplete
}) => {
  const [showExport, setShowExport] = useState(false);
  const [currentSection, setCurrentSection] = useState(0);
  const [sectionsComplete, setSectionsComplete] = useState<boolean[]>([false, false, false, false]);

  const sections = [
    { id: 'summary', title: '分析摘要', subtitle: 'Summary', icon: '📋', color: 'from-blue-500 to-cyan-500' },
    { id: 'findings', title: '关键发现', subtitle: 'Key Findings', icon: '🔍', color: 'from-purple-500 to-pink-500' },
    { id: 'recommendations', title: '专业建议', subtitle: 'Recommendations', icon: '💡', color: 'from-green-500 to-emerald-500' },
    { id: 'report', title: '详细报告', subtitle: 'Full Report', icon: '📄', color: 'from-orange-500 to-amber-500' }
  ];

  const handleSectionComplete = (index: number) => {
    setSectionsComplete(prev => {
      const newComplete = [...prev];
      newComplete[index] = true;
      return newComplete;
    });
    
    if (index < sections.length - 1) {
      setTimeout(() => setCurrentSection(index + 1), 300);
    } else if (onComplete) {
      onComplete();
    }
  };

  const handleExportMD = () => {
    const content = `
# 房产分析报告

## 分析摘要
${reportData.summary || '无'}

## 关键发现
${(reportData.findings || []).map((f, i) => `${i + 1}. ${f}`).join('\n') || '无'}

## 专业建议
${(reportData.recommendations || []).map((r, i) => `${i + 1}. ${r}`).join('\n') || '无'}

## 详细报告
${reportData.report || '无'}

---
生成时间: ${new Date().toLocaleString('zh-CN')}
${taskId ? `任务ID: ${taskId}` : ''}
${reportData.integral_cost ? `消耗积分: ${reportData.integral_cost}` : ''}
    `.trim();

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `房产分析报告_${new Date().toISOString().split('T')[0]}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportHTML = () => {
    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>房产分析报告</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      min-height: 100vh;
      padding: 40px 20px;
    }
    .container { max-width: 900px; margin: 0 auto; }
    .header {
      text-align: center;
      padding: 40px 0;
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
      border-radius: 20px;
      margin-bottom: 30px;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .header h1 {
      font-size: 36px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 10px;
    }
    .header p { color: rgba(255,255,255,0.6); }
    .section {
      background: rgba(255,255,255,0.05);
      border-radius: 16px;
      padding: 30px;
      margin-bottom: 20px;
      border: 1px solid rgba(255,255,255,0.1);
      backdrop-filter: blur(10px);
    }
    .section-header {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 20px;
    }
    .section-icon {
      width: 50px;
      height: 50px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
    }
    .section-icon.summary { background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%); }
    .section-icon.findings { background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); }
    .section-icon.recommendations { background: linear-gradient(135deg, #10b981 0%, #34d399 100%); }
    .section-icon.report { background: linear-gradient(135deg, #f97316 0%, #fbbf24 100%); }
    .section-title {
      font-size: 20px;
      font-weight: 600;
      color: #fff;
    }
    .section-subtitle {
      font-size: 14px;
      color: rgba(255,255,255,0.5);
    }
    .section-content {
      color: rgba(255,255,255,0.8);
      line-height: 1.8;
    }
    .findings-list, .recommendations-list {
      list-style: none;
      padding: 0;
    }
    .findings-list li, .recommendations-list li {
      padding: 12px 0;
      padding-left: 30px;
      position: relative;
      border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .findings-list li:last-child, .recommendations-list li:last-child {
      border-bottom: none;
    }
    .findings-list li::before {
      content: '🔍';
      position: absolute;
      left: 0;
    }
    .recommendations-list li::before {
      content: '💡';
      position: absolute;
      left: 0;
    }
    .footer {
      text-align: center;
      padding: 30px;
      color: rgba(255,255,255,0.4);
      font-size: 14px;
    }
    .stats {
      display: flex;
      justify-content: center;
      gap: 40px;
      margin-top: 20px;
    }
    .stat {
      text-align: center;
    }
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .stat-label {
      font-size: 12px;
      color: rgba(255,255,255,0.5);
      margin-top: 5px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🏠 房产分析报告</h1>
      <p>智能分析系统 · 专业数据洞察</p>
      ${reportData.integral_cost || reportData.steps_count ? `
      <div class="stats">
        ${reportData.integral_cost ? `<div class="stat"><div class="stat-value">${reportData.integral_cost}</div><div class="stat-label">消耗积分</div></div>` : ''}
        ${reportData.steps_count ? `<div class="stat"><div class="stat-value">${reportData.steps_count}</div><div class="stat-label">执行步骤</div></div>` : ''}
      </div>
      ` : ''}
    </div>
    
    ${reportData.summary ? `
    <div class="section">
      <div class="section-header">
        <div class="section-icon summary">📋</div>
        <div>
          <div class="section-title">分析摘要</div>
          <div class="section-subtitle">Summary</div>
        </div>
      </div>
      <div class="section-content">${reportData.summary}</div>
    </div>
    ` : ''}
    
    ${(reportData.findings && reportData.findings.length > 0) ? `
    <div class="section">
      <div class="section-header">
        <div class="section-icon findings">🔍</div>
        <div>
          <div class="section-title">关键发现</div>
          <div class="section-subtitle">Key Findings</div>
        </div>
      </div>
      <ul class="findings-list">
        ${reportData.findings.map(f => `<li>${f}</li>`).join('')}
      </ul>
    </div>
    ` : ''}
    
    ${(reportData.recommendations && reportData.recommendations.length > 0) ? `
    <div class="section">
      <div class="section-header">
        <div class="section-icon recommendations">💡</div>
        <div>
          <div class="section-title">专业建议</div>
          <div class="section-subtitle">Recommendations</div>
        </div>
      </div>
      <ul class="recommendations-list">
        ${reportData.recommendations.map(r => `<li>${r}</li>`).join('')}
      </ul>
    </div>
    ` : ''}
    
    ${reportData.report ? `
    <div class="section">
      <div class="section-header">
        <div class="section-icon report">📄</div>
        <div>
          <div class="section-title">详细报告</div>
          <div class="section-subtitle">Full Report</div>
        </div>
      </div>
      <div class="section-content" style="white-space: pre-wrap;">${reportData.report}</div>
    </div>
    ` : ''}
    
    <div class="footer">
      <p>🏠 房产智能分析系统</p>
      <p>生成时间: ${new Date().toLocaleString('zh-CN')}</p>
      ${taskId ? `<p>任务ID: ${taskId}</p>` : ''}
    </div>
  </div>
</body>
</html>
    `.trim();

    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `房产分析报告_${new Date().toISOString().split('T')[0]}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const hasContent = (index: number): boolean => {
    switch (index) {
      case 0: return !!reportData.summary;
      case 1: return !!(reportData.findings && reportData.findings.length > 0);
      case 2: return !!(reportData.recommendations && reportData.recommendations.length > 0);
      case 3: return !!reportData.report;
      default: return false;
    }
  };

  const getAvailableSections = () => sections.filter((_, i) => hasContent(i));
  const availableSections = getAvailableSections();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl overflow-hidden border border-gray-700/50 shadow-2xl"
    >
      {/* Header */}
      <div className="relative bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-pink-600/20 p-8 border-b border-gray-700/50">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PHBhdGggZD0iTTM2IDM0djItSDI0di0yaDEyek0zNiAyNHYySDI0di0yaDEyeiIvPjwvZz48L2c+PC9zdmc+')] opacity-50"></div>
        
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-4">
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", duration: 0.8 }}
              className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-3xl shadow-lg shadow-purple-500/30"
            >
              🏠
            </motion.div>
            <div>
              <motion.h2
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent"
              >
                房产分析报告
              </motion.h2>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="text-gray-400 text-sm mt-1"
              >
                智能分析系统 · 专业数据洞察
              </motion.p>
            </div>
          </div>

          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            onClick={() => setShowExport(!showExport)}
            className="px-5 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-purple-500/25"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            导出报告
          </motion.button>
        </div>

        {/* Stats */}
        {(reportData.integral_cost || reportData.steps_count) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="relative flex gap-8 mt-6 pt-6 border-t border-gray-700/50"
          >
            {reportData.integral_cost && (
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                  {reportData.integral_cost}
                </div>
                <div className="text-xs text-gray-500 mt-1">消耗积分</div>
              </div>
            )}
            {reportData.steps_count && (
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  {reportData.steps_count}
                </div>
                <div className="text-xs text-gray-500 mt-1">执行步骤</div>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Export Options */}
      <AnimatePresence>
        {showExport && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-gray-800/50 flex gap-3 border-b border-gray-700/50">
              <button
                onClick={handleExportMD}
                className="flex-1 px-4 py-3 bg-gray-700/50 hover:bg-gray-700 text-gray-300 rounded-xl flex items-center justify-center gap-2 transition-colors border border-gray-600/50"
              >
                <span className="text-lg">📝</span>
                <span>Markdown</span>
              </button>
              <button
                onClick={handleExportHTML}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-green-500/25"
              >
                <span className="text-lg">🎨</span>
                <span>精美HTML</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress Dots */}
      <div className="flex justify-center gap-3 py-4 bg-gray-800/30">
        {availableSections.map((section, index) => (
          <motion.div
            key={section.id}
            initial={{ scale: 0.8, opacity: 0.3 }}
            animate={{
              scale: currentSection === index ? 1.3 : 1,
              opacity: currentSection >= index || sectionsComplete[index] ? 1 : 0.3
            }}
            className={`w-2.5 h-2.5 rounded-full bg-gradient-to-r ${section.color} shadow-lg`}
            style={{
              boxShadow: currentSection >= index ? `0 0 10px ${section.color.includes('blue') ? '#3b82f6' : section.color.includes('purple') ? '#8b5cf6' : section.color.includes('green') ? '#10b981' : '#f97316'}` : 'none'
            }}
          />
        ))}
      </div>

      {/* Content Sections */}
      <div className="p-6 space-y-6">
        {/* Summary */}
        {reportData.summary && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: currentSection >= 0 ? 1 : 0, y: currentSection >= 0 ? 0 : 20 }}
            className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-xl p-6 border border-blue-500/20"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${sections[0].color} flex items-center justify-center text-xl shadow-lg`}>
                {sections[0].icon}
              </div>
              <div>
                <h3 className={`text-lg font-semibold bg-gradient-to-r ${sections[0].color} bg-clip-text text-transparent`}>
                  {sections[0].title}
                </h3>
                <p className="text-xs text-gray-500">{sections[0].subtitle}</p>
              </div>
            </div>
            <div className="text-gray-300 leading-relaxed">
              <TypewriterText
                text={reportData.summary}
                speed={15}
                onComplete={() => handleSectionComplete(0)}
                className="text-gray-300"
              />
            </div>
          </motion.div>
        )}

        {/* Findings */}
        {reportData.findings && reportData.findings.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: currentSection >= 1 ? 1 : 0, y: currentSection >= 1 ? 0 : 20 }}
            className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-xl p-6 border border-purple-500/20"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${sections[1].color} flex items-center justify-center text-xl shadow-lg`}>
                {sections[1].icon}
              </div>
              <div>
                <h3 className={`text-lg font-semibold bg-gradient-to-r ${sections[1].color} bg-clip-text text-transparent`}>
                  {sections[1].title}
                </h3>
                <p className="text-xs text-gray-500">{sections[1].subtitle}</p>
              </div>
            </div>
            <ul className="space-y-3">
              {reportData.findings.map((finding, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.15 }}
                  className="flex items-start gap-3"
                >
                  <span className={`w-6 h-6 rounded-full bg-gradient-to-r ${sections[1].color} text-white flex items-center justify-center text-sm font-bold flex-shrink-0 shadow-md`}>
                    {index + 1}
                  </span>
                  <TypewriterText
                    text={finding}
                    speed={10}
                    className="text-gray-300 leading-relaxed"
                  />
                </motion.li>
              ))}
            </ul>
            {reportData.findings.length > 0 && (
              <div className="mt-4 opacity-0">
                <TypewriterText
                  text=""
                  speed={1}
                  onComplete={() => handleSectionComplete(1)}
                />
              </div>
            )}
          </motion.div>
        )}

        {/* Recommendations */}
        {reportData.recommendations && reportData.recommendations.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: currentSection >= 2 ? 1 : 0, y: currentSection >= 2 ? 0 : 20 }}
            className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-xl p-6 border border-green-500/20"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${sections[2].color} flex items-center justify-center text-xl shadow-lg`}>
                {sections[2].icon}
              </div>
              <div>
                <h3 className={`text-lg font-semibold bg-gradient-to-r ${sections[2].color} bg-clip-text text-transparent`}>
                  {sections[2].title}
                </h3>
                <p className="text-xs text-gray-500">{sections[2].subtitle}</p>
              </div>
            </div>
            <ul className="space-y-3">
              {reportData.recommendations.map((rec, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.15 }}
                  className="flex items-start gap-3"
                >
                  <span className={`w-6 h-6 rounded-full bg-gradient-to-r ${sections[2].color} text-white flex items-center justify-center text-sm font-bold flex-shrink-0 shadow-md`}>
                    {index + 1}
                  </span>
                  <TypewriterText
                    text={rec}
                    speed={10}
                    className="text-gray-300 leading-relaxed"
                  />
                </motion.li>
              ))}
            </ul>
            {reportData.recommendations.length > 0 && (
              <div className="mt-4 opacity-0">
                <TypewriterText
                  text=""
                  speed={1}
                  onComplete={() => handleSectionComplete(2)}
                />
              </div>
            )}
          </motion.div>
        )}

        {/* Detailed Report */}
        {reportData.report && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: currentSection >= 3 ? 1 : 0, y: currentSection >= 3 ? 0 : 20 }}
            className="bg-gradient-to-br from-orange-500/10 to-amber-500/10 rounded-xl p-6 border border-orange-500/20"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${sections[3].color} flex items-center justify-center text-xl shadow-lg`}>
                {sections[3].icon}
              </div>
              <div>
                <h3 className={`text-lg font-semibold bg-gradient-to-r ${sections[3].color} bg-clip-text text-transparent`}>
                  {sections[3].title}
                </h3>
                <p className="text-xs text-gray-500">{sections[3].subtitle}</p>
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4 max-h-96 overflow-y-auto">
              <TypewriterText
                text={reportData.report}
                speed={5}
                onComplete={() => handleSectionComplete(3)}
                className="whitespace-pre-wrap text-gray-300 leading-relaxed"
              />
            </div>
          </motion.div>
        )}
      </div>

      {/* Footer */}
      <div className="px-6 py-4 bg-gray-800/50 border-t border-gray-700/50 text-center">
        <p className="text-gray-500 text-sm">
          🏠 房产智能分析系统 · 生成时间: {new Date().toLocaleString('zh-CN')}
        </p>
        {taskId && <p className="text-gray-600 text-xs mt-1">任务ID: {taskId}</p>}
      </div>
    </motion.div>
  );
};

export default AnalysisReport;
