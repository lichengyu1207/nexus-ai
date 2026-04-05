import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

const ProgressBar: React.FC = () => {
  const location = useLocation();
  const [progress, setProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    setProgress(0);

    const timer1 = setTimeout(() => setProgress(30), 50);
    const timer2 = setTimeout(() => setProgress(60), 150);
    const timer3 = setTimeout(() => setProgress(90), 300);
    const timer4 = setTimeout(() => {
      setProgress(100);
      setTimeout(() => setIsLoading(false), 200);
    }, 500);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
    };
  }, [location.pathname]);

  if (!isLoading) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[9999] h-1 bg-transparent">
      <div
        className="h-full bg-primary-600 transition-all duration-200 ease-out"
        style={{ width: `${progress}%` }}
      >
        <div className="absolute right-0 top-0 h-full w-24 bg-gradient-to-r from-transparent to-primary-400 opacity-50" />
      </div>
    </div>
  );
};

export default ProgressBar;
