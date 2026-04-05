import React from 'react';

interface ScrollAreaProps {
  children: React.ReactNode;
  className?: string;
}

const ScrollArea: React.FC<ScrollAreaProps> = ({ children, className = '' }) => (
  <div className={`overflow-y-auto ${className}`}>
    {children}
  </div>
);

export default ScrollArea;
export { ScrollArea };
