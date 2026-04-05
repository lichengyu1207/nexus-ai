import React, { useState } from 'react';
import { Card, Table, Tag, Button, Space, Input, Select, Rate, Modal } from 'antd';
import { SearchOutlined, EyeOutlined, DeleteOutlined, PlusOutlined, ProtectOutlined } from '@ant-design/icons';

const MemoryPage: React.FC = () => {
  const [memories] = useState([
    { id: 1, summary: '用户关注深圳南山区学区房，预算1000万', type: '情景', importance: 5, created: '2026-04-01', accessed: '2026-04-02' },
    { id: 2, summary: '偏好三居室、近地铁、有学位', type: '语义', importance: 4, created: '2026-04-01', accessed: '2026-04-02' },
    { id: 3, summary: '投资回报率要求>5%', type: '程序性', importance: 3, created: '2026-03-30', accessed: '2026-04-01' },
    { id: 4, summary: '曾咨询过北京朝阳区房产', type: '情景', importance: 4, created: '2026-03-28', accessed: '2026-03-30' },
    { id: 5, summary: '对高层住宅有顾虑', type: '语义', importance: 3, created: '2026-03-25', accessed: '2026-03-28' }
  ]);

  const columns = [
    { title: '记忆摘要', dataIndex: 'summary', key: 'summary', ellipsis: true },
    { title: '类型', dataIndex: 'type', key: 'type',
      render: (t: string) => <Tag color={t === '情景' ? 'blue' : t === '语义' ? 'green' : 'orange'}>{t}</Tag>
    },
    { title: '重要度', dataIndex: 'importance', key: 'importance',
      render: (v: number) => <Rate disabled defaultValue={v} count={5} style={{ fontSize: 14 }} />
    },
    { title: '创建时间', dataIndex: 'created', key: 'created' },
    { title: '最后访问', dataIndex: 'accessed', key: 'accessed' },
    {
      title: '操作', key: 'action',
      render: () => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} />
          <Button size="small" icon={<ProtectOutlined />} />
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="海马体记忆系统"
        extra={<Space><Input.Search placeholder="搜索记忆..." style={{ width: 200 }} /><Button type="primary" icon={<PlusOutlined />}>新增记忆</Button></Space>}
      >
        <p style={{ color: '#666', marginBottom: 16 }}>
          海马体记忆系统存储用户的交互历史、偏好和知识，实现跨会话个性化服务。
          记忆采用三层架构：情景记忆（近期交互）、语义记忆（长期知识）、程序性记忆（操作习惯），
          并支持主动遗忘机制自动清理低价值记忆。
        </p>
        <Table dataSource={memories} rowKey="id" columns={columns} pagination={{ pageSize: 8 }} />
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
        <Card title="记忆统计">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 12 }}>
            {[
              { label: '总记忆数', value: 156 },
              { label: '情景记忆', value: 89 },
              { label: '语义记忆', value: 48 },
              { label: '程序性记忆', value: 19 },
              { label: '受保护记忆', value: 12 },
              { label: '待遗忘', value: 8 }
            ].map((item, i) => (
              <div key={i} style={{ padding: 12, background: '#fafafa', borderRadius: 6, textAlign: 'center' }}>
                <div style={{ fontSize: 11, color: '#888' }}>{item.label}</div>
                <div style={{ fontSize: 22, fontWeight: 'bold', color: '#1890ff' }}>{item.value}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="记忆图谱可视化">
          <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fafafa', borderRadius: 8 }}>
            <p style={{ color: '#888' }}>力导向图展示记忆之间的关联网络<br/>节点大小与重要度成正比，边粗细代表关联强度</p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default MemoryPage;
