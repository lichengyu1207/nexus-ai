import React from 'react';
import { StarIcon } from '@heroicons/react/24/solid';

const testimonials = [
  {
    name: '张先生',
    role: '首次购房者',
    avatar: 'Z',
    content: '房都督AI帮我分析了深圳南山区的学区房，报告详细且专业，让我对房价有了清晰的认识，避免了盲目出价。',
    rating: 5,
  },
  {
    name: '李女士',
    role: '投资客',
    avatar: 'L',
    content: '作为一个房产投资者，这个工具帮我快速评估多个房源的投资价值，节省了大量调研时间，非常实用！',
    rating: 5,
  },
  {
    name: '王先生',
    role: '置换业主',
    avatar: 'W',
    content: '报告中的风险提示非常到位，让我注意到一些之前忽略的问题，帮我做出了更明智的决策。',
    rating: 5,
  },
];

const Testimonials: React.FC = () => {
  return (
    <section className="py-16 bg-gray-50">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            用户真实评价
          </h2>
          <p className="text-gray-600">
            看看其他用户怎么说
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center space-x-1 mb-4">
                {Array.from({ length: testimonial.rating }).map((_, i) => (
                  <StarIcon key={i} className="w-5 h-5 text-yellow-400" />
                ))}
              </div>
              
              <p className="text-gray-600 mb-6 leading-relaxed">
                "{testimonial.content}"
              </p>
              
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-medium">
                  {testimonial.avatar}
                </div>
                <div>
                  <div className="font-medium text-gray-900">{testimonial.name}</div>
                  <div className="text-sm text-gray-500">{testimonial.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
