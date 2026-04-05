import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import AtmosphereDashboard from '@/components/AtmosphereValuation/AtmosphereDashboard';
import AtmosphereChat from '@/components/AtmosphereValuation/AtmosphereChat';
import { slideIn } from '@/config/animation';

const AtmosphereValuationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <motion.div {...slideIn} className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text-primary">氛围估价</h1>
        <p className="text-text-secondary">
          基于环境氛围感知的房产价值评估系统
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="dashboard">仪表盘估价</TabsTrigger>
          <TabsTrigger value="chat">智能咨询估价</TabsTrigger>
        </TabsList>
        <TabsContent value="dashboard" className="mt-6">
          <AtmosphereDashboard />
        </TabsContent>
        <TabsContent value="chat" className="mt-6">
          <AtmosphereChat />
        </TabsContent>
      </Tabs>

      <div className="mt-8 p-6 bg-bg-secondary rounded-lg border border-border-light">
        <h3 className="text-lg font-medium text-text-primary mb-4">关于氛围估价</h3>
        <div className="space-y-3 text-text-secondary text-sm">
          <p>氛围估价是一种基于环境氛围感知的房产价值评估系统，通过分析房产周边的环境氛围、社区文化、生活品质等非物理属性因素，为您提供更全面、更个性化的房产价值评估。</p>
          <p>评估因素包括：社区氛围、自然环境、生活便利、安全指数、文化底蕴、发展潜力等六个维度。</p>
          <p>最终估价结果 = 基础价值 × 氛围调整系数，其中氛围调整系数基于氛围评分计算得出。</p>
        </div>
      </div>
    </motion.div>
  );
};

export default AtmosphereValuationPage;