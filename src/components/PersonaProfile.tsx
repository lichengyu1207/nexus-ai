import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { api } from '../services/api';

type PersonaType = 'zhouyu' | 'luxun';

interface PersonaProfileProps {
  persona?: PersonaType;
  interactionCount?: number;
  memberSince?: string;
}

const PERSONA_STORIES = {
  zhouyu: {
    name: '周瑜',
    title: '公瑾',
    era: '东汉末年',
    birth: '175年',
    death: '210年',
    origin: '庐江舒县',
    style: '儒雅智谋，风度翩翩',
    description: '东吴大都督，儒雅风流，智谋超群。赤壁之战中，亲率水军大破曹操，奠定三分天下基础。精通音律，时人赞曰"曲有误，周郎顾"。',
    achievements: [
      { name: '赤壁之谋', description: '火烧赤壁，奠定三分天下', unlocked: true },
      { name: '羽扇纶巾', description: '谈笑间，樯橹灰飞烟灭', unlocked: true },
      { name: '曲有误周郎顾', description: '精通音律，风度翩翩', unlocked: false },
    ],
    quotes: [
      '主公此事，且听瑜一言。',
      '羽扇轻摇，数据尽在掌握。',
      '谈笑间，房价走势了然于胸。',
    ],
    colorPrimary: '#1E3A5F',
    colorSecondary: '#D4AF37',
    emoji: '🪭',
  },
  luxun: {
    name: '陆逊',
    title: '伯言',
    era: '三国时期',
    birth: '183年',
    death: '245年',
    origin: '吴郡吴县',
    style: '沉稳隐忍，后发制人',
    description: '东吴大都督，沉稳内敛，深谋远虑。夷陵之战中，坚守不战，待刘备军疲敝，火烧连营七百里，一战定荆州。被誉为"社稷之臣"。',
    achievements: [
      { name: '夷陵之智', description: '火烧连营，一战定荆州', unlocked: true },
      { name: '社稷之臣', description: '深谋远虑，值得信赖', unlocked: true },
      { name: '后发制人', description: '静观其变，一击必中', unlocked: false },
    ],
    quotes: [
      '主公且慢，听逊一言。',
      '房产之事，犹如用兵，需知彼知己。',
      '时机未至，当静观其变。',
    ],
    colorPrimary: '#2C5F2D',
    colorSecondary: '#B08D57',
    emoji: '⚔️',
  },
};

export const PersonaProfile: React.FC<PersonaProfileProps> = ({
  persona: initialPersona,
  interactionCount = 0,
  memberSince,
}) => {
  const [persona, setPersona] = useState<PersonaType>(initialPersona || 'zhouyu');
  const [activeTab, setActiveTab] = useState<'story' | 'achievements' | 'quotes'>('story');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!initialPersona) {
      fetchPersona();
    }
  }, [initialPersona]);

  const fetchPersona = async () => {
    try {
      setLoading(true);
      const response = await api.get('/consult/persona');
      setPersona(response.data.persona);
    } catch (error) {
      console.error('Failed to fetch persona:', error);
    } finally {
      setLoading(false);
    }
  };

  const config = PERSONA_STORIES[persona];

  if (loading) {
    return (
      <div className="animate-pulse bg-gray-100 rounded-xl p-6">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
        <div className="h-4 bg-gray-200 rounded w-2/3 mb-2" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      {/* 头部 */}
      <div
        className="p-6 text-white"
        style={{
          background: `linear-gradient(135deg, ${config.colorPrimary}, ${config.colorSecondary}40)`,
        }}
      >
        <div className="flex items-center space-x-4">
          <motion.div
            className="w-20 h-20 rounded-full flex items-center justify-center text-3xl"
            style={{
              background: `linear-gradient(135deg, ${config.colorPrimary}, ${config.colorSecondary})`,
              border: `3px solid ${config.colorSecondary}`,
            }}
            whileHover={{ scale: 1.05 }}
          >
            <span className="text-white font-bold text-2xl">{config.name[0]}</span>
          </motion.div>
          
          <div>
            <h2 className="text-2xl font-bold">
              {config.name} · {config.title}
            </h2>
            <p className="text-white/80 text-sm">{config.style}</p>
            <p className="text-white/60 text-xs mt-1">
              您的专属都督 · 互动 {interactionCount} 次
            </p>
          </div>
        </div>
      </div>

      {/* 标签页 */}
      <div className="border-b">
        <div className="flex">
          {(['story', 'achievements', 'quotes'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'text-primary-600 border-b-2 border-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={{
                color: activeTab === tab ? config.colorPrimary : undefined,
                borderColor: activeTab === tab ? config.colorPrimary : undefined,
              }}
            >
              {tab === 'story' && '人物小传'}
              {tab === 'achievements' && '成就徽章'}
              {tab === 'quotes' && '名言警句'}
            </button>
          ))}
        </div>
      </div>

      {/* 内容区 */}
      <div className="p-6">
        {activeTab === 'story' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-500">时代</p>
                <p className="font-medium">{config.era}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">籍贯</p>
                <p className="font-medium">{config.origin}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">生卒</p>
                <p className="font-medium">{config.birth} - {config.death}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">相伴时长</p>
                <p className="font-medium">{memberSince || '刚刚相识'}</p>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-gray-700 leading-relaxed">{config.description}</p>
            </div>
          </motion.div>
        )}

        {activeTab === 'achievements' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            {config.achievements.map((achievement, index) => (
              <div
                key={index}
                className={`flex items-center p-3 rounded-lg ${
                  achievement.unlocked
                    ? 'bg-amber-50 border border-amber-200'
                    : 'bg-gray-50 border border-gray-200 opacity-60'
                }`}
              >
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center mr-3"
                  style={{
                    background: achievement.unlocked
                      ? `linear-gradient(135deg, ${config.colorSecondary}, ${config.colorPrimary})`
                      : '#e5e7eb',
                  }}
                >
                  <span className="text-white text-lg">
                    {achievement.unlocked ? '🏆' : '🔒'}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-800">{achievement.name}</p>
                  <p className="text-xs text-gray-500">{achievement.description}</p>
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {activeTab === 'quotes' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            {config.quotes.map((quote, index) => (
              <motion.div
                key={index}
                className="relative pl-4 border-l-4 py-2"
                style={{ borderColor: config.colorSecondary }}
                whileHover={{ x: 4 }}
              >
                <p className="text-gray-700 italic">"{quote}"</p>
                <p className="text-xs text-gray-400 mt-1">—— {config.name}</p>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>

      {/* 底部嘟嘟装饰 */}
      <div className="px-6 pb-6">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>🐼 嘟嘟为您服务</span>
          <span>房都督 · 您的AI房产指挥官</span>
        </div>
      </div>
    </div>
  );
};

export default PersonaProfile;
