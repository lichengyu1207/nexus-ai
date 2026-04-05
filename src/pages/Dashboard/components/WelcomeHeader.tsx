import { motion } from 'framer-motion';
import { ChevronDownIcon, SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import type { UserRole } from '../types';
import { ROLE_CONFIG } from '../types';

interface WelcomeHeaderProps {
  userName: string;
  role: UserRole;
  onRoleSwitch: (role: UserRole) => void;
  healthScore: number;
}

const HealthRing = ({ score }: { score: number }) => {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  
  const getColor = (s: number) => {
    if (s >= 80) return '#22c55e';
    if (s >= 60) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="relative w-24 h-24">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="8"
        />
        <motion.circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-bold text-white">{score}%</span>
      </div>
    </div>
  );
};

export function WelcomeHeader({ userName, role, onRoleSwitch, healthScore }: WelcomeHeaderProps) {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 6) return '夜深了';
    if (hour < 12) return '早上好';
    if (hour < 14) return '中午好';
    if (hour < 18) return '下午好';
    return '晚上好';
  };

  const getIcon = () => {
    const hour = new Date().getHours();
    return hour >= 6 && hour < 18 ? (
      <SunIcon className="w-5 h-5 text-amber-400" />
    ) : (
      <MoonIcon className="w-5 h-5 text-blue-400" />
    );
  };

  return (
    <div className="flex items-center justify-between px-6 py-4">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          {getIcon()}
          <span className="text-slate-400 text-sm">{getGreeting()}</span>
        </div>
        <h1 className="text-2xl font-bold text-white">{userName}</h1>
        
        <div className="relative">
          <select
            value={role}
            onChange={(e) => onRoleSwitch(e.target.value as UserRole)}
            className="appearance-none bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 pr-8 text-white text-sm focus:outline-none focus:border-amber-500/50 cursor-pointer"
          >
            <option value="requester">{ROLE_CONFIG.requester.label}</option>
            <option value="provider">{ROLE_CONFIG.provider.label}</option>
          </select>
          <ChevronDownIcon className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-sm text-slate-400">集群健康度</p>
          <p className="text-xs text-slate-500">{healthScore >= 80 ? '优秀' : healthScore >= 60 ? '良好' : '需关注'}</p>
        </div>
        <HealthRing score={healthScore} />
      </div>
    </div>
  );
}
