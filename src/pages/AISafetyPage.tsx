import React, { useState, useEffect } from 'react';
import {
  SafetyCertificateOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SearchOutlined,
  FileProtectOutlined,
  DatabaseOutlined,
  SettingOutlined,
  BarChartOutlined,
  FilterOutlined,
  KeyOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
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
  Input,
  InputNumber,
  Switch,
  Collapse,
  Descriptions,
  Badge,
  Tooltip,
  Tabs,
  Form,
  Modal,
  List,
  Empty,
} from 'antd';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;

interface SystemStats {
  input_stats: {
    total_inputs: number;
    risk_safe: number;
    risk_low: number;
    risk_medium: number;
    risk_high: number;
    risk_critical: number;
    total_outputs: number;
    output_violations: number;
    knowledge_added: number;
  };
  abuse_protection: {
    total_audits: number;
    risk_distribution: Record<string, number>;
    recent_critical: Array<{
      risk_level: string;
      categories: string[];
      reason: string;
      timestamp: number;
    }>;
  };
  knowledge_base: {
    total_knowledge: number;
    total_keywords: number;
    categories: Record<string, number>;
  };
  streaming_audit: {
    chunks_processed: number;
    violations_count: number;
  };
}

interface AuditResult {
  allowed: boolean;
  audit: {
    risk_level: string;
    categories: string[];
    confidence: number;
    action: string;
    reason: string;
  };
  enhanced_prompt: string | null;
  sources: Array<{
    id: string;
    source: string;
    relevance: number;
  }>;
  warning?: string;
}

interface KnowledgeItem {
  id: string;
  content: string;
  source: string;
  category: string;
  credibility: number;
  relevance_score: number;
}

const AISafetyPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null);
  const [watermarkResult, setWatermarkResult] = useState<any>(null);
  const [knowledgeResults, setKnowledgeResults] = useState<KnowledgeItem[]>([]);
  const [ragResult, setRagResult] = useState<any>(null);

  const [auditInput, setAuditInput] = useState('');
  const [auditContext, setAuditContext] = useState('');
  const [enableRag, setEnableRag] = useState(true);

  const [outputText, setOutputText] = useState('');
  const [addWatermark, setAddWatermark] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');
  const [knowledgeModalVisible, setKnowledgeModalVisible] = useState(false);
  const [knowledgeForm] = Form.useForm();

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/ai-safety/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchStats().finally(() => setLoading(false));
  }, []);

  const handleAuditInput = async () => {
    if (!auditInput.trim()) {
      message.warning('请输入要审核的内容');
      return;
    }

    try {
      const response = await fetch('/api/ai-safety/audit/input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_input: auditInput,
          context: auditContext ? JSON.parse(auditContext) : null,
          enable_rag: enableRag,
        }),
      });
      const data = await response.json();
      setAuditResult(data);
      
      if (!data.allowed) {
        message.error(`输入被拦截: ${data.audit.reason}`);
      } else if (data.warning) {
        message.warning(data.warning);
      } else {
        message.success('审核通过');
      }
    } catch (error) {
      message.error('审核失败');
    }
  };

  const handleProcessOutput = async () => {
    if (!outputText.trim()) {
      message.warning('请输入要处理的输出内容');
      return;
    }

    try {
      const response = await fetch('/api/ai-safety/audit/output', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          output: outputText,
          content_type: 'text',
          add_watermark: addWatermark,
        }),
      });
      const data = await response.json();
      setWatermarkResult(data);
      message.success('输出处理完成');
    } catch (error) {
      message.error('处理失败');
    }
  };

  const handleSearchKnowledge = async () => {
    if (!searchQuery.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }

    try {
      const response = await fetch(`/api/ai-safety/knowledge/retrieve?query=${encodeURIComponent(searchQuery)}&top_k=10`);
      const data = await response.json();
      setKnowledgeResults(data);
    } catch (error) {
      message.error('搜索失败');
    }
  };

  const handleAddKnowledge = async (values: any) => {
    try {
      const response = await fetch('/api/ai-safety/knowledge/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      const data = await response.json();
      if (data.success) {
        message.success('知识添加成功');
        setKnowledgeModalVisible(false);
        knowledgeForm.resetFields();
        fetchStats();
      }
    } catch (error) {
      message.error('添加失败');
    }
  };

  const handleRagEnhance = async () => {
    if (!auditInput.trim()) {
      message.warning('请先输入查询内容');
      return;
    }

    try {
      const response = await fetch('/api/ai-safety/rag/enhance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: auditInput,
          system_prompt: '',
        }),
      });
      const data = await response.json();
      setRagResult(data);
      message.success('RAG增强完成');
    } catch (error) {
      message.error('RAG增强失败');
    }
  };

  const getRiskColor = (level: string) => {
    const colors: Record<string, string> = {
      safe: 'green',
      low: 'blue',
      medium: 'orange',
      high: 'red',
      critical: 'purple',
    };
    return colors[level] || 'default';
  };

  const getRiskText = (level: string) => {
    const texts: Record<string, string> = {
      safe: '安全',
      low: '低风险',
      medium: '中风险',
      high: '高风险',
      critical: '严重',
    };
    return texts[level] || level;
  };

  const columns = [
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level: string) => (
        <Tag color={getRiskColor(level)}>{getRiskText(level)}</Tag>
      ),
    },
    {
      title: '检测类别',
      dataIndex: 'categories',
      key: 'categories',
      render: (categories: string[]) => (
        <Space wrap>
          {categories.map((c) => (
            <Tag key={c}>{c}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '原因',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (t: number) => new Date(t * 1000).toLocaleString(),
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="container mx-auto px-4">
        <Title level={2}>
          <SafetyCertificateOutlined className="mr-2" />
          AI安全合规防护系统
        </Title>
        <Paragraph type="secondary">
          防知识污染 · 防版权侵权 · 防幻觉误导 · 内容标识 · RAG增强
        </Paragraph>

        <Divider />

        <Spin spinning={loading}>
          <Row gutter={[16, 16]}>
            <Col span={4}>
              <Card>
                <Statistic
                  title="总审核次数"
                  value={stats?.input_stats?.total_inputs || 0}
                  prefix={<FilterOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="安全请求"
                  value={stats?.input_stats?.risk_safe || 0}
                  prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="高风险拦截"
                  value={(stats?.input_stats?.risk_high || 0) + (stats?.input_stats?.risk_critical || 0)}
                  prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="输出处理"
                  value={stats?.input_stats?.total_outputs || 0}
                  prefix={<FileProtectOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="知识库条目"
                  value={stats?.knowledge_base?.total_knowledge || 0}
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: '#13c2c2' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="流式审核块"
                  value={stats?.streaming_audit?.chunks_processed || 0}
                  prefix={<EyeOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
          </Row>

          <Divider orientation="left">风险分布</Divider>

          {stats?.input_stats && (
            <Row gutter={24} className="mb-4">
              <Col span={4}>
                <Progress
                  percent={Math.round(((stats.input_stats.risk_safe || 0) / Math.max(stats.input_stats.total_inputs, 1)) * 100)}
                  status="success"
                  strokeColor="#52c41a"
                />
                <div className="text-center mt-2">
                  <Text strong>安全</Text>
                </div>
              </Col>
              <Col span={4}>
                <Progress
                  percent={Math.round(((stats.input_stats.risk_low || 0) / Math.max(stats.input_stats.total_inputs, 1)) * 100)}
                  strokeColor="#1890ff"
                />
                <div className="text-center mt-2">
                  <Text strong>低风险</Text>
                </div>
              </Col>
              <Col span={4}>
                <Progress
                  percent={Math.round(((stats.input_stats.risk_medium || 0) / Math.max(stats.input_stats.total_inputs, 1)) * 100)}
                  strokeColor="#faad14"
                />
                <div className="text-center mt-2">
                  <Text strong>中风险</Text>
                </div>
              </Col>
              <Col span={4}>
                <Progress
                  percent={Math.round(((stats.input_stats.risk_high || 0) / Math.max(stats.input_stats.total_inputs, 1)) * 100)}
                  strokeColor="#ff4d4f"
                />
                <div className="text-center mt-2">
                  <Text strong>高风险</Text>
                </div>
              </Col>
              <Col span={4}>
                <Progress
                  percent={Math.round(((stats.input_stats.risk_critical || 0) / Math.max(stats.input_stats.total_inputs, 1)) * 100)}
                  strokeColor="#722ed1"
                />
                <div className="text-center mt-2">
                  <Text strong>严重</Text>
                </div>
              </Col>
              <Col span={4}>
                <Progress
                  percent={Math.round(((stats.input_stats.output_violations || 0) / Math.max(stats.input_stats.total_outputs, 1)) * 100)}
                  strokeColor="#eb2f96"
                />
                <div className="text-center mt-2">
                  <Text strong>输出违规</Text>
                </div>
              </Col>
            </Row>
          )}

          <Tabs defaultActiveKey="audit" size="large">
            <TabPane
              tab={
                <span>
                  <FilterOutlined />
                  输入审核
                </span>
              }
              key="audit"
            >
              <Card>
                <Row gutter={24}>
                  <Col span={16}>
                    <div className="mb-2">
                      <Text strong>用户输入</Text>
                    </div>
                    <TextArea
                      rows={4}
                      value={auditInput}
                      onChange={(e) => setAuditInput(e.target.value)}
                      placeholder="输入要审核的用户内容..."
                    />
                  </Col>
                  <Col span={8}>
                    <div className="mb-2">
                      <Text strong>配置</Text>
                    </div>
                    <div className="mb-4">
                      <Switch
                        checked={enableRag}
                        onChange={setEnableRag}
                      /> <Text>启用RAG增强</Text>
                    </div>
                    <Space direction="vertical" className="w-full">
                      <Button
                        type="primary"
                        icon={<FilterOutlined />}
                        onClick={handleAuditInput}
                        block
                      >
                        审核输入
                      </Button>
                      <Button
                        icon={<SearchOutlined />}
                        onClick={handleRagEnhance}
                        block
                      >
                        RAG增强
                      </Button>
                    </Space>
                  </Col>
                </Row>

                {auditResult && (
                  <div className="mt-4">
                    <Divider />
                    <Alert
                      type={auditResult.allowed ? 'success' : 'error'}
                      message={auditResult.allowed ? '审核通过' : '审核未通过'}
                      description={
                        <div>
                          <p><strong>风险等级：</strong>
                            <Tag color={getRiskColor(auditResult.audit.risk_level)}>
                              {getRiskText(auditResult.audit.risk_level)}
                            </Tag>
                          </p>
                          <p><strong>处理动作：</strong>{auditResult.audit.action}</p>
                          <p><strong>原因：</strong>{auditResult.audit.reason}</p>
                          {auditResult.sources.length > 0 && (
                            <div>
                              <strong>RAG知识来源：</strong>
                              <ul>
                                {auditResult.sources.map((s, i) => (
                                  <li key={i}>{s.source} (相关度: {(s.relevance * 100).toFixed(0)}%)</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      }
                      showIcon
                    />
                  </div>
                )}

                {ragResult && (
                  <div className="mt-4">
                    <Divider>增强提示词</Divider>
                    <Paragraph>
                      <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 16 }}>
                        {ragResult.enhanced_prompt}
                      </pre>
                    </Paragraph>
                  </div>
                )}
              </Card>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <FileProtectOutlined />
                  输出处理
                </span>
              }
              key="output"
            >
              <Card>
                <Row gutter={24}>
                  <Col span={16}>
                    <div className="mb-2">
                      <Text strong>模型输出</Text>
                    </div>
                    <TextArea
                      rows={6}
                      value={outputText}
                      onChange={(e) => setOutputText(e.target.value)}
                      placeholder="输入AI生成的输出内容..."
                    />
                  </Col>
                  <Col span={8}>
                    <div className="mb-2">
                      <Text strong>配置</Text>
                    </div>
                    <div className="mb-4">
                      <Switch
                        checked={addWatermark}
                        onChange={setAddWatermark}
                      /> <Text>添加水印标识</Text>
                    </div>
                    <Button
                      type="primary"
                      icon={<FileProtectOutlined />}
                      onClick={handleProcessOutput}
                      block
                    >
                      处理输出
                    </Button>
                  </Col>
                </Row>

                {watermarkResult && (
                  <div className="mt-4">
                    <Divider />
                    <Alert
                      type="success"
                      message="输出处理完成"
                      description={
                        <div>
                          <p><strong>水印ID：</strong>{watermarkResult.watermark?.content_id}</p>
                          <p><strong>AI生成标识：</strong>{watermarkResult.watermark?.ai_generated ? '是' : '否'}</p>
                          <Divider />
                          <p><strong>处理后内容：</strong></p>
                          <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 16, maxHeight: 200, overflow: 'auto' }}>
                            {watermarkResult.content}
                          </pre>
                        </div>
                      }
                      showIcon
                    />
                  </div>
                )}
              </Card>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <DatabaseOutlined />
                  知识库管理
                </span>
              }
              key="knowledge"
            >
              <Card>
                <Row gutter={24} className="mb-4">
                  <Col span={16}>
                    <Input.Search
                      placeholder="搜索知识库..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onSearch={handleSearchKnowledge}
                      enterButton
                      size="large"
                    />
                  </Col>
                  <Col span={8} className="text-right">
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => setKnowledgeModalVisible(true)}
                    >
                      添加知识
                    </Button>
                  </Col>
                </Row>

                {knowledgeResults.length > 0 ? (
                  <List
                    itemLayout="vertical"
                    dataSource={knowledgeResults}
                    renderItem={(item) => (
                      <List.Item>
                        <List.Item.Meta
                          title={
                            <Space>
                              <Tag color="blue">{item.category}</Tag>
                              <Text>来源: {item.source}</Text>
                              <Tag>可信度: {(item.credibility * 100).toFixed(0)}%</Tag>
                              <Tag color="green">相关度: {(item.relevance_score * 100).toFixed(0)}%</Tag>
                            </Space>
                          }
                          description={item.content}
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="搜索知识库获取相关内容" />
                )}

                <Divider />

                <Descriptions title="知识库统计" bordered column={3}>
                  <Descriptions.Item label="总条目数">
                    {stats?.knowledge_base?.total_knowledge || 0}
                  </Descriptions.Item>
                  <Descriptions.Item label="关键词数">
                    {stats?.knowledge_base?.total_keywords || 0}
                  </Descriptions.Item>
                  <Descriptions.Item label="类别分布">
                    {stats?.knowledge_base?.categories &&
                      Object.entries(stats.knowledge_base.categories).map(([cat, count]) => (
                        <Tag key={cat}>{cat}: {count}</Tag>
                      ))}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <WarningOutlined />
                  审核历史
                </span>
              }
              key="history"
            >
              <Card>
                <div className="mb-4">
                  <Button icon={<ReloadOutlined />} onClick={fetchStats}>
                    刷新
                  </Button>
                </div>
                <Table
                  dataSource={stats?.abuse_protection?.recent_critical || []}
                  columns={columns}
                  rowKey={(record, index) => `history-${index}`}
                  pagination={{ pageSize: 10 }}
                />
              </Card>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <SettingOutlined />
                  系统配置
                </span>
              }
              key="config"
            >
              <Card>
                <Collapse defaultActiveKey={['1', '2', '3', '4']}>
                  <Panel header="滥用防护配置" key="1">
                    <Descriptions bordered column={2}>
                      <Descriptions.Item label="状态">已启用</Descriptions.Item>
                      <Descriptions.Item label="安全级别动作">
                        <Tag color="green">允许</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="低风险动作">
                        <Tag color="blue">允许（警告）</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="中风险动作">
                        <Tag color="orange">观察</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="高风险动作">
                        <Tag color="red">拦截</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="严重风险动作">
                        <Tag color="purple">阻断</Tag>
                      </Descriptions.Item>
                    </Descriptions>
                  </Panel>
                  <Panel header="水印配置" key="2">
                    <Descriptions bordered column={2}>
                      <Descriptions.Item label="状态">已启用</Descriptions.Item>
                      <Descriptions.Item label="默认显示标识">是</Descriptions.Item>
                      <Descriptions.Item label="生成器名称">房都督AI</Descriptions.Item>
                      <Descriptions.Item label="平台">智链五方</Descriptions.Item>
                    </Descriptions>
                  </Panel>
                  <Panel header="RAG配置" key="3">
                    <Descriptions bordered column={2}>
                      <Descriptions.Item label="状态">已启用</Descriptions.Item>
                      <Descriptions.Item label="默认检索数量">5</Descriptions.Item>
                    </Descriptions>
                  </Panel>
                  <Panel header="流式审核配置" key="4">
                    <Descriptions bordered column={2}>
                      <Descriptions.Item label="状态">已启用</Descriptions.Item>
                      <Descriptions.Item label="切片大小">100字符</Descriptions.Item>
                      <Descriptions.Item label="窗口大小">200字符</Descriptions.Item>
                      <Descriptions.Item label="最大缓冲">10000字符</Descriptions.Item>
                    </Descriptions>
                  </Panel>
                </Collapse>
              </Card>
            </TabPane>
          </Tabs>
        </Spin>

        <Modal
          title="添加知识"
          visible={knowledgeModalVisible}
          onCancel={() => setKnowledgeModalVisible(false)}
          onOk={() => knowledgeForm.submit()}
        >
          <Form
            form={knowledgeForm}
            layout="vertical"
            onFinish={handleAddKnowledge}
          >
            <Form.Item
              name="knowledge_id"
              label="知识ID"
              rules={[{ required: true, message: '请输入知识ID' }]}
            >
              <Input placeholder="唯一标识符，如: policy_xxx_2025" />
            </Form.Item>
            <Form.Item
              name="content"
              label="知识内容"
              rules={[{ required: true, message: '请输入知识内容' }]}
            >
              <TextArea rows={4} placeholder="知识内容描述..." />
            </Form.Item>
            <Form.Item
              name="source"
              label="来源"
              rules={[{ required: true, message: '请输入来源' }]}
            >
              <Input placeholder="如: 深圳市住房和建设局" />
            </Form.Item>
            <Form.Item
              name="category"
              label="类别"
              rules={[{ required: true, message: '请选择类别' }]}
            >
              <Select placeholder="选择类别">
                <Option value="购房政策">购房政策</Option>
                <Option value="贷款政策">贷款政策</Option>
                <Option value="税费政策">税费政策</Option>
                <Option value="风险提示">风险提示</Option>
                <Option value="市场分析">市场分析</Option>
                <Option value="法律法规">法律法规</Option>
              </Select>
            </Form.Item>
            <Form.Item
              name="credibility"
              label="可信度"
              initialValue={1.0}
            >
              <InputNumber min={0} max={1} step={0.1} />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </div>
  );
};

export default AISafetyPage;
