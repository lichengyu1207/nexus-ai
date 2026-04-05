import React, { useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useDemoStore } from '@/stores/demoStore';
import chartData from '@/data/chartData.json';

const LiveReportPreview: React.FC = () => {
  const { reportData, currentScene } = useDemoStore();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [reportData]);

  const renderSection = useCallback((section: { type: string; title?: string; content?: string; chartType?: string; visible: boolean }, index: number) => {
    switch (section.type) {
      case 'loading':
        return (
          <motion.div
            key={index}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center justify-center py-8"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full"
            />
            <span className="ml-3 text-white/70">{section.content}</span>
          </motion.div>
        );

      case 'title':
        return (
          <motion.h2
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl font-bold text-white mb-2"
          >
            {section.content?.split('').map((char, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
              >
                {char}
              </motion.span>
            ))}
          </motion.h2>
        );

      case 'subtitle':
        return (
          <motion.p
            key={index}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-white/50 text-sm mb-6"
          >
            {section.content}
          </motion.p>
        );

      case 'section':
        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="mb-4 p-4 bg-white/5 rounded-xl"
          >
            <h3 className="text-white font-semibold mb-2">{section.title}</h3>
            <p className="text-white/70 text-sm leading-relaxed">{section.content}</p>
          </motion.div>
        );

      case 'chart':
        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-4 p-4 bg-white/5 rounded-xl"
          >
            <h4 className="text-white/80 text-sm mb-3">{section.title}</h4>
            <div className="h-32">
              {section.chartType === 'priceTrend' && (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData.priceTrend.data}>
                    <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} width={45} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                      labelStyle={{ color: '#9ca3af' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      dot={{ fill: '#8b5cf6', r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
              {section.chartType === 'areaCompare' && (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData.areaCompare.data} layout="vertical">
                    <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                    <YAxis dataKey="area" type="category" tick={{ fill: '#9ca3af', fontSize: 10 }} width={50} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                    />
                    <Bar dataKey="price" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
              {section.chartType === 'facility' && (
                <div className="flex justify-around items-end h-full">
                  {chartData.facility.data.map((item, i) => (
                    <motion.div
                      key={i}
                      initial={{ height: 0 }}
                      animate={{ height: `${(item.count / 50) * 100}%` }}
                      transition={{ delay: i * 0.1, duration: 0.5 }}
                      className="flex flex-col items-center"
                    >
                      <span className="text-lg mb-1">{item.icon}</span>
                      <div
                        className="w-8 bg-gradient-to-t from-purple-600 to-purple-400 rounded-t"
                        style={{ height: '100%' }}
                      />
                      <span className="text-white/50 text-xs mt-1">{item.count}</span>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        );

      case 'summary':
        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-4 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl border border-purple-500/30"
          >
            <p className="text-white font-semibold text-center">{section.content}</p>
          </motion.div>
        );

      case 'cta':
        return (
          <motion.button
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full mt-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-semibold shadow-lg shadow-purple-500/30"
          >
            {section.content} →
          </motion.button>
        );

      default:
        return null;
    }
  }, []);

  if (currentScene === 'idle') {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-white/30">
          <div className="text-6xl mb-4">📊</div>
          <p>报告预览区</p>
          <p className="text-sm">开始分析后将在此显示</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-white/10 overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-red-500" />
        <div className="w-3 h-3 rounded-full bg-yellow-500" />
        <div className="w-3 h-3 rounded-full bg-green-500" />
        <span className="ml-2 text-white/50 text-sm">实时报告预览</span>
        {currentScene === 'scene2' && (
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="ml-auto flex items-center gap-1"
          >
            <div className="w-2 h-2 bg-green-400 rounded-full" />
            <span className="text-green-400 text-xs">生成中</span>
          </motion.div>
        )}
      </div>
      
      <div
        ref={containerRef}
        className="p-4 h-[calc(100%-52px)] overflow-y-auto"
        style={{ scrollbarWidth: 'thin', scrollbarColor: '#4b5563 transparent' }}
      >
        <AnimatePresence mode="popLayout">
          {reportData.map((section, index) => (
            <motion.div
              key={index}
              layout
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              {renderSection(section, index)}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default LiveReportPreview;
