import { 
  ReportChunk, 
  ChartData, 
  ChartPoint, 
  AGENT_CONFIG,
  TypingRecordData,
  ReferenceData,
  DisclaimerData,
  CopyrightData,
  SectionTitleData,
  ParagraphData
} from './types/reportStream';

const agents = Object.keys(AGENT_CONFIG);

function randomAgent(): string {
  return agents[Math.floor(Math.random() * agents.length)];
}

function randomDelay(min: number = 100, max: number = 500): number {
  return Math.floor(Math.random() * (max - min) + min);
}

export const mockPriceTrendData: ChartPoint[] = [
  { x: '2024-01', y: 65000, agent: 'hubu' },
  { x: '2024-02', y: 67000, agent: 'hubu' },
  { x: '2024-03', y: 68000, agent: 'hubu' },
  { x: '2024-04', y: 69500, agent: 'hubu' },
  { x: '2024-05', y: 71000, agent: 'hubu' },
  { x: '2024-06', y: 72500, agent: 'hubu' },
  { x: '2024-07', y: 74000, agent: 'hubu' },
  { x: '2024-08', y: 75800, agent: 'hubu' },
  { x: '2024-09', y: 76200, agent: 'hubu' },
  { x: '2024-10', y: 77500, agent: 'hubu' },
  { x: '2024-11', y: 78300, agent: 'hubu' },
  { x: '2024-12', y: 79500, agent: 'hubu' },
];

export const mockDistrictCompareData: ChartPoint[] = [
  { x: '南山区', y: 85000, agent: 'analyst' },
  { x: '福田区', y: 78000, agent: 'analyst' },
  { x: '罗湖区', y: 62000, agent: 'analyst' },
  { x: '宝安区', y: 55000, agent: 'analyst' },
  { x: '龙岗区', y: 48000, agent: 'analyst' },
  { x: '龙华区', y: 52000, agent: 'analyst' },
];

export const mockRiskDistributionData: ChartPoint[] = [
  { x: '低风险', y: 45, agent: 'bingbu' },
  { x: '中低风险', y: 25, agent: 'bingbu' },
  { x: '中等风险', y: 18, agent: 'bingbu' },
  { x: '中高风险', y: 8, agent: 'bingbu' },
  { x: '高风险', y: 4, agent: 'bingbu' },
];

export const mockCharts: ChartData[] = [
  {
    chartId: 'price-trend',
    chartType: 'line',
    title: '深圳房价走势趋势',
    data: mockPriceTrendData,
    xAxisLabel: '月份',
    yAxisLabel: '均价(元/㎡)',
    colors: ['#3B82F6'],
  },
  {
    chartId: 'district-compare',
    chartType: 'bar',
    title: '各区房价对比',
    data: mockDistrictCompareData,
    xAxisLabel: '行政区',
    yAxisLabel: '均价(元/㎡)',
    colors: ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'],
  },
  {
    chartId: 'risk-distribution',
    chartType: 'pie',
    title: '风险评估分布',
    data: mockRiskDistributionData,
    colors: ['#10B981', '#84CC16', '#F59E0B', '#EF4444', '#DC2626'],
  },
];

export const mockTypingRecords: TypingRecordData[] = [
  {
    id: 'typing-1',
    agent: 'hubu',
    content: '正在从房价数据库提取南山区2024年成交数据...',
    timestamp: 0,
    isVirtual: false,
    source: '户部房价数据库',
  },
  {
    id: 'typing-2',
    agent: 'analyst',
    content: '收到数据，开始进行趋势分析计算...',
    timestamp: 0,
    isVirtual: false,
    source: '分析师AI模型',
  },
  {
    id: 'typing-3',
    agent: 'bingbu',
    content: '正在评估区域风险等级，结合政策调控因素...',
    timestamp: 0,
    isVirtual: false,
    source: '兵部风险评估系统',
  },
  {
    id: 'typing-4',
    agent: 'gongbu',
    content: '获取前海自贸区最新规划数据，分析对房价影响...',
    timestamp: 0,
    isVirtual: false,
    source: '工部城市规划数据库',
  },
  {
    id: 'typing-5',
    agent: 'analyst',
    content: '综合各部数据，生成投资建议模型输出...',
    timestamp: 0,
    isVirtual: true,
    source: 'AI综合分析引擎',
  },
  {
    id: 'typing-6',
    agent: 'libu',
    content: '检索学区划分信息，计算学区房溢价率...',
    timestamp: 0,
    isVirtual: false,
    source: '吏部教育资源数据库',
  },
];

