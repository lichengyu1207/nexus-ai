import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tabs,
  Tab,
  Badge,
  Alert,
  Snackbar,
  LinearProgress,
  Grid,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Cancel as RejectIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Memory as MemoryIcon,
  Psychology as PsychologyIcon,
  AutoFixHigh as AutoFixIcon,
  History as HistoryIcon,
  Info as InfoIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon
} from '@mui/icons-material';

interface Suggestion {
  suggestion_id: string;
  agent_id: string;
  agent_type: string;
  category: string;
  suggestion_text: string;
  anomaly_score: number;
  metrics: Record<string, number>;
  status: 'pending' | 'accepted' | 'rejected' | 'applied';
  created_at: string;
  processed_at?: string;
  processed_by?: string;
}

interface VersionInfo {
  version_id: string;
  agent_type: string;
  version: string;
  model_path: string;
  metrics: Record<string, number>;
  created_at: string;
  deployed_at?: string;
  is_active: boolean;
  is_staging: boolean;
}

interface SystemStatus {
  running: boolean;
  version_manager: {
    total_agent_types: number;
    active_versions: Record<string, string>;
    version_counts: Record<string, number>;
  };
  aggregator: {
    common_issue: string | null;
    category_counts: Record<string, number>;
    agent_stats: Record<string, any>;
  };
  pending_suggestions: number;
  total_suggestions: number;
  evolution_history_count: number;
}

const categoryColors: Record<string, 'error' | 'warning' | 'info' | 'success'> = {
  data_drift: 'warning',
  model_decay: 'error',
  env_change: 'info',
  other: 'success'
};

const categoryLabels: Record<string, string> = {
  data_drift: '数据漂移',
  model_decay: '模型衰减',
  env_change: '环境变化',
  other: '其他问题'
};

const statusColors: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
  pending: 'warning',
  accepted: 'primary',
  rejected: 'error',
  applied: 'success'
};

const statusLabels: Record<string, string> = {
  pending: '待处理',
  accepted: '已接受',
  rejected: '已拒绝',
  applied: '已应用'
};

