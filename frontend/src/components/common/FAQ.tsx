import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface FAQItem {
  question: string;
  answer: string;
}

interface AccordionItemProps {
  question: string;
  answer: string;
  isOpen: boolean;
  onToggle: () => void;
}

const AccordionItem: React.FC<AccordionItemProps> = ({
  question,
  answer,
  isOpen,
  onToggle,
}) => {
  return (
    <div className="border-b border-gray-200 last:border-b-0">
      <button
        onClick={onToggle}
        className="w-full py-4 px-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
      >
        <span className="font-medium text-gray-900 pr-4">{question}</span>
        <motion.span
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="flex-shrink-0 text-gray-500"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 text-gray-600">{answer}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

interface AccordionProps {
  items: FAQItem[];
  allowMultiple?: boolean;
  className?: string;
}

const Accordion: React.FC<AccordionProps> = ({
  items,
  allowMultiple = false,
  className = '',
}) => {
  const [openItems, setOpenItems] = useState<number[]>([]);

  const handleToggle = (index: number) => {
    if (allowMultiple) {
      setOpenItems((prev) =>
        prev.includes(index)
          ? prev.filter((i) => i !== index)
          : [...prev, index]
      );
    } else {
      setOpenItems((prev) =>
        prev.includes(index) ? [] : [index]
      );
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {items.map((item, index) => (
        <AccordionItem
          key={index}
          question={item.question}
          answer={item.answer}
          isOpen={openItems.includes(index)}
          onToggle={() => handleToggle(index)}
        />
      ))}
    </div>
  );
};

interface FAQProps {
  items?: FAQItem[];
  title?: string;
  className?: string;
}

const defaultFAQItems: FAQItem[] = [
  {
    question: '房都督AI的分析报告准确吗？',
    answer:
      '我们的分析报告基于多智能体协同工作，从多个数据源获取信息并进行交叉验证。虽然我们努力确保数据的准确性，但报告仅供参考，不可用于正式的法律用途。建议您在做重大决策前咨询专业人士。',
  },
  {
    question: '分析一份房产需要多长时间？',
    answer:
      '通常情况下，一份完整的房产分析报告需要10-15分钟。我们的多智能体系统会并行处理多个数据采集和分析任务，大大缩短了传统调研所需的时间。',
  },
  {
    question: '积分是如何计算的？',
    answer:
      '每次房产分析消耗1个积分。积分可以通过充值获得，我们也为新注册用户提供免费积分体验。专业版会员每月享有固定积分额度。',
  },
  {
    question: '如何成为IP合作伙伴？',
    answer:
      '您可以在IP合作页面提交申请，审核通过后即可享受专属权益，包括佣金分成、批量分析工具、AI辅助内容创作等。',
  },
  {
    question: '数据来源是否可靠？',
    answer:
      '我们的数据来源于公开的房产交易平台、政府公开数据、第三方数据服务商等。报告中会标注数据来源和置信度，让您了解每个结论的依据。',
  },
  {
    question: '支持哪些城市的房产分析？',
    answer:
      '目前支持全国主要一二线城市的房产分析，包括北京、上海、深圳、广州、杭州、成都、武汉等。我们正在持续扩展覆盖范围。',
  },
];

const FAQ: React.FC<FAQProps> = ({
  items = defaultFAQItems,
  title = '常见问题',
  className = '',
}) => {
  return (
    <div className={`py-12 ${className}`}>
      <h2 className="text-2xl md:text-3xl font-bold text-center mb-8">
        {title}
      </h2>
      <div className="max-w-3xl mx-auto px-4">
        <Accordion items={items} />
      </div>
    </div>
  );
};

interface SearchableFAQProps {
  items?: FAQItem[];
  className?: string;
}

const SearchableFAQ: React.FC<SearchableFAQProps> = ({
  items = defaultFAQItems,
  className = '',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredItems, setFilteredItems] = useState(items);

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    if (!term.trim()) {
      setFilteredItems(items);
      return;
    }
    const filtered = items.filter(
      (item) =>
        item.question.toLowerCase().includes(term.toLowerCase()) ||
        item.answer.toLowerCase().includes(term.toLowerCase())
    );
    setFilteredItems(filtered);
  };

  return (
    <div className={className}>
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="搜索问题..."
            className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      {filteredItems.length > 0 ? (
        <Accordion items={filteredItems} />
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>未找到相关问题</p>
          <p className="text-sm mt-2">请尝试其他关键词</p>
        </div>
      )}
    </div>
  );
};

interface CategoryFAQProps {
  categories: {
    name: string;
    items: FAQItem[];
  }[];
  className?: string;
}

const CategoryFAQ: React.FC<CategoryFAQProps> = ({ categories, className = '' }) => {
  const [activeCategory, setActiveCategory] = useState(0);

  return (
    <div className={className}>
      <div className="flex flex-wrap gap-2 mb-6">
        {categories.map((category, index) => (
          <button
            key={index}
            onClick={() => setActiveCategory(index)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              activeCategory === index
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {category.name}
          </button>
        ))}
      </div>
      <Accordion items={categories[activeCategory].items} />
    </div>
  );
};

export { Accordion, AccordionItem, FAQ, SearchableFAQ, CategoryFAQ };
export type { FAQItem };
export default FAQ;
