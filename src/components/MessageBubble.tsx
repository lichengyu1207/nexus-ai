import React from 'react';
import { motion } from 'framer-motion';
import { CharacterAvatar } from './CharacterAvatar';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  persona?: string;
  timestamp?: string;
  isLoading?: boolean;
}

const personaConfig = {
  zhouyu: {
    name: '周瑜',
    bgColor: 'bg-gradient-to-br from-red-50 to-orange-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-900',
  },
  luxun: {
    name: '陆逊',
    bgColor: 'bg-gradient-to-br from-blue-50 to-cyan-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-900',
  },
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  role,
  content,
  persona = 'zhouyu',
  timestamp,
  isLoading = false,
}) => {
  const isUser = role === 'user';
  const config = personaConfig[persona as keyof typeof personaConfig] || personaConfig.zhouyu;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-end gap-2 max-w-[80%]`}>
        {!isUser && (
          <CharacterAvatar
            persona={persona}
            emotion={isLoading ? 'thinking' : 'default'}
            size="sm"
          />
        )}
        
        <div
          className={`
            relative px-4 py-3 rounded-2xl
            ${isUser 
              ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' 
              : `${config.bgColor} ${config.textColor} border ${config.borderColor}`
            }
            shadow-sm
          `}
        >
          {isLoading ? (
            <div className="flex items-center gap-2">
              <motion.div
                className="w-2 h-2 bg-gray-400 rounded-full"
                animate={{ scale: [1, 1.5, 1] }}
                transition={{ repeat: Infinity, duration: 1 }}
              />
              <motion.div
                className="w-2 h-2 bg-gray-400 rounded-full"
                animate={{ scale: [1, 1.5, 1] }}
                transition={{ repeat: Infinity, duration: 1, delay: 0.2 }}
              />
              <motion.div
                className="w-2 h-2 bg-gray-400 rounded-full"
                animate={{ scale: [1, 1.5, 1] }}
                transition={{ repeat: Infinity, duration: 1, delay: 0.4 }}
              />
            </div>
          ) : (
            <div className="whitespace-pre-wrap break-words">
              {content}
            </div>
          )}
          
          {timestamp && (
            <div className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-400'}`}>
              {timestamp}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export const MessageList: React.FC<{
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
  }>;
  persona?: string;
  isLoading?: boolean;
}> = ({ messages, persona = 'zhouyu', isLoading = false }) => {
  return (
    <div className="space-y-4">
      {messages.map((msg, idx) => (
        <MessageBubble
          key={idx}
          role={msg.role}
          content={msg.content}
          persona={persona}
          timestamp={msg.timestamp}
        />
      ))}
      {isLoading && (
        <MessageBubble
          role="assistant"
          content=""
          persona={persona}
          isLoading={true}
        />
      )}
    </div>
  );
};

export default MessageBubble;
