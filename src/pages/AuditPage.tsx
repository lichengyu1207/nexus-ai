import React, { useState } from 'react';
import { Card, Table, Tag, Button, Space, Select, Input, Modal, Timeline } from 'antd';
import { SearchOutlined, EyeOutlined, DownloadOutlined, AlertOutlined } from '@ant-design/icons';

const AuditPage: React.FC = () => {
  const [logs] = useState([
    { id: 1, operator: 'admin', time: '2026-04-02 10:30:15', action: '登录系统', traceId: 'trace-001', result: '成功' },
    { id: 2, operator: '张三', time: '2026-04-02 10:28:42', action: '创建房产分析任务', traceId: 'trace-002', result: '成功' },
    { id: 3, operator: 'system', time: '2026-04-02 10:25:00', action: '数据采集任务执行', traceId: 'trace-003', result: '成功' },
    { id: 4, operator: '李四', time: '2026-04-02 10:20:33', action: '下载报告', traceId: 'trace-004', result: '成功' },
    { id: 5, operator: '王五', time: '2026-04-02 10:15:18', action: '修改智能体配置', traceId: 'trace-005', result: '失败' }
  ]);

  const columns = [
    { title: '操作人', dataIndex: 'operator', key: 'operator' },
    { title: '时间', dataIndex: 'time', key: 'time' },
    { title: '操作内容', dataIndex: 'action', key: 'action',
      render: (a: string) => <span style={{ color: '#1890ff' }}>{a}</span>
    },
    { title: 'Trace ID', dataIndex: 'traceId', key: 'traceId',
      render: (t: string) => <code style={{ background: '#f5f5f5', padding: '2px 6px', borderRadius: 4 }}>{t}</code>
    },
    { title: '结果', dataIndex: 'result', key: 'result',
      render: (r: string) => <Tag color={r === '成功' ? 'green' : 'red'}>{r}</Tag>
    },
    {
      title: '操作', key: 'action',
      render: (_: any, r: any) => (
        <Button size="small" icon={<EyeOutlined />} onClick={() => Modal.info({ title: '全链路调用链', content: `查看 ${r.traceId} 的完整调用链` })}>
          查看链路
        </Button>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="运维与审计（管理员）"
        extra={
          <Space>
            <Input.Search placeholder="搜索日志..." style={{ width: 200 }} />
            <Select defaultValue="all" options={[{ value: 'all', label: '全部操作' }, { value: 'login', label: '登录' }, { value: 'task', label: '任务' }, { value: 'data', label: '数据' }]} />
            <Button icon={<DownloadOutlined />}>导出</Button>
          </Space>
        }
      >
        <Table dataSource={logs} rowKey="id" columns={columns} pagination={{ pageSize: 10 }} />
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
        <Card title="配置备份与回滚">
          <Timeline items={[
            { color: 'green', children: <><strong>v2.3.1</strong> - 当前版本 - 2026-04-02 06:00</> },
            { color: 'green', children: <><strong>v2.3.0</strong> - 2026-04-01 06:00 <Button size="small" type="link">回滚</Button></> },
            { color: 'blue', children: <><strong>v2.2.9</strong> - 2026-03-31 06:00 <Button size="small" type="link">回滚</Button></> }
          ]} />
          <p style={{ marginTop: 12, fontSize: 12, color: '#888' }}>系统自动备份配置，保留最近20个版本。备用网关切换确保主网关故障时系统自动切换。</p>
        </Card>

        <Card title="告警设置">
          <Space direction="vertical" style={{ width: '100%' }}>
            {['CPU使用率 > 80%', '内存使用率 > 85%', '任务队列 > 1000', '响应时间 > 5s'].map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                <span><AlertOutlined style={{ marginRight: 8, color: '#faad14' }} />{item}</span>
                <Tag color="blue">钉钉 + 邮件</Tag>
              </div>
            ))}
          </Space>
        </Card>
      </div>
    </div>
  );
};

export default AuditPage;
