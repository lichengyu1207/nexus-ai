import React from 'react';
import { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  const avatar = message.agent === 'zhouyu' ? '🎵' : message.agent === 'luxun' ? '📜' : null;

  if (isUser) {
    return (
      <div className="message user">
        <div className="message-content">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="message agent">
      <div className="agent-info">
        {avatar && <span className="agent-avatar">{avatar}</span>}
        <div className="message-content">
          {message.content}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
