export { default as TypingText } from './TypingText';
export type { TypingTextRef } from './TypingText';

export { default as DynamicParagraph } from './DynamicParagraph';
export type { DynamicParagraphRef } from './DynamicParagraph';

export { default as ProgressiveChart } from './ProgressiveChart';
export type { ProgressiveChartRef } from './ProgressiveChart';

export { default as AgentContributor } from './AgentContributor';

export { default as PlaybackControls } from './PlaybackControls';

export { default as ReportGenerator } from './ReportGenerator';

export { default as AgentProcessingAnimation } from './AgentProcessingAnimation';

export { useReportGeneratorStore } from './reportGeneratorStore';

export type {
  ReportChunkType,
  ChartPoint,
  ChartData,
  InsightData,
  TypingRecordData,
  ReferenceData,
  DisclaimerData,
  CopyrightData,
  SectionTitleData,
  ParagraphData,
  ReportChunk,
  AgentContribution,
  ReportState,
  PlaybackState,
} from './types/reportStream';

export { AGENT_CONFIG, getAgentInfo } from './types/reportStream';

export {
  mockPriceTrendData,
  mockDistrictCompareData,
  mockRiskDistributionData,
  mockCharts,
  mockTypingRecords,
  mockReferences,
  mockDisclaimer,
  mockCopyright,
  mockReportSections,
  generateMockReportStream,
  createMockReportStreamPlayer,
  MockReportStreamPlayer,
} from './mockReportStream';
