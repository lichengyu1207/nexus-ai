import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDownIcon,
  ChevronUpIcon,
  StarIcon,
  CurrencyDollarIcon,
  CheckBadgeIcon,
} from '@heroicons/react/24/outline';
import type { TalentFilters, Availability } from '../types';
import { DOMAINS, AVAILABILITY_CONFIG } from '../types';

export interface TalentFiltersPanelProps {
  filters: TalentFilters;
  onFiltersChange: (filters: TalentFilters) => void;
}

const SKILL_OPTIONS = [
  '数据分析',
  '房产估值',
  '模型训练',
  '报告生成',
  'API集成',
  '自然语言处理',
  '图像识别',
  '风险评估',
];

const PRICE_RANGES = [
  { label: '不限', min: undefined, max: undefined },
  { label: '¥0-100', min: 0, max: 100 },
  { label: '¥100-300', min: 100, max: 300 },
  { label: '¥300-500', min: 300, max: 500 },
  { label: '¥500+', min: 500, max: undefined },
];

const RATING_OPTIONS = [
  { label: '不限', value: undefined },
  { label: '4星及以上', value: 4 },
  { label: '4.5星及以上', value: 4.5 },
  { label: '5星', value: 5 },
];

export function TalentFiltersPanel({ filters, onFiltersChange }: TalentFiltersPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    skills: true,
    domain: true,
    price: false,
    rating: false,
    availability: false,
    verified: false,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleSkillToggle = (skill: string) => {
    const currentSkills = filters.skills ?? [];
    const newSkills = currentSkills.includes(skill)
      ? currentSkills.filter((s) => s !== skill)
      : [...currentSkills, skill];
    onFiltersChange({ ...filters, skills: newSkills.length > 0 ? newSkills : undefined });
  };

  const handlePriceChange = (min?: number, max?: number) => {
    onFiltersChange({ ...filters, priceMin: min, priceMax: max });
  };

  const handleRatingChange = (value?: number) => {
    onFiltersChange({ ...filters, ratingMin: value });
  };

  const handleAvailabilityChange = (value?: Availability) => {
    onFiltersChange({ ...filters, availability: value });
  };

  const handleVerifiedToggle = () => {
    onFiltersChange({ ...filters, verified: filters.verified ? undefined : true });
  };

  const clearAllFilters = () => {
    onFiltersChange({});
  };

  const hasActiveFilters =
    (filters.skills?.length ?? 0) > 0 ||
    filters.domain ||
    filters.priceMin !== undefined ||
    filters.priceMax !== undefined ||
    filters.ratingMin !== undefined ||
    filters.verified ||
    filters.availability;

  return (
    <div className="w-[280px] bg-gray-900/50 backdrop-blur-sm border-r border-white/10 h-full overflow-y-auto">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">筛选条件</h3>
        {hasActiveFilters && (
          <button
            onClick={clearAllFilters}
            className="text-xs text-amber-400 hover:text-amber-300 transition-colors"
          >
            清除全部
          </button>
        )}
      </div>

      <div className="p-2">
        <FilterSection
          title="技能标签"
          expanded={expandedSections.skills}
          onToggle={() => toggleSection('skills')}
        >
          <div className="flex flex-wrap gap-1.5">
            {SKILL_OPTIONS.map((skill) => (
              <button
                key={skill}
                onClick={() => handleSkillToggle(skill)}
                className={`px-2 py-1 text-xs rounded-full transition-colors ${
                  filters.skills?.includes(skill)
                    ? 'bg-amber-500 text-gray-900'
                    : 'bg-white/5 text-gray-300 hover:bg-white/10'
                }`}
              >
                {skill}
              </button>
            ))}
          </div>
        </FilterSection>

        <FilterSection
          title="领域"
          expanded={expandedSections.domain}
          onToggle={() => toggleSection('domain')}
        >
          <div className="space-y-1">
            {Object.entries(DOMAINS).map(([key, label]) => (
              <button
                key={key}
                onClick={() =>
                  onFiltersChange({
                    ...filters,
                    domain: filters.domain === key ? undefined : key,
                  })
                }
                className={`w-full px-3 py-2 text-sm text-left rounded-lg transition-colors ${
                  filters.domain === key
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'text-gray-300 hover:bg-white/5'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </FilterSection>

        <FilterSection
          title="价格范围"
          expanded={expandedSections.price}
          onToggle={() => toggleSection('price')}
          icon={<CurrencyDollarIcon className="w-4 h-4" />}
        >
          <div className="space-y-1">
            {PRICE_RANGES.map((range) => (
              <button
                key={range.label}
                onClick={() => handlePriceChange(range.min, range.max)}
                className={`w-full px-3 py-2 text-sm text-left rounded-lg transition-colors ${
                  filters.priceMin === range.min && filters.priceMax === range.max
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'text-gray-300 hover:bg-white/5'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </FilterSection>

        <FilterSection
          title="评分"
          expanded={expandedSections.rating}
          onToggle={() => toggleSection('rating')}
          icon={<StarIcon className="w-4 h-4" />}
        >
          <div className="space-y-1">
            {RATING_OPTIONS.map((option) => (
              <button
                key={option.label}
                onClick={() => handleRatingChange(option.value)}
                className={`w-full px-3 py-2 text-sm text-left rounded-lg transition-colors ${
                  filters.ratingMin === option.value
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'text-gray-300 hover:bg-white/5'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </FilterSection>

        <FilterSection
          title="可用性"
          expanded={expandedSections.availability}
          onToggle={() => toggleSection('availability')}
        >
          <div className="space-y-1">
            <button
              onClick={() => handleAvailabilityChange(undefined)}
              className={`w-full px-3 py-2 text-sm text-left rounded-lg transition-colors ${
                !filters.availability
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'text-gray-300 hover:bg-white/5'
              }`}
            >
              不限
            </button>
            {Object.entries(AVAILABILITY_CONFIG).map(([key, config]) => (
              <button
                key={key}
                onClick={() => handleAvailabilityChange(key as Availability)}
                className={`w-full px-3 py-2 text-sm text-left rounded-lg transition-colors ${
                  filters.availability === key
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'text-gray-300 hover:bg-white/5'
                }`}
              >
                <span className={config.color}>{config.label}</span>
              </button>
            ))}
          </div>
        </FilterSection>

        <FilterSection
          title="认证状态"
          expanded={expandedSections.verified}
          onToggle={() => toggleSection('verified')}
          icon={<CheckBadgeIcon className="w-4 h-4" />}
        >
          <label className="flex items-center gap-3 px-3 py-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.verified ?? false}
              onChange={handleVerifiedToggle}
              className="w-4 h-4 rounded border-gray-600 text-amber-500 focus:ring-amber-500/50"
            />
            <span className="text-sm text-gray-300">仅显示认证人才</span>
          </label>
        </FilterSection>
      </div>
    </div>
  );
}

interface FilterSectionProps {
  title: string;
  expanded: boolean;
  onToggle: () => void;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

function FilterSection({ title, expanded, onToggle, icon, children }: FilterSectionProps) {
  return (
    <div className="border-b border-white/5 last:border-b-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-3 text-sm font-medium text-gray-300 hover:text-white transition-colors"
      >
        <span className="flex items-center gap-2">
          {icon}
          {title}
        </span>
        {expanded ? (
          <ChevronUpIcon className="w-4 h-4" />
        ) : (
          <ChevronDownIcon className="w-4 h-4" />
        )}
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden px-3 pb-3"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
