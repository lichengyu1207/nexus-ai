import React from 'react';

interface RegionalItem {
  id: string;
  city: string;
  project: string;
  industry: string;
  impact: string;
  icon: string;
  tags: string[];
}

const regionalData: RegionalItem[] = [
  {
    id: '1',
    city: '长沙宁乡',
    project: '圣饼科技锂电池项目落地',
    industry: '新能源',
    impact: '新能源产业集聚效应凸显，周边产城融合加速，带动区域住房需求增长。',
    icon: '🔋',
    tags: ['新能源', '产城融合'],
  },
  {
    id: '2',
    city: '浏阳',
    project: '蓝思科技3D玻璃研发项目',
    industry: '智能制造',
    impact: '带动智能制造人才流入，区域居住需求看涨，配套服务设施持续完善。',
    icon: '🏭',
    tags: ['智能制造', '人才流入'],
  },
  {
    id: '3',
    city: '郴州',
    project: '新能源动力和储能产业基地',
    industry: '绿色能源',
    impact: '打造绿色能源示范区，生态宜居价值提升，康养地产发展前景广阔。',
    icon: '🌱',
    tags: ['绿色能源', '生态宜居'],
  },
];

const policyInsights = [
  {
    id: '1',
    policy: '"5+5"先进制造业集群',
    insight: '长沙、株洲、湘潭等核心城市群将吸引人口流入，支撑住房需求持续增长。',
    icon: '🏙️',
  },
  {
    id: '2',
    policy: '"园区闲置资产清查处置"',
    insight: '盘活存量资产，带来城市更新机会，老旧工业区改造潜力大。',
    icon: '🔄',
  },
  {
    id: '3',
    policy: '"银发经济"发展',
    insight: '养老地产、康养社区在湖南发展前景广阔，适老化改造需求增加。',
    icon: '👴',
  },
];

const RegionalDynamics: React.FC = () => {
  return (
    <section className="py-12 bg-white">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-fluent-jade-400 to-fluent-jade-600 rounded-xl flex items-center justify-center text-xl">
                🗺️
              </div>
              <div>
                <h3 className="text-xl font-bold text-fluent-deepOcean-500">区域发展动态（湖南）</h3>
                <p className="text-sm text-fluent-deepOcean-400">2026年重点产业项目与房产影响</p>
              </div>
            </div>

            <div className="space-y-4">
              {regionalData.map((item) => (
                <div
                  key={item.id}
                  className="group bg-fluent-deepOcean-50 rounded-xl p-4 hover:bg-fluent-deepOcean-100 transition-colors cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center text-xl flex-shrink-0 shadow-sm">
                      {item.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-fluent-gold-500">{item.city}</span>
                        <span className="text-xs text-fluent-deepOcean-400">{item.industry}</span>
                      </div>
                      <h4 className="text-sm font-semibold text-fluent-deepOcean-500 mb-1 group-hover:text-fluent-gold-600 transition-colors">
                        {item.project}
                      </h4>
                      <p className="text-xs text-fluent-deepOcean-400 line-clamp-2">
                        {item.impact}
                      </p>
                      <div className="flex gap-2 mt-2">
                        {item.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="text-xs bg-white text-fluent-deepOcean-500 px-2 py-0.5 rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <a
              href="/policy/hunan"
              className="inline-flex items-center gap-2 mt-4 text-fluent-gold-500 hover:text-fluent-gold-600 text-sm font-medium transition-colors"
            >
              <span>查看更多湖南省政策解读</span>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>

          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600 rounded-xl flex items-center justify-center text-xl">
                💡
              </div>
              <div>
                <h3 className="text-xl font-bold text-fluent-deepOcean-500">政策解读与房产影响</h3>
                <p className="text-sm text-fluent-deepOcean-400">湖南省2026年重点政策分析</p>
              </div>
            </div>

            <div className="space-y-4">
              {policyInsights.map((insight) => (
                <div
                  key={insight.id}
                  className="bg-gradient-to-r from-fluent-deepOcean-50 to-fluent-gold-50 rounded-xl p-4 border border-fluent-gold-100"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center text-lg flex-shrink-0 shadow-sm">
                      {insight.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-semibold text-fluent-deepOcean-500 mb-1">
                        {insight.policy}
                      </h4>
                      <p className="text-xs text-fluent-deepOcean-400">
                        {insight.insight}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 bg-fluent-jade-50 rounded-xl p-4 border border-fluent-jade-100">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-fluent-jade-500">📊</span>
                <span className="text-sm font-medium text-fluent-deepOcean-500">房都督分析建议</span>
              </div>
              <p className="text-xs text-fluent-deepOcean-400">
                湖南省长株潭城市群产业升级加速，建议关注产业园区周边住宅、人才公寓投资机会；
                银发经济政策利好养老地产，可重点关注长沙、株洲康养社区项目。
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default RegionalDynamics;
