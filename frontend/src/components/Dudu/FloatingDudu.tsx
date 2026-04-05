import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence, useDragControls } from 'framer-motion';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Badge,
  Menu,
  MenuItem,
  Divider,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Snackbar,
  Alert,
  LinearProgress,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Pets as PetsIcon,
  Close as CloseIcon,
  Settings as SettingsIcon,
  ShoppingBag as ShoppingBagIcon,
  EmojiEvents as EmojiEventsIcon,
  Restaurant as RestaurantIcon,
  Favorite as FavoriteIcon,
  AutoAwesome as AutoAwesomeIcon,
  DragIndicator as DragIndicatorIcon
} from '@mui/icons-material';
import { useDuduStore, emotionEmojiMap, actionLabelMap } from '../stores/duduStore';
import DuduProfile from './DuduProfile';

interface FloatingDuduProps {
  userId?: string;
  onProfileOpen?: () => void;
}

const FloatingDudu: React.FC<FloatingDuduProps> = ({ userId = 'default_user', onProfileOpen }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const {
    state,
    isVisible,
    position,
    setVisibility,
    setPosition,
    clickDudu,
    showMessage,
    fetchState,
    getRandomAction
  } = useDuduStore();
  
  const [isDragging, setIsDragging] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [showProfile, setShowProfile] = useState(false);
  const [showFeedDialog, setShowFeedDialog] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; type: 'success' | 'info' | 'warning' }>({
    open: false,
    message: '',
    type: 'info'
  });
  
  const dragControls = useDragControls();
  const containerRef = useRef<HTMLDivElement>(null);
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  useEffect(() => {
    fetchState(userId);
    
    return () => {
      if (idleTimerRef.current) {
        clearInterval(idleTimerRef.current);
      }
    };
  }, [userId, fetchState]);
  
  useEffect(() => {
    idleTimerRef.current = setInterval(async () => {
      if (!isDragging && state) {
        const random = await getRandomAction(userId);
        if (random.message) {
          showMessage(random.message, 4000);
        }
      }
    }, 30000);
    
    return () => {
      if (idleTimerRef.current) {
        clearInterval(idleTimerRef.current);
      }
    };
  }, [userId, isDragging, state, getRandomAction, showMessage]);
  
  const handleClick = useCallback(async (e: React.MouseEvent) => {
    if (isDragging) return;
    
    e.stopPropagation();
    const result = await clickDudu(userId);
    
    if (result.integralBonus > 0) {
      setSnackbar({
        open: true,
        message: `获得 ${result.integralBonus} 积分！`,
        type: 'success'
      });
    }
    
    if (result.message) {
      showMessage(result.message, 3000);
    }
  }, [userId, isDragging, clickDudu, showMessage]);
  
  const handleDragEnd = useCallback((event: MouseEvent | TouchEvent | PointerEvent, info: { point: { x: number; y: number } }) => {
    setIsDragging(false);
    
    const x = Math.max(0, Math.min(window.innerWidth - 100, info.point.x - 50));
    const y = Math.max(0, Math.min(window.innerHeight - 100, info.point.y - 50));
    
    setPosition({ x, y });
  }, [setPosition]);
  
  const handleMenuOpen = (e: React.MouseEvent<HTMLElement>) => {
    e.stopPropagation();
    setMenuAnchor(e.currentTarget);
    setShowMenu(true);
  };
  
  const handleMenuClose = () => {
    setMenuAnchor(null);
    setShowMenu(false);
  };
  
  const handleProfileOpen = () => {
    setShowProfile(true);
    handleMenuClose();
    onProfileOpen?.();
  };
  
  const handleFeed = () => {
    setShowFeedDialog(true);
    handleMenuClose();
  };
  
  const handleHide = () => {
    setVisibility(false);
    handleMenuClose();
  };
  
  const getEmotionColor = () => {
    if (!state) return theme.palette.primary.main;
    
    const { pleasure } = state.emotion_state;
    if (pleasure >= 70) return theme.palette.success.main;
    if (pleasure >= 40) return theme.palette.warning.main;
    return theme.palette.error.main;
  };
  
  const getAnimationClass = () => {
    if (!state) return 'idle';
    
    switch (state.current_action) {
      case 'wave':
        return 'animate-wave';
      case 'spin':
        return 'animate-spin';
      case 'confetti':
        return 'animate-bounce';
      case 'heart':
        return 'animate-pulse';
      default:
        return 'idle';
    }
  };
  
  if (!isVisible) {
    return (
      <IconButton
        onClick={() => setVisibility(true)}
        sx={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 1000,
          bgcolor: 'background.paper',
          boxShadow: 3,
          '&:hover': { bgcolor: 'action.hover' }
        }}
      >
        <PetsIcon color="primary" />
      </IconButton>
    );
  }
  
  return (
    <>
      <motion.div
        ref={containerRef}
        drag
        dragControls={dragControls}
        dragListener={false}
        dragConstraints={{
          left: 0,
          right: window.innerWidth - 100,
          top: 0,
          bottom: window.innerHeight - 100
        }}
        dragElastic={0.1}
        onDragStart={() => setIsDragging(true)}
        onDragEnd={handleDragEnd}
        initial={{ x: position.x, y: position.y }}
        animate={{ x: position.x, y: position.y }}
        style={{
          position: 'fixed',
          zIndex: 1000,
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
      >
        <Paper
          elevation={4}
          sx={{
            width: isMobile ? 80 : 100,
            height: isMobile ? 80 : 100,
            borderRadius: '50%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'background.paper',
            border: `3px solid ${getEmotionColor()}`,
            position: 'relative',
            overflow: 'visible',
            transition: 'border-color 0.3s ease'
          }}
          onClick={handleClick}
        >
          <Box
            onPointerDown={(e) => {
              e.preventDefault();
              dragControls.start(e);
            }}
            sx={{
              position: 'absolute',
              top: -10,
              left: '50%',
              transform: 'translateX(-50%)',
              cursor: 'grab',
              color: 'text.disabled',
              '&:active': { cursor: 'grabbing' }
            }}
          >
            <DragIndicatorIcon fontSize="small" />
          </Box>
          
          <IconButton
            size="small"
            onClick={handleMenuOpen}
            sx={{
              position: 'absolute',
              top: -5,
              right: -5,
              bgcolor: 'background.paper',
              boxShadow: 1,
              width: 24,
              height: 24,
              '&:hover': { bgcolor: 'action.hover' }
            }}
          >
            <SettingsIcon sx={{ fontSize: 14 }} />
          </IconButton>
          
          <Badge
            badgeContent={state?.level_info.level || 1}
            color="primary"
            sx={{
              '& .MuiBadge-badge': {
                bottom: 5,
                right: 5,
                fontSize: '0.7rem',
                height: 18,
                minWidth: 18
              }
            }}
          >
            <motion.div
              className={getAnimationClass()}
              animate={{
                scale: [1, 1.05, 1],
                rotate: state?.current_action === 'spin' ? 360 : 0
              }}
              transition={{
                duration: 0.5,
                repeat: state?.current_action === 'spin' ? 2 : 0,
                ease: 'easeInOut'
              }}
              style={{ fontSize: isMobile ? '2.5rem' : '3rem' }}
            >
              {emotionEmojiMap[state?.current_emotion || 'idle']}
            </motion.div>
          </Badge>
          
          <AnimatePresence>
            {state?.current_message && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.8 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.8 }}
                style={{
                  position: 'absolute',
                  bottom: '100%',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  marginBottom: 8,
                  whiteSpace: 'nowrap'
                }}
              >
                <Paper
                  elevation={3}
                  sx={{
                    px: 2,
                    py: 1,
                    bgcolor: 'background.paper',
                    borderRadius: 2,
                    maxWidth: 200,
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      bottom: -6,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      borderLeft: '6px solid transparent',
                      borderRight: '6px solid transparent',
                      borderTop: '6px solid',
                      borderTopColor: 'background.paper'
                    }
                  }}
                >
                  <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>
                    {state.current_message}
                  </Typography>
                </Paper>
              </motion.div>
            )}
          </AnimatePresence>
          
          {state && (
            <LinearProgress
              variant="determinate"
              value={(state.emotion_state.intimacy / 100) * 100}
              sx={{
                position: 'absolute',
                bottom: 2,
                left: 10,
                right: 10,
                height: 3,
                borderRadius: 2,
                bgcolor: 'divider'
              }}
              color="secondary"
            />
          )}
        </Paper>
      </motion.div>
      
      <Menu
        anchorEl={menuAnchor}
        open={showMenu}
        onClose={handleMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={handleProfileOpen}>
          <EmojiEventsIcon sx={{ mr: 1 }} fontSize="small" />
          成长面板
        </MenuItem>
        <MenuItem onClick={handleFeed}>
          <RestaurantIcon sx={{ mr: 1 }} fontSize="small" />
          喂食
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleHide}>
          <CloseIcon sx={{ mr: 1 }} fontSize="small" />
          隐藏嘟嘟
        </MenuItem>
      </Menu>
      
      <Dialog
        open={showProfile}
        onClose={() => setShowProfile(false)}
        maxWidth="sm"
        fullWidth
      >
        <DuduProfile userId={userId} onClose={() => setShowProfile(false)} />
      </Dialog>
      
      <Dialog
        open={showFeedDialog}
        onClose={() => setShowFeedDialog(false)}
        maxWidth="xs"
      >
        <DialogTitle>喂食嘟嘟</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RestaurantIcon />}
              onClick={() => {
                useDuduStore.getState().feedDudu(userId, 'default', 10);
                setShowFeedDialog(false);
                setSnackbar({ open: true, message: '喂食成功！亲密度+5', type: 'success' });
              }}
            >
              普通食物 (10积分)
            </Button>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<FavoriteIcon />}
              onClick={() => {
                useDuduStore.getState().feedDudu(userId, 'deluxe', 25);
                setShowFeedDialog(false);
                setSnackbar({ open: true, message: '喂食成功！亲密度+12', type: 'success' });
              }}
            >
              精致食物 (25积分)
            </Button>
            <Button
              variant="contained"
              color="secondary"
              startIcon={<AutoAwesomeIcon />}
              onClick={() => {
                useDuduStore.getState().feedDudu(userId, 'premium', 50);
                setShowFeedDialog(false);
                setSnackbar({ open: true, message: '喂食成功！亲密度+25', type: 'success' });
              }}
            >
              高级食物 (50积分)
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowFeedDialog(false)}>取消</Button>
        </DialogActions>
      </Dialog>
      
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.type} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default FloatingDudu;
