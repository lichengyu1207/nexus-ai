import React, { useState, useEffect } from 'react';
import { districtInfoApi, DistrictInfo } from '../services/api';

interface DistrictInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  city: string;
  district?: string;
}

const DistrictInfoModal: React.FC<DistrictInfoModalProps> = ({
  isOpen,
  onClose,
  city,
  district
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<DistrictInfo | null>(null);
  const [activeTab, setActiveTab] = useState<'intro' | 'transport' | 'edu' | 'commercial' | 'future'>('intro');

  useEffect(() => {
    if (isOpen && city && district) {
      fetchDistrictInfo();
    }
  }, [isOpen, city, district]);

  const fetchDistrictInfo = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await districtInfoApi.getDetail(city, district || '');
      setInfo(data);
    } catch (err) {
      setError('暂无该区域信息');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const tabs = [
    { key: 'intro', label: '区域简介', icon: '📍' },
    { key: 'transport', label: '交通', icon: '🚇' },
    { key: 'edu', label: '教育', icon: '🎓' },
    { key: 'commercial', label: '商业', icon: '🏪' },
    { key: 'future', label: '规划', icon: '🏗️' },
  ];

  const getTabContent = () => {
    if (!info) return null;
    
    switch (activeTab) {
      case 'intro':
        return info.introduction;
      case 'transport':
        return info.transportation;
      case 'edu':
        return info.education;
      case 'commercial':
        return info.commercial;
      case 'future':
        return info.future_plan;
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />
      
      <div className="relative bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">
                {city} {district || ''} 区域介绍
              </h2>
              <p className="text-primary-100 text-sm mt-1">
                了解区域详情，辅助购房决策
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-primary-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="overflow-y-auto max-h-[calc(90vh-180px)]">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          )}

          {error && (
            <div className="text-center py-12 text-gray-500">
              <p>{error}</p>
            </div>
          )}

          {info && !loading && (
            <div className="p-6">
              <div className="flex space-x-2 mb-6 overflow-x-auto pb-2">
                {tabs.map(tab => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key as typeof activeTab)}
                    className={`flex items-center space-x-1 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                      activeTab === tab.key
                        ? 'bg-primary-100 text-primary-700'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    <span>{tab.icon}</span>
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>

              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {getTabContent() || '暂无信息'}
                </p>
              </div>

              {(info.pros?.length || info.cons?.length) ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {info.pros && info.pros.length > 0 && (
                    <div className="bg-green-50 rounded-lg p-4">
                      <h3 className="text-green-800 font-semibold mb-3 flex items-center">
                        <span className="mr-2">✅</span>
                        区域优势
                      </h3>
                      <ul className="space-y-2">
                        {info.pros.map((pro, index) => (
                          <li key={index} className="text-green-700 text-sm flex items-start">
                            <span className="mr-2">•</span>
                            {pro}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {info.cons && info.cons.length > 0 && (
                    <div className="bg-orange-50 rounded-lg p-4">
                      <h3 className="text-orange-800 font-semibold mb-3 flex items-center">
                        <span className="mr-2">⚠️</span>
                        注意事项
                      </h3>
                      <ul className="space-y-2">
                        {info.cons.map((con, index) => (
                          <li key={index} className="text-orange-700 text-sm flex items-start">
                            <span className="mr-2">•</span>
                            {con}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          )}
        </div>

        <div className="border-t px-6 py-4 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default DistrictInfoModal;
