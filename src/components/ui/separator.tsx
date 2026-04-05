import React from 'react';

interface SeparatorProps {
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

const Separator: React.FC<SeparatorProps> = ({ orientation = 'horizontal', className = '' }) => (
  <div
    className={`shrink-0 bg-gray-200 ${
      orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]'
    } ${className}`}
  />
);

export default Separator;
export { Separator };
