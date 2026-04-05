import React, { useState, useEffect } from 'react';
import {
  ClusterOutlined,
  ThunderboltOutlined,
  ApiOutlined,
  MessageOutlined,
  DatabaseOutlined,
  LineChartOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  SearchOutlined,
  EyeOutlined,
  NodeIndexOutlined,
  BranchesOutlined,
  HeartOutlined,
  ClockCircleOutlined,
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
  Tabs,
  Collapse,
  Descriptions,
  Badge,
  Tooltip,
  Timeline,
  List,
  Avatar,
  Empty,
  Modal,
  Form,
  InputNumber,
} from 'antd';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { TabPane } = Tabs;
const { Option } = Select;
const { Search } = Input;

interface AgentStatus {
  agent_id: string;
  name: string;
  species: string;
  state: string;
  energy: number;
  age: number;
  stats: {
    tasks_completed: number;
    tasks_failed: number;
    total_reward: number;
    reproduction_count: number;
    messages_sent: number;
    messages_received: number;
  };
  genes: Record<string, any>;
  experience_count: number;
}

interface OverviewData {
  timestamp: number;
  registry: {
    total_agents: number;
    species_distribution: Record<string, number>;
    state_distribution: Record<string, number>;
    total_energy: number;
    avg_energy: number;
  };
  blackboard: {
    total_keys: number;
    keys: string[];
  };
  message_bus: {
    registered_agents: number;
  };
}

interface EnergyFlowData {
  total_energy: number;
  max_possible_energy: number;
  utilization: number;
  species_energy: Record<string, number>;
  hibernating_count: number;
  reproducible_count: number;
}

const FullChainPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [energyFlow, setEnergyFlow] = useState<EnergyFlowData | null>(null);
  const [blackboardKeys, setBlackboardKeys] = useState<any[]>([]);
  const [diagnoses, setDiagnoses] = useState<any[]>([]);
  const [reproductions, setReproductions] = useState<any[]>([]);
  const [deaths, setDeaths] = useState<any[]>([]);

  const [selectedSpecies, setSelectedSpecies] = useState<string | undefined>();
  const [selectedState, setSelectedState] = useState<string | undefined>();
  const [searchKey, setSearchKey] = useState('');
  const [blackboardSearchResults, setBlackboardSearchResults] = useState<any[]>([]);
  
  const [createAgentModalVisible, setCreateAgentModalVisible] = useState(false);
  const [agentForm] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [overviewRes, agentsRes, energyRes, blackboardRes, diagnosesRes, reproductionsRes, deathsRes] = await Promise.all([
        fetch('/api/fullchain/overview').then(r => r.json()),
        fetch('/api/fullchain/agents').then(r => r.json()),
        fetch('/api/fullchain/energy-flow').then(r => r.json()),
        fetch('/api/fullchain/blackboard').then(r => r.json()),
        fetch('/api/fullchain/diagnoses').then(r => r.json()),
        fetch('/api/fullchain/reproductions').then(r => r.json()),
        fetch('/api/fullchain/deaths').then(r => r.json()),
      ]);
      
      setOverview(overviewRes);
      setAgents(agentsRes);
      setEnergyFlow(energyRes);
      setBlackboardKeys(blackboardRes.entries || []);
      setDiagnoses(diagnosesRes);
      setReproductions(reproductionsRes);
      setDeaths(deathsRes);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSearchBlackboard = async (query: string) => {
    if (!query.trim()) return;
    try {
      const response = await fetch(`/api/fullchain/blackboard/search/${encodeURIComponent(query)}`);
      const data = await response.json();
      setBlackboardSearchResults(data);
    } catch (error) {
      message.error('搜索失败');
    }
  };

  const handleCleanup = async () => {
    try {
      const response = await fetch('/api/fullchain/cleanup', { method: 'POST' });
      const data = await response.json();
      message.success(`清理完成，过期条目: ${data.expired_blackboard_entries}`);
      fetchData();
    } catch (error) {
      message.error('清理失败');
    }
  };

  const getStateColor = (state: string) => {
    const colors: Record<string, string> = {
      idle: 'green',
      busy: 'blue',
      thinking: 'purple',
      success: 'cyan',
      error: 'red',
      hibernating: 'orange',
      reproducing: 'magenta',
      dying: 'red',
    };
    return colors[state] || 'default';
  };

  const getStateText = (state: string) => {
    const texts: Record<string, string> = {
      idle: '空闲',
      busy: '忙碌',
      thinking: '思考中',
      success: '成功',
      error: '错误',
      hibernating: '休眠',
      reproducing: '繁殖中',
      dying: '消亡中',
    };
    return texts[state] || state;
  };

  const getSpeciesName = (species: string) => {
    const names: Record<string, string> = {
      li: '礼部',
      gong: '工部',
      hu: '户部',
      bing: '兵部',
      li2: '吏部',
      xing: '刑部',
      attack: '攻击智能体',
      defense: '防御智能体',
      audit: '审计智能体',
      memory: '记忆智能体',
    };
    return names[species] || species;
  };

  const agentColumns = [
    {
      title: 'ID',
      dataIndex: 'agent_id',
      key: 'agent_id',
      width: 120,
      ellipsis: true,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 100,
    },
    {
      title: '物种',
      dataIndex: 'species',
      key: 'species',
      width: 100,
      render: (species: string) => <Tag color="blue">{getSpeciesName(species)}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'state',
      key: 'state',
      width: 100,
      render: (state: string) => (
        <Tag color={getStateColor(state)}>{getStateText(state)}</Tag>
      ),
    },
    {
      title: '能量',
      dataIndex: 'energy',
      key: 'energy',
      width: 150,
      render: (energy: number) => (
        <Progress
          percent={Math.min(100, energy / 2)}
          size="small"
          status={energy < 20 ? 'exception' : 'normal'}
          format={() => `${energy.toFixed(0)}`}
        />
      ),
    },
    {
      title: '年龄',
      dataIndex: 'age',
      key: 'age',
      width: 80,
      render: (age: number) => {
        const hours = Math.floor(age / 3600);
        return hours > 0 ? `${hours}h` : `${Math.floor(age / 60)}m`;
      },
    },
    {
      title: '完成任务',
      dataIndex: ['stats', 'tasks_completed'],
      key: 'tasks_completed',
      width: 80,
    },
    {
      title: '繁殖次数',
      dataIndex: ['stats', 'reproduction_count'],
      key: 'reproduction_count',
      width: 80,
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: any, record: AgentStatus) => (
        <Space>
          <Tooltip title="查看详情">
            <Button type="link" size="small" icon={<EyeOutlined />} />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const filteredAgents = agents.filter(a => {
    if (selectedSpecies && a.species !== selectedSpecies) return false;
    if (selectedState && a.state !== selectedState) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="container mx-auto px-4">
        <Title level={2}>
          <ClusterOutlined className="mr-2" />
          全链路智能体监控系统
        </Title>
        <Paragraph type="secondary">
          智能体集群 · 能量系统 · 繁殖变异 · 元认知诊断 · 黑板共享 · 消息总线
        </Paragraph>

        <Divider />

        <Spin spinning={loading}>
          <Row gutter={[16, 16]}>
            <Col span={4}>
              <Card>
                <Statistic
                  title="智能体总数"
                  value={overview?.registry?.total_agents || 0}
                  prefix={<ClusterOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="总能量"
                  value={energyFlow?.total_energy?.toFixed(0) || 0}
                  prefix={<ThunderboltOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="平均能量"
                  value={overview?.registry?.avg_energy?.toFixed(1) || 0}
                  prefix={<HeartOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="休眠中"
                  value={energyFlow?.hibernating_count || 0}
                  prefix={<PauseCircleOutlined />}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="可繁殖"
                  value={energyFlow?.reproducible_count || 0}
                  prefix={<BranchesOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="黑板条目"
                  value={overview?.blackboard?.total_keys || 0}
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: '#13c2c2' }}
                />
              </Card>
            </Col>
          </Row>

          {energyFlow && (
            <>
              <Divider orientation="left">能量分布</Divider>
              <Row gutter={24} className="mb-4">
                <Col span={12}>
                  <Card title="物种能量分布">
                    {Object.entries(energyFlow.species_energy || {}).map(([species, energy]) => (
                      <div key={species} className="mb-2">
                        <Text>{getSpeciesName(species)}</Text>
                        <Progress
                          percent={(energy as number / energyFlow.total_energy) * 100}
                          format={() => `${(energy as number).toFixed(0)}`}
                          strokeColor={{
                            '0%': '#108ee9',
                            '100%': '#87d068',
                          }}
                        />
                      </div>
                    ))}
                  </Card>
                </Col>
                <Col span={12}>
                  <Card title="状态分布">
                    {overview?.registry?.state_distribution && 
                      Object.entries(overview.registry.state_distribution).map(([state, count]) => (
                        <div key={state} className="mb-2">
                          <Text>{getStateText(state)}</Text>
                          <Progress
                            percent={((count as number) / overview.registry.total_agents) * 100}
                            format={() => `${count}`}
                            strokeColor={getStateColor(state)}
                          />
                        </div>
                      ))
                    }
                  </Card>
                </Col>
              </Row>
            </>
          )}

          <Tabs defaultActiveKey="agents" size="large">
            <TabPane
              tab={
                <span>
                  <ClusterOutlined />
                  智能体列表
                </span>
              }
              key="agents"
            >
              <Card>
                <Row gutter={16} className="mb-4">
                  <Col span={6}>
                    <Select
                      placeholder="筛选物种"
                      allowClear
                      style={{ width: '100%' }}
                      onChange={setSelectedSpecies}
                      value={selectedSpecies}
                    >
                      <Option value="li">礼部</Option>
                      <Option value="gong">工部</Option>
                      <Option value="hu">户部</Option>
                      <Option value="bing">兵部</Option>
                      <Option value="li2">吏部</Option>
                      <Option value="xing">刑部</Option>
                      <Option value="attack">攻击智能体</Option>
                      <Option value="defense">防御智能体</Option>
                      <Option value="audit">审计智能体</Option>
                      <Option value="memory">记忆智能体</Option>
                    </Select>
                  </Col>
                  <Col span={6}>
                    <Select
                      placeholder="筛选状态"
                      allowClear
                      style={{ width: '100%' }}
                      onChange={setSelectedState}
                      value={selectedState}
                    >
                      <Option value="idle">空闲</Option>
                      <Option value="busy">忙碌</Option>
                      <Option value="thinking">思考中</Option>
                      <Option value="hibernating">休眠</Option>
                      <Option value="reproducing">繁殖中</Option>
                    </Select>
                  </Col>
                  <Col span={12} className="text-right">
                    <Space>
                      <Button icon={<ReloadOutlined />} onClick={fetchData}>
                        刷新
                      </Button>
                      <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateAgentModalVisible(true)}>
                        创建智能体
                      </Button>
                    </Space>
                  </Col>
                </Row>

                <Table
                  dataSource={filteredAgents}
                  columns={agentColumns}
                  rowKey="agent_id"
                  pagination={{ pageSize: 10 }}
                  size="small"
                />
              </Card>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <DatabaseOutlined />
                  共享黑板
                </span>
              }
              key="blackboard"
            >
              <Card>
                <Row gutter={16} className="mb-4">
                  <Col span={12}>
                    <Search
                      placeholder="搜索黑板内容..."
                      onSearch={handleSearchBlackboard}
                      enterButton
                    />
                  </Col>
                  <Col span={12} className="text-right">
                    <Button icon={<DeleteOutlined />} onClick={handleCleanup}>
                      清理过期数据
                    </Button>
                  </Col>
                </Row>

                {blackboardSearchResults.length > 0 ? (
                  <List
                    header="搜索结果"
                    bordered
                    dataSource={blackboardSearchResults}
                    renderItem={(item: any) => (
                      <List.Item>
                        <List.Item.Meta
                          title={item.key}
                          description={JSON.stringify(item.value).slice(0, 200)}
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <List
                    header="黑板条目"
                    bordered
                    dataSource={blackboardKeys.slice(0, 50)}
                    renderItem={(item: any) => (
                      <List.Item>
                        <List.Item.Meta
                          title={<Tag color="blue">{item.key}</Tag>}
                          description={item.value}
                        />
                      </List.Item>
                    )}
                  />
                )}
              </Card>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <MessageOutlined />
                  消息总线
                </span>
              }
              key="messages"
            >
              <Card>
                <Descriptions title="消息总线状态" bordered column={2}>
                  <Descriptions.Item label="注册智能体数">
                    {overview?.message_bus?.registered_agents || 0}
                  </Descriptions.Item>
                  <Descriptions.Item label="状态">
                    <Tag color="green">运行中</Tag>
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <LineChartOutlined />
                  诊断记录
                </span>
              }
              key="diagnoses"
            >
              <Card>
                {diagnoses.length > 0 ? (
                  <Timeline>
                    {diagnoses.map((d: any, i: number) => (
                      <Timeline.Item key={i} color={d.anomaly_type === 'performance_drop' ? 'red' : 'blue'}>
                        <Text strong>{d.agent_id}</Text>
                        <br />
                        <Text type="secondary">
                          {d.anomaly_type} - 置信度: {(d.confidence * 100).toFixed(0)}%
                        </Text>
                        <br />
                        <Text>{d.suggestion}</Text>
                      </Timeline.Item>
                    ))}
                  </Timeline>
                ) : (
                  <Empty description="暂无诊断记录" />
                )}
              </Card>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <BranchesOutlined />
                  繁殖记录
                </span>
              }
              key="reproductions"
            >
              <Card>
                {reproductions.length > 0 ? (
                  <List
                    bordered
                    dataSource={reproductions}
                    renderItem={(item: any) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<Avatar style={{ backgroundColor: '#722ed1' }}>R</Avatar>}
                          title={`${item.parent_id} → ${item.child_id}`}
                          description={new Date(item.timestamp * 1000).toLocaleString()}
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="暂无繁殖记录" />
                )}
              </Card>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <ClockCircleOutlined />
                  死亡记录
                </span>
              }
              key="deaths"
            >
              <Card>
                {deaths.length > 0 ? (
                  <List
                    bordered
                    dataSource={deaths}
                    renderItem={(item: any) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<Avatar style={{ backgroundColor: '#ff4d4f' }}>D</Avatar>}
                          title={`${item.name} (${item.species})`}
                          description={`原因: ${item.reason} | 年龄: ${Math.floor(item.age / 3600)}h`}
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="暂无死亡记录" />
                )}
              </Card>
            </TabPane>
          </Tabs>
        </Spin>

        <Modal
          title="创建智能体"
          visible={createAgentModalVisible}
          onCancel={() => setCreateAgentModalVisible(false)}
          onOk={() => agentForm.submit()}
        >
          <Form
            form={agentForm}
            layout="vertical"
            onFinish={async (values) => {
              message.success('智能体创建请求已提交');
              setCreateAgentModalVisible(false);
              agentForm.resetFields();
            }}
          >
            <Form.Item
              name="species"
              label="物种"
              rules={[{ required: true, message: '请选择物种' }]}
            >
              <Select placeholder="选择物种">
                <Option value="li">礼部（咨询）</Option>
                <Option value="gong">工部（分析）</Option>
                <Option value="hu">户部（积分）</Option>
                <Option value="bing">兵部（采集）</Option>
                <Option value="li2">吏部（管理）</Option>
                <Option value="xing">刑部（风控）</Option>
              </Select>
            </Form.Item>
            <Form.Item
              name="name"
              label="名称"
              rules={[{ required: true, message: '请输入名称' }]}
            >
              <Input placeholder="智能体名称" />
            </Form.Item>
            <Form.Item
              name="initial_energy"
              label="初始能量"
              initialValue={100}
            >
              <InputNumber min={10} max={200} style={{ width: '100%' }} />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </div>
  );
};

export default FullChainPage;
