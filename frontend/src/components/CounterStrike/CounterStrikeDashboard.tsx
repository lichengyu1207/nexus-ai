import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Alert,
  LinearProgress,
  Badge,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar
} from '@mui/material';
import {
  Shield as ShieldIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  BugReport as BugReportIcon,
  Router as RouterIcon,
  Psychology as PsychologyIcon,
  Group as GroupIcon,
  Timeline as TimelineIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Block as BlockIcon,
  GpsFixed as GpsFixedIcon,
  LocalFireDepartment as FireIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassEmptyIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

const CounterStrikeDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [activeThreats, setActiveThreats] = useState<any[]>([]);
  const [attackers, setAttackers] = useState<any[]>([]);
  const [attackChains, setAttackChains] = useState<any[]>([]);
  const [honeypots, setHoneypots] = useState<any[]>([]);
  const [counterStrikes, setCounterStrikes] = useState<any[]>([]);
  const [tactics, setTactics] = useState<any[]>([]);
  const [pendingApprovals, setPendingApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState<{ type: 'success' | 'error' | 'warning' | 'info'; message: string } | null>(null);
  
  const [createHoneypotOpen, setCreateHoneypotOpen] = useState(false);
  const [createCounterStrikeOpen, setCreateCounterStrikeOpen] = useState(false);
  const [selectedHoneypotType, setSelectedHoneypotType] = useState('http');
  const [selectedActionType, setSelectedActionType] = useState('rate_limit');
  const [targetIP, setTargetIP] = useState('');
  const [targetIdentity, setTargetIdentity] = useState('');

  const API_BASE = '/api/counterstrike';

  const fetchSystemStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/status`);
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  }, []);

  const fetchActiveThreats = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/threats/active`);
      const data = await response.json();
      setActiveThreats(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch active threats:', error);
    }
  }, []);

  const fetchAttackers = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/recon/attackers`);
      const data = await response.json();
      setAttackers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch attackers:', error);
    }
  }, []);

  const fetchAttackChains = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/trace/chains`);
      const data = await response.json();
      setAttackChains(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch attack chains:', error);
    }
  }, []);

  const fetchHoneypots = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/honeypot/list`);
      const data = await response.json();
      setHoneypots(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch honeypots:', error);
    }
  }, []);

  const fetchCounterStrikes = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/counter-strike/active`);
      const data = await response.json();
      setCounterStrikes(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch counter strikes:', error);
    }
  }, []);

  const fetchTactics = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/tactics`);
      const data = await response.json();
      setTactics(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch tactics:', error);
    }
  }, []);

  const fetchPendingApprovals = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/console/approvals/pending`);
      const data = await response.json();
      setPendingApprovals(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch pending approvals:', error);
    }
  }, []);

  const fetchAllData = useCallback(async () => {
    setLoading(true);
    await Promise.all([
      fetchSystemStatus(),
      fetchActiveThreats(),
      fetchAttackers(),
      fetchAttackChains(),
      fetchHoneypots(),
      fetchCounterStrikes(),
      fetchTactics(),
      fetchPendingApprovals()
    ]);
    setLoading(false);
  }, [fetchSystemStatus, fetchActiveThreats, fetchAttackers, fetchAttackChains, fetchHoneypots, fetchCounterStrikes, fetchTactics, fetchPendingApprovals]);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const handleCreateHoneypot = async () => {
    try {
      const response = await fetch(`${API_BASE}/honeypot/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          honeypot_type: selectedHoneypotType
        })
      });
      
      if (response.ok) {
        setAlert({ type: 'success', message: '蜜罐创建成功' });
        setCreateHoneypotOpen(false);
        fetchHoneypots();
      } else {
        setAlert({ type: 'error', message: '蜜罐创建失败' });
      }
    } catch (error) {
      setAlert({ type: 'error', message: '请求失败' });
    }
  };

  const handleCreateCounterStrike = async () => {
    try {
      const response = await fetch(`${API_BASE}/counter-strike/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action_type: selectedActionType,
          target_identity: targetIdentity,
          target_ip: targetIP
        })
      });
      
      if (response.ok) {
        setAlert({ type: 'success', message: '反击行动创建成功' });
        setCreateCounterStrikeOpen(false);
        fetchCounterStrikes();
      } else {
        setAlert({ type: 'error', message: '反击行动创建失败' });
      }
    } catch (error) {
      setAlert({ type: 'error', message: '请求失败' });
    }
  };

  const handleShutdownHoneypot = async (honeypotId: string) => {
    try {
      const response = await fetch(`${API_BASE}/honeypot/${honeypotId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setAlert({ type: 'success', message: '蜜罐已关闭' });
        fetchHoneypots();
      }
    } catch (error) {
      setAlert({ type: 'error', message: '关闭失败' });
    }
  };

  const handleApproveAction = async (requestId: string) => {
    try {
      const response = await fetch(`${API_BASE}/console/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          request_id: requestId,
          approver: 'admin'
        })
      });
      
      if (response.ok) {
        setAlert({ type: 'success', message: '已批准' });
        fetchPendingApprovals();
      }
    } catch (error) {
      setAlert({ type: 'error', message: '批准失败' });
    }
  };

  const getThreatLevelColor = (level: number) => {
    switch (level) {
      case 4: return 'error';
      case 3: return 'warning';
      case 2: return 'info';
      default: return 'success';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
      case 'approved':
        return 'success';
      case 'pending':
      case 'executing':
        return 'warning';
      case 'failed':
      case 'rejected':
        return 'error';
      default:
        return 'default';
    }
  };

  const threatDistributionData = [
    { name: 'SQL注入', value: 35 },
    { name: '暴力破解', value: 25 },
    { name: 'DDoS', value: 20 },
    { name: '端口扫描', value: 15 },
    { name: '其他', value: 5 }
  ];

  const responseTimeData = [
    { time: '00:00', detection: 45, response: 120 },
    { time: '04:00', detection: 38, response: 95 },
    { time: '08:00', detection: 52, response: 140 },
    { time: '12:00', detection: 48, response: 110 },
    { time: '16:00', detection: 55, response: 130 },
    { time: '20:00', detection: 42, response: 100 }
  ];

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {alert && (
        <Alert severity={alert.type} onClose={() => setAlert(null)} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      )}

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          <ShieldIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          反击系统指挥中心
        </Typography>
        <Box>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={fetchAllData}
            sx={{ mr: 1 }}
          >
            刷新
          </Button>
          <Chip
            icon={<CheckCircleIcon />}
            label={systemStatus?.system_state || '监控中'}
            color={systemStatus?.system_state === 'alerted' ? 'error' : 'success'}
          />
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                活跃威胁
              </Typography>
              <Typography variant="h3" component="div">
                {activeThreats.length}
              </Typography>
              <Typography variant="body2" color="error.main">
                <WarningIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                需要关注
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                活跃蜜罐
              </Typography>
              <Typography variant="h3" component="div">
                {honeypots.filter(h => h.state === 'active').length}
              </Typography>
              <Typography variant="body2" color="primary.main">
                <BugReportIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                诱捕中
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                反击行动
              </Typography>
              <Typography variant="h3" component="div">
                {counterStrikes.length}
              </Typography>
              <Typography variant="body2" color="warning.main">
                <FireIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                执行中
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                待审批
              </Typography>
              <Typography variant="h3" component="div">
                {pendingApprovals.length}
              </Typography>
              <Typography variant="body2" color="info.main">
                <HourglassEmptyIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                等待确认
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={tabValue}
          onChange={(e, v) => setTabValue(v)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab icon={<WarningIcon />} label="威胁态势" />
          <Tab icon={<BugReportIcon />} label="蜜罐管理" />
          <Tab icon={<FireIcon />} label="反击行动" />
          <Tab icon={<PsychologyIcon />} label="战术库" />
          <Tab icon={<SettingsIcon />} label="控制台" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    活跃威胁列表
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>威胁ID</TableCell>
                          <TableCell>攻击者</TableCell>
                          <TableCell>攻击类型</TableCell>
                          <TableCell>威胁等级</TableCell>
                          <TableCell>置信度</TableCell>
                          <TableCell>发现时间</TableCell>
                          <TableCell>操作</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {activeThreats.slice(0, 10).map((threat, index) => (
                          <TableRow key={index}>
                            <TableCell>{threat.report_id?.slice(0, 12)}...</TableCell>
                            <TableCell>{threat.attacker_profile?.attacker_id?.slice(0, 12)}...</TableCell>
                            <TableCell>
                              <Chip
                                label={threat.detected_attack_types?.[0] || 'unknown'}
                                size="small"
                                color="primary"
                              />
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={`Level ${threat.threat_level || 1}`}
                                size="small"
                                color={getThreatLevelColor(threat.threat_level)}
                              />
                            </TableCell>
                            <TableCell>{(threat.confidence * 100).toFixed(0)}%</TableCell>
                            <TableCell>{new Date(threat.created_at).toLocaleString()}</TableCell>
                            <TableCell>
                              <IconButton size="small">
                                <VisibilityIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    攻击类型分布
                  </Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={threatDistributionData}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      >
                        {threatDistributionData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    响应时间趋势
                  </Typography>
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart data={responseTimeData}>
                      <XAxis dataKey="time" />
                      <YAxis />
                      <ChartTooltip />
                      <Line type="monotone" dataKey="detection" stroke="#8884d8" name="检测(ms)" />
                      <Line type="monotone" dataKey="response" stroke="#82ca9d" name="响应(ms)" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 2 }}>
            <Button
              variant="contained"
              startIcon={<PlayArrowIcon />}
              onClick={() => setCreateHoneypotOpen(true)}
            >
              创建蜜罐
            </Button>
          </Box>
          <Grid container spacing={3}>
            {honeypots.map((hp, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="h6">
                        {hp.config?.honeypot_type?.toUpperCase()}
                      </Typography>
                      <Chip
                        label={hp.state}
                        size="small"
                        color={getStatusColor(hp.state)}
                      />
                    </Box>
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      端口: {hp.config?.port}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      交互次数: {hp.interaction_count || 0}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      捕获凭证: {hp.credentials_captured || 0}
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        startIcon={<StopIcon />}
                        onClick={() => handleShutdownHoneypot(hp.config?.honeypot_id)}
                      >
                        关闭
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box sx={{ mb: 2 }}>
            <Button
              variant="contained"
              color="error"
              startIcon={<FireIcon />}
              onClick={() => setCreateCounterStrikeOpen(true)}
            >
              发起反击
            </Button>
          </Box>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>行动ID</TableCell>
                  <TableCell>类型</TableCell>
                  <TableCell>目标IP</TableCell>
                  <TableCell>状态</TableCell>
                  <TableCell>效果评分</TableCell>
                  <TableCell>创建时间</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {counterStrikes.map((cs, index) => (
                  <TableRow key={index}>
                    <TableCell>{cs.action_id?.slice(0, 12)}...</TableCell>
                    <TableCell>
                      <Chip label={cs.action_type} size="small" color="primary" />
                    </TableCell>
                    <TableCell>{cs.target_ip}</TableCell>
                    <TableCell>
                      <Chip label={cs.status} size="small" color={getStatusColor(cs.status)} />
                    </TableCell>
                    <TableCell>{(cs.effectiveness_score * 100).toFixed(0)}%</TableCell>
                    <TableCell>{new Date(cs.created_at).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            {tactics.map((tactic, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">{tactic.name}</Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      {tactic.description}
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Chip label={tactic.category} size="small" sx={{ mr: 1 }} />
                      <Chip
                        label={`成功率: ${(tactic.success_rate * 100).toFixed(0)}%`}
                        size="small"
                        color="success"
                      />
                    </Box>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      使用次数: {tactic.use_count}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    待审批请求
                  </Typography>
                  {pendingApprovals.length === 0 ? (
                    <Typography color="textSecondary">无待审批请求</Typography>
                  ) : (
                    <List>
                      {pendingApprovals.map((approval, index) => (
                        <ListItem key={index} divider>
                          <ListItemIcon>
                            <Avatar sx={{ bgcolor: 'warning.main' }}>
                              <HourglassEmptyIcon />
                            </Avatar>
                          </ListItemIcon>
                          <ListItemText
                            primary={approval.action_type}
                            secondary={`目标: ${approval.target}`}
                          />
                          <Button
                            variant="contained"
                            color="success"
                            size="small"
                            onClick={() => handleApproveAction(approval.request_id)}
                          >
                            批准
                          </Button>
                        </ListItem>
                      ))}
                    </List>
                  )}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    系统状态
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemIcon><ShieldIcon /></ListItemIcon>
                      <ListItemText primary="系统状态" secondary={systemStatus?.system_state || 'monitoring'} />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><TimelineIcon /></ListItemIcon>
                      <ListItemText primary="OODA阶段" secondary={systemStatus?.current_ooda_phase || 'observe'} />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><GroupIcon /></ListItemIcon>
                      <ListItemText primary="注册智能体" secondary={systemStatus?.registered_agents?.length || 0} />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><AssessmentIcon /></ListItemIcon>
                      <ListItemText primary="威胁已消除" secondary={systemStatus?.stats?.threats_neutralized || 0} />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      <Dialog open={createHoneypotOpen} onClose={() => setCreateHoneypotOpen(false)}>
        <DialogTitle>创建蜜罐</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>蜜罐类型</InputLabel>
            <Select
              value={selectedHoneypotType}
              onChange={(e) => setSelectedHoneypotType(e.target.value)}
            >
              <MenuItem value="http">HTTP</MenuItem>
              <MenuItem value="https">HTTPS</MenuItem>
              <MenuItem value="ssh">SSH</MenuItem>
              <MenuItem value="mysql">MySQL</MenuItem>
              <MenuItem value="ftp">FTP</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateHoneypotOpen(false)}>取消</Button>
          <Button onClick={handleCreateHoneypot} variant="contained">创建</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={createCounterStrikeOpen} onClose={() => setCreateCounterStrikeOpen(false)}>
        <DialogTitle>发起反击</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>行动类型</InputLabel>
            <Select
              value={selectedActionType}
              onChange={(e) => setSelectedActionType(e.target.value)}
            >
              <MenuItem value="rate_limit">限流</MenuItem>
              <MenuItem value="tcp_window">TCP窗口限制</MenuItem>
              <MenuItem value="delay_response">延迟响应</MenuItem>
              <MenuItem value="forged_data">伪造数据</MenuItem>
              <MenuItem value="upstream_notification">通知上游</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="目标IP"
            value={targetIP}
            onChange={(e) => setTargetIP(e.target.value)}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            label="目标身份ID"
            value={targetIdentity}
            onChange={(e) => setTargetIdentity(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateCounterStrikeOpen(false)}>取消</Button>
          <Button onClick={handleCreateCounterStrike} variant="contained" color="error">发起</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CounterStrikeDashboard;
