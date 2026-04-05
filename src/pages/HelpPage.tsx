import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  QuestionMarkCircleIcon,
  BookOpenIcon,
  ChatBubbleLeftRightIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  EnvelopeIcon,
  PhoneIcon,
} from '@heroicons/react/24/outline';

const HelpPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  const categories = ['all', 'faq', 'tutorial', 'contact'];

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'all': return <QuestionMarkCircleIcon className="w-5 h-5" />;
      case 'faq': return <ChatBubbleLeftRightIcon className="w-5 h-5" />;
      case 'tutorial': return <BookOpenIcon className="w-5 h-5" />;
      case 'contact': return <EnvelopeIcon className="w-5 h-5" />;
      default: return <QuestionMarkCircleIcon className="w-5 h-5" />;
    }
  };

  const faqs = [
    { question: '如何开始使用房都督AI？', answer: '注册账号后，在仪表盘点击"新建分析"，输入房产地址即可开始。' },
    { question: '分析报告包含哪些内容？', answer: '报告包含执行摘要、核心发现、详细分析、投资建议、风险提示等部分。' },
    { question: '可以导出报告吗？', answer: '是的，专业版和企业版用户可以导出PDF和Excel格式的报告。' },
    { question: '数据来源是什么？', answer: '我们整合了官方房产交易平台、政府公开数据和第三方数据提供商的数据。' },
  ];

  const tutorials = [
    { title: '快速入门指南', description: '5分钟学会使用房都督AI进行房产分析', duration: '5分钟' },
    { title: '高级分析技巧', description: '深入了解多智能体协同分析的工作原理', duration: '10分钟' },
    { title: '报告解读指南', description: '学会如何解读分析报告中的各项指标', duration: '8分钟' },
  ];

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-2">帮助中心</h1>
          <p className="text-lg text-gray-600">快速找到答案，学习使用技巧，获取专业支持</p>
        </motion.div>

        <div className="flex flex-col lg:flex-row gap-8">
          <aside className="w-full lg:w-64 bg-gray-50 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">目录</h2>
            <div className="space-y-2">
              {categories.map(category => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    selectedCategory === category
                      ? 'bg-blue-100 text-blue-700'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  {getCategoryIcon(category)}
                  <span className="font-medium">
                    {category === 'all' ? '全部' : category === 'faq' ? '常见问题' : category === 'tutorial' ? '使用教程' : '联系我们'}
                  </span>
                </button>
              ))}
            </div>
          </aside>

          <div className="flex-1">
            {(selectedCategory === 'all' || selectedCategory === 'faq') && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mb-8"
              >
                <h2 className="text-2xl font-bold text-gray-900 mb-4">常见问题</h2>
                <div className="space-y-3">
                  {faqs.map((faq, index) => (
                    <div key={index} className="bg-gray-50 rounded-xl overflow-hidden">
                      <button
                        className="w-full px-6 py-4 flex items-center justify-between text-left"
                        onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                      >
                        <span className="font-medium text-gray-900">{faq.question}</span>
                        <ChevronDownIcon className={`w-5 h-5 text-gray-400 transition-transform ${expandedFaq === index ? 'rotate-180' : ''}`} />
                      </button>
                      {expandedFaq === index && (
                        <div className="px-6 pb-4 text-gray-600">{faq.answer}</div>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {(selectedCategory === 'all' || selectedCategory === 'tutorial') && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mb-8"
              >
                <h2 className="text-2xl font-bold text-gray-900 mb-4">使用教程</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {tutorials.map((tutorial, index) => (
                    <div key={index} className="bg-gray-50 rounded-xl p-6 hover:shadow-md transition-shadow cursor-pointer">
                      <h3 className="font-semibold text-gray-900 mb-2">{tutorial.title}</h3>
                      <p className="text-sm text-gray-600 mb-2">{tutorial.description}</p>
                      <span className="text-xs text-blue-600">{tutorial.duration}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {(selectedCategory === 'all' || selectedCategory === 'contact') && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <h2 className="text-2xl font-bold text-gray-900 mb-4">联系我们</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-xl p-6">
                    <EnvelopeIcon className="w-8 h-8 text-blue-600 mb-3" />
                    <h3 className="font-semibold text-gray-900 mb-2">邮件支持</h3>
                    <p className="text-gray-600">support@fangtanai.com</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-6">
                    <PhoneIcon className="w-8 h-8 text-blue-600 mb-3" />
                    <h3 className="font-semibold text-gray-900 mb-2">电话支持</h3>
                    <p className="text-gray-600">400-888-8888</p>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpPage;
