import React from 'react';

const BrandGuide: React.FC = () => {
  const primaryColors = [
    { name: 'Primary 50', hex: '#0A5C5C', class: 'bg-primary-50' },
    { name: 'Primary 100', hex: '#3B82F6', class: 'bg-primary-100' },
    { name: 'Primary 200', hex: '#60A5FA', class: 'bg-primary-200' },
    { name: 'Primary 300', hex: '#34D399', class: 'bg-primary-300' },
    { name: 'Primary 400', hex: '#2563EB', class: 'bg-primary-400' },
    { name: 'Primary 500', hex: '#059669', class: 'bg-primary-500' },
    { name: 'Primary 600', hex: '#1D4ED8', class: 'bg-primary-600' },
    { name: 'Primary 700', hex: '#1E40AF', class: 'bg-primary-700' },
    { name: 'Primary 800', hex: '#1E3A8A', class: 'bg-primary-800' },
    { name: 'Primary 900', hex: '#18181B', class: 'bg-primary-900' },
  ];

  const secondaryColors = [
    { name: 'Secondary 50', hex: '#64748B', class: 'bg-secondary-50' },
    { name: 'Secondary 100', hex: '#7C3AED', class: 'bg-secondary-100' },
    { name: 'Secondary 200', hex: '#10B981', class: 'bg-secondary-200' },
    { name: 'Secondary 300', hex: '#059669', class: 'bg-secondary-300' },
    { name: 'Secondary 400', hex: '#6B7280', class: 'bg-secondary-400' },
    { name: 'Secondary 500', hex: '#374151', class: 'bg-secondary-500' },
    { name: 'Secondary 600', hex: '#9CA3AF', class: 'bg-secondary-600' },
    { name: 'Secondary 700', hex: '#3B82F6', class: 'bg-secondary-700' },
    { name: 'Secondary 800', hex: '#2563EB', class: 'bg-secondary-800' },
    { name: 'Secondary 900', hex: '#1F2937', class: 'bg-secondary-900' },
  ];

  const semanticColors = [
    { name: 'Success', hex: '#10B981', class: 'bg-success' },
    { name: 'Warning', hex: '#F59E0B', class: 'bg-warning' },
    { name: 'Error', hex: '#EF4444', class: 'bg-error' },
  ];

  const typography = [
    { name: 'Heading 1', class: 'text-4xl font-bold', sample: '房都督AI 智能分析' },
    { name: 'Heading 2', class: 'text-3xl font-semibold', sample: '房产数据洞察' },
    { name: 'Heading 3', class: 'text-2xl font-semibold', sample: '区域分析报告' },
    { name: 'Heading 4', class: 'text-xl font-medium', sample: '市场趋势' },
    { name: 'Body', class: 'text-base', sample: '这是一段正文文本，用于展示常规内容的字体样式。' },
    { name: 'Small', class: 'text-sm', sample: '辅助说明文本，通常用于提示或次要信息。' },
  ];

  const buttons = [
    { name: 'Primary', class: 'bg-primary-600 text-white hover:bg-primary-700' },
    { name: 'Secondary', class: 'bg-secondary-600 text-white hover:bg-secondary-700' },
    { name: 'Outline', class: 'border border-primary-600 text-primary-600 hover:bg-primary-50' },
    { name: 'Ghost', class: 'text-primary-600 hover:bg-primary-50' },
  ];

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 space-y-12">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">房都督AI 品牌指南</h1>
        <p className="text-gray-600 dark:text-gray-400">
          统一的品牌视觉元素，确保全站视觉一致性。
        </p>
      </div>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Logo</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 flex items-center justify-center">
          <div className="text-center">
            <div className="w-24 h-24 bg-primary-50 rounded-xl flex items-center justify-center mb-4 mx-auto">
              <span className="text-4xl font-bold text-white">房</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">房都督AI</h3>
            <p className="text-sm text-gray-500">智能房产分析平台</p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">主色调</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {primaryColors.map((color) => (
            <div key={color.name} className="text-center">
              <div className={`${color.class} h-20 rounded-lg shadow-md mb-2`} />
              <p className="text-sm font-medium text-gray-900 dark:text-white">{color.name}</p>
              <p className="text-xs text-gray-500">{color.hex}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">辅助色</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {secondaryColors.map((color) => (
            <div key={color.name} className="text-center">
              <div className={`${color.class} h-20 rounded-lg shadow-md mb-2`} />
              <p className="text-sm font-medium text-gray-900 dark:text-white">{color.name}</p>
              <p className="text-xs text-gray-500">{color.hex}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">语义色</h2>
        <div className="grid grid-cols-3 gap-4">
          {semanticColors.map((color) => (
            <div key={color.name} className="text-center">
              <div className={`${color.class} h-20 rounded-lg shadow-md mb-2`} />
              <p className="text-sm font-medium text-gray-900 dark:text-white">{color.name}</p>
              <p className="text-xs text-gray-500">{color.hex}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">字体层级</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-4">
          {typography.map((type) => (
            <div key={type.name} className="border-b border-gray-200 dark:border-gray-700 pb-4 last:border-0">
              <p className="text-xs text-gray-500 mb-1">{type.name}</p>
              <p className={type.class}>{type.sample}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">按钮样式</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex flex-wrap gap-4">
            {buttons.map((btn) => (
              <button
                key={btn.name}
                className={`px-6 py-2 rounded-lg font-medium transition-colors ${btn.class}`}
              >
                {btn.name} Button
              </button>
            ))}
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">卡片样式</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">默认卡片</h4>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              这是默认的卡片样式，使用白色背景和中等阴影。
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border-l-4 border-primary-600">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">强调卡片</h4>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              带有左侧强调边框的卡片，用于重要信息展示。
            </p>
          </div>
          <div className="bg-primary-50 dark:bg-primary-900/20 rounded-xl p-6">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">主题卡片</h4>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              使用主题色背景的卡片，用于突出显示。
            </p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">表单元素</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              输入框
            </label>
            <input
              type="text"
              placeholder="请输入内容..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              文本域
            </label>
            <textarea
              placeholder="请输入详细描述..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              rows={3}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              下拉选择
            </label>
            <select className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 focus:ring-2 focus:ring-primary-500 focus:border-transparent">
              <option>选项一</option>
              <option>选项二</option>
              <option>选项三</option>
            </select>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">徽章样式</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex flex-wrap gap-3">
            <span className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
              Primary
            </span>
            <span className="px-3 py-1 bg-secondary-100 text-secondary-700 rounded-full text-sm font-medium">
              Secondary
            </span>
            <span className="px-3 py-1 bg-success-100 text-success-700 rounded-full text-sm font-medium">
              Success
            </span>
            <span className="px-3 py-1 bg-warning-100 text-warning-700 rounded-full text-sm font-medium">
              Warning
            </span>
            <span className="px-3 py-1 bg-error-100 text-error-700 rounded-full text-sm font-medium">
              Error
            </span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default BrandGuide;
