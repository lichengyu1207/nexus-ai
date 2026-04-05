import React from 'react';
import { ShieldCheckIcon, UserGroupIcon, BoltIcon, ClockIcon } from '@heroicons/react/24/outline';

const trustTags = [
  {
    icon: ShieldCheckIcon,
    label: '数据加密',
    description: '银行级安全防护',
  },
  {
    icon: UserGroupIcon,
    label: '10万+用户',
    description: '真实用户信赖',
  },
  {
    icon: BoltIcon,
    label: '秒级响应',
    description: 'AI快速分析',
  },
  {
    icon: ClockIcon,
    label: '7x24服务',
    description: '全天候在线',
  },
];

const TrustBadges: React.FC = () => {
  return (
    <div className="flex flex-wrap justify-center gap-6 md:gap-8 py-6">
      {trustTags.map((tag) => (
        <div
          key={tag.label}
          className="flex items-center space-x-2 text-gray-600"
        >
          <tag.icon className="w-5 h-5 text-primary-600" />
          <div className="text-sm">
            <span className="font-medium text-gray-900">{tag.label}</span>
            <span className="hidden md:inline ml-1 text-gray-500">
              {tag.description}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TrustBadges;
