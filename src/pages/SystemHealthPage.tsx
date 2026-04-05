import React, { useState } from 'react';
import { Card, Table, Tag, Button, Space, Progress, Statistic } from 'antd';
import { SafetyCertificateOutlined, ApiOutlined, DatabaseOutlined, CloudServerOutlined } from '@ant-design/icons';

const SystemHealthPage: React.FC = () => {
  const [healthData] = useState([
    { name: 'API网关', status: '健康', uptime: 99.99, responseTime: 45 },
    { name: 'PostgreSQL', status: '健康', uptime: 99.95, connections: 156 },
    { name: 'Redis缓存', status: '健康', uptime: 99.98, memory: 62 },
    { name: 'RabbitMQ', status: '降级', uptime: 98.5, queueLength: 234 },
    { name: 'LLM服务', status: '健康', uptime: 99.8, avgLatency: 1230 }
  ]);

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ marginBottom: 16 }}>系统性能指标监控看板</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: 12, marginBottom: 24 }}>
        {[
          { title: 'API平均响应', value: '1.23s', icon: <ApiOutlined /> },
          { title: 'P95响应时间', value: '2.85s', icon: <SafetyCertificateOutlined /> },
          { title: 'P99响应时间', value: '5.12s', icon: <SafetyCertificateOutlined /> },
          { title: '实时并发', value: '1,234', icon: <CloudServerOutlined /> },
          { title: '吞吐量/s', value: '856', icon: <DatabaseOutlined /> },
          { title: '可用性', value: '99.9%', icon: <SafetyCertificateOutlined /> }
        ].map((item, i) => (
          <Card key={i} size="small">
            <Statistic title={item.title} value={item.value} prefix={<span style={{ color: '#1890ff' }}>{item.icon}</span>} />
          </Card>
        ))}
      </div>

      <Card title="基础设施健康状态">
        <Table
          dataSource={healthData}
          rowKey="name"
          pagination={false}
          columns={[
            { title: '组件', dataIndex: 'name', key: 'name' },
            { title: '状态', dataIndex: 'status', key: 'status',
              render: (s: string) => <Tag color={s === '健康' ? 'green' : 'orange'}>{s}</Tag>
            },
            { title: '可用性(%)', dataIndex: 'uptime', key: 'uptime',
              render: (v: number) => <Progress percent={v} size="small" format={p => `${p}%`} />
            },
            { title: '关键指标', key: 'metric',
              render: (_: any, r: any) => r.responseTime ? `${r.responseTime}ms` : r.connections ? `${r.connections}连接` : r.memory ? `${r.memory}%内存` : r.queueLength ? `队列${r.queueLength}` : `${r.avgLatency}ms`
            }
          ]}
        />
      </Card>

      <Card title="资源使用率" style={{ marginTop: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 24 }}>
          {[
            { label: 'CPU使用率', value: 45, color: '#52c41a' },
            { label: '内存使用率', value: 68, color: '#faad14' },
            { label: '磁盘使用率', value: 35, color: '#1890ff' }
          ].map((item, i) => (
            <div key={i}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <strong>{item.label}</strong><span style={{ color: item.color }}>{item.value}%</span>
              </div>
              <Progress percent={item.value} strokeColor={item.color} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default SystemHealthPage;
