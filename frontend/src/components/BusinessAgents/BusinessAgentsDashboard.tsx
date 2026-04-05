import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  LinearProgress,
  Alert,
  AlertTitle,
  Alert as MuiAlert,
  Snackbar,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Psychology as PsychologyIcon,
  Groups as GroupsIcon,
  AutoGraph as AutoGraphIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  Speed as SpeedIcon,
  Battery80 as Battery80Icon,
  EmojiEvents as EmojiEventsIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import {
  Chart as RechartsChart,
  PieChart,
  LineChart,
  BarChart,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

const BusinessAgentsDashboard = () => {
  const [agents, setAgents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({});
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState(0);
  const [createTaskOpen, setCreateTaskOpen] = useState(false);
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [agentsRes, tasksRes, statsRes, rulesRes] = await Promise.all([
        axios.get(`${API_BASE}/business-agents/agents`),
        axios.get(`${API_BASE}/business-agents/tasks`),
        axios.get(`${API_BASE}/business-agents/stats`),
        axios.get(`${API_BASE}/business-agents/rules`),
      ]);

      setAgents(agentsRes.data.agents || []);
      setTasks(tasksRes.data.tasks || []);
      setStats(statsRes.data || {});
      setRules(rulesRes.data.rules || []);
      setLoading(false);
    } catch (error) {
    console.error('Failed to fetch dashboard data:', error);
      setLoading(false);
    }
  };

  const getAgentStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'default';
      case 'working': return 'primary';
      case 'learning': return 'secondary';
      case 'reproducing': return 'success';
      case 'hibernating': return 'warning';
      case 'dead': return 'error';
      default: return 'default';
    }
  };

  const getEnergyColor = (energy: number) => {
    if (energy > 70) return 'success';
    if (energy > 30) return 'warning';
    return 'error';
  };

  const handleCreateTask = async (taskData: any) => {
    try {
      await axios.post(`${API_BASE}/business-agents/tasks`, taskData);
      setCreateTaskOpen(false);
      fetchDashboardData();
    } catch (error) {
    console.error('Failed to create task:', error);
    }
  };

  const handleSubmitFeedback = async (feedbackData: any) => {
    try {
      await axios.post(`${API_BASE}/business-agents/feedback`, feedbackData);
      setFeedbackDialogOpen(false);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <LinearProgress />
      </Box>
    );
  }

  const tabs = [
    { label: '智能体状态', icon: <GroupsIcon /> },
    { label: '任务市场', icon: <TrendingUpIcon /> },
    { label: '协作网络', icon: <AutoGraphIcon /> },
    { label: '规则引擎', icon: <SettingsIcon /> },
    { label: '生命指数', icon: <AssessmentIcon /> },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        业务层活体智能体仪表板
      </Typography>
      
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={selectedTab}
          onChange={(_, newValue) => setSelectedTab(newValue)}
          variant="fullWidth"
        >
          {tabs.map((tab, index) => (
            <Tab
              key={index}
              label={tab.label}
              icon={tab.icon}
              id={`business-tab-${index}`}
            />
          ))}
        </Tabs>
      </Paper>

      <TabPanel value={selectedTab} index={0}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  活跃智能体
                </Typography>
                <Typography variant="h3">
                  {agents.filter(a => a.is_alive).length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  平均能量
                </Typography>
                <Typography variant="h3">
                  {agents.length > 0 
                    ? (agents.reduce((sum, a) => sum + a.energy, 0) / agents.length).toFixed(1)
                    : 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  任务完成率
                </Typography>
                <Typography variant="h3">
                  {stats.task_market?.tasks_completed || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                智能体列表
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>名称</TableCell>
                    <TableCell>角色</TableCell>
                    <TableCell>能量</TableCell>
                    <TableCell>年龄</TableCell>
                    <TableCell>状态</TableCell>
                    <TableCell>操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {agents.slice(0, 10).map((agent) => (
                    <TableRow key={agent.agent_id}>
                      <TableCell>{agent.agent_id}</TableCell>
                      <TableCell>{agent.name}</TableCell>
                      <TableCell>{agent.role}</TableCell>
                      <TableCell>
                        <Chip 
                          label={agent.energy?.toFixed(1)} 
                          color={getEnergyColor(agent.energy)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{agent.age}</TableCell>
                      <TableCell>
                        <Chip 
                          label={agent.status} 
                          color={getAgentStatusColor(agent.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Button 
                          size="small" 
                          onClick={() => {
                            setSelectedAgent(agent);
                            setFeedbackDialogOpen(true);
                          }}
                        >
                          反馈
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={selectedTab} index={1}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  任务列表
                </Typography>
                <Button 
                  variant="contained" 
                  startIcon={<AddIcon />}
                  onClick={() => setCreateTaskOpen(true)}
                >
                  创建任务
                </Button>
              </Box>
            <Paper sx={{ p: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>任务ID</TableCell>
                    <TableCell>标题</TableCell>
                    <TableCell>类型</TableCell>
                    <TableCell>奖励能量</TableCell>
                    <TableCell>状态</TableCell>
                    <TableCell>截止时间</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tasks.slice(0, 10).map((task) => (
                    <TableRow key={task.task_id}>
                      <TableCell>{task.task_id}</TableCell>
                      <TableCell>{task.title}</TableCell>
                      <TableCell>{task.task_type}</TableCell>
                      <TableCell>{task.reward_energy}</TableCell>
                      <TableCell>
                        <Chip label={task.status} size="small" />
                      </TableCell>
                      <TableCell>
                        {new Date(task.deadline * 1000).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={selectedTab} index={2}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                协作统计
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary">团队数量</Typography>
                      <Typography variant="h4">{stats.cooperation?.active_teams || 0}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary">协作成功率</Typography>
                      <Typography variant="h4">
                        {stats.cooperation?.avg_team_success_rate?.toFixed(2) || '0.00'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary">能量转移</Typography>
                      <Typography variant="h4">
                        {stats.cooperation?.total_energy_transferred?.toFixed(1) || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={selectedTab} index={3}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                局部规则
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>规则名称</TableCell>
                    <TableCell>部门</TableCell>
                    <TableCell>触发类型</TableCell>
                    <TableCell>执行次数</TableCell>
                    <TableCell>成功率</TableCell>
                    <TableCell>状态</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rules.slice(0, 10).map((rule) => (
                    <TableRow key={rule.rule_id}>
                      <TableCell>{rule.name}</TableCell>
                      <TableCell>{rule.department}</TableCell>
                      <TableCell>{rule.trigger_type}</TableCell>
                      <TableCell>{rule.execution_count}</TableCell>
                      <TableCell>
                        {(rule.success_rate * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={rule.state} 
                          color={rule.state === 'active' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={selectedTab} index={4}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                生命指数分布
              </Typography>
              <Box height={300}>
                <RadarChart data={[
                  { subject: '适应性', A: stats.life_index?.avg_adaptability || 0.5, fullMark: 1 },
                  { subject: '学习效率', A: stats.life_index?.avg_learning_efficiency || 0.5, fullMark: 1 },
                  { subject: '协作度', A: stats.life_index?.avg_collaboration_degree || 0.5, fullMark: 1 },
                  { subject: '涌现智能', A: stats.life_index?.avg_emergent_intelligence || 0.5, fullMark: 1 },
                  { subject: '繁殖健康', A: stats.life_index?.avg_reproduction_health || 0.5, fullMark: 1 },
                ]}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis />
                  <Radar name="生命指数" dataKey="subject" strokeColor="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                </RadarChart>
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                评估等级分布
              </Typography>
                <Box height={300}>
                  <PieChart>
                    <Pie data={[
                      { name: '优秀', value: stats.life_index?.grade_distribution?.excellent || 0, fill: '#4caf50' },
                      { name: '良好', value: stats.life_index?.grade_distribution?.good || 0, fill: '#2196f3' },
                      { name: '一般', value: stats.life_index?.grade_distribution?.average || 0, fill: '#ff9800' },
                      { name: '较差', value: stats.life_index?.grade_distribution?.poor || 0, fill: '#f44336' },
                    ]} cx={200} cy={200} innerRadius={60} outerRadius={80} />
                  </PieChart>
                </Box>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      <Dialog open={createTaskOpen} onClose={() => setCreateTaskOpen(false)}>
        <DialogTitle>创建新任务</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="任务标题"
              margin="normal"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>任务类型</InputLabel>
              <Select defaultValue="consultation">
                <MenuItem value="consultation">咨询</MenuItem>
                <MenuItem value="analysis">分析</MenuItem>
                <MenuItem value="data_collection">数据采集</MenuItem>
                <MenuItem value="report_generation">报告生成</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="描述"
              margin="normal"
              multiline
              rows={3}
            />
            <TextField
              fullWidth
              label="奖励能量"
              margin="normal"
              type="number"
              defaultValue={10}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateTaskOpen(false)}>取消</Button>
          <Button onClick={() => handleCreateTask({})} variant="contained">
            创建
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={feedbackDialogOpen} onClose={() => setFeedbackDialogOpen(false)}>
        <DialogTitle>提交反馈</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <Typography gutterBottom>
              智能体: {selectedAgent?.name}
            </Typography>
            <FormControl fullWidth margin="normal">
              <InputLabel>反馈类型</InputLabel>
              <Select defaultValue="like">
                <MenuItem value="like">点赞</MenuItem>
                <MenuItem value="dislike">点踩</MenuItem>
                <MenuItem value="complaint">投诉</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="评分"
              margin="normal"
              type="number"
              inputProps={{ min: 1, max: 5 }}
              defaultValue={5}
            />
            <TextField
              fullWidth
              label="内容"
              margin="normal"
              multiline
              rows={3}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackDialogOpen(false)}>取消</Button>
          <Button onClick={() => handleSubmitFeedback({})} variant="contained">
            提交
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BusinessAgentsDashboard;
