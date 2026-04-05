import React, { useState, useEffect, useCallback, useRef } from 'react';
import { taskApi, parseApi, disambiguateApi, ParsedQuery, DisambiguationCandidate } from '../services/api';
import DistrictInfoModal from './DistrictInfoModal';
import DetailedOptionsPanel from './DetailedOptionsPanel';
import DisambiguationModal from './DisambiguationModal';

interface AmbiguousField {
  field: string;
  value: string;
  message: string;
  candidate_count: number;
}

const QueryInput: React.FC = () => {
  const [query, setQuery] = useState('');
  const [parsedData, setParsedData] = useState<ParsedQuery | null>(null);
  const [showDetailedPanel, setShowDetailedPanel] = useState(false);
  const [showDistrictModal, setShowDistrictModal] = useState(false);
  const [showDisambiguateModal, setShowDisambiguateModal] = useState(false);
  const [ambiguousFields, setAmbiguousFields] = useState<AmbiguousField[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [isEstimating, setIsEstimating] = useState(false);
  const [isCheckingAmbiguity, setIsCheckingAmbiguity] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ task_id: string; status: string } | null>(null);
  
  const parseTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastParsedQueryRef = useRef<string>('');

  const parseQuery = useCallback(async (text: string) => {
    if (!text.trim() || text === lastParsedQueryRef.current) return;
    
    setIsParsing(true);
    try {
      const result = await parseApi.parseQuery(text, true);
      setParsedData(result);
      lastParsedQueryRef.current = text;
      
      checkAmbiguity(text, result);
    } catch (err) {
      console.error('Parse error:', err);
    } finally {
      setIsParsing(false);
    }
  }, []);

  const checkAmbiguity = async (text: string, parsed: ParsedQuery) => {
    if (!parsed.district && !parsed.community) return;
    
    setIsCheckingAmbiguity(true);
    try {
      const ambiguityCheck = await disambiguateApi.checkAmbiguity({
        query: text,
        city: parsed.city || undefined,
        district: parsed.district || undefined,
        community: parsed.community || undefined
      });
      
      if (ambiguityCheck.has_ambiguity) {
        setAmbiguousFields(ambiguityCheck.ambiguous_fields);
        setShowDisambiguateModal(true);
      }
    } catch (err) {
      console.error('Ambiguity check error:', err);
    } finally {
      setIsCheckingAmbiguity(false);
    }
  };

  useEffect(() => {
    if (parseTimeoutRef.current) {
      clearTimeout(parseTimeoutRef.current);
    }

    if (query.trim().length >= 2) {
      parseTimeoutRef.current = setTimeout(() => {
        parseQuery(query);
      }, 500);
    }

    return () => {
      if (parseTimeoutRef.current) {
        clearTimeout(parseTimeoutRef.current);
      }
    };
  }, [query, parseQuery]);

  const handleFieldChange = (field: string, value: unknown) => {
    if (!parsedData) return;
    
    setParsedData(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        [field]: value,
        missing_fields: prev.missing_fields.filter(f => f !== field)
      };
    });
  };

  const handleEstimate = async () => {
    if (!parsedData) return;
    
    setIsEstimating(true);
    try {
      const estimate = await parseApi.estimate({
        city: parsedData.city || undefined,
        district: parsedData.district || undefined,
        room_count: parsedData.room_count || undefined,
        hall_count: parsedData.hall_count || undefined,
        area_min: parsedData.area_min || undefined,
        area_max: parsedData.area_max || undefined,
        special_requirements: parsedData.special_requirements
      });

      setParsedData(prev => {
        if (!prev) return prev;
        
        const updates: Partial<ParsedQuery> = { ...prev };
        
        if (estimate.area_estimate && !prev.area_min) {
          updates.area_min = estimate.area_estimate.min;
          updates.area_max = estimate.area_estimate.max;
          updates.area_avg = estimate.area_estimate.avg;
          updates.area_estimated = true;
        }
        
        if (estimate.price_estimate && !prev.price_max) {
          updates.price_min = estimate.price_estimate.min;
          updates.price_max = estimate.price_estimate.max;
          updates.price_avg = estimate.price_estimate.avg;
          updates.price_estimated = true;
        }
        
        return updates as ParsedQuery;
      });
    } catch (err) {
      console.error('Estimate error:', err);
    } finally {
      setIsEstimating(false);
    }
  };

  const handleDisambiguationConfirm = (selections: Record<string, DisambiguationCandidate>) => {
    setParsedData(prev => {
      if (!prev) return prev;
      
      const updates = { ...prev };
      
      for (const [field, candidate] of Object.entries(selections)) {
        if (field === 'district' && candidate.city && candidate.district) {
          updates.city = candidate.city;
          updates.district = candidate.district;
        } else if (field === 'community' && candidate.city && candidate.district && candidate.community) {
          updates.city = candidate.city;
          updates.district = candidate.district;
          updates.community = candidate.community;
        }
      }
      
      return updates;
    });
    
    setShowDisambiguateModal(false);
    setAmbiguousFields([]);
  };

  const generateFinalQuery = (): string => {
    if (!parsedData) return query;
    
    const parts: string[] = [];
    
    if (parsedData.city) parts.push(parsedData.city);
    if (parsedData.district) parts.push(parsedData.district);
    if (parsedData.community) parts.push(parsedData.community);
    
    if (parsedData.room_count) {
      const hall = parsedData.hall_count || 1;
      parts.push(`${parsedData.room_count}室${hall}厅`);
    }
    
    if (parsedData.area_min && parsedData.area_max) {
      parts.push(`${parsedData.area_min}-${parsedData.area_max}平`);
    } else if (parsedData.area_min) {
      parts.push(`${parsedData.area_min}平以上`);
    } else if (parsedData.area_max) {
      parts.push(`${parsedData.area_max}平以下`);
    }
    
    if (parsedData.price_max) {
      parts.push(`${Math.round(parsedData.price_max / 10000)}万以内`);
    }
    
    if (parsedData.is_school_district) parts.push('学区房');
    if (parsedData.is_near_subway) parts.push('近地铁');
    
    if (parsedData.orientation) parts.push(`${parsedData.orientation}向`);
    if (parsedData.decoration) parts.push(parsedData.decoration);
    
    if (parsedData.special_requirements?.length) {
      parts.push(...parsedData.special_requirements);
    }
    
    return parts.join(' ') || query;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const finalQuery = generateFinalQuery();
      const response = await taskApi.create({ query: finalQuery });

      if (response.id) {
        setResult({ task_id: response.id, status: 'created' });
        setQuery('');
        setParsedData(null);
        setShowDetailedPanel(false);
      }
    } catch (err) {
      setError('提交失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  const locationInfo = {
    city: parsedData?.city,
    district: parsedData?.district
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            描述您的房产需求
          </label>
          <div className="relative">
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="例如：深圳南山区三室两厅 500万以内 学区房 近地铁&#10;&#10;您可以随意描述，我们会智能解析您的需求..."
              rows={3}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            />
            {(isParsing || isCheckingAmbiguity) && (
              <div className="absolute right-3 top-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
              </div>
            )}
          </div>
          
          <div className="mt-2 flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              {parsedData && (
                <button
                  type="button"
                  onClick={() => setShowDetailedPanel(!showDetailedPanel)}
                  className="flex items-center space-x-1 text-primary-600 hover:text-primary-700"
                >
                  <span>{showDetailedPanel ? '▼' : '▶'}</span>
                  <span>详细选项</span>
                  {parsedData.missing_fields.length > 0 && (
                    <span className="bg-yellow-100 text-yellow-700 text-xs px-1.5 py-0.5 rounded-full">
                      {parsedData.missing_fields.length}项待补充
                    </span>
                  )}
                </button>
              )}
              
              {locationInfo.city && (
                <button
                  type="button"
                  onClick={() => setShowDistrictModal(true)}
                  className="flex items-center space-x-1 text-gray-500 hover:text-primary-600"
                >
                  <span>📍</span>
                  <span>{locationInfo.city}{locationInfo.district && ` · ${locationInfo.district}`}</span>
                  <span className="text-xs text-primary-600">(查看区域介绍)</span>
                </button>
              )}
              
              {ambiguousFields.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowDisambiguateModal(true)}
                  className="flex items-center space-x-1 text-amber-600 hover:text-amber-700"
                >
                  <span>🤔</span>
                  <span>需要确认位置</span>
                  <span className="bg-amber-100 text-amber-700 text-xs px-1.5 py-0.5 rounded-full">
                    {ambiguousFields.length}项
                  </span>
                </button>
              )}
            </div>
            
            <span className="text-gray-400">{query.length}字</span>
          </div>
        </div>

        <DetailedOptionsPanel
          isOpen={showDetailedPanel}
          parsedData={parsedData}
          onFieldChange={handleFieldChange}
          onEstimate={handleEstimate}
          isEstimating={isEstimating}
        />

        <div className="pt-2">
          <button
            type="submit"
            disabled={isSubmitting || !query.trim()}
            className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>分析中...</span>
              </>
            ) : (
              <>
                <span>🔍</span>
                <span>开始分析</span>
              </>
            )}
          </button>
        </div>

        {parsedData && parsedData.confidence > 0.5 && (
          <div className="text-center text-sm text-gray-500">
            识别到：{generateFinalQuery()}
          </div>
        )}
      </form>

      {error && (
        <div className="mt-4 p-4 bg-red-100 text-red-800 rounded-lg">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-lg font-semibold text-green-800 mb-3">✅ 任务已创建</h3>
          <p className="text-gray-700">任务ID: {result.task_id}</p>
          <p className="text-sm text-gray-500 mt-2">正在分析中，请稍候查看结果...</p>
        </div>
      )}

      <DistrictInfoModal
        isOpen={showDistrictModal}
        onClose={() => setShowDistrictModal(false)}
        city={locationInfo.city || ''}
        district={locationInfo.district || undefined}
      />

      <DisambiguationModal
        isOpen={showDisambiguateModal}
        onClose={() => setShowDisambiguateModal(false)}
        onConfirm={handleDisambiguationConfirm}
        query={query}
        ambiguousFields={ambiguousFields}
        context={{
          city: parsedData?.city,
          district: parsedData?.district
        }}
      />
    </div>
  );
};

export default QueryInput;
