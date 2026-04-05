import React from 'react';
import { motion } from 'framer-motion';
import {
  RocketLaunchIcon,
  UserGroupIcon,
  EnvelopeIcon,
  BriefcaseIcon,
  StarIcon,
} from '@heroicons/react/24/outline';

const AboutPage: React.FC = () => {
  const coreMembers = [
    {
      name: 'Cheng Li',
      initial: 'C',
      position: '创始人 & CEO',
      bio: '深耕房产科技领域多年，拥有丰富的行业洞察与战略规划经验，致力于用AI技术重塑房产信息透明度。',
      isStar: true,
    },
    {
      name: 'Kang Wu',
      initial: 'K',
      position: '联合创始人 & CTO',
      bio: '多智能体系统专家，专注AI算法与分布式架构，主导平台核心AI引擎的研发，让复杂数据变得可解释。',
      isStar: true,
    },
    {
      name: 'Chuqiao Peng',
      initial: 'C',
      position: '联合创始人 & CPO',
      bio: '资深产品设计师，擅长从用户需求出发打造直观体验，主导产品从0到1的迭代，让数据服务真正可用。',
      isStar: true,
    },
  ];

  const teamMembers = [
    {
      name: 'Youpeng Huang',
      initial: 'Y',
      position: '后端开发工程师',
      bio: '专注高性能API设计与系统稳定性，确保平台在高并发下依然流畅。',
    },
    {
      name: 'Pin Li',
      initial: 'P',
      position: '前端开发工程师',
      bio: '热爱代码优雅与交互细节，负责将产品设计转化为丝滑的用户界面。',
    },
    {
      name: 'Liu Tang',
      initial: 'L',
      position: '全栈运维工程师',
      bio: '精通CI/CD与云原生技术，保障平台7x24小时稳定运行，让用户无感访问。',
    },
    {
      name: 'Shuting Chen',
      initial: 'S',
      position: 'UI/UX 设计师',
      bio: '擅长将复杂数据转化为直观视觉语言，让用户一眼看懂房产价值。',
    },
    {
      name: 'Haifeng Long',
      initial: 'H',
      position: '市场运营经理',
      bio: '深耕房产社群运营，擅长用户增长与品牌传播，让好产品被更多人看见。',
    },
    {
      name: 'Longxiang Xiao',
      initial: 'L',
      position: '数据采集工程师',
      bio: '数据"矿工"，负责全网房产数据采集与清洗，为AI提供高质量"食粮"。',
    },
  ];

  const values = [
    { icon: RocketLaunchIcon, title: '创新驱动', description: '我们相信技术创新是推动行业进步的核心动力。' },
    { icon: UserGroupIcon, title: '用户至上', description: '以用户需求为中心，持续优化产品体验。' },
    { icon: BriefcaseIcon, title: '专业可靠', description: '提供准确、可信的房产分析服务，助力明智决策。' },
  ];

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-4">关于我们</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            用AI技术，重新定义房产分析体验
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">我们的使命</h2>
          <p className="text-lg text-gray-600 leading-relaxed max-w-4xl mx-auto text-center">
            房都督AI致力于通过人工智能技术，为用户提供透明、高效、可信赖的房产分析服务。
            我们相信，数据驱动的决策能够帮助用户做出更明智的房产投资选择。
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {values.map((value, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
              className="bg-gray-50 rounded-2xl p-8 text-center"
            >
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <value.icon className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">{value.title}</h3>
              <p className="text-gray-600">{value.description}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-16"
        >
          <div className="flex items-center justify-center gap-2 mb-8">
            <StarIcon className="w-6 h-6 text-yellow-500" />
            <h2 className="text-3xl font-bold text-gray-900">核心成员</h2>
            <StarIcon className="w-6 h-6 text-yellow-500" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {coreMembers.map((member, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 text-center border-2 border-blue-200 shadow-lg relative overflow-hidden"
              >
                <div className="absolute top-3 right-3">
                  <StarIcon className="w-6 h-6 text-yellow-500" />
                </div>
                <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <span className="text-3xl font-bold text-white">{member.initial}</span>
                </div>
                <h3 className="text-xl font-bold text-gray-900">{member.name}</h3>
                <p className="text-sm text-blue-600 font-semibold mb-3">{member.position}</p>
                <p className="text-gray-600 text-sm leading-relaxed">{member.bio}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">团队成员</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {teamMembers.map((member, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 + index * 0.05 }}
                className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start gap-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-lg font-bold text-gray-600">{member.initial}</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-900 mb-1">{member.name}</h3>
                    <p className="text-sm text-blue-600 font-medium mb-2">{member.position}</p>
                    <p className="text-gray-600 text-sm leading-relaxed">{member.bio}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="bg-gradient-to-r from-blue-600 to-blue-500 rounded-3xl p-8 text-center text-white"
        >
          <h2 className="text-2xl font-bold mb-4">加入我们</h2>
          <p className="mb-6">我们正在寻找热爱技术、追求卓越的人才加入我们的团队。</p>
          <a
            href="mailto:lichengyu@fangsuanyun.cn"
            className="inline-flex items-center gap-2 px-8 py-3 bg-white text-blue-600 rounded-full font-semibold hover:bg-gray-100 transition-colors"
          >
            <EnvelopeIcon className="w-5 h-5" />
            发送简历
          </a>
        </motion.div>

        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>© 2026 房都督AI 智能房产分析平台. 保留所有权利.</p>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
