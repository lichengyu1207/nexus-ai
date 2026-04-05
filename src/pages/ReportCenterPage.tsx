import React, { useState } from 'react';
import { Card, Table, Tag, Button, Space, Progress, Modal } from 'antd';
import { EyeOutlined, DownloadOutlined, ShareAltOutlined, FileTextOutlined } from '@ant-design/icons';

const ReportCenterPage: React.FC = () => {
  const [reports] = useState([
    { id: 1, title: '深圳南山区学区房分析报告', type: '房产分析', time: '2026-04-02 10:30', taskId: 'TASK-001', status: '已完成' },
    { id: 2, title: '北京朝阳区投资价值评估', type: '投资评估', time: '2026-04-02 09:15', taskId: 'TASK-002', status: '已完成' },
    { id: 3, title: '上海浦东新区趋势预测报告', type: '趋势预测', time: '2026-04-01 16:45', taskId: 'TASK-003', status: '已完成' },
    { id: 4, title: '广州天河区政策解读报告', type: '政策解读', time: '2026-04-01 14:20', taskId: 'TASK-004', status: '生成中' },
    { id: 5, title: '杭州西湖区房价深度分析', type: '房产分析', time: '2026-04-01 11:00', taskId: 'TASK-005', status: '已完成' },
    { id: 6, title: '成都高新区综合评估报告', type: '综合评估', time: '2026-03-31 17:30', taskId: 'TASK-006', status: '已完成' }
  ]);

  const columns = [
    { title: '报告标题', dataIndex: 'title', key: 'title' },
    { title: '类型', dataIndex: 'type', key: 'type',
      render: (t: string) => <Tag color={['blue', 'green', 'orange', 'purple', 'blue', 'cyan'][['房产分析','投资评估','趋势预测','政策解读','房产分析','综合评估'].indexOf(t)]}>{t}</Tag>
    },
    { title: '生成时间', dataIndex: 'time', key: 'time' },
    { title: '任务ID', dataIndex: 'taskId', key: 'taskId' },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === '已完成' ? 'green' : 'processing'}>{s}</Tag>
    },
    {
      title: '操作', key: 'action',
      render: () => (
        <Space>
          <Button size="small" icon={<EyeOutlined />}>预览</Button>
          <Button size="small" icon={<DownloadOutlined />}>下载</Button>
          <Button size="small" icon={<ShareAltOutlined />}>分享</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="报告中心"
        extra={<Space><Button>对比报告</Button><Button type="primary">新建报告</Button></Space>}
      >
        <Table dataSource={reports} rowKey="id" columns={columns} pagination={{ pageSize: 8 }} />
      </Card>

      <Card title="报告统计" style={{ marginTop: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 16 }}>
          {[
            { label: '总报告数', value: 12847, color: '#1890ff' },
            { label: '本月新增', value: 1234, color: '#52c41a' },
            { label: '房产分析', value: 5678, color: '#faad14' },
            { label: '投资评估', value: 3456, color: '#e94560' },
            { label: '平均评分', value: '4.8/5', color: '#722ed1' }
          ].map((item, i) => (
            <div key={i} style={{ padding: 20, background: '#fafafa', borderRadius: 8, textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: '#888' }}>{item.label}</div>
              <div style={{ fontSize: 28, fontWeight: 'bold', color: item.color, marginTop: 8 }}>{item.value}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default ReportCenterPage;
