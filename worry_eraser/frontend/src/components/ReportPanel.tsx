import React from 'react';
import { Report } from '../types';

interface ReportPanelProps {
  report: Report | null;
  onGenerate: () => void;
  isLoading: boolean;
}

const ReportPanel: React.FC<ReportPanelProps> = ({ report, onGenerate, isLoading }) => {
  return (
    <div className="report-section">
      <div className="report-header">
        <h2>烦恼分析报告</h2>
        <button
          className="generate-report-btn"
          onClick={onGenerate}
          disabled={isLoading}
        >
          {isLoading ? '生成中...' : '生成报告'}
        </button>
      </div>
      <div className="report-content">
        {isLoading ? (
          <div className="loading" style={{ margin: '20px auto', display: 'block' }}></div>
        ) : report ? (
          <>
            <div className="report-card">
              <h3>{report.title}</h3>
              <p>{report.summary}</p>
            </div>
            <div className="report-card">
              <h3>情绪趋势</h3>
              <p>{report.emotion_trend}</p>
            </div>
            <div className="report-card">
              <h3>建议</h3>
              <ul className="suggestions">
                {report.suggestions.map((s, idx) => (
                  <li key={idx}>• {s}</li>
                ))}
              </ul>
            </div>
          </>
        ) : (
          <p>点击上方按钮生成分析报告</p>
        )}
      </div>
    </div>
  );
};

export default ReportPanel;
