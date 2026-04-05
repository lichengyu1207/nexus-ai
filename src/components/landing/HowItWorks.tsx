import { motion, useAnimation } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { useEffect } from 'react';
import {
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  ChartBarIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import Mascot from '../mascot/Mascot';

const steps = [
  {
    icon: ChatBubbleLeftRightIcon,
    title: '1. 输入需求',
    desc: '输入房产地址或自然语言描述',
    color: 'bg-blue-100 text-blue-600',
  },
  {
    icon: UserGroupIcon,
    title: '2. AI团队分工',
    desc: '需求分析师、数据采集师、市场分析师协同工作',
    color: 'bg-purple-100 text-purple-600',
    showMascots: true,
  },
  {
    icon: ChartBarIcon,
    title: '3. 数据分析',
    desc: '实时搜索、价格估算、趋势预测',
    color: 'bg-green-100 text-green-600',
  },
  {
    icon: DocumentTextIcon,
    title: '4. 生成报告',
    desc: '结构化报告，含摘要、建议、风险提示',
    color: 'bg-orange-100 text-orange-600',
  },
];

export default function HowItWorks() {
  const controls = useAnimation();
  const [ref, inView] = useInView({ triggerOnce: true, threshold: 0.2 });

  useEffect(() => {
    if (inView) {
      controls.start('visible');
    }
  }, [controls, inView]);

  return (
    <section ref={ref} className="py-20 bg-gradient-to-b from-white to-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            一分钟看懂房都督AI如何工作
          </h2>
          <p className="text-lg text-gray-600">从输入到报告，全程透明可见</p>
        </motion.div>

        <div className="relative">
          {/* 连接线 */}
          <div className="hidden lg:block absolute top-24 left-[12.5%] right-[12.5%] h-1 bg-gradient-to-r from-blue-200 via-purple-200 to-orange-200 rounded-full" />
          
          {/* 流动光点 */}
          <motion.div
            className="hidden lg:block absolute top-24 w-4 h-4 bg-blue-500 rounded-full shadow-lg shadow-blue-500/50"
            style={{ left: '12.5%' }}
            animate={inView ? {
              left: ['12.5%', '87.5%', '12.5%'],
            } : {}}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                custom={index}
                initial="hidden"
                animate={controls}
                variants={{
                  hidden: { opacity: 0, y: 30 },
                  visible: (i) => ({
                    opacity: 1,
                    y: 0,
                    transition: { delay: i * 0.2, duration: 0.5 },
                  }),
                }}
                className="relative bg-white rounded-3xl p-6 shadow-lg hover:shadow-xl transition-all border border-gray-100 group"
              >
                <div className={`w-16 h-16 mx-auto mb-4 ${step.color} rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform`}>
                  {step.showMascots ? (
                    <div className="flex -space-x-2">
                      <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center text-xs">🤖</div>
                      <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center text-xs">📊</div>
                      <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center text-xs">🏠</div>
                    </div>
                  ) : (
                    <step.icon className="w-8 h-8" />
                  )}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2 text-center">{step.title}</h3>
                <p className="text-gray-600 text-center text-sm">{step.desc}</p>
                
                {/* 步骤编号 */}
                <div className="absolute -top-3 -left-3 w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg">
                  {index + 1}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* 智能体协作的微观展示 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 1, duration: 0.6 }}
          className="mt-16 p-8 bg-white rounded-3xl border border-gray-100 shadow-lg"
        >
          <p className="text-center text-gray-500 mb-6 font-medium">✨ 实时协作过程 ✨</p>
          <div className="flex flex-col md:flex-row justify-center items-center gap-4 md:gap-8">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mb-2">
                <Mascot emotion="thinking" pose="standing" size="sm" />
              </div>
              <span className="text-sm text-gray-600">需求分析师</span>
            </div>
            
            <motion.div
              className="flex items-center gap-2"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <div className="w-3 h-3 bg-blue-400 rounded-full" />
              <div className="w-8 h-0.5 bg-gradient-to-r from-blue-400 to-purple-400" />
              <div className="w-3 h-3 bg-purple-400 rounded-full" />
            </motion.div>
            
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mb-2">
                <Mascot emotion="happy" pose="waving" size="sm" />
              </div>
              <span className="text-sm text-gray-600">数据采集师</span>
            </div>
            
            <motion.div
              className="flex items-center gap-2"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.5 }}
            >
              <div className="w-3 h-3 bg-purple-400 rounded-full" />
              <div className="w-8 h-0.5 bg-gradient-to-r from-purple-400 to-orange-400" />
              <div className="w-3 h-3 bg-orange-400 rounded-full" />
            </motion.div>
            
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-orange-100 rounded-2xl flex items-center justify-center mb-2">
                <Mascot emotion="default" pose="sitting" size="sm" />
              </div>
              <span className="text-sm text-gray-600">市场分析师</span>
            </div>
          </div>
          
          <motion.div
            className="mt-6 flex justify-center"
            initial={{ opacity: 0 }}
            animate={inView ? { opacity: 1 } : {}}
            transition={{ delay: 1.5 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-50 rounded-full text-green-700 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              协同分析中...
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
