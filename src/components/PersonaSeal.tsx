import React from 'react';
import { motion } from 'framer-motion';

type PersonaType = 'zhouyu' | 'luxun';

interface PersonaSealProps {
  persona: PersonaType;
  size?: 'sm' | 'md' | 'lg';
  showSignature?: boolean;
  signatureText?: string;
}

const SEAL_CONFIGS = {
  zhouyu: {
    name: '公瑾',
    color: '#C41E3A', // 红色印章
    bgImage: 'radial-gradient(circle, #C41E3A 0%, #8B0000 100%)',
    borderStyle: 'double',
    signature: '此报告乃瑜心血，望主公珍视',
  },
  luxun: {
    name: '伯言',
    color: '#1a1a1a', // 黑色印章
    bgImage: 'radial-gradient(circle, #2a2a2a 0%, #1a1a1a 100%)',
    borderStyle: 'solid',
    signature: '此报告已反复验证，可放心使用',
  },
};

const SIZE_MAP = {
  sm: { width: 60, height: 60, fontSize: 16 },
  md: { width: 80, height: 80, fontSize: 20 },
  lg: { width: 100, height: 100, fontSize: 24 },
};

export const PersonaSeal: React.FC<PersonaSealProps> = ({
  persona,
  size = 'md',
  showSignature = true,
  signatureText,
}) => {
  const config = SEAL_CONFIGS[persona];
  const sizeConfig = SIZE_MAP[size];
  const displaySignature = signatureText || config.signature;

  return (
    <div className="flex flex-col items-end">
      {/* 印章 */}
      <motion.div
        className="relative"
        initial={{ opacity: 0, rotate: -15, scale: 0.8 }}
        animate={{ opacity: 0.9, rotate: 0, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <div
          className="relative flex items-center justify-center"
          style={{
            width: sizeConfig.width,
            height: sizeConfig.height,
            background: config.bgImage,
            borderRadius: '8px',
            border: `3px ${config.borderStyle} ${config.color}`,
            boxShadow: '2px 2px 4px rgba(0,0,0,0.3)',
          }}
        >
          {/* 印章内部装饰 */}
          <div
            className="absolute inset-2 border border-white/30 rounded"
            style={{ borderColor: 'rgba(255,255,255,0.3)' }}
          />
          
          {/* 印章文字 */}
          <div className="relative z-10 text-center">
            <div
              className="text-white font-bold"
              style={{ fontSize: sizeConfig.fontSize }}
            >
              {config.name}
            </div>
            <div className="text-white/80 text-xs mt-1">之印</div>
          </div>
          
          {/* 印章纹理效果 */}
          <div
            className="absolute inset-0 opacity-20"
            style={{
              background: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 100 100\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noise\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.8\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noise)\'/%3E%3C/svg%3E")',
            }}
          />
        </div>
      </motion.div>

      {/* 签名寄语 */}
      {showSignature && (
        <motion.div
          className="mt-2 text-right"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <p
            className="text-sm italic"
            style={{
              color: config.color,
              fontFamily: 'serif',
            }}
          >
            "{displaySignature}"
          </p>
          <p className="text-xs text-gray-400 mt-1">
            —— {persona === 'zhouyu' ? '周瑜' : '陆逊'}
          </p>
        </motion.div>
      )}
    </div>
  );
};

export default PersonaSeal;
