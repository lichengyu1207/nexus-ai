import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation } from 'react-router-dom';
import { CurrencyDollarIcon, StarIcon } from '@heroicons/react/24/outline';
import { integralApi } from '@/services/api';

const IntegralBadge: React.FC = () => {
  const location = useLocation();
  
  const { data: integralInfo } = useQuery({
    queryKey: ['integral'],
    queryFn: integralApi.getIntegral,
    staleTime: 60000, // 1分钟内不重新请求
  });

  const isMember = integralInfo?.is_member;
  const integral = integralInfo?.integral ?? 0;

  return (
    <Link
      to="/integral"
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full transition-colors ${
        location.pathname === '/integral'
          ? 'bg-primary-100 text-primary-700'
          : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
      }`}
    >
      {isMember ? (
        <>
          <StarIcon className="w-4 h-4 text-yellow-500" />
          <span className="text-sm font-medium">会员</span>
        </>
      ) : (
        <>
          <CurrencyDollarIcon className="w-4 h-4 text-primary-600" />
          <span className="text-sm font-medium">{integral}</span>
        </>
      )}
    </Link>
  );
};

export default IntegralBadge;
