import React, { useState, useEffect } from 'react';
import { disambiguateApi, DisambiguationCandidate } from '../services/api';

interface AmbiguousField {
  field: string;
  value: string;
  message: string;
  candidate_count: number;
}

interface DisambiguationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selections: Record<string, DisambiguationCandidate>) => void;
  query: string;
  ambiguousFields: AmbiguousField[];
  context?: Record<string, unknown>;
}

const DisambiguationModal: React.FC<DisambiguationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  query,
  ambiguousFields,
  context
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [candidates, setCandidates] = useState<DisambiguationCandidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<DisambiguationCandidate | null>(null);
  const [selections, setSelections] = useState<Record<string, DisambiguationCandidate>>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (isOpen && ambiguousFields.length > 0) {
      setCurrentIndex(0);
      setSelections({});
      loadCandidates(ambiguousFields[0]);
    }
  }, [isOpen, ambiguousFields]);

  const loadCandidates = async (field: AmbiguousField) => {
    setLoading(true);
    setSelectedCandidate(null);
    try {
      const result = await disambiguateApi.resolve({
        query,
        ambiguous_field: field.field,
        current_value: field.value,
        context
      });
      
      setCandidates(result.candidates);
      setMessage(result.message);
      
      if (!result.requires_selection && result.candidates.length === 1) {
        setSelectedCandidate(result.candidates[0]);
      }
    } catch (err) {
      console.error('Failed to load candidates:', err);
      setCandidates([]);
      setMessage('无法加载候选选项');
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (candidate: DisambiguationCandidate) => {
    setSelectedCandidate(candidate);
  };

  const handleNext = () => {
    if (!selectedCandidate) return;

    const currentField = ambiguousFields[currentIndex];
    const newSelections = {
      ...selections,
      [currentField.field]: selectedCandidate
    };
    setSelections(newSelections);

    if (currentIndex < ambiguousFields.length - 1) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      loadCandidates(ambiguousFields[nextIndex]);
    } else {
      onConfirm(newSelections);
    }
  };

  const handleSkip = () => {
    if (currentIndex < ambiguousFields.length - 1) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      loadCandidates(ambiguousFields[nextIndex]);
    } else {
      onConfirm(selections);
    }
  };

  if (!isOpen || ambiguousFields.length === 0) return null;

  const currentField = ambiguousFields[currentIndex];
  const progress = ((currentIndex + 1) / ambiguousFields.length) * 100;

  const fieldLabels: Record<string, string> = {
    district: '区域',
    community: '小区',
    city: '城市'
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />
      
      <div className="relative bg-white rounded-xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden">
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold flex items-center">
                <span className="mr-2">🤔</span>
                需要您的确认
              </h2>
              <p className="text-amber-100 text-sm mt-1">
                请帮我们确认一下具体位置
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-amber-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div className="mt-3">
            <div className="flex items-center justify-between text-sm text-amber-100 mb-1">
              <span>进度 {currentIndex + 1}/{ambiguousFields.length}</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-amber-300 rounded-full h-2">
              <div 
                className="bg-white rounded-full h-2 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <div className="flex items-center space-x-2 text-gray-600 mb-2">
              <span className="text-lg">📍</span>
              <span className="font-medium">{fieldLabels[currentField.field] || currentField.field}</span>
            </div>
            <p className="text-gray-800">{message}</p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
            </div>
          ) : (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {candidates.map((candidate, index) => (
                <button
                  key={index}
                  onClick={() => handleSelect(candidate)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    selectedCandidate?.value === candidate.value
                      ? 'border-amber-500 bg-amber-50'
                      : 'border-gray-200 hover:border-amber-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium text-gray-900">{candidate.label}</div>
                      {candidate.description && (
                        <div className="text-sm text-gray-500 mt-1">{candidate.description}</div>
                      )}
                    </div>
                    {candidate.avg_price && (
                      <div className="text-right">
                        <div className="text-sm text-gray-500">均价</div>
                        <div className="text-amber-600 font-medium">
                          {(candidate.avg_price / 10000).toFixed(1)}万/㎡
                        </div>
                      </div>
                    )}
                  </div>
                  {selectedCandidate?.value === candidate.value && (
                    <div className="mt-2 flex items-center text-amber-600 text-sm">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      已选择
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}

          {!loading && candidates.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              未找到匹配的候选选项
            </div>
          )}
        </div>

        <div className="border-t px-6 py-4 bg-gray-50 flex justify-between">
          <button
            onClick={handleSkip}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            跳过此项
          </button>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleNext}
              disabled={!selectedCandidate}
              className="px-6 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {currentIndex < ambiguousFields.length - 1 ? '下一步' : '确认'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DisambiguationModal;
