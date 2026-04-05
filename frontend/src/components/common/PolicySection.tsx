import React from 'react';
import { Link } from 'react-router-dom';

interface PolicyItem {
  id: string;
  title: string;
  department: string;
  publishDate: string;
  summary: string;
  platformImpact: string;
  icon: string;
  link: string;
}

const policies: PolicyItem[] = [
  {
    id: '1',
    title: '《算力基础设施高质量发展行动计划》',
    department: '国家六部门联合发布',
    publishDate: '2023-10',
    summary: '提出2025年算力规模目标，推动算力基础设施高质量发展，支撑数字经济战略实施。',
    platformImpact: '房都督平台智能体集群将优先采用绿色算力，响应"东数西算"战略，为用户提供更高效、更环保的AI分析服务。',
    icon: '🖥️',
    link: 'https://www.gov.cn/zhengce/zhengceku/202310/content_6908334.htm',
  },
  {
    id: '2',
    title: '《算力基础设施高质量发展行动计划》',
    department: '国家发展改革委等',
    publishDate: '2023-10',
    summary: '明确全国算力网络布局，建设国家算力枢纽节点，推动算力资源高效调度。',
    platformImpact: '房都督平台将依托国家算力枢纽，为智能体集群提供高效计算支撑，确保分析报告的快速生成。',
    icon: '📊',
    link: 'https://www.gov.cn/zhengce/zhengceku/202310/content_6908334.htm',
  },
  {
    id: '3',
    title: '《关于促进数据产业高质量发展的指导意见》',
    department: '国家数据局等印发',
    publishDate: '2024-01',
    summary: '规范数据要素市场，促进数据合规流通，培育数据产业生态，推动数据价值释放。',
    platformImpact: '房都督平台数据源建设严格遵循合规流通原则，确保房产数据来源合法、可溯源、可验证。',
    icon: '📁',
    link: 'https://www.gov.cn/zhengce/zhengceku/202401/content_6925332.htm',
  },
];

const PolicySection: React.FC = () => {
  return (
    <section className="py-16 bg-gradient-to-b from-fluent-deepOcean-50 to-white">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-fluent-gold-100 text-fluent-gold-600 px-4 py-2 rounded-full text-sm font-medium mb-4">
            <span>📢</span>
            <span>政策动态</span>
          </div>
          <h2 className="text-3xl font-bold text-fluent-deepOcean-500 mb-4">
            政策风向标
          </h2>
          <p className="text-fluent-deepOcean-300 max-w-2xl mx-auto">
            紧跟国家政策导向，合规运营，为用户提供安全可靠的服务
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {policies.map((policy) => (
            <div
              key={policy.id}
              className="group bg-white rounded-2xl p-6 shadow-fluent-md hover:shadow-fluent-xl transition-all duration-300 border border-fluent-deepOcean-100 hover:border-fluent-gold-300"
            >
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-fluent-gold-100 to-fluent-gold-200 rounded-xl flex items-center justify-center text-2xl flex-shrink-0">
                  {policy.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-fluent-deepOcean-400 mb-1">
                    {policy.department} · {policy.publishDate}
                  </p>
                  <h3 className="text-lg font-semibold text-fluent-deepOcean-500 line-clamp-2 group-hover:text-fluent-gold-600 transition-colors">
                    {policy.title}
                  </h3>
                </div>
              </div>

              <p className="text-sm text-fluent-deepOcean-400 mb-4 line-clamp-2">
                {policy.summary}
              </p>

              <div className="bg-fluent-deepOcean-50 rounded-xl p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-fluent-gold-500">🏠</span>
                  <span className="text-sm font-medium text-fluent-deepOcean-500">平台响应</span>
                </div>
                <p className="text-sm text-fluent-deepOcean-400">
                  {policy.platformImpact}
                </p>
              </div>

              <a
                href={policy.link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-fluent-gold-500 hover:text-fluent-gold-600 text-sm font-medium transition-colors"
              >
                <span>查看详情</span>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <div className="inline-flex items-center gap-4 bg-white rounded-full px-6 py-3 shadow-fluent-sm border border-fluent-deepOcean-100">
            <span className="text-fluent-deepOcean-400 text-sm">政策合规，安全可靠</span>
            <span className="w-1 h-1 bg-fluent-deepOcean-300 rounded-full"></span>
            <span className="text-fluent-deepOcean-400 text-sm">数据溯源，透明可信</span>
            <span className="w-1 h-1 bg-fluent-deepOcean-300 rounded-full"></span>
            <span className="text-fluent-deepOcean-400 text-sm">绿色算力，低碳发展</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PolicySection;
