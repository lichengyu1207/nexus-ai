import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Palette,
  Type,
  Layout,
  Box,
  Sparkles,
  Moon,
  Sun,
  ChevronRight,
} from 'lucide-react';
import AcrylicContainer from './AcrylicContainer';
import FluentButton from './FluentButton';
import FluentCard from './FluentCard';
import AgentCard from './AgentCard';
import ProgressBar from './ProgressBar';
import GachaAnimation from './GachaAnimation';

const FluentShowcase: React.FC = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [showGacha, setShowGacha] = useState(false);

  const sampleAgent = {
    id: '1',
    name: '周瑜·大都督',
    avatar: '/agents/zhouyu.png',
    level: 45,
    department: '战略规划部',
    status: 'working' as const,
    currentTask: '分析深圳南山区房价趋势',
    rarity: 'legendary' as const,
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''}`}>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-fluent-deepOcean-600 dark:to-fluent-deepOcean-800 p-8">
        <div className="max-w-6xl mx-auto">
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-fluent-gold-100 text-fluent-gold-600 mb-4">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-medium">Fluent Design System</span>
            </div>
            <h1 className="text-4xl font-bold text-fluent-deepOcean-500 dark:text-white mb-4">
              房都督视觉系统演示
            </h1>
            <p className="text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
              基于微软Fluent Design设计语言，融合三国文化元素，打造具有科技感、沉浸感、高辨识度的视觉系统
            </p>
            <div className="flex justify-center gap-4 mt-6">
              <FluentButton
                variant={darkMode ? 'outline' : 'primary'}
                onClick={() => setDarkMode(!darkMode)}
                icon={darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              >
                {darkMode ? '浅色模式' : '深色模式'}
              </FluentButton>
            </div>
          </motion.div>

          <motion.div
            className="space-y-12"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.section variants={itemVariants}>
              <div className="flex items-center gap-2 mb-6">
                <Palette className="w-6 h-6 text-fluent-gold-500" />
                <h2 className="text-2xl font-bold text-fluent-deepOcean-500 dark:text-white">色彩系统</h2>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {[
                  { name: '深海蓝', color: 'bg-fluent-deepOcean-500', hex: '#0A1A2F' },
                  { name: '帝王金', color: 'bg-fluent-gold-500', hex: '#D4AF37' },
                  { name: '墨玉绿', color: 'bg-fluent-jade-500', hex: '#2C5530' },
                  { name: '象牙白', color: 'bg-fluent-ivory-500', hex: '#FFFFF0' },
                  { name: '檀木棕', color: 'bg-fluent-sandalwood-500', hex: '#8B5A2B' },
                  { name: '成功绿', color: 'bg-success', hex: '#27AE60' },
                ].map((item) => (
                  <motion.div
                    key={item.name}
                    className="text-center"
                    whileHover={{ scale: 1.05 }}
                  >
                    <div className={`${item.color} h-20 rounded-xl shadow-lg mb-2`} />
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{item.name}</p>
                    <p className="text-xs text-gray-500">{item.hex}</p>
                  </motion.div>
                ))}
              </div>
            </motion.section>

            <motion.section variants={itemVariants}>
              <div className="flex items-center gap-2 mb-6">
                <Box className="w-6 h-6 text-fluent-gold-500" />
                <h2 className="text-2xl font-bold text-fluent-deepOcean-500 dark:text-white">按钮组件</h2>
              </div>
              <FluentCard>
                <div className="flex flex-wrap gap-4">
                  <FluentButton variant="primary">Primary</FluentButton>
                  <FluentButton variant="secondary">Secondary</FluentButton>
                  <FluentButton variant="outline">Outline</FluentButton>
                  <FluentButton variant="ghost">Ghost</FluentButton>
                  <FluentButton variant="gold">Gold</FluentButton>
                  <FluentButton variant="primary" size="sm">Small</FluentButton>
                  <FluentButton variant="gold" size="lg">Large</FluentButton>
                  <FluentButton variant="primary" loading>Loading</FluentButton>
                </div>
              </FluentCard>
            </motion.section>

            <motion.section variants={itemVariants}>
              <div className="flex items-center gap-2 mb-6">
                <Layout className="w-6 h-6 text-fluent-gold-500" />
                <h2 className="text-2xl font-bold text-fluent-deepOcean-500 dark:text-white">卡片组件</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <FluentCard elevated>普通卡片</FluentCard>
                <FluentCard goldAccent>金色装饰卡片</FluentCard>
                <FluentCard acrylic>毛玻璃卡片</FluentCard>
              </div>
            </motion.section>

            <motion.section variants={itemVariants}>
              <div className="flex items-center gap-2 mb-6">
                <Sparkles className="w-6 h-6 text-fluent-gold-500" />
                <h2 className="text-2xl font-bold text-fluent-deepOcean-500 dark:text-white">智能体卡片</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <AgentCard agent={{ ...sampleAgent, status: 'idle', rarity: 'common' }} />
                <AgentCard agent={{ ...sampleAgent, status: 'busy', rarity: 'rare' }} />
                <AgentCard agent={{ ...sampleAgent, status: 'working', rarity: 'epic' }} />
                <AgentCard agent={{ ...sampleAgent, status: 'autonomous', rarity: 'legendary' }} />
              </div>
            </motion.section>

            <motion.section variants={itemVariants}>
              <div className="flex items-center gap-2 mb-6">
                <Type className="w-6 h-6 text-fluent-gold-500" />
                <h2 className="text-2xl font-bold text-fluent-deepOcean-500 dark:text-white">进度条</h2>
              </div>
              <FluentCard>
                <div className="space-y-6">
                  <ProgressBar value={75} label="任务进度" variant="gold" />
                  <ProgressBar value={45} label="经验值" variant="gradient" />
                  <ProgressBar value={90} label="完成度" variant="default" />
                </div>
              </FluentCard>
            </motion.section>

            <motion.section variants={itemVariants}>
              <div className="flex items-center gap-2 mb-6">
                <Sparkles className="w-6 h-6 text-fluent-gold-500" />
                <h2 className="text-2xl font-bold text-fluent-deepOcean-500 dark:text-white">毛玻璃效果</h2>
              </div>
              <div
                className="relative h-64 rounded-2xl overflow-hidden"
                style={{
                  backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23D4AF37\' fill-opacity=\'0.1\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
                }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-fluent-deepOcean-300 to-fluent-gold-300" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <AcrylicContainer blur="lg" opacity={0.8} goldAccent className="p-8">
                    <h3 className="text-xl font-bold text-fluent-deepOcean-500 mb-2">亚克力容器</h3>
                    <p className="text-gray-600">
                      这是一个带有毛玻璃效果的容器组件，支持自定义模糊度和透明度
                    </p>
                  </AcrylicContainer>
                </div>
              </div>
            </motion.section>

            <motion.section variants={itemVariants}>
              <div className="flex items-center gap-2 mb-6">
                <Sparkles className="w-6 h-6 text-fluent-gold-500" />
                <h2 className="text-2xl font-bold text-fluent-deepOcean-500 dark:text-white">抽卡动画</h2>
              </div>
              <FluentCard className="text-center">
                <p className="text-gray-500 mb-4">点击按钮体验抽卡动画效果</p>
                <FluentButton variant="gold" onClick={() => setShowGacha(true)}>
                  <Sparkles className="w-4 h-4 mr-2" />
                  开始招募
                </FluentButton>
              </FluentCard>
            </motion.section>

            <motion.section variants={itemVariants}>
              <div className="flex items-center gap-2 mb-6">
                <ChevronRight className="w-6 h-6 text-fluent-gold-500" />
                <h2 className="text-2xl font-bold text-fluent-deepOcean-500 dark:text-white">动画效果</h2>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {['fade-in', 'pulse-gold', 'float', 'shimmer'].map((anim) => (
                  <motion.div
                    key={anim}
                    className={`h-20 rounded-xl bg-fluent-gold-500 flex items-center justify-center text-white font-medium animate-${anim}`}
                    whileHover={{ scale: 1.05 }}
                  >
                    {anim}
                  </motion.div>
                ))}
              </div>
            </motion.section>
          </motion.div>
        </div>
      </div>

      <GachaAnimation
        isOpen={showGacha}
        onClose={() => setShowGacha(false)}
        agent={{
          name: '周瑜·大都督',
          avatar: '/agents/zhouyu.png',
          rarity: 'legendary',
          level: 45,
          department: '战略规划部',
        }}
      />
    </div>
  );
};

export default FluentShowcase;