export const mockReferences: ReferenceData[] = [
  {
    id: 'ref-1',
    title: '深圳市2024年房地产市场运行报告',
    source: '深圳市住房和建设局',
    url: 'https://zjj.sz.gov.cn/',
    publishDate: '2024-12-15',
    agent: 'hubu',
  },
  {
    id: 'ref-2',
    title: '南山区国土空间总体规划(2021-2035)',
    source: '深圳市规划和自然资源局南山管理局',
    url: 'https://szgs.sz.gov.cn/',
    publishDate: '2024-06-20',
    agent: 'gongbu',
  },
  {
    id: 'ref-3',
    title: '前海深港现代服务业合作区总体发展规划',
    source: '国家发展和改革委员会',
    url: 'https://www.ndrc.gov.cn/',
    publishDate: '2024-03-10',
    agent: 'gongbu',
  },
  {
    id: 'ref-4',
    title: '深圳市学区划分及教育资源配置报告',
    source: '深圳市教育局',
    url: 'https://szeb.sz.gov.cn/',
    publishDate: '2024-09-01',
    agent: 'libu',
  },
  {
    id: 'ref-5',
    title: '房地产金融风险评估指引',
    source: '中国人民银行',
    url: 'https://www.pbc.gov.cn/',
    publishDate: '2024-01-15',
    agent: 'bingbu',
  },
  {
    id: 'ref-6',
    title: '贝壳研究院深圳二手房市场分析',
    source: '贝壳研究院',
    url: 'https://www.ke.com/',
    publishDate: '2024-11-30',
    agent: 'analyst',
  },
];

export const mockDisclaimer: DisclaimerData = {
  title: '免责声明',
  content: '本报告由房都督AI智能体集群自动生成，仅供参考，不构成任何投资建议。报告中的数据来源于公开渠道和AI模型推算，可能存在时效性差异和预测偏差。投资者应结合自身情况，独立判断并承担相应风险。房都督平台不对因使用本报告所导致的任何损失承担责任。如有疑问，请咨询专业投资顾问。',
};

export const mockCopyright: CopyrightData = {
  holder: '房都督AI智能决策平台',
  year: '2024-2025',
  rights: '保留所有权利。未经书面授权，禁止转载、摘编或建立镜像。',
  contact: 'contact@fangdudu.com',
};

export const mockReportSections = [
  {
    title: '一、市场概况分析',
    paragraphs: [
    '深圳南山区作为深圳市科技创新核心区域，2024年房地产市场表现活跃。全年住宅均价达到79,500元/平方米，同比上涨18.5%，涨幅位居全市首位。区域内存量住宅交易活跃，新增供应相对有限，供需关系持续紧张。',
    '从区域定位来看，南山区聚集了大量高新技术企业总部和研发中心，包括腾讯、大疆、中兴等知名企业。产业聚集效应带动了区域内高收入人群增长，形成了强劲的购房需求。同时，深圳湾超级总部基地的建设进一步提升了区域价值。',
    '交通配套方面，地铁2号线、7号线、9号线、11号线、12号线、13号线等多条轨道交通覆盖，形成便捷的交通网络。深圳湾口岸的开通加强了与香港的联系，提升了区域的国际化程度。',
  ],
  },
  {
    title: '二、价格走势深度分析',
    paragraphs: [
    '从月度数据来看，南山区房价呈现稳步上涨态势。1月均价65,000元/平方米，至12月达到79,500元/平方米，全年累计涨幅22.3%。其中，3-5月春季行情涨幅明显，主要受学区房需求带动；7-9月相对平稳，市场进入观望期；10-12月再次加速上涨，受益于政策利好预期。',
    '价格分化现象值得关注。科技园片区均价突破90,000元/平方米，成为南山最高价区域；西丽片区相对较低，均价约65,000元/平方米，但涨幅同样显著。这种分化反映了市场对不同板块价值的差异化认知。',
    '二手房市场方面，全年成交约15,000套，同比略有下降。成交均价78,000元/平方米，略低于新房价格。市场呈现"量跌价涨"特征，说明业主惜售情绪较浓，买家议价空间有限。',
  ],
  },
  {
    title: '三、学区房专项研究',
    paragraphs: [
    '南山区教育资源丰富，拥有南山外国语学校、南山实验教育集团等优质教育资源。学区房溢价明显，重点学区房价较普通区域高出25%-35%。以南山外国语学校学区为例，区域内房价均价达95,000元/平方米，显著高于周边非学区房源。',
    '从投资回报角度看，学区房具有较强的保值增值能力。近五年数据显示，学区房年均涨幅约15%，高于区域平均水平。同时，学区房租赁需求旺盛，租金回报率可达3.2%，高于普通住宅的2.5%。',
    '需要注意的是，学区政策存在调整风险。2024年教育局发布的多校划片政策试点，可能对部分学区房价值产生影响。建议投资者关注政策动向，选择教育资源相对稳定的区域。',
  ],
  },
  {
    title: '四、风险评估与预警',
    paragraphs: [
    '当前市场存在以下主要风险：一是政策调控风险，房地产税立法进程可能影响市场预期；二是金融风险，部分购房者杠杆率较高，需关注还款能力变化；三是市场过热风险，部分区域房价短期涨幅过大，存在回调可能。',
    '从风险评估模型来看，南山区整体风险等级为"中低风险"。其中，科技园片区因产业支撑强劲，风险较低；前海片区因规划利好明确，风险可控；部分老旧小区因配套相对落后，需关注流动性风险。',
    '建议投资者采取以下风险应对措施：合理控制杠杆比例，月供不超过家庭收入的40%；分散投资，避免过度集中于单一区域；保持充足现金流，应对可能的短期波动；关注政策信号，及时调整投资策略。',
  ],
  },
  {
    title: '五、投资建议与策略',
    paragraphs: [
    '基于以上分析，我们对不同类型投资者提出差异化建议。对于自住型购房者，建议关注科技园、深圳湾等核心区域，优先选择交通便利、配套完善的优质房源，可适当放宽学区要求以控制预算。',
    '对于投资型购房者，建议关注前海自贸区辐射区域，如前海周边的老前海、蛇口等板块，未来升值潜力较大。同时可考虑西丽片区，受益于西丽高铁站规划，存在价值重估空间。',
    '对于改善型购房者，建议关注深圳湾超级总部基地周边的高端改善盘，区域发展潜力大，品质较高，适合长期持有。同时可考虑蛇口海上世界片区，国际化程度高，生活品质优越。',
  ],
  },
];