const SuggestionPanel: React.FC = () => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [versions, setVersions] = useState<VersionInfo[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    suggestionId: string;
    action: 'accept' | 'reject';
  }>({ open: false, suggestionId: '', action: 'accept' });
  const [reason, setReason] = useState('');
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [suggestionsRes, statusRes, versionsRes] = await Promise.all([
        fetch('/api/evolution/suggestions?limit=50'),
        fetch('/api/evolution/status'),
        fetch('/api/evolution/versions')
      ]);

      if (suggestionsRes.ok) {
        setSuggestions(await suggestionsRes.json());
      }
      if (statusRes.ok) {
        setSystemStatus(await statusRes.json());
      }
      if (versionsRes.ok) {
        setVersions(await versionsRes.json());
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setSnackbar({ open: true, message: '获取数据失败', severity: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleAction = async () => {
    const { suggestionId, action } = confirmDialog;
    try {
      const response = await fetch(`/api/evolution/suggestions/${suggestionId}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approver: 'admin', reason })
      });

      if (response.ok) {
        setSnackbar({
          open: true,
          message: `建议已${action === 'accept' ? '接受' : '拒绝'}`,
          severity: 'success'
        });
        fetchData();
      } else {
        throw new Error('Action failed');
      }
    } catch (error) {
      setSnackbar({ open: true, message: '操作失败', severity: 'error' });
    } finally {
      setConfirmDialog({ open: false, suggestionId: '', action: 'accept' });
      setReason('');
    }
  };

  const pendingSuggestions = suggestions.filter(s => s.status === 'pending');
  const processedSuggestions = suggestions.filter(s => s.status !== 'pending');

  const renderSuggestionCard = (suggestion: Suggestion) => (
    <Card key={suggestion.suggestion_id} sx={{ mb: 2, border: suggestion.status === 'pending' ? '2px solid #ff9800' : 'none' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="div">
              {suggestion.agent_type} - {suggestion.agent_id}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Chip
                label={categoryLabels[suggestion.category] || suggestion.category}
                color={categoryColors[suggestion.category] || 'default'}
                size="small"
              />
              <Chip
                label={statusLabels[suggestion.status]}
                color={statusColors[suggestion.status]}
                size="small"
              />
            </Box>
          </Box>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="body2" color="text.secondary">
              异常分数
            </Typography>
            <Typography
              variant="h5"
              color={suggestion.anomaly_score > 3 ? 'error' : suggestion.anomaly_score > 2 ? 'warning' : 'success'}
            >
              {suggestion.anomaly_score.toFixed(2)}
            </Typography>
          </Box>
        </Box>

        <Alert severity={suggestion.status === 'pending' ? 'warning' : 'info'} sx={{ mb: 2 }}>
          {suggestion.suggestion_text}
        </Alert>

        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2">详细指标</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {Object.entries(suggestion.metrics).map(([key, value]) => (
                <Grid item xs={6} sm={3} key={key}>
                  <Typography variant="caption" color="text.secondary">
                    {key}
                  </Typography>
                  <Typography variant="body2">
                    {typeof value === 'number' ? value.toFixed(4) : value}
                  </Typography>
                </Grid>
              ))}
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, color: 'text.secondary' }}>
          <ScheduleIcon fontSize="small" />
          <Typography variant="caption">
            创建于: {new Date(suggestion.created_at).toLocaleString('zh-CN')}
          </Typography>
          {suggestion.processed_at && (
            <>
              <Divider orientation="vertical" flexItem />
              <PersonIcon fontSize="small" />
              <Typography variant="caption">
                处理人: {suggestion.processed_by} | {new Date(suggestion.processed_at).toLocaleString('zh-CN')}
              </Typography>
            </>
          )}
        </Box>
      </CardContent>

      {suggestion.status === 'pending' && (
        <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2 }}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<RejectIcon />}
            onClick={() => setConfirmDialog({ open: true, suggestionId: suggestion.suggestion_id, action: 'reject' })}
          >
            拒绝
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<CheckIcon />}
            onClick={() => setConfirmDialog({ open: true, suggestionId: suggestion.suggestion_id, action: 'accept' })}
          >
            接受
          </Button>
        </CardActions>
      )}
    </Card>
  );

  const renderVersionCard = (version: VersionInfo) => (
    <Card key={version.version_id} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h6">
              {version.agent_type} - {version.version}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              {version.is_active && <Chip label="当前版本" color="success" size="small" />}
              {version.is_staging && <Chip label="预发布" color="warning" size="small" />}
            </Box>
          </Box>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="caption" color="text.secondary">
              创建时间
            </Typography>
            <Typography variant="body2">
              {new Date(version.created_at).toLocaleString('zh-CN')}
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Grid container spacing={2}>
          {Object.entries(version.metrics).map(([key, value]) => (
            <Grid item xs={6} sm={4} key={key}>
              <Typography variant="caption" color="text.secondary">
                {key}
              </Typography>
              <Typography variant="body2">
                {typeof value === 'number' ? (value * 100).toFixed(2) + '%' : value}
              </Typography>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );

  const renderSystemStatus = () => {
    if (!systemStatus) return null;

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            系统状态
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="h4" color={systemStatus.running ? 'success.main' : 'error.main'}>
                  {systemStatus.running ? '运行中' : '已停止'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  进化引擎状态
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="h4" color="warning.main">
                  {systemStatus.pending_suggestions}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  待处理建议
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="h4" color="primary.main">
                  {systemStatus.version_manager.total_agent_types}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  智能体类型
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="h4" color="info.main">
                  {systemStatus.total_suggestions}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  总建议数
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {systemStatus.aggregator.common_issue && (
            <Alert severity="warning" sx={{ mt: 2 }} icon={<WarningIcon />}>
              检测到系统共性问题: {categoryLabels[systemStatus.aggregator.common_issue] || systemStatus.aggregator.common_issue}
            </Alert>
          )}

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            问题分类统计
          </Typography>
          <Grid container spacing={1}>
            {Object.entries(systemStatus.aggregator.category_counts).map(([category, count]) => (
              <Grid item key={category}>
                <Chip
                  label={`${categoryLabels[category] || category}: ${count}`}
                  color={categoryColors[category] || 'default'}
                  size="small"
                />
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          <PsychologyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          智能体进化管理系统
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchData}
          disabled={loading}
        >
          刷新
        </Button>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {renderSystemStatus()}

      <Box sx={{ mt: 3 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab
            label={
              <Badge badgeContent={pendingSuggestions.length} color="warning">
                待处理建议
              </Badge>
            }
          />
          <Tab label="历史建议" />
          <Tab label="版本管理" />
        </Tabs>

        <Box sx={{ mt: 2 }}>
          {activeTab === 0 && (
            <Box>
              {pendingSuggestions.length === 0 ? (
                <Card>
                  <CardContent>
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <CheckIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
                      <Typography variant="h6">暂无待处理建议</Typography>
                      <Typography variant="body2" color="text.secondary">
                        所有智能体运行正常
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              ) : (
                pendingSuggestions.map(renderSuggestionCard)
              )}
            </Box>
          )}

          {activeTab === 1 && (
            <Box>
              {processedSuggestions.length === 0 ? (
                <Card>
                  <CardContent>
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <HistoryIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="h6">暂无历史记录</Typography>
                    </Box>
                  </CardContent>
                </Card>
              ) : (
                processedSuggestions.map(renderSuggestionCard)
              )}
            </Box>
          )}

          {activeTab === 2 && (
            <Box>
              {versions.length === 0 ? (
                <Card>
                  <CardContent>
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <MemoryIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="h6">暂无版本记录</Typography>
                    </Box>
                  </CardContent>
                </Card>
              ) : (
                versions.map(renderVersionCard)
              )}
            </Box>
          )}
        </Box>
      </Box>

      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ ...confirmDialog, open: false })}>
        <DialogTitle>
          {confirmDialog.action === 'accept' ? '确认接受建议' : '确认拒绝建议'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="处理原因（可选）"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}>
            取消
          </Button>
          <Button
            variant="contained"
            color={confirmDialog.action === 'accept' ? 'primary' : 'error'}
            onClick={handleAction}
          >
            确认
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SuggestionPanel;
