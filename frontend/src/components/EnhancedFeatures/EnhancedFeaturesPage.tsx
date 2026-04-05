import React, { useState, useEffect, useCallback } from 'react';
import './EnhancedFeaturesPage.css';

interface Notification {
  id: string;
  type: string;
  title: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

interface Announcement {
  id: string;
  title: string;
  content: string;
  category: string;
  is_popup: boolean;
  created_at: string;
}

interface Activity {
  id: string;
  name: string;
  description: string;
  type: string;
  start_time: string;
  end_time: string;
  current_participants: number;
  rewards: Record<string, any>;
}

interface Badge {
  id: string;
  code: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  earned_at?: string;
  is_displayed?: boolean;
}

interface UserLevel {
  level: number;
  level_name: string;
  level_icon: string;
  exp: number;
  total_exp: number;
  next_level_exp: number | null;
  daily_checkin_streak: number;
  tasks_completed: number;
}

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  score: number;
}

type TabType = 'notifications' | 'announcements' | 'activities' | 'badges' | 'level' | 'leaderboard' | 'feedback';

const EnhancedFeaturesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('notifications');
  const [loading, setLoading] = useState(false);
  
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [userLevel, setUserLevel] = useState<UserLevel | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [leaderboardType, setLeaderboardType] = useState('integral');
  const [leaderboardPeriod, setLeaderboardPeriod] = useState('weekly');
  
  const [showRedeemModal, setShowRedeemModal] = useState(false);
  const [redeemCode, setRedeemCode] = useState('');
  const [redeemResult, setRedeemResult] = useState<any>(null);
  
  const [feedbackSubject, setFeedbackSubject] = useState('');
  const [feedbackContent, setFeedbackContent] = useState('');
  const [feedbackType, setFeedbackType] = useState('feedback');
  const [feedbackRating, setFeedbackRating] = useState(5);

  const token = localStorage.getItem('token');

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await fetch('/api/enhanced/notifications', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications);
        setUnreadCount(data.unread_count);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  }, [token]);

  const fetchAnnouncements = useCallback(async () => {
    try {
      const response = await fetch('/api/enhanced/announcements');
      if (response.ok) {
        const data = await response.json();
        setAnnouncements(data.announcements);
      }
    } catch (error) {
      console.error('Failed to fetch announcements:', error);
    }
  }, []);

  const fetchActivities = useCallback(async () => {
    try {
      const response = await fetch('/api/enhanced/activities');
      if (response.ok) {
        const data = await response.json();
        setActivities(data.activities);
      }
    } catch (error) {
      console.error('Failed to fetch activities:', error);
    }
  }, []);

  const fetchBadges = useCallback(async () => {
    try {
      const response = await fetch('/api/enhanced/user/badges', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setBadges(data.badges);
      }
    } catch (error) {
      console.error('Failed to fetch badges:', error);
    }
  }, [token]);

  const fetchUserLevel = useCallback(async () => {
    try {
      const response = await fetch('/api/enhanced/user/level', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setUserLevel(data);
      }
    } catch (error) {
      console.error('Failed to fetch user level:', error);
    }
  }, [token]);

  const fetchLeaderboard = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/enhanced/leaderboard?type=${leaderboardType}&period=${leaderboardPeriod}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.ok) {
        const data = await response.json();
        setLeaderboard(data.leaderboard);
      }
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    }
  }, [token, leaderboardType, leaderboardPeriod]);

  useEffect(() => {
    switch (activeTab) {
      case 'notifications':
        fetchNotifications();
        break;
      case 'announcements':
        fetchAnnouncements();
        break;
      case 'activities':
        fetchActivities();
        break;
      case 'badges':
        fetchBadges();
        break;
      case 'level':
        fetchUserLevel();
        break;
      case 'leaderboard':
        fetchLeaderboard();
        break;
    }
  }, [activeTab, fetchNotifications, fetchAnnouncements, fetchActivities, fetchBadges, fetchUserLevel, fetchLeaderboard]);

  const markAsRead = async (notificationId: string) => {
    try {
      await fetch(`/api/enhanced/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await fetch('/api/enhanced/notifications/read-all', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const joinActivity = async (activityId: string) => {
    try {
      const response = await fetch(`/api/enhanced/activities/${activityId}/join`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        alert('参与成功！');
        fetchActivities();
      } else {
        const error = await response.json();
        alert(error.detail || '参与失败');
      }
    } catch (error) {
      console.error('Failed to join activity:', error);
    }
  };

  const handleRedeem = async () => {
    if (!redeemCode.trim()) return;
    
    try {
      const response = await fetch('/api/enhanced/redeem', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ code: redeemCode }),
      });
      
      const data = await response.json();
      if (response.ok) {
        setRedeemResult(data);
      } else {
        setRedeemResult({ error: data.detail || '兑换失败' });
      }
    } catch (error) {
      console.error('Failed to redeem:', error);
    }
  };

  const submitFeedback = async () => {
    if (!feedbackSubject.trim() || !feedbackContent.trim()) return;
    
    try {
      const response = await fetch('/api/enhanced/feedbacks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          type: feedbackType,
          subject: feedbackSubject,
          content: feedbackContent,
          rating: feedbackRating,
        }),
      });
      
      if (response.ok) {
        alert('反馈提交成功！');
        setFeedbackSubject('');
        setFeedbackContent('');
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const renderNotifications = () => (
    <div className="notifications-panel">
      <div className="panel-header">
        <h3>消息通知</h3>
        {unreadCount > 0 && (
          <button className="mark-all-btn" onClick={markAllAsRead}>
            全部标为已读 ({unreadCount})
          </button>
        )}
      </div>
      <div className="notification-list">
        {notifications.length === 0 ? (
          <div className="empty-state">暂无通知</div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className={`notification-item ${n.is_read ? 'read' : 'unread'}`}
              onClick={() => !n.is_read && markAsRead(n.id)}
            >
              <div className="notification-header">
                <span className="notification-type">{n.type}</span>
                <span className="notification-time">{formatDate(n.created_at)}</span>
              </div>
              <div className="notification-title">{n.title}</div>
              <div className="notification-content">{n.content}</div>
              {!n.is_read && <span className="unread-dot"></span>}
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderAnnouncements = () => (
    <div className="announcements-panel">
      <h3>平台公告</h3>
      <div className="announcement-list">
        {announcements.map((a) => (
          <div key={a.id} className="announcement-card">
            <div className="announcement-header">
              <span className={`category-tag ${a.category}`}>{a.category}</span>
              <span className="announcement-time">{formatDate(a.created_at)}</span>
            </div>
            <h4>{a.title}</h4>
            <p>{a.content}</p>
          </div>
        ))}
      </div>
    </div>
  );

  const renderActivities = () => (
    <div className="activities-panel">
      <div className="panel-header">
        <h3>限时活动</h3>
        <button className="redeem-btn" onClick={() => setShowRedeemModal(true)}>
          兑换码
        </button>
      </div>
      <div className="activity-list">
        {activities.map((a) => (
          <div key={a.id} className="activity-card">
            <div className="activity-header">
              <span className="activity-type">{a.type}</span>
              <span className="activity-participants">
                {a.current_participants} 人参与
              </span>
            </div>
            <h4>{a.name}</h4>
            <p>{a.description}</p>
            <div className="activity-footer">
              <span className="activity-time">
                {formatDate(a.start_time)} - {formatDate(a.end_time)}
              </span>
              <button
                className="join-btn"
                onClick={() => joinActivity(a.id)}
              >
                立即参与
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderBadges = () => (
    <div className="badges-panel">
      <h3>我的勋章</h3>
      <div className="badge-grid">
        {badges.map((b) => (
          <div key={b.id} className="badge-card">
            <div className="badge-icon">{b.icon}</div>
            <div className="badge-name">{b.name}</div>
            <div className="badge-desc">{b.description}</div>
            {b.earned_at && (
              <div className="badge-earned">获得于 {formatDate(b.earned_at)}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderLevel = () => (
    <div className="level-panel">
      {userLevel && (
        <>
          <div className="level-header">
            <div className="level-icon">{userLevel.level_icon}</div>
            <div className="level-info">
              <div className="level-name">Lv.{userLevel.level} {userLevel.level_name}</div>
              <div className="exp-bar">
                <div
                  className="exp-fill"
                  style={{
                    width: userLevel.next_level_exp
                      ? `${(userLevel.exp / userLevel.next_level_exp) * 100}%`
                      : '100%',
                  }}
                ></div>
              </div>
              <div className="exp-text">
                {userLevel.exp} / {userLevel.next_level_exp || '∞'} EXP
              </div>
            </div>
          </div>
          
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{userLevel.total_exp}</span>
              <span className="stat-label">总经验值</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{userLevel.daily_checkin_streak}</span>
              <span className="stat-label">连续签到</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{userLevel.tasks_completed}</span>
              <span className="stat-label">完成任务</span>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderLeaderboard = () => (
    <div className="leaderboard-panel">
      <div className="panel-header">
        <h3>排行榜</h3>
        <div className="leaderboard-filters">
          <select
            value={leaderboardType}
            onChange={(e) => setLeaderboardType(e.target.value)}
          >
            <option value="integral">积分榜</option>
            <option value="tasks">任务榜</option>
            <option value="invitations">邀请榜</option>
          </select>
          <select
            value={leaderboardPeriod}
            onChange={(e) => setLeaderboardPeriod(e.target.value)}
          >
            <option value="daily">今日</option>
            <option value="weekly">本周</option>
            <option value="monthly">本月</option>
            <option value="all">总榜</option>
          </select>
        </div>
      </div>
      <div className="leaderboard-list">
        {leaderboard.map((entry) => (
          <div key={entry.user_id} className="leaderboard-item">
            <span className={`rank ${entry.rank <= 3 ? `top-${entry.rank}` : ''}`}>
              {entry.rank}
            </span>
            <span className="username">{entry.username}</span>
            <span className="score">{entry.score}</span>
          </div>
        ))}
      </div>
    </div>
  );

  const renderFeedback = () => (
    <div className="feedback-panel">
      <h3>意见反馈</h3>
      <div className="feedback-form">
        <div className="form-group">
          <label>类型</label>
          <select
            value={feedbackType}
            onChange={(e) => setFeedbackType(e.target.value)}
          >
            <option value="feedback">功能建议</option>
            <option value="suggestion">改进建议</option>
            <option value="complaint">问题投诉</option>
          </select>
        </div>
        <div className="form-group">
          <label>主题</label>
          <input
            type="text"
            value={feedbackSubject}
            onChange={(e) => setFeedbackSubject(e.target.value)}
            placeholder="请输入主题"
          />
        </div>
        <div className="form-group">
          <label>内容</label>
          <textarea
            value={feedbackContent}
            onChange={(e) => setFeedbackContent(e.target.value)}
            placeholder="请详细描述您的建议或问题..."
            rows={5}
          />
        </div>
        <div className="form-group">
          <label>评分</label>
          <div className="rating-stars">
            {[1, 2, 3, 4, 5].map((star) => (
              <span
                key={star}
                className={`star ${star <= feedbackRating ? 'active' : ''}`}
                onClick={() => setFeedbackRating(star)}
              >
                ★
              </span>
            ))}
          </div>
        </div>
        <button className="submit-btn" onClick={submitFeedback}>
          提交反馈
        </button>
      </div>
    </div>
  );

  return (
    <div className="enhanced-features-page">
      <header className="page-header">
        <h1>🎯 增强功能中心</h1>
      </header>

      <div className="page-body">
        <nav className="side-nav">
          <button
            className={`nav-item ${activeTab === 'notifications' ? 'active' : ''}`}
            onClick={() => setActiveTab('notifications')}
          >
            🔔 通知
            {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
          </button>
          <button
            className={`nav-item ${activeTab === 'announcements' ? 'active' : ''}`}
            onClick={() => setActiveTab('announcements')}
          >
            📢 公告
          </button>
          <button
            className={`nav-item ${activeTab === 'activities' ? 'active' : ''}`}
            onClick={() => setActiveTab('activities')}
          >
            🎉 活动
          </button>
          <button
            className={`nav-item ${activeTab === 'level' ? 'active' : ''}`}
            onClick={() => setActiveTab('level')}
          >
            ⭐ 等级
          </button>
          <button
            className={`nav-item ${activeTab === 'badges' ? 'active' : ''}`}
            onClick={() => setActiveTab('badges')}
          >
            🏅 勋章
          </button>
          <button
            className={`nav-item ${activeTab === 'leaderboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('leaderboard')}
          >
            📊 排行榜
          </button>
          <button
            className={`nav-item ${activeTab === 'feedback' ? 'active' : ''}`}
            onClick={() => setActiveTab('feedback')}
          >
            💬 反馈
          </button>
        </nav>

        <main className="main-content">
          {loading && <div className="loading">加载中...</div>}
          
          {activeTab === 'notifications' && renderNotifications()}
          {activeTab === 'announcements' && renderAnnouncements()}
          {activeTab === 'activities' && renderActivities()}
          {activeTab === 'badges' && renderBadges()}
          {activeTab === 'level' && renderLevel()}
          {activeTab === 'leaderboard' && renderLeaderboard()}
          {activeTab === 'feedback' && renderFeedback()}
        </main>
      </div>

      {showRedeemModal && (
        <div className="modal-overlay" onClick={() => setShowRedeemModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>兑换码</h3>
            <input
              type="text"
              value={redeemCode}
              onChange={(e) => setRedeemCode(e.target.value)}
              placeholder="请输入兑换码"
            />
            <button className="redeem-submit-btn" onClick={handleRedeem}>
              兑换
            </button>
            {redeemResult && (
              <div className={`redeem-result ${redeemResult.error ? 'error' : 'success'}`}>
                {redeemResult.error || redeemResult.message}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedFeaturesPage;
