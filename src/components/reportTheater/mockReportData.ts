import { ReportData, ReportChart, ReportInsight } from './types';

export const generateMockReportData = (): ReportData => ({
  id: 'report_001',
  taskId: 'task_001',
  title: '深圳南山区学区房分析报告',
  summary: '经过六部智能体协同分析，该区域学区房具有较高的投资价值和居住品质，建议重点关注地铁规划区域和优质学区覆盖范围。',
  createdAt: new Date().toISOString(),
  charts: [
    {
      id: 'chart_001',
      type: 'line',
      title: '房价趋势分析',
      data: [
        { month: '1月', price: 78000 },
        { month: '2月', price: 79500 },
        { month: '3月', price: 81000 },
        { month: '4月', price: 82500 },
        { month: '5月', price: 84000 },
        { month: '6月', price: 85000 },
        { month: '7月', price: 86200 },
        { month: '8月', price: 87500 },
        { month: '9月', price: 88800 },
        { month: '10月', price: 90200 },
        { month: '11月', price: 91500 },
        { month: '12月', price: 92800 },
      ],
      config: {
        colors: ['#D4AF37'],
        xAxisLabel: '月份',
        yAxisLabel: '均价(元/㎡)',
      },
    },
    {
      id: 'chart_002',
      type: 'bar',
      title: '区域均价对比',
      data: [
        { area: '科技园', price: 95000, growth: 8.5 },
        { area: '后海', price: 92000, growth: 7.2 },
        { area: '蛇口', price: 85000, growth: 6.8 },
        { area: '西丽', price: 72000, growth: 12.3 },
        { area: '桃源', price: 68000, growth: 15.6 },
      ],
      config: {
        colors: ['#D4AF37', '#F59E0B', '#10B981', '#3B82F6', '#8B5CF6'],
        xAxisLabel: '区域',
        yAxisLabel: '均价(元/㎡)',
      },
    },
    {
      id: 'chart_003',
      type: 'pie',
      title: '配套分布',
      data: [
        { name: '优质学校', value: 35, color: '#3B82F6' },
        { name: '地铁站', value: 25, color: '#10B981' },
        { name: '商业中心', value: 20, color: '#F59E0B' },
        { name: '医疗设施', value: 12, color: '#EF4444' },
        { name: '公园绿地', value: 8, color: '#8B5CF6' },
      ],
      config: {
        colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
      },
    },
  ],
  insights: [
    {
      id: 'insight_001',
      content: '近三个月均价上涨5.2%，高于全市平均水平',
      confidence: 0.92,
      sourceAgent: 'hu',
      type: 'positive',
    },
    {
      id: 'insight_002',
      content: '学区房溢价率约15-20%，优质学区房源稀缺',
      confidence: 0.88,
      sourceAgent: 'li_guan',
      type: 'neutral',
    },
    {
      id: 'insight_003',
      content: '地铁13号线规划站点周边增值潜力大',
      confidence: 0.85,
      sourceAgent: 'bing',
      type: 'positive',
    },
    {
      id: 'insight_004',
      content: '西丽、桃源片区价格相对较低，性价比高',
      confidence: 0.90,
      sourceAgent: 'li',
      type: 'positive',
    },
    {
      id: 'insight_005',
      content: '部分老旧小区存在产权风险，需谨慎核查',
      confidence: 0.75,
      sourceAgent: 'xing',
      type: 'negative',
    },
  ],
});

export const generateMockProgress = (step: number): { progress: number; status: string; currentStep: string } => {
  const steps = [
    { progress: 0, status: 'pending', currentStep: '准备生成报告...' },
    { progress: 15, status: 'collecting', currentStep: '正在采集数据...' },
    { progress: 35, status: 'collecting', currentStep: '数据采集中...' },
    { progress: 50, status: 'analyzing', currentStep: '正在分析趋势...' },
    { progress: 70, status: 'analyzing', currentStep: '生成洞察中...' },
    { progress: 85, status: 'rendering', currentStep: '渲染图表...' },
    { progress: 95, status: 'rendering', currentStep: '生成摘要...' },
    { progress: 100, status: 'completed', currentStep: '报告生成完成' },
  ];
  
  return steps[Math.min(step, steps.length - 1)];
};
