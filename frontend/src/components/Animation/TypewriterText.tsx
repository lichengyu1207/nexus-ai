import React, { useState, useEffect } from 'react';

interface TypewriterTextProps {
  texts: string[];
  speed?: number;
  deleteSpeed?: number;
  pauseTime?: number;
  className?: string;
  cursorChar?: string;
  loop?: boolean;
}

const TypewriterText: React.FC<TypewriterTextProps> = ({
  texts,
  speed = 100,
  deleteSpeed = 50,
  pauseTime = 2000,
  className = '',
  cursorChar = '|',
  loop = true,
}) => {
  const [displayText, setDisplayText] = useState('');
  const [textIndex, setTextIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (texts.length === 0) return;

    const currentText = texts[textIndex];
    
    if (isPaused) {
      const pauseTimer = setTimeout(() => {
        setIsPaused(false);
        setIsDeleting(true);
      }, pauseTime);
      return () => clearTimeout(pauseTimer);
    }

    const timer = setTimeout(() => {
      if (!isDeleting) {
        if (displayText.length < currentText.length) {
          setDisplayText(currentText.slice(0, displayText.length + 1));
        } else {
          setIsPaused(true);
        }
      } else {
        if (displayText.length > 0) {
          setDisplayText(displayText.slice(0, -1));
        } else {
          setIsDeleting(false);
          const nextIndex = (textIndex + 1) % texts.length;
          if (nextIndex === 0 && !loop) {
            return;
          }
          setTextIndex(nextIndex);
        }
      }
    }, isDeleting ? deleteSpeed : speed);

    return () => clearTimeout(timer);
  }, [displayText, isDeleting, isPaused, textIndex, texts, speed, deleteSpeed, pauseTime, loop]);

  return (
    <span className={className}>
      {displayText}
      <span className="animate-blink">{cursorChar}</span>
    </span>
  );
};

interface TypewriterHeadingProps {
  staticText: string;
  dynamicTexts: string[];
  className?: string;
}

const TypewriterHeading: React.FC<TypewriterHeadingProps> = ({
  staticText,
  dynamicTexts,
  className = '',
}) => {
  return (
    <h1 className={className}>
      {staticText}
      <br />
      <TypewriterText
        texts={dynamicTexts}
        speed={80}
        deleteSpeed={40}
        pauseTime={2500}
        className="text-fluent-gold-500"
      />
    </h1>
  );
};

interface TypewriterPromoProps {
  className?: string;
}

const TypewriterPromo: React.FC<TypewriterPromoProps> = ({ className = '' }) => {
  const promoTexts = [
    '多智能体协同分析',
    '3分钟生成专业报告',
    '数据可溯源可验证',
    '让房产决策更明智',
    'AI赋能房产投资',
  ];

  return (
    <div className={`typewriter-promo ${className}`}>
      <div className="text-2xl md:text-3xl lg:text-4xl font-bold text-fluent-deepOcean-500">
        <TypewriterText
          texts={promoTexts}
          speed={60}
          deleteSpeed={30}
          pauseTime={3000}
          cursorChar="_"
        />
      </div>
    </div>
  );
};

export { TypewriterText, TypewriterHeading, TypewriterPromo };
export default TypewriterText;
