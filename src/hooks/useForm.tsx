import React, { useState, useCallback, useMemo } from 'react';

export interface ValidationRule {
  required?: boolean | string;
  minLength?: number | { value: number; message: string };
  maxLength?: number | { value: number; message: string };
  pattern?: RegExp | { value: RegExp; message: string };
  min?: number | { value: number; message: string };
  max?: number | { value: number; message: string };
  validate?: (value: any) => boolean | string;
}

export interface FieldError {
  field: string;
  message: string;
}

export interface FormFieldConfig {
  name: string;
  label: string;
  rules?: ValidationRule;
  defaultValue?: any;
}

export interface UseFormOptions {
  fields: FormFieldConfig[];
  onSubmit: (values: Record<string, any>) => Promise<void> | void;
}

export interface FormContextValue {
  values: Record<string, any>;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
  isSubmitting: boolean;
  isValid: boolean;
  setValue: (name: string, value: any) => void;
  setTouched: (name: string) => void;
  validateField: (name: string) => string | null;
  validateAll: () => boolean;
  handleSubmit: (e?: React.FormEvent) => Promise<void>;
  reset: () => void;
  getFieldProps: (name: string) => {
    name: string;
    value: any;
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
    onBlur: () => void;
  };
  getFieldError: (name: string) => string | undefined;
}

const validateValue = (value: any, rules?: ValidationRule): string | null => {
  if (!rules) return null;

  if (rules.required) {
    const isEmpty = value === undefined || value === null || value === '';
    if (isEmpty) {
      return typeof rules.required === 'string' ? rules.required : '此字段必填';
    }
  }

  if (rules.minLength) {
    const config = typeof rules.minLength === 'number' 
      ? { value: rules.minLength, message: `最少需要 ${rules.minLength} 个字符` }
      : rules.minLength;
    if (typeof value === 'string' && value.length < config.value) {
      return config.message;
    }
  }

  if (rules.maxLength) {
    const config = typeof rules.maxLength === 'number'
      ? { value: rules.maxLength, message: `最多允许 ${rules.maxLength} 个字符` }
      : rules.maxLength;
    if (typeof value === 'string' && value.length > config.value) {
      return config.message;
    }
  }

  if (rules.pattern) {
    const config = rules.pattern instanceof RegExp
      ? { value: rules.pattern, message: '格式不正确' }
      : rules.pattern;
    if (!config.value.test(value)) {
      return config.message;
    }
  }

  if (rules.min !== undefined) {
    const config = typeof rules.min === 'number'
      ? { value: rules.min, message: `最小值为 ${rules.min}` }
      : rules.min;
    if (typeof value === 'number' && value < config.value) {
      return config.message;
    }
  }

  if (rules.max !== undefined) {
    const config = typeof rules.max === 'number'
      ? { value: rules.max, message: `最大值为 ${rules.max}` }
      : rules.max;
    if (typeof value === 'number' && value > config.value) {
      return config.message;
    }
  }

  if (rules.validate) {
    const result = rules.validate(value);
    if (result !== true) {
      return typeof result === 'string' ? result : '验证失败';
    }
  }

  return null;
};

export const useForm = (options: UseFormOptions): FormContextValue => {
  const initialValues = useMemo(() => {
    const values: Record<string, any> = {};
    options.fields.forEach(field => {
      values[field.name] = field.defaultValue ?? '';
    });
    return values;
  }, [options.fields]);

  const [values, setValues] = useState<Record<string, any>>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouchedState] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fieldRules = useMemo(() => {
    const rules: Record<string, ValidationRule> = {};
    options.fields.forEach(field => {
      if (field.rules) {
        rules[field.name] = field.rules;
      }
    });
    return rules;
  }, [options.fields]);

  const setValue = useCallback((name: string, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[name];
      return newErrors;
    });
  }, []);

  const setTouched = useCallback((name: string) => {
    setTouchedState(prev => ({ ...prev, [name]: true }));
  }, []);

  const validateField = useCallback((name: string): string | null => {
    const rules = fieldRules[name];
    const error = validateValue(values[name], rules);
    if (error) {
      setErrors(prev => ({ ...prev, [name]: error }));
    }
    return error;
  }, [values, fieldRules]);

  const validateAll = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};
    let isValid = true;

    options.fields.forEach(field => {
      const error = validateValue(values[field.name], field.rules);
      if (error) {
        newErrors[field.name] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    setTouchedState(
      options.fields.reduce((acc, field) => ({ ...acc, [field.name]: true }), {})
    );

    return isValid;
  }, [values, options.fields]);

  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!validateAll()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await options.onSubmit(values);
    } finally {
      setIsSubmitting(false);
    }
  }, [values, validateAll, options.onSubmit]);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouchedState({});
    setIsSubmitting(false);
  }, [initialValues]);

  const getFieldProps = useCallback((name: string) => ({
    name,
    value: values[name] ?? '',
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setValue(name, e.target.value);
    },
    onBlur: () => {
      setTouched(name);
      validateField(name);
    },
  }), [values, setValue, setTouched, validateField]);

  const getFieldError = useCallback((name: string): string | undefined => {
    return touched[name] ? errors[name] : undefined;
  }, [errors, touched]);

  const isValid = useMemo(() => Object.keys(errors).length === 0, [errors]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    isValid,
    setValue,
    setTouched,
    validateField,
    validateAll,
    handleSubmit,
    reset,
    getFieldProps,
    getFieldError,
  };
};

interface FormFieldProps {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  error,
  required,
  children,
  className = '',
}) => {
  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
      {error && (
        <p className="mt-1 text-sm text-red-500 dark:text-red-400">{error}</p>
      )}
    </div>
  );
};

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input: React.FC<InputProps> = ({ error, className = '', ...props }) => {
  return (
    <input
      className={`
        w-full px-3 py-2 border rounded-lg
        bg-white dark:bg-gray-700
        text-gray-900 dark:text-white
        focus:ring-2 focus:ring-primary-500 focus:border-transparent
        transition-colors
        ${error 
          ? 'border-red-500 dark:border-red-400' 
          : 'border-gray-300 dark:border-gray-600'
        }
        ${className}
      `}
      {...props}
    />
  );
};

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export const TextArea: React.FC<TextAreaProps> = ({ error, className = '', ...props }) => {
  return (
    <textarea
      className={`
        w-full px-3 py-2 border rounded-lg
        bg-white dark:bg-gray-700
        text-gray-900 dark:text-white
        focus:ring-2 focus:ring-primary-500 focus:border-transparent
        transition-colors
        ${error 
          ? 'border-red-500 dark:border-red-400' 
          : 'border-gray-300 dark:border-gray-600'
        }
        ${className}
      `}
      {...props}
    />
  );
};

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
  options: Array<{ value: string; label: string }>;
}

export const Select: React.FC<SelectProps> = ({ error, options, className = '', ...props }) => {
  return (
    <select
      className={`
        w-full px-3 py-2 border rounded-lg
        bg-white dark:bg-gray-700
        text-gray-900 dark:text-white
        focus:ring-2 focus:ring-primary-500 focus:border-transparent
        transition-colors
        ${error 
          ? 'border-red-500 dark:border-red-400' 
          : 'border-gray-300 dark:border-gray-600'
        }
        ${className}
      `}
      {...props}
    >
      {options.map(option => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
};

export default useForm;
