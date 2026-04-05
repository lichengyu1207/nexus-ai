import React from 'react';

interface SettingFieldProps {
  label: string;
  description?: string;
  type: 'bool' | 'string' | 'int' | 'password' | 'select';
  value: any;
  onChange: (value: any) => void;
  options?: string[];
  min?: number;
  max?: number;
  disabled?: boolean;
}

const SettingField: React.FC<SettingFieldProps> = ({
  label,
  description,
  type,
  value,
  onChange,
  options,
  min,
  max,
  disabled,
}) => {
  const renderInput = () => {
    switch (type) {
      case 'bool':
        return (
          <button
            type="button"
            onClick={() => !disabled && onChange(!value)}
            disabled={disabled}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-full
              transition-colors duration-200 ease-in-out
              focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
              ${value ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <span
              className={`
                inline-block h-4 w-4 transform rounded-full bg-white shadow-sm
                transition-transform duration-200 ease-in-out
                ${value ? 'translate-x-6' : 'translate-x-1'}
              `}
            />
          </button>
        );

      case 'int':
        return (
          <input
            type="number"
            value={value ?? ''}
            onChange={(e) => {
              const val = parseInt(e.target.value);
              if (!isNaN(val)) {
                onChange(val);
              }
            }}
            min={min}
            max={max}
            disabled={disabled}
            className="w-32 px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
          />
        );

      case 'password':
        return (
          <input
            type="password"
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder="••••••••"
            className="w-full max-w-md px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
          />
        );

      case 'select':
        return (
          <select
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="w-full max-w-md px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
          >
            {options?.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        );

      case 'string':
      default:
        return (
          <input
            type="text"
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="w-full max-w-md px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
          />
        );
    }
  };

  return (
    <div className="flex items-start justify-between gap-4 py-4 border-b border-gray-100 dark:border-gray-700 last:border-b-0">
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-900 dark:text-white">
          {label}
        </label>
        {description && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {description}
          </p>
        )}
        {type === 'int' && (min !== undefined || max !== undefined) && (
          <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
            范围: {min ?? '∞'} - {max ?? '∞'}
          </p>
        )}
      </div>
      <div className="flex-shrink-0">{renderInput()}</div>
    </div>
  );
};

export default SettingField;
