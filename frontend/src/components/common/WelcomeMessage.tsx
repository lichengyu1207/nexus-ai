import React from 'react'

interface WelcomeMessageProps {
  source: string | null
  sourceName: string | null
  bonusLabel: string | null
  username: string | null
}

const sourceConfig: Record<string, { message: string; emoji: string; color: string }> = {
  laohai: {
    message: '老骇的朋友，你好！',
    emoji: '👋',
    color: 'bg-gradient-to-r from-purple-500 to-pink-500'
  },
  seo: {
    message: '我找到你关心的区域了！',
    emoji: '🔍',
    color: 'bg-gradient-to-r from-blue-500 to-cyan-500'
  },
  urgent: {
    message: '时间宝贵，我们直接开始！',
    emoji: '⏰',
    color: 'bg-gradient-to-r from-orange-500 to-red-500'
  },
  direct: {
    message: '欢迎来到房都督AI！',
    emoji: '🏠',
    color: 'bg-gradient-to-r from-green-500 to-teal-500'
  }
}

const WelcomeMessage: React.FC<WelcomeMessageProps> = ({ 
  source, 
  sourceName, 
  bonusLabel, 
  username 
}) => {
  const config = sourceConfig[source || 'direct'] || sourceConfig.direct
  
  return (
    <div className={`${config.color} rounded-lg p-4 mb-4 text-white shadow-lg`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{config.emoji}</span>
          <div>
            <p className="font-medium text-lg">
              {config.message}
              {username && <span className="ml-2 opacity-90">{username}</span>}
            </p>
            {sourceName && (
              <p className="text-sm opacity-80 mt-1">
                来源: {sourceName}
              </p>
            )}
          </div>
        </div>
        {bonusLabel && (
          <div className="bg-white/20 backdrop-blur-sm rounded-full px-4 py-1.5 text-sm font-medium">
            🎁 {bonusLabel}
          </div>
        )}
      </div>
    </div>
  )
}

export default WelcomeMessage
