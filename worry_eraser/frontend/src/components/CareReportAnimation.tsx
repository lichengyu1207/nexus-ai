import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { Report } from '../types';

interface CareReportAnimationProps {
  reportData: Report;
  onComplete?: () => void;
}

const CareReportAnimation: React.FC<CareReportAnimationProps> = ({ reportData, onComplete }) => {
  const [visibleSections, setVisibleSections] = useState(0);

  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];
    const sections = ['title', 'summary', 'chart', 'suggestions'];
    
    sections.forEach((_, idx) => {
      const timer = setTimeout(() => setVisibleSections(idx + 1), (idx + 1) * 800);
      timers.push(timer);
    });

    const completeTimer = setTimeout(() => {
      onComplete?.();
    }, sections.length * 800 + 500);
    timers.push(completeTimer);

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [onComplete]);

  const chartData = reportData.chart_data.labels.map((label, idx) => ({
    name: label,
    value: reportData.chart_data.values[idx],
  }));

  return (
    <motion.div
      className="care-report"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {visibleSections >= 1 && (
        <motion.h1
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          {reportData.title}
        </motion.h1>
      )}
      
      {visibleSections >= 2 && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          {reportData.summary}
        </motion.p>
      )}
      
      {visibleSections >= 3 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          style={{ marginBottom: '16px' }}
        >
          <h3>情绪分析</h3>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={chartData}>
              <XAxis dataKey="name" stroke="#666" />
              <YAxis stroke="#666" />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#667eea"
                strokeWidth={2}
                dot={{ fill: '#667eea', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
          <p style={{ color: '#666', marginTop: '8px' }}>{reportData.emotion_trend}</p>
        </motion.div>
      )}
      
      {visibleSections >= 4 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <h3>暖心建议</h3>
          <ul>
            {reportData.suggestions.map((s, idx) => (
              <motion.li
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                {s}
              </motion.li>
            ))}
          </ul>
        </motion.div>
      )}
    </motion.div>
  );
};

export default CareReportAnimation;