export function generateMockReportStream(): ReportChunk[] {
  const chunks: ReportChunk[] = [];
  let timestamp = Date.now();

  chunks.push({
    type: 'title',
    content: '深圳南山区房产投资分析报告',
    agent: 'analyst',
    timestamp: timestamp,
  });
  timestamp += randomDelay(300, 600);

  mockTypingRecords.forEach((record) => {
    chunks.push({
      type: 'typing-record',
      content: record,
      agent: record.agent,
      timestamp: timestamp,
    });
    timestamp += randomDelay(150, 300);
  });

  chunks.push({
    type: 'summary',
    content: '本报告基于2024年全年数据，对深圳南山区房产市场进行了深入分析。通过多维度数据对比，结合宏观经济指标和区域发展规划，为投资者提供全面的决策参考。',
    agent: 'analyst',
    timestamp: timestamp,
  });
  timestamp += randomDelay(400, 600);

  mockReportSections.forEach((section) => {
    chunks.push({
      type: 'section-title',
      content: {
        id: `section-${timestamp}`,
        text: section.title,
        level: 2,
      },
      agent: 'analyst',
      timestamp: timestamp,
    });
    timestamp += randomDelay(200, 400);

    section.paragraphs.forEach((paragraph, pIndex) => {
      chunks.push({
        type: 'paragraph',
        content: {
          id: `para-${timestamp}-${pIndex}`,
          text: paragraph,
          agent: 'analyst',
        },
        agent: 'analyst',
        timestamp: timestamp,
      });
      timestamp += randomDelay(800, 1500);
    });
  });

  const insights = [
    {
      text: '南山区房价全年涨幅达18.5%，高于全市平均水平12个百分点，显示出强劲的区域竞争力。',
      agent: 'hubu',
      type: 'positive' as const,
    },
    {
      text: '科技园周边房价突破9万元/㎡，成为南山最热门板块，主要受互联网产业聚集效应驱动。',
      agent: 'analyst',
      type: 'positive' as const,
    },
    {
      text: '学区房溢价明显，重点学区房价较普通区域高出25%-35%，投资回报率稳定。',
      agent: 'libu',
      type: 'neutral' as const,
    },
    {
      text: '前海自贸区规划落地加速，预计未来3年将带动周边房价上涨15%-20%。',
      agent: 'gongbu',
      type: 'positive' as const,
    },
    {
      text: '当前市场存在一定过热风险，建议投资者关注政策调控动向，合理控制杠杆。',
      agent: 'bingbu',
      type: 'negative' as const,
    },
  ];

  insights.forEach((insight) => {
    chunks.push({
      type: 'insight',
      content: insight.text,
      agent: insight.agent,
      timestamp: timestamp,
    });
    timestamp += randomDelay(300, 500);
  });

  mockCharts.forEach((chart) => {
    chunks.push({
      type: 'chart',
      content: chart,
      agent: chart.data[0]?.agent || 'analyst',
      timestamp: timestamp,
      chartId: chart.chartId,
    });
    timestamp += randomDelay(500, 800);
  });

  mockReferences.forEach((ref) => {
    chunks.push({
      type: 'reference',
      content: ref,
      agent: ref.agent,
      timestamp: timestamp,
    });
    timestamp += randomDelay(100, 200);
  });

  chunks.push({
    type: 'disclaimer',
    content: mockDisclaimer,
    timestamp: timestamp,
  });
  timestamp += randomDelay(200, 400);

  chunks.push({
    type: 'copyright',
    content: mockCopyright,
    timestamp: timestamp,
  });
  timestamp += randomDelay(100, 200);

  chunks.push({
    type: 'complete',
    content: '报告生成完成',
    timestamp: timestamp,
  });

  return chunks;
}

