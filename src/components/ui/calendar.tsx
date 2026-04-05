import React, { useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface CalendarProps {
  mode?: 'single' | 'range';
  selected?: Date | Date[] | undefined;
  onSelect?: (date: Date | undefined) => void;
  onDayClick?: (date: Date) => void;
  disabled?: (date: Date) => boolean;
  className?: string;
  signedDays?: number[];
  currentMonth?: number;
}

const Calendar: React.FC<CalendarProps> = ({
  mode = 'single',
  selected,
  onSelect,
  onDayClick,
  disabled,
  className = '',
  signedDays = [],
  currentMonth,
}) => {
  const today = new Date();
  const [viewDate, setViewDate] = useState(selected instanceof Date ? selected : today);
  
  const year = viewDate.getFullYear();
  const month = currentMonth !== undefined ? currentMonth : viewDate.getMonth();
  
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startDayOfWeek = firstDay.getDay();
  
  const days = [];
  for (let i = 0; i < startDayOfWeek; i++) {
    days.push(null);
  }
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(i);
  }
  
  const prevMonth = () => {
    setViewDate(new Date(year, month - 1, 1));
  };
  
  const nextMonth = () => {
    setViewDate(new Date(year, month + 1, 1));
  };
  
  const handleDayClick = (day: number) => {
    const date = new Date(year, month, day);
    if (disabled && disabled(date)) return;
    if (onDayClick) onDayClick(date);
    if (onSelect) onSelect(date);
  };
  
  const isSelected = (day: number) => {
    if (!selected) return false;
    const date = new Date(year, month, day);
    if (selected instanceof Date) {
      return date.toDateString() === selected.toDateString();
    }
    return false;
  };
  
  const isToday = (day: number) => {
    const date = new Date(year, month, day);
    return date.toDateString() === today.toDateString();
  };
  
  const isSigned = (day: number) => {
    return signedDays.includes(day);
  };
  
  const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'];
  const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
  
  return (
    <div className={`p-4 bg-white dark:bg-gray-800 rounded-lg ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={prevMonth}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
        >
          <ChevronLeftIcon className="w-5 h-5" />
        </button>
        <span className="font-medium text-gray-900 dark:text-white">
          {year}年 {monthNames[month]}
        </span>
        <button
          onClick={nextMonth}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
        >
          <ChevronRightIcon className="w-5 h-5" />
        </button>
      </div>
      
      <div className="grid grid-cols-7 gap-1">
        {weekDays.map((day) => (
          <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
            {day}
          </div>
        ))}
        
        {days.map((day, index) => (
          <div key={index} className="aspect-square">
            {day && (
              <button
                onClick={() => handleDayClick(day)}
                disabled={disabled && disabled(new Date(year, month, day))}
                className={`
                  w-full h-full flex items-center justify-center rounded-md text-sm
                  transition-colors relative
                  ${isSelected(day) ? 'bg-primary-600 text-white' : ''}
                  ${isToday(day) && !isSelected(day) ? 'ring-2 ring-primary-500' : ''}
                  ${isSigned(day) && !isSelected(day) ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : ''}
                  ${!isSelected(day) && !isSigned(day) ? 'hover:bg-gray-100 dark:hover:bg-gray-700' : ''}
                  ${disabled && disabled(new Date(year, month, day)) ? 'text-gray-300 cursor-not-allowed' : ''}
                `}
              >
                {day}
                {isSigned(day) && (
                  <span className="absolute bottom-1 w-1 h-1 bg-green-500 rounded-full" />
                )}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Calendar;
export { Calendar };
