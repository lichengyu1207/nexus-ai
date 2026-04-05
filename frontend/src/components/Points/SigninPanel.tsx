import React, { useState, useEffect } from 'react';
import { pointsApi, SigninStatus } from '../../api/points';
import { useAuth } from '../../hooks/useAuth';

const REWARDS = [10, 20, 30, 50, 80, 120, 200];

export const SigninPanel: React.FC = () => {
  const { user } = useAuth();
  const [status, setStatus] = useState<SigninStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await pointsApi.getSigninStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to load signin status:', error);
    }
  };

  const handleSignin = async () => {
    if (loading || status?.today_signed) return;
    
    setLoading(true);
    try {
      const result = await pointsApi.doSignin();
      setMessage(result.message);
      await loadStatus();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      setMessage(err.response?.data?.detail || '签到失败');
    } finally {
      setLoading(false);
    }
  };

  const today = new Date();
  const currentDay = today.getDate();
  const currentMonth = today.getMonth();
  const currentYear = today.getFullYear();

  const getDaysInMonth = (month: number, year: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (month: number, year: number) => {
    return new Date(year, month, 1).getDay();
  };

  const isSigned = (day: number) => {
    const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return status?.signed_dates.includes(dateStr);
  };

  const daysInMonth = getDaysInMonth(currentMonth, currentYear);
  const firstDay = getFirstDayOfMonth(currentMonth, currentYear);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-md mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">每日签到</h2>
        <p className="text-gray-500">连续签到获得更多积分奖励</p>
      </div>

      {message && (
        <div className={`mb-4 p-3 rounded-lg ${status?.today_signed ? 'bg-green-50 text-green-700' : 'bg-blue-50 text-blue-700'}`}>
          {message}
        </div>
      )}

      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <span className="text-lg font-medium">
            {currentYear}年{currentMonth + 1}月
          </span>
          <span className="text-sm text-gray-500">
            连续签到: {status?.consecutive_days || 0}天
          </span>
        </div>

        <div className="grid grid-cols-7 gap-1 text-center text-sm">
          {['日', '一', '二', '三', '四', '五', '六'].map((day) => (
            <div key={day} className="py-2 text-gray-500 font-medium">
              {day}
            </div>
          ))}
          
          {Array.from({ length: firstDay }).map((_, i) => (
            <div key={`empty-${i}`} />
          ))}
          
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1;
            const signed = isSigned(day);
            const isToday = day === currentDay;
            
            return (
              <div
                key={day}
                className={`py-2 rounded-lg cursor-default transition-colors
                  ${signed ? 'bg-green-500 text-white' : 'text-gray-700'}
                  ${isToday && !signed ? 'ring-2 ring-blue-500' : ''}
                  ${isToday ? 'font-bold' : ''}
                `}
              >
                {day}
              </div>
            );
          })}
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">签到奖励规则</h3>
        <div className="grid grid-cols-7 gap-1 text-center text-xs">
          {REWARDS.map((reward, index) => (
            <div
              key={index}
              className={`py-2 px-1 rounded-lg ${
                index < (status?.consecutive_days || 0)
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              <div className="font-medium">第{index + 1}天</div>
              <div className="text-green-600 font-bold">+{reward}</div>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={handleSignin}
        disabled={loading || status?.today_signed}
        className={`w-full py-3 rounded-lg font-medium text-white transition-colors
          ${status?.today_signed
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700'
          }
          ${loading ? 'opacity-50' : ''}
        `}
      >
        {loading ? '签到中...' : status?.today_signed ? '今日已签到' : `签到 (+${status?.today_reward || REWARDS[0]}积分)`}
      </button>
    </div>
  );
};

export default SigninPanel;
