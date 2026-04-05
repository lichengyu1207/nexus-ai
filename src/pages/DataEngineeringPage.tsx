import React, { useState, useEffect } from 'react';
import {
  PlayCircleOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  SyncOutlined,
  SettingOutlined,
  BarChartOutlined,
  FilterOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Progress,
  Tag,
  Space,
  Typography,
  Divider,
  message,
  Spin,
  Alert,
  Select,
  InputNumber,
  Switch,
  Collapse,
  Descriptions,
  Badge,
  Tooltip,
} from 'antd';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { Option } = Select;

interface DataStats {
  total_samples: number;
  consult_samples: number;
  task_samples: number;
  registry_count: number;
  last_export: string | null;
}

interface DataRegistry {
  id: number;
  name: string;
  version: string;
  source: string;
  record_count: number;
  file_size: number;
  created_at: string;
  status: string;
}

interface QualityReport {
  total_samples: number;
  avg_quality_score: number;
  high_quality_count: number;
  medium_quality_count: number;
  low_quality_count: number;
  persona_distribution: { zhouyu: number; luxun: number; unknown: number };
  intent_distribution: Record<string, number>;
}

interface PipelineResult {
  version: string;
  output_path: string;
  stats: {
    exported: number;
    cleaned: number;
    preprocessed: number;
    augmented: number;
    classified: number;
    formatted: number;
  };
  quality_score: number;
}

const DataEngineeringPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<DataStats | null>(null);
  const [registry, setRegistry] = useState<DataRegistry[]>([]);
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null);
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null);
  const [running, setRunning] = useState(false);

  const [config, setConfig] = useState({
    export_limit: 1000,
    augment: true,
    augment_multiplier: 2,
    min_quality: 0.6,
    output_format: 'instruction',
  });

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/data-engine/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchRegistry = async () => {
    try {
      const response = await fetch('/api/data-engine/registry');
      const data = await response.json();
      setRegistry(data.registry || []);
    } catch (error) {
      console.error('Failed to fetch registry:', error);
    }
  };

  const fetchQualityReport = async () => {
    try {
      const response = await fetch('/api/data-engine/quality-report');
      const data = await response.json();
      setQualityReport(data);
    } catch (error) {
      console.error('Failed to fetch quality report:', error);
    }
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchStats(), fetchRegistry(), fetchQualityReport()]).finally(() => {
      setLoading(false);
    });
  }, []);

  const runPipeline = async () => {
    setRunning(true);
    setPipelineResult(null);
    try {
      const response = await fetch('/api/data-engine/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      const data = await response.json();
      if (data.success) {
        setPipelineResult(data.result);
        message.success(`数据管道执行成功！版本: ${data.result.version}`);
        fetchStats();
        fetchRegistry();
      } else {
        message.error(data.message || '执行失败');
      }
    } catch (error) {
      message.error('执行失败，请检查网络连接');
    } finally {
      setRunning(false);
    }
  };

  const runClassification = async () => {
    try {
      const response = await fetch('/api/data-engine/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sample_size: 100 }),
      });
      const data = await response.json();
      if (data.success) {
        message.success(`分类完成！处理了 ${data.classified_count} 条样本`);
        fetchQualityReport();
      }
    } catch (error) {
      message.error('分类失败');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'green';
    if (score >= 0.6) return 'orange';
    return 'red';
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      active: { color: 'green', text: '活跃' },
      archived: { color: 'default', text: '已归档' },
      pending: { color: 'orange', text: '待处理' },
    };
    const s = statusMap[status] || { color: 'default', text: status };
    return <Tag color={s.color}>{s.text}</Tag>;
  };

  const registryColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
    },
    {
      title: '记录数',
      dataIndex: 'record_count',
      key: 'record_count',
      render: (n: number) => n.toLocaleString(),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (bytes: number) => formatFileSize(bytes),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (t: string) => new Date(t).toLocaleString(),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="container mx-auto px-4">
        <Title level={2}>
          <DatabaseOutlined className="mr-2" />
          底层初始训练数据集构建
        </Title>
        <Paragraph type="secondary">
          构建高质量训练数据集，支持数据导出、清洗、预处理、增强、分类、质量评估全流程
        </Paragraph>

        <Divider />

        <Spin spinning={loading}>
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总样本数"
                  value={stats?.total_samples || 0}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="咨询样本"
                  value={stats?.consult_samples || 0}
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="任务样本"
                  value={stats?.task_samples || 0}
                  prefix={<BarChartOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="数据集版本"
                  value={stats?.registry_count || 0}
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
          </Row>

          <Divider orientation="left">管道配置</Divider>

          <Card className="mb-4">
            <Row gutter={24}>
              <Col span={6}>
                <div className="mb-2">
                  <Text strong>导出限制</Text>
                </div>
                <InputNumber
                  min={100}
                  max={50000}
                  value={config.export_limit}
                  onChange={(v) => setConfig({ ...config, export_limit: v || 1000 })}
                  style={{ width: '100%' }}
                />
              </Col>
              <Col span={6}>
                <div className="mb-2">
                  <Text strong>数据增强</Text>
                </div>
                <Switch
                  checked={config.augment}
                  onChange={(v) => setConfig({ ...config, augment: v })}
                />
              </Col>
              <Col span={6}>
                <div className="mb-2">
                  <Text strong>增强倍数</Text>
                </div>
                <InputNumber
                  min={1}
                  max={5}
                  value={config.augment_multiplier}
                  onChange={(v) => setConfig({ ...config, augment_multiplier: v || 2 })}
                  disabled={!config.augment}
                  style={{ width: '100%' }}
                />
              </Col>
              <Col span={6}>
                <div className="mb-2">
                  <Text strong>最低质量分</Text>
                </div>
                <InputNumber
                  min={0}
                  max={1}
                  step={0.1}
                  value={config.min_quality}
                  onChange={(v) => setConfig({ ...config, min_quality: v || 0.6 })}
                  style={{ width: '100%' }}
                />
              </Col>
            </Row>
            <Row gutter={24} className="mt-4">
              <Col span={6}>
                <div className="mb-2">
                  <Text strong>输出格式</Text>
                </div>
                <Select
                  value={config.output_format}
                  onChange={(v) => setConfig({ ...config, output_format: v })}
                  style={{ width: '100%' }}
                >
                  <Option value="instruction">指令格式</Option>
                  <Option value="chat">对话格式</Option>
                  <Option value="completion">完成格式</Option>
                  <Option value="persona">角色感知格式</Option>
                </Select>
              </Col>
              <Col span={18} className="text-right">
                <Space>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={runPipeline}
                    loading={running}
                    size="large"
                  >
                    执行数据管道
                  </Button>
                  <Button
                    icon={<FilterOutlined />}
                    onClick={runClassification}
                  >
                    运行分类
                  </Button>
                </Space>
              </Col>
            </Row>
          </Card>

          {pipelineResult && (
            <Alert
              type="success"
              message={`管道执行成功 - 版本 ${pipelineResult.version}`}
              description={
                <Descriptions size="small" column={4}>
                  <Descriptions.Item label="导出">{pipelineResult.stats.exported}</Descriptions.Item>
                  <Descriptions.Item label="清洗">{pipelineResult.stats.cleaned}</Descriptions.Item>
                  <Descriptions.Item label="预处理">{pipelineResult.stats.preprocessed}</Descriptions.Item>
                  <Descriptions.Item label="增强">{pipelineResult.stats.augmented}</Descriptions.Item>
                  <Descriptions.Item label="分类">{pipelineResult.stats.classified}</Descriptions.Item>
                  <Descriptions.Item label="格式化">{pipelineResult.stats.formatted}</Descriptions.Item>
                  <Descriptions.Item label="质量分">
                    <Tag color={getQualityColor(pipelineResult.quality_score)}>
                      {(pipelineResult.quality_score * 100).toFixed(1)}%
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="输出路径">{pipelineResult.output_path}</Descriptions.Item>
                </Descriptions>
              }
              showIcon
              className="mb-4"
            />
          )}

          <Divider orientation="left">质量报告</Divider>

          {qualityReport && (
            <Row gutter={[16, 16]} className="mb-4">
              <Col span={6}>
                <Card>
                  <Statistic
                    title="平均质量分"
                    value={(qualityReport.avg_quality_score * 100).toFixed(1)}
                    suffix="%"
                    valueStyle={{ color: getQualityColor(qualityReport.avg_quality_score) }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="高质量样本"
                    value={qualityReport.high_quality_count}
                    prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="中等质量样本"
                    value={qualityReport.medium_quality_count}
                    prefix={<WarningOutlined style={{ color: '#faad14' }} />}
                    valueStyle={{ color: '#faad14' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="低质量样本"
                    value={qualityReport.low_quality_count}
                    prefix={<WarningOutlined style={{ color: '#ff4d4f' }} />}
                    valueStyle={{ color: '#ff4d4f' }}
                  />
                </Card>
              </Col>
            </Row>
          )}

          {qualityReport && (
            <Card title="角色分布" className="mb-4">
              <Row gutter={24}>
                <Col span={8}>
                  <Progress
                    percent={Math.round((qualityReport.persona_distribution.zhouyu / qualityReport.total_samples) * 100) || 0}
                    status="active"
                    strokeColor="#1890ff"
                  />
                  <div className="text-center mt-2">
                    <Text strong>周瑜风格</Text>
                    <Text type="secondary" className="ml-2">
                      ({qualityReport.persona_distribution.zhouyu})
                    </Text>
                  </div>
                </Col>
                <Col span={8}>
                  <Progress
                    percent={Math.round((qualityReport.persona_distribution.luxun / qualityReport.total_samples) * 100) || 0}
                    status="active"
                    strokeColor="#722ed1"
                  />
                  <div className="text-center mt-2">
                    <Text strong>陆逊风格</Text>
                    <Text type="secondary" className="ml-2">
                      ({qualityReport.persona_distribution.luxun})
                    </Text>
                  </div>
                </Col>
                <Col span={8}>
                  <Progress
                    percent={Math.round((qualityReport.persona_distribution.unknown / qualityReport.total_samples) * 100) || 0}
                    status="active"
                    strokeColor="#8c8c8c"
                  />
                  <div className="text-center mt-2">
                    <Text strong>未识别</Text>
                    <Text type="secondary" className="ml-2">
                      ({qualityReport.persona_distribution.unknown})
                    </Text>
                  </div>
                </Col>
              </Row>
            </Card>
          )}

          <Divider orientation="left">数据注册表</Divider>

          <Card>
            <Table
              dataSource={registry}
              columns={registryColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </Card>

          <Divider orientation="left">数据流程说明</Divider>

          <Collapse defaultActiveKey={['1']}>
            <Panel header="数据工程全流程" key="1">
              <Row gutter={16}>
                <Col span={4}>
                  <Card size="small" className="text-center">
                    <DatabaseOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                    <div className="mt-2"><Text strong>数据导出</Text></div>
                    <Text type="secondary" className="text-xs">从数据库导出原始数据</Text>
                  </Card>
                </Col>
                <Col span={4}>
                  <Card size="small" className="text-center">
                    <SyncOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                    <div className="mt-2"><Text strong>数据清洗</Text></div>
                    <Text type="secondary" className="text-xs">去重、脱敏、格式化</Text>
                  </Card>
                </Col>
                <Col span={4}>
                  <Card size="small" className="text-center">
                    <FileTextOutlined style={{ fontSize: 24, color: '#722ed1' }} />
                    <div className="mt-2"><Text strong>文本预处理</Text></div>
                    <Text type="secondary" className="text-xs">分词、实体识别</Text>
                  </Card>
                </Col>
                <Col span={4}>
                  <Card size="small" className="text-center">
                    <PlayCircleOutlined style={{ fontSize: 24, color: '#faad14' }} />
                    <div className="mt-2"><Text strong>数据增强</Text></div>
                    <Text type="secondary" className="text-xs">同义替换、回译</Text>
                  </Card>
                </Col>
                <Col span={4}>
                  <Card size="small" className="text-center">
                    <FilterOutlined style={{ fontSize: 24, color: '#13c2c2' }} />
                    <div className="mt-2"><Text strong>分类标注</Text></div>
                    <Text type="secondary" className="text-xs">意图、角色分类</Text>
                  </Card>
                </Col>
                <Col span={4}>
                  <Card size="small" className="text-center">
                    <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                    <div className="mt-2"><Text strong>质量评估</Text></div>
                    <Text type="secondary" className="text-xs">评分、筛选、输出</Text>
                  </Card>
                </Col>
              </Row>
            </Panel>
            <Panel header="输出格式说明" key="2">
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="指令格式">
                  <code>{'{"instruction": "...", "input": "...", "output": "..."}'}</code>
                </Descriptions.Item>
                <Descriptions.Item label="对话格式">
                  <code>{'{"messages": [{"role": "user", "content": "...}]}'}</code>
                </Descriptions.Item>
                <Descriptions.Item label="完成格式">
                  <code>{'{"prompt": "...", "completion": "..."}'}</code>
                </Descriptions.Item>
                <Descriptions.Item label="角色感知格式">
                  <code>{'{"persona": "zhouyu", "instruction": "...}'}</code>
                </Descriptions.Item>
              </Descriptions>
            </Panel>
          </Collapse>
        </Spin>
      </div>
    </div>
  );
};

export default DataEngineeringPage;
