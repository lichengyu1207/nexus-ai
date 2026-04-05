import React, { useState } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

const faqs = [
  {
    question: '房都督AI的分析结果有多准确？',
    answer: '我们的AI模型基于大量真实交易数据和官方数据源，分析准确率达到85%以上。报告中会显示置信度，让你了解分析结果的可信程度。',
  },
  {
    question: '免费版和专业版有什么区别？',
    answer: '免费版提供3次分析机会，可以查看基础报告。专业版无限次分析，支持PDF导出、批量分析、房源对比等高级功能，适合有购房需求的用户。',
  },
  {
    question: '如何获取更多分析次数？',
    answer: '你可以升级到专业版获得无限次分析，或者通过邀请好友、参与活动等方式获得额外次数。',
  },
  {
    question: '分析报告包含哪些内容？',
    answer: '报告包含房产估值、周边配套分析（学校、医院、交通）、市场趋势、投资建议、风险提示等完整信息，帮助你全面了解房产价值。',
  },
  {
    question: '数据来源可靠吗？',
    answer: '我们整合了官方房产数据、公开交易记录、地图POI数据等多个可信来源，并在报告中标注数据来源，确保透明可信。',
  },
  {
    question: '支持哪些城市的房产分析？',
    answer: '目前支持全国主要一二线城市的房产分析，覆盖300+城市。如果你所在的城市暂未覆盖，可以联系我们优先支持。',
  },
];

const FAQ: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="py-20 bg-white">
      <div className="max-w-3xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            常见问题
          </h2>
          <p className="text-lg text-gray-600">
            关于房都督AI，你可能想知道的
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="border border-gray-200 rounded-xl overflow-hidden"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
              >
                <span className="font-medium text-gray-900">{faq.question}</span>
                <ChevronDownIcon
                  className={`w-5 h-5 text-gray-500 transition-transform ${
                    openIndex === index ? 'rotate-180' : ''
                  }`}
                />
              </button>
              {openIndex === index && (
                <div className="px-6 pb-4 text-gray-600">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FAQ;
