import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MapPinIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  LockClosedIcon,
  SparklesIcon,
  ArrowRightIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import { PreviewResult } from '@/services/previewApi';
import Mascot from '@/components/mascot/Mascot';

interface PreviewResultCardProps {
  result: PreviewResult;
  onClose?: () => void;
}

const PreviewResultCard: React.FC<PreviewResultCardProps> = ({ result, onClose }) => {
  const navigate = useNavigate();

  const handleRegister = () => {
    sessionStorage.setItem('preview_query', result.query);
    navigate('/register');
  };

  const formatPrice = (price: number) => {
    return (price / 10000).toFixed(1);
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden max-w-2xl mx-auto">
      <div className="bg-gradient-to-r from-primary-500 to-primary-700 p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold mb-1">预览分析结果</h3>
            <p className="text-primary-100 text-sm">{result.query}</p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-full transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="p-6">
        {result.location && (result.location.city || result.location.district) && (
          <div className="flex items-center gap-2 mb-4 text-gray-600">
            <MapPinIcon className="w-5 h-5 text-primary-500" />
            <span>
              {[result.location.city, result.location.district, result.location.community]
                .filter(Boolean)
                .join(' · ')}
            </span>
          </div>
        )}

        {result.market_overview && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">
                {formatPrice(result.market_overview.avg_price)}
              </p>
              <p className="text-xs text-gray-500">均价(万/㎡)</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">
                {result.market_overview.price_trend}
              </p>
              <p className="text-xs text-gray-500">价格趋势</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 text-center">
              <p className={`text-2xl font-bold ${result.market_overview.year_change > 0 ? 'text-red-500' : 'text-green-500'}`}>
                {result.market_overview.year_change > 0 ? '+' : ''}{result.market_overview.year_change}%
              </p>
              <p className="text-xs text-gray-500">年涨幅</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">
                {result.market_overview.transaction_volume}
              </p>
              <p className="text-xs text-gray-500">成交量</p>
            </div>
          </div>
        )}

        {result.key_highlights && result.key_highlights.length > 0 && (
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-yellow-500" />
              核心发现
            </h4>
            <ul className="space-y-2">
              {result.key_highlights.map((highlight, index) => (
                <li key={index} className="flex items-start gap-2 text-gray-600">
                  <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.sample_report_sections && result.sample_report_sections.length > 0 && (
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <ChartBarIcon className="w-5 h-5 text-primary-500" />
              报告预览
            </h4>
            <div className="space-y-2">
              {result.sample_report_sections.map((section, index) => (
                <div key={index} className="relative">
                  <p className="text-gray-600 text-sm line-clamp-2">{section}</p>
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-white pointer-events-none"></div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-6 border border-primary-100">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <Mascot emotion="happy" size="lg" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 mb-2">
                {result.registration_incentive.title}
              </h4>
              <ul className="space-y-1 mb-4">
                {result.registration_incentive.benefits.map((benefit, index) => (
                  <li key={index} className="flex items-center gap-2 text-sm text-gray-600">
                    <LockClosedIcon className="w-4 h-4 text-primary-500" />
                    {benefit}
                  </li>
                ))}
              </ul>
              <button
                onClick={handleRegister}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
              >
                {result.registration_incentive.cta_text}
                <ArrowRightIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreviewResultCard;