export type ReportStreamCallback = (chunk: ReportChunk) => void;

export class MockReportStreamPlayer {
  private chunks: ReportChunk[];
  private currentIndex: number = 0;
  private isPlaying: boolean = false;
  private timeoutId: NodeJS.Timeout | null = null;
  private callbacks: Set<ReportStreamCallback> = new Set();
  private speed: number = 1;
  private startTime: number = 0;
  private pausedTime: number = 0;

  constructor(chunks?: ReportChunk[]) {
    this.chunks = chunks || generateMockReportStream();
  }

  subscribe(callback: ReportStreamCallback): () => void {
    this.callbacks.add(callback);
    return () => this.callbacks.delete(callback);
  }

  play(): void {
    if (this.isPlaying) return;
    
    this.isPlaying = true;
    
    if (this.currentIndex === 0) {
      this.startTime = Date.now();
    }
    
    this.emitNext();
  }

  pause(): void {
    this.isPlaying = false;
    this.pausedTime = Date.now();
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }

  reset(): void {
    this.pause();
    this.currentIndex = 0;
    this.startTime = 0;
    this.pausedTime = 0;
  }

  setSpeed(speed: number): void {
    this.speed = Math.max(0.1, Math.min(5, speed));
  }

  seekToProgress(progress: number): void {
    const targetIndex = Math.floor((progress / 100) * this.chunks.length);
    this.currentIndex = Math.max(0, Math.min(targetIndex, this.chunks.length - 1));
    
    if (this.isPlaying) {
      this.emitNext();
    }
  }

  getProgress(): number {
    return (this.currentIndex / this.chunks.length) * 100;
  }

  getCurrentTime(): number {
    if (this.currentIndex === 0) return 0;
    return this.chunks[this.currentIndex - 1]?.timestamp - this.chunks[0].timestamp || 0;
  }

  getTotalDuration(): number {
    if (this.chunks.length === 0) return 0;
    return this.chunks[this.chunks.length - 1].timestamp - this.chunks[0].timestamp;
  }

  isComplete(): boolean {
    return this.currentIndex >= this.chunks.length;
  }

  private emitNext(): void {
    if (!this.isPlaying || this.currentIndex >= this.chunks.length) {
      this.isPlaying = false;
      return;
    }

    const chunk = this.chunks[this.currentIndex];
    this.callbacks.forEach(cb => cb(chunk));
    this.currentIndex++;

    if (this.currentIndex < this.chunks.length) {
      const nextChunk = this.chunks[this.currentIndex];
      const delay = (nextChunk.timestamp - chunk.timestamp) / this.speed;
      
      this.timeoutId = setTimeout(() => {
        this.emitNext();
      }, Math.max(50, delay));
    } else {
      this.isPlaying = false;
    }
  }

  getAllChunks(): ReportChunk[] {
    return [...this.chunks];
  }

  getChunksUpToProgress(progress: number): ReportChunk[] {
    const targetIndex = Math.floor((progress / 100) * this.chunks.length);
    return this.chunks.slice(0, targetIndex);
  }
}

export function createMockReportStreamPlayer(): MockReportStreamPlayer {
  return new MockReportStreamPlayer();
}
