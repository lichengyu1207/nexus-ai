import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Avatar,
  IconButton,
  Tabs,
  Tab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Badge,
  Skeleton,
  Alert,
  Divider,
  useTheme
} from '@mui/material';
import {
  Close as CloseIcon,
  EmojiEvents as EmojiEventsIcon,
  ShoppingBag as ShoppingBagIcon,
  History as HistoryIcon,
  Favorite as FavoriteIcon,
  Star as StarIcon,
  Lock as LockIcon,
  Check as CheckIcon,
  AutoAwesome as AutoAwesomeIcon
} from '@mui/icons-material';
import { useDuduStore, emotionEmojiMap, rarityColorMap, Costume } from '../../stores/duduStore';

interface DuduProfileProps {
  userId: string;
  onClose?: () => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <Box hidden={value !== index} sx={{ pt: 2 }}>
    {value === index && children}
  </Box>
);

const DuduProfile: React.FC<DuduProfileProps> = ({ userId, onClose }) => {
  const theme = useTheme();
  const { state, fetchState, equipCostume } = useDuduStore();
  
  const [activeTab, setActiveTab] = useState(0);
  const [costumes, setCostumes] = useState<Costume[]>([]);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [interactions, setInteractions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCostume, setSelectedCostume] = useState<Costume | null>(null);
  const [buyDialogOpen, setBuyDialogOpen] = useState(false);
  
  useEffect(() => {
    loadData();
  }, [userId]);
  
  const loadData = async () => {
    setLoading(true);
    try {
      await fetchState(userId);
      await Promise.all([loadCostumes(), loadAchievements(), loadInteractions()]);
    } finally {
      setLoading(false);
    }
  };
  
  const loadCostumes = async () => {
    try {
      const response = await fetch(`/api/dudu/costumes/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setCostumes(data.costumes || []);
      }
    } catch (error) {
      console.error('Failed to load costumes:', error);
    }
  };
  
  const loadAchievements = async () => {
    try {
      const response = await fetch(`/api/dudu/achievements/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setAchievements(data.achievements || []);
      }
    } catch (error) {
      console.error('Failed to load achievements:', error);
    }
  };
  
  const loadInteractions = async () => {
    try {
      const response = await fetch(`/api/dudu/interactions/${userId}?limit=20`);
      if (response.ok) {
        const data = await response.json();
        setInteractions(data.interactions || []);
      }
    } catch (error) {
      console.error('Failed to load interactions:', error);
    }
  };
  
  const handleEquipCostume = async (costume: Costume) => {
    if (!costume.owned) {
      setSelectedCostume(costume);
      setBuyDialogOpen(true);
      return;
    }
    
    const success = await equipCostume(userId, costume.costume_id);
    if (success) {
      await loadCostumes();
    }
  };
  
  const handleBuyCostume = async () => {
    if (!selectedCostume) return;
    
    try {
      const response = await fetch('/api/dudu/confirm-buy-costume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, costume_id: selectedCostume.costume_id })
      });
      
      if (response.ok) {
        await loadCostumes();
        setBuyDialogOpen(false);
        setSelectedCostume(null);
      }
    } catch (error) {
      console.error('Failed to buy costume:', error);
    }
  };
  
  const getRarityChip = (rarity: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error'> = {
      common: 'default',
      rare: 'primary',
      epic: 'secondary',
      legendary: 'warning'
    };
    return (
      <Chip
        label={rarity.toUpperCase()}
        size="small"
        color={colors[rarity] || 'default'}
        sx={{ fontSize: '0.65rem' }}
      />
    );
  };
  
  if (loading || !state) {
    return (
      <Box sx={{ p: 3 }}>
        <Skeleton variant="rectangular" height={200} sx={{ mb: 2, borderRadius: 2 }} />
        <Skeleton variant="text" />
        <Skeleton variant="text" />
      </Box>
    );
  }
  
  return (
    <Box sx={{ p: 0 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EmojiEventsIcon color="primary" />
          嘟嘟成长面板
        </Typography>
        {onClose && (
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        )}
      </Box>
      
      <Box sx={{ p: 2, bgcolor: 'background.default' }}>
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item>
                <Badge
                  badgeContent={`Lv.${state.level_info.level}`}
                  color="primary"
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                >
                  <Avatar
                    sx={{
                      width: 80,
                      height: 80,
                      bgcolor: 'primary.light',
                      fontSize: '2.5rem'
                    }}
                  >
                    {emotionEmojiMap[state.current_emotion]}
                  </Avatar>
                </Badge>
              </Grid>
              <Grid item xs>
                <Typography variant="h6" gutterBottom>
                  嘟嘟
                </Typography>
                <Box sx={{ mb: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      经验值
                    </Typography>
                    <Typography variant="caption">
                      {state.level_info.exp} / {state.level_info.exp_required}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(state.level_info.exp / state.level_info.exp_required) * 100}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip
                    icon={<FavoriteIcon />}
                    label={`亲密度 ${state.emotion_state.intimacy}`}
                    size="small"
                    color="secondary"
                    variant="outlined"
                  />
                  <Chip
                    icon={<StarIcon />}
                    label={`互动 ${state.level_info.total_interactions}次`}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
        
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle2" gutterBottom>
              情绪状态
            </Typography>
            <Grid container spacing={1}>
              {Object.entries(state.emotion_state).map(([key, value]) => (
                <Grid item xs={4} key={key}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      {key === 'pleasure' ? '愉悦度' : key === 'activity' ? '活跃度' : '亲密度'}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={value}
                      sx={{ height: 6, borderRadius: 3, mt: 0.5 }}
                      color={
                        value >= 70 ? 'success' :
                        value >= 40 ? 'warning' : 'error'
                      }
                    />
                    <Typography variant="caption">{value}%</Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
        
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} variant="fullWidth">
          <Tab icon={<ShoppingBagIcon />} label="装扮" />
          <Tab icon={<EmojiEventsIcon />} label="成就" />
          <Tab icon={<HistoryIcon />} label="记录" />
        </Tabs>
        
        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={1}>
            {costumes.map((costume) => (
              <Grid item xs={6} sm={4} key={costume.costume_id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    border: costume.equipped ? 2 : 0,
                    borderColor: 'primary.main',
                    opacity: costume.unlocked ? 1 : 0.5,
                    '&:hover': { boxShadow: 4 }
                  }}
                  onClick={() => handleEquipCostume(costume)}
                >
                  <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                    <Box sx={{ position: 'relative', mb: 1 }}>
                      <Avatar
                        sx={{
                          width: 50,
                          height: 50,
                          mx: 'auto',
                          bgcolor: 'background.default'
                        }}
                      >
                        {costume.owned ? (
                          costume.equipped ? <CheckIcon color="primary" /> : <AutoAwesomeIcon />
                        ) : (
                          <LockIcon color="disabled" />
                        )}
                      </Avatar>
                      {costume.equipped && (
                        <Chip
                          label="已装备"
                          size="small"
                          color="primary"
                          sx={{ position: 'absolute', bottom: -8, left: '50%', transform: 'translateX(-50%)', fontSize: '0.6rem' }}
                        />
                      )}
                    </Box>
                    <Typography variant="caption" display="block" noWrap>
                      {costume.name}
                    </Typography>
                    {getRarityChip(costume.rarity)}
                    {!costume.owned && costume.unlocked && (
                      <Typography variant="caption" color="warning.main" display="block">
                        {costume.price} 积分
                      </Typography>
                    )}
                    {!costume.unlocked && (
                      <Typography variant="caption" color="text.disabled" display="block">
                        Lv.{costume.unlock_level} 解锁
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>
        
        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={1}>
            {achievements.map((achievement) => (
              <Grid item xs={6} sm={4} key={achievement.id}>
                <Card sx={{ opacity: achievement.unlocked ? 1 : 0.5 }}>
                  <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                    <Avatar
                      sx={{
                        width: 50,
                        height: 50,
                        mx: 'auto',
                        bgcolor: achievement.unlocked ? 'warning.light' : 'grey.300'
                      }}
                    >
                      <EmojiEventsIcon />
                    </Avatar>
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      {achievement.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                      {achievement.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>
        
        <TabPanel value={activeTab} index={2}>
          {interactions.length === 0 ? (
            <Alert severity="info">暂无互动记录</Alert>
          ) : (
            <Box>
              {interactions.map((interaction, index) => (
                <Box key={index} sx={{ py: 1, borderBottom: 1, borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">{interaction.interaction_type}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(interaction.created_at).toLocaleString()}
                    </Typography>
                  </Box>
                  {(interaction.intimacy_change || interaction.exp_change) && (
                    <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                      {interaction.intimacy_change > 0 && (
                        <Chip label={`亲密度+${interaction.intimacy_change}`} size="small" color="secondary" />
                      )}
                      {interaction.exp_change > 0 && (
                        <Chip label={`经验+${interaction.exp_change}`} size="small" color="primary" />
                      )}
                    </Box>
                  )}
                </Box>
              ))}
            </Box>
          )}
        </TabPanel>
      </Box>
      
      <Dialog open={buyDialogOpen} onClose={() => setBuyDialogOpen(false)}>
        <DialogTitle>购买装扮</DialogTitle>
        <DialogContent>
          {selectedCostume && (
            <Box sx={{ pt: 1 }}>
              <Typography variant="h6">{selectedCostume.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedCostume.description}
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body1">
                  价格：<strong>{selectedCostume.price}</strong> 积分
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBuyDialogOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleBuyCostume}>
            确认购买
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DuduProfile;
