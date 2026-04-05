import React, { useState, useEffect, useCallback } from 'react';
import { parseApi, ParsedQuery } from '../services/api';

interface DetailedOptionsPanelProps {
  isOpen: boolean;
  parsedData: ParsedQuery | null;
  onFieldChange: (field: string, value: unknown) => void;
  onEstimate: () => void;
  isEstimating: boolean;
}

interface Recommendation {
  value: string | number;
  label: string;
}

const DetailedOptionsPanel: React.FC<DetailedOptionsPanelProps> = ({
  isOpen,
  parsedData,
  onFieldChange,
  onEstimate,
  isEstimating
}) => {
  const [districtRecommendations, setDistrictRecommendations] = useState<Recommendation[]>([]);
  const [areaRecommendations, setAreaRecommendations] = useState<Recommendation[]>([]);
  const [priceRecommendations, setPriceRecommendations] = useState<Recommendation[]>([]);
  const [loadingDistricts, setLoadingDistricts] = useState(false);

  useEffect(() => {
    if (parsedData?.city && !parsedData?.district) {
      loadDistrictRecommendations(parsedData.city);
    }
  }, [parsedData?.city, parsedData?.district]);

  useEffect(() => {
    if (parsedData?.room_count && !parsedData?.area_min) {
      loadAreaRecommendations(parsedData.room_count);
    }
  }, [parsedData?.room_count, parsedData?.area_min]);

  const loadDistrictRecommendations = async (city: string) => {
    setLoadingDistricts(true);
    try {
      const result = await parseApi.getDistrictRecommendations(city);
      setDistrictRecommendations(
        result.districts.slice(0, 5).map(d => ({
          value: d.value,
          label: `${d.label} (均价${(d.avg_price / 10000).toFixed(1)}万/㎡)`
        }))
      );
    } catch {
      setDistrictRecommendations([]);
    } finally {
      setLoadingDistricts(false);
    }
  };

  const loadAreaRecommendations = async (roomCount: number) => {
    try {
      const result = await parseApi.getAreaRecommendations(roomCount);
      setAreaRecommendations(
        result.areas.map(a => ({
          value: a.value,
          label: a.label
        }))
      );
    } catch {
      setAreaRecommendations([]);
    }
  };

  const loadPriceRecommendations = async () => {
    try {
      const result = await parseApi.getPriceRecommendations(parsedData?.city || undefined);
      setPriceRecommendations(
        result.prices.map(p => ({
          value: p.value,
          label: `${p.label} (${p.tier})`
        }))
      );
    } catch {
      setPriceRecommendations([]);
    }
  };

  const handleQuickSelect = (field: string, value: unknown) => {
    onFieldChange(field, value);
  };

  if (!isOpen) return null;

  const missingFields = parsedData?.missing_fields || [];
  const hasMissingFields = missingFields.length > 0;

  const fieldLabels: Record<string, string> = {
    city: '城市',
    district: '区域',
    community: '小区',
    room_count: '户型',
    area_min: '面积',
    price_max: '预算',
    orientation: '朝向',
    floor_type: '楼层',
    decoration: '装修',
  };

  const fieldIcons: Record<string, string> = {
    city: '🏙️',
    district: '📍',
    community: '🏠',
    room_count: '🛏️',
    area_min: '📐',
    price_max: '💰',
    orientation: '🧭',
    floor_type: '🏢',
    decoration: '🎨',
  };

  return (
    <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-lg">📋</span>
            <span className="font-medium text-gray-800">详细选项</span>
            {parsedData?.confidence !== undefined && (
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                parsedData.confidence > 0.7 ? 'bg-green-100 text-green-700' :
                parsedData.confidence > 0.4 ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700'
              }`}>
                识别度 {Math.round(parsedData.confidence * 100)}%
              </span>
            )}
          </div>
          
          {hasMissingFields && (
            <button
              type="button"
              onClick={onEstimate}
              disabled={isEstimating}
              className="flex items-center space-x-1 px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {isEstimating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>估算中...</span>
                </>
              ) : (
                <>
                  <span>✨</span>
                  <span>帮我估算</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {parsedData?.inferences && parsedData.inferences.length > 0 && (
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="flex items-center space-x-2 text-blue-700 text-sm font-medium mb-2">
              <span>💡</span>
              <span>智能推断</span>
            </div>
            <div className="space-y-2">
              {parsedData.inferences.map((inference, index) => (
                <div key={index} className="text-sm text-blue-600">
                  <span className="font-medium">{fieldLabels[inference.field] || inference.field}：</span>
                  {inference.field === 'area' && (
                    <span>
                      {inference.inferred_value.min}-{inference.inferred_value.max}㎡
                      <span className="text-blue-400 ml-1">({inference.reasoning})</span>
                    </span>
                  )}
                  {inference.field === 'price' && (
                    <span>
                      {(inference.inferred_value.min as number / 10000).toFixed(0)}-
                      {(inference.inferred_value.max as number / 10000).toFixed(0)}万
                      <span className="text-blue-400 ml-1">({inference.reasoning})</span>
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              🏙️ 城市
            </label>
            <input
              type="text"
              value={parsedData?.city || ''}
              onChange={(e) => onFieldChange('city', e.target.value)}
              placeholder="如：深圳"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              📍 区域
            </label>
            <div className="relative">
              <input
                type="text"
                value={parsedData?.district || ''}
                onChange={(e) => onFieldChange('district', e.target.value)}
                placeholder="如：南山区"
                className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
              />
              {districtRecommendations.length > 0 && !parsedData?.district && (
                <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg">
                  <div className="p-2 text-xs text-gray-500 border-b">推荐区域</div>
                  {districtRecommendations.map((rec, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleQuickSelect('district', rec.value)}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
                    >
                      {rec.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              🏠 小区
            </label>
            <input
              type="text"
              value={parsedData?.community || ''}
              onChange={(e) => onFieldChange('community', e.target.value)}
              placeholder="如：华润城润府"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              🛏️ 户型
            </label>
            <div className="flex space-x-2">
              <select
                value={parsedData?.room_count || ''}
                onChange={(e) => onFieldChange('room_count', e.target.value ? parseInt(e.target.value) : null)}
                className="flex-1 px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
              >
                <option value="">室</option>
                {[1, 2, 3, 4, 5].map(n => (
                  <option key={n} value={n}>{n}室</option>
                ))}
              </select>
              <select
                value={parsedData?.hall_count || ''}
                onChange={(e) => onFieldChange('hall_count', e.target.value ? parseInt(e.target.value) : null)}
                className="flex-1 px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
              >
                <option value="">厅</option>
                {[0, 1, 2, 3].map(n => (
                  <option key={n} value={n}>{n}厅</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              📐 面积 (㎡)
            </label>
            <div className="flex space-x-2">
              <input
                type="number"
                value={parsedData?.area_min || ''}
                onChange={(e) => onFieldChange('area_min', e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="最小"
                className="flex-1 px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
              />
              <span className="flex items-center text-gray-400">-</span>
              <input
                type="number"
                value={parsedData?.area_max || ''}
                onChange={(e) => onFieldChange('area_max', e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="最大"
                className="flex-1 px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
              />
            </div>
            {parsedData?.area_estimated && (
              <div className="mt-1 text-xs text-blue-600">
                ✓ 已估算: {parsedData.area_avg}㎡
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              💰 预算 (万)
            </label>
            <div className="flex space-x-2">
              <input
                type="number"
                value={parsedData?.price_min ? parsedData.price_min / 10000 : ''}
                onChange={(e) => onFieldChange('price_min', e.target.value ? parseFloat(e.target.value) * 10000 : null)}
                placeholder="最低"
                className="flex-1 px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
              />
              <span className="flex items-center text-gray-400">-</span>
              <input
                type="number"
                value={parsedData?.price_max ? parsedData.price_max / 10000 : ''}
                onChange={(e) => onFieldChange('price_max', e.target.value ? parseFloat(e.target.value) * 10000 : null)}
                placeholder="最高"
                className="flex-1 px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
              />
            </div>
            {parsedData?.price_estimated && (
              <div className="mt-1 text-xs text-blue-600">
                ✓ 已估算: {Math.round((parsedData.price_avg || 0) / 10000)}万
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              🧭 朝向
            </label>
            <select
              value={parsedData?.orientation || ''}
              onChange={(e) => onFieldChange('orientation', e.target.value || null)}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
            >
              <option value="">不限</option>
              <option value="南">南向</option>
              <option value="东南">东南</option>
              <option value="西南">西南</option>
              <option value="东">东向</option>
              <option value="西">西向</option>
              <option value="北">北向</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              🏢 楼层
            </label>
            <select
              value={parsedData?.floor_type || ''}
              onChange={(e) => onFieldChange('floor_type', e.target.value || null)}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
            >
              <option value="">不限</option>
              <option value="low">低楼层 (1-6层)</option>
              <option value="mid">中楼层 (7-15层)</option>
              <option value="high">高楼层 (16层以上)</option>
              <option value="top">顶层</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              🎨 装修
            </label>
            <select
              value={parsedData?.decoration || ''}
              onChange={(e) => onFieldChange('decoration', e.target.value || null)}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm"
            >
              <option value="">不限</option>
              <option value="毛坯">毛坯</option>
              <option value="简装">简装</option>
              <option value="精装">精装</option>
              <option value="豪装">豪装</option>
            </select>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={parsedData?.is_school_district || false}
              onChange={(e) => onFieldChange('is_school_district', e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">🎓 学区房</span>
          </label>
          
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={parsedData?.is_near_subway || false}
              onChange={(e) => onFieldChange('is_near_subway', e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">🚇 近地铁</span>
          </label>
        </div>

        {parsedData?.special_requirements && parsedData.special_requirements.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📌 特殊需求
            </label>
            <div className="flex flex-wrap gap-2">
              {parsedData.special_requirements.map((req, i) => (
                <span
                  key={i}
                  className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
                >
                  {req}
                </span>
              ))}
            </div>
          </div>
        )}

        {hasMissingFields && (
          <div className="bg-yellow-50 rounded-lg p-3">
            <div className="flex items-center space-x-2 text-yellow-700 text-sm font-medium mb-2">
              <span>⚠️</span>
              <span>建议补充以下信息</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {missingFields.map((field, i) => (
                <span
                  key={i}
                  className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-sm"
                >
                  {fieldIcons[field] || '📝'} {fieldLabels[field] || field}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DetailedOptionsPanel;
