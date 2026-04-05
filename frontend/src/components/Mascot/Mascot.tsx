import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import Draggable, { DraggableData, DraggableEvent } from 'react-draggable';
import { useUIStore, useUserStore, useSourceStore } from '../../stores';

type Emotion = 'happy' | 'thinking' | 'excited' | 'confused' | 'sleepy' | 'wink';
type Pose = 'standing' | 'sitting' | 'pointing' | 'waving';

interface Quote {
  text: string;
  emotion?: Emotion;
}

const quotes: Quote[] = [
  { text: '有什么可以帮您的吗？', emotion: 'happy' },
  { text: '房产分析找我，准没错！', emotion: 'excited' },
  { text: '让我想想...', emotion: 'thinking' },
  { text: '您今天分析了几套房？', emotion: 'wink' },
  { text: '数据都在我脑子里呢~', emotion: 'happy' },
  { text: '买房是大事，让我帮您参谋参谋！', emotion: 'pointing' },
  { text: '累了就休息一下吧~', emotion: 'sleepy' },
  { text: '这个区域我熟，听我给您分析！', emotion: 'excited' },
  { text: '有疑问随时问我哦！', emotion: 'waving' },
  { text: '房都督AI，您的智能房产顾问！', emotion: 'happy' },
];

const sourceQuotes: Record<string, Quote[]> = {
  laohai: [
    { text: '老骇的朋友，欢迎你！', emotion: 'excited' },
    { text: '听说你是老骇推荐的？眼光不错！', emotion: 'wink' },
  ],
  seo: [
    { text: '找到我们啦！', emotion: 'happy' },
    { text: '搜索达人就是你！', emotion: 'excited' },
  ],
  social: [
    { text: '社交媒体的朋友你好！', emotion: 'waving' },
    { text: '感谢关注我们！', emotion: 'happy' },
  ],
};

const pageEmotions: Record<string, { emotion: Emotion; pose: Pose }> = {
  '/': { emotion: 'happy', pose: 'waving' },
  '/dashboard': { emotion: 'happy', pose: 'standing' },
  '/dashboard/property-analysis': { emotion: 'thinking', pose: 'standing' },
  '/dashboard/my-reports': { emotion: 'happy', pose: 'sitting' },
  '/dashboard/integral': { emotion: 'excited', pose: 'standing' },
  '/dashboard/recharge': { emotion: 'excited', pose: 'pointing' },
  '/help': { emotion: 'happy', pose: 'waving' },
};

const emotionEmojis: Record<Emotion, string> = {
  happy: '🐕',
  thinking: '🤔',
  excited: '🎉',
  confused: '😕',
  sleepy: '😴',
  wink: '😉',
};

const Mascot: React.FC = () => {
  const location = useLocation();
  const { mascotEnabled, mascotPosition, setMascotPosition, toggleMascot } = useUIStore();
  const { user, isAuthenticated } = useUserStore();
  const { source } = useSourceStore();
  
  const [showBubble, setShowBubble] = useState(false);
  const [currentQuote, setCurrentQuote] = useState<Quote>(quotes[0]);
  const [currentEmotion, setCurrentEmotion] = useState<Emotion>('happy');
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: mascotPosition.x, y: mascotPosition.y });

  useEffect(() => {
    const pageConfig = pageEmotions[location.pathname];
    if (pageConfig) {
      setCurrentEmotion(pageConfig.emotion);
    }
  }, [location.pathname]);

  useEffect(() => {
    if (source && sourceQuotes[source]) {
      const sourceSpecificQuotes = sourceQuotes[source];
      if (sourceSpecificQuotes.length > 0) {
        setTimeout(() => {
          const randomQuote = sourceSpecificQuotes[Math.floor(Math.random() * sourceSpecificQuotes.length)];
          setCurrentQuote(randomQuote);
          if (randomQuote.emotion) {
            setCurrentEmotion(randomQuote.emotion);
          }
          setShowBubble(true);
          setTimeout(() => setShowBubble(false), 5000);
        }, 2000);
      }
    }
  }, [source]);

  const handleClick = useCallback(() => {
    if (isDragging) return;
    
    const allQuotes = [...quotes];
    if (source && sourceQuotes[source]) {
      allQuotes.push(...sourceQuotes[source]);
    }
    
    const randomQuote = allQuotes[Math.floor(Math.random() * allQuotes.length)];
    setCurrentQuote(randomQuote);
    if (randomQuote.emotion) {
      setCurrentEmotion(randomQuote.emotion);
    }
    setShowBubble(true);
    
    setTimeout(() => setShowBubble(false), 4000);
  }, [isDragging, source]);

  const handleDrag = (_e: DraggableEvent, data: DraggableData) => {
    setPosition({ x: data.x, y: data.y });
  };

  const handleDragStart = () => {
    setIsDragging(true);
  };

  const handleDragStop = (_e: DraggableEvent, data: DraggableData) => {
    setMascotPosition({ x: data.x, y: data.y });
    setTimeout(() => setIsDragging(false), 100);
  };

  if (!mascotEnabled) {
    return (
      <button
        onClick={toggleMascot}
        className="fixed bottom-6 right-6 z-50 bg-gray-200 rounded-full p-2 hover:bg-gray-300 transition-colors"
        title="显示吉祥物"
      >
        🐕
      </button>
    );
  }

  return (
    <Draggable
      position={position}
      onDrag={handleDrag}
      onStart={handleDragStart}
      onStop={handleDragStop}
      bounds="parent"
    >
      <div className="fixed bottom-6 right-6 z-50 cursor-move select-none">
        {/* 对话气泡 */}
        {showBubble && (
          <div className="absolute bottom-full right-0 mb-2 w-48 bg-white rounded-lg shadow-lg p-3 animate-fade-in">
            <p className="text-sm text-gray-700">{currentQuote.text}</p>
            <div className="absolute bottom-0 right-4 transform translate-y-1/2 rotate-45 w-3 h-3 bg-white shadow-lg"></div>
          </div>
        )}
        
        {/* 吉祥物主体 */}
        <div
          onClick={handleClick}
          className={`relative w-16 h-16 bg-yellow-400 rounded-full flex items-center justify-center text-3xl shadow-lg cursor-pointer hover:scale-110 transition-transform ${
            currentEmotion === 'excited' ? 'animate-bounce' : ''
          }`}
        >
          {emotionEmojis[currentEmotion]}
          
          {/* 状态指示器 */}
          {isAuthenticated && user?.integral !== undefined && user.integral < 5 && (
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs">!</span>
            </div>
          )}
        </div>
        
        {/* 关闭按钮 */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            toggleMascot();
          }}
          className="absolute -top-2 -left-2 w-5 h-5 bg-gray-400 rounded-full flex items-center justify-center text-white text-xs hover:bg-gray-500"
        >
          ✕
        </button>
      </div>
    </Draggable>
  );
};

export default Mascot;
