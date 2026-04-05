import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Calendar } from '@/components/ui/calendar';
import { Gift, Flame, CalendarDays, CheckCircle2 } from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';

interface SigninStatus {
  today_signed: boolean;
  current_streak: number;
  max_streak: number;
  total_days: number;
  today_reward: number;
  next_reward: number;
  signed_dates: string[];
  makeup_cards: number;
}

interface SigninModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSigninSuccess?: () => void;
}

export default function SigninModal({ open, onOpenChange, onSigninSuccess }: SigninModalProps) {
  const [status, setStatus] = useState<SigninStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [signing, setSigning] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<Date>(new Date());
  const [calendarDates, setCalendarDates] = useState<string[]>([]);

  useEffect(() => {
    if (open) {
      fetchStatus();
      fetchCalendar();
    }
  }, [open]);

  useEffect(() => {
    if (open) {
      fetchCalendar();
    }
  }, [selectedMonth]);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await api.get('/signin/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch signin status:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCalendar = async () => {
    try {
      const month = `${selectedMonth.getFullYear()}-${String(selectedMonth.getMonth() + 1).padStart(2, '0')}`;
      const response = await api.get(`/signin/calendar?month=${month}`);
      setCalendarDates(response.data.signed_dates);
    } catch (error) {
      console.error('Failed to fetch calendar:', error);
    }
  };

  const handleSignin = async () => {
    if (status?.today_signed) return;

    setSigning(true);
    try {
      const response = await api.post('/signin');
      toast.success(response.data.message, {
        description: `获得 ${response.data.reward_integral} 积分 (${response.data.reward_tokens} Token)`,
      });
      fetchStatus();
      fetchCalendar();
      onSigninSuccess?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '签到失败');
    } finally {
      setSigning(false);
    }
  };

  const getStreakMessage = () => {
    if (!status) return '';
    if (status.current_streak >= 30) return '🎉 太棒了！连续签到30天！';
    if (status.current_streak >= 14) return '🔥 坚持签到14天，继续加油！';
    if (status.current_streak >= 7) return '👏 连续签到一周，太厉害了！';
    if (status.current_streak >= 3) return '💪 连续签到3天，继续保持！';
    return '🌟 每天签到领取积分奖励！';
  };

  const signedDateObjects = calendarDates.map(d => new Date(d));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Gift className="h-5 w-5 text-yellow-500" />
            每日签到
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-2">
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-2xl font-bold text-primary">
                    {status?.current_streak || 0}
                  </div>
                  <div className="text-xs text-muted-foreground">连续签到</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-2xl font-bold text-yellow-500">
                    {status?.total_days || 0}
                  </div>
                  <div className="text-xs text-muted-foreground">累计签到</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-3 text-center">
                  <div className="text-2xl font-bold text-orange-500">
                    {status?.today_reward?.toFixed(1) || '1.0'}
                  </div>
                  <div className="text-xs text-muted-foreground">今日奖励</div>
                </CardContent>
              </Card>
            </div>

            <div className="text-center text-sm text-muted-foreground">
              {getStreakMessage()}
            </div>

            <div className="border rounded-lg p-2">
              <div className="flex items-center justify-between mb-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const prevMonth = new Date(selectedMonth);
                    prevMonth.setMonth(prevMonth.getMonth() - 1);
                    setSelectedMonth(prevMonth);
                  }}
                >
                  ◀
                </Button>
                <span className="font-medium">
                  {selectedMonth.getFullYear()}年{selectedMonth.getMonth() + 1}月
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const nextMonth = new Date(selectedMonth);
                    nextMonth.setMonth(nextMonth.getMonth() + 1);
                    setSelectedMonth(nextMonth);
                  }}
                >
                  ▶
                </Button>
              </div>
              <Calendar
                mode="multiple"
                selected={signedDateObjects}
                className="rounded-md border"
                disabled={(date) => date > new Date()}
                modifiers={{
                  signed: signedDateObjects,
                }}
                modifiersStyles={{
                  signed: {
                    backgroundColor: 'hsl(var(--primary))',
                    color: 'hsl(var(--primary-foreground))',
                    borderRadius: '50%',
                  },
                }}
              />
            </div>

            <Button
              className="w-full"
              size="lg"
              onClick={handleSignin}
              disabled={status?.today_signed || signing}
            >
              {status?.today_signed ? (
                <>
                  <CheckCircle2 className="mr-2 h-5 w-5" />
                  今日已签到
                </>
              ) : (
                <>
                  <Flame className="mr-2 h-5 w-5" />
                  {signing ? '签到中...' : '立即签到'}
                </>
              )}
            </Button>

            <div className="text-center text-xs text-muted-foreground">
              1积分 = 100 Token | 连续签到可获得额外奖励
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
