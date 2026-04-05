import { motion } from 'framer-motion';
import Mascot from '@/components/mascot/Mascot';

const agents = [
  {
    name: '需求分析师',
    desc: '理解您的分析需求',
    emotion: 'thinking',
    pose: 'standing',
  },
  {
    name: '数据采集师',
    desc: '收集房产相关数据',
    emotion: 'happy',
    pose: 'waving',
  },
  {
    name: '市场分析师',
    desc: '深度分析市场趋势',
    emotion: 'default',
    pose: 'sitting',
  },
];

const TeamSection: React.FC = () => {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">认识你的AI团队</h2>
        <p className="text-lg text-gray-600 text-center mb-12">
          我们不只是分析数据，更是帮你做出明智决策的智能伙伴
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {agents.map((agent, idx) => (
            <div key={idx} className="text-center p-6 rounded-2xl bg-gray-50 hover:shadow-lg transition">
              <div className="flex justify-center mb-4">
                <Mascot emotion={agent.emotion as any} pose={agent.pose as any} size="lg" />
              </div>
              <h3 className="text-xl font-semibold mb-2">{agent.name}</h3>
              <p className="text-gray-600">{agent.desc}</p>
            </div>
          ))}
        </div>
        
        <div className="mt-16 flex items-center justify-center gap-4 text-gray-500">
          <Mascot emotion="happy" pose="waving" size="sm" />
          <span className="text-sm">我们的AI团队24小时在线，随时为您服务</span>
          <Mascot emotion="default" pose="standing" size="sm" />
        </div>
      </div>
    </section>
  );
};

export default TeamSection;
