import React, { useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, isLoading }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="input-section">
      <textarea
        className="message-input"
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="倾诉你的烦恼..."
        disabled={isLoading}
        rows={1}
      />
      <button
        className="send-btn"
        onClick={handleSend}
        disabled={isLoading || !input.trim()}
      >
        {isLoading ? '发送中...' : '发送'}
      </button>
    </div>
  );
};

export default ChatInput;
