"""
吉祥物智能体 DuduAgent
房都督平台吉祥物"嘟嘟"的核心智能体

拥有独立的情绪状态机、行为决策器和学习成长模块
通过动作、表情和简单气泡文字与用户互动
"""

import json
import time
import uuid
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import math


class EmotionType(Enum):
    """情绪类型"""
    HAPPY = "happy"
    THINKING = "thinking"
    SURPRISED = "surprised"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CUTE = "cute"
    IDLE = "idle"


class ActionType(Enum):
    """动作类型"""
    WAVE = "wave"
    SPIN = "spin"
    GONG = "gong"
    POINT = "point"
    HEAD_HOLD = "head_hold"
    CONFETTI = "confetti"
    YAWN = "yawn"
    IDLE = "idle"
    HEART = "heart"
    CLAP = "clap"
    ALERT = "alert"


class EventType(Enum):
    """事件类型"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    TASK_COMPLETE = "task_complete"
    TASK_FAIL = "task_fail"
    INTEGRAL_GAINED = "integral_gained"
    INTEGRAL_SPENT = "integral_spent"
    RISK_ALERT = "risk_alert"
    NEW_FEATURE = "new_feature"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    LEVEL_UP = "level_up"
    SIGN_IN = "sign_in"
    INVITE_SUCCESS = "invite_success"
    REPORT_GENERATED = "report_generated"
    LONG_IDLE = "long_idle"
    USER_CLICK = "user_click"
    USER_FEED = "user_feed"


@dataclass
class EmotionState:
    """情绪状态"""
    pleasure: float = 50.0
    activity: float = 50.0
    intimacy: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "pleasure": self.pleasure,
            "activity": self.activity,
            "intimacy": self.intimacy
        }
    
    def clamp(self):
        """限制范围在0-100"""
        self.pleasure = max(0, min(100, self.pleasure))
        self.activity = max(0, min(100, self.activity))
        self.intimacy = max(0, min(100, self.intimacy))
    
    def decay(self, rate: float = 0.1):
        """情绪衰减"""
        self.pleasure = max(50, self.pleasure - rate)
        self.activity = max(30, self.activity - rate * 0.5)
        self.clamp()


@dataclass
class DuduLevel:
    """嘟嘟等级信息"""
    level: int = 1
    exp: int = 0
    total_interactions: int = 0
    
    def exp_for_next_level(self) -> int:
        """下一级所需经验"""
        return self.level * 100
    
    def add_exp(self, amount: int) -> bool:
        """添加经验，返回是否升级"""
        self.exp += amount
        self.total_interactions += 1
        
        if self.exp >= self.exp_for_next_level():
            self.level += 1
            self.exp = 0
            return True
        return False
    
    def to_dict(self) -> Dict:
        return {
            "level": self.level,
            "exp": self.exp,
            "exp_required": self.exp_for_next_level(),
            "total_interactions": self.total_interactions
        }


@dataclass
class DuduCostume:
    """嘟嘟装扮"""
    costume_id: str
    name: str
    category: str
    rarity: str
    unlock_level: int = 1
    price: int = 0
    equipped: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "costume_id": self.costume_id,
            "name": self.name,
            "category": self.category,
            "rarity": self.rarity,
            "unlock_level": self.unlock_level,
            "price": self.price,
            "equipped": self.equipped
        }


class EmotionEngine:
    """情绪引擎"""
    
    EMOTION_MAPPING = {
        (70, 70, 50): EmotionType.HAPPY,
        (70, 30, 70): EmotionType.CUTE,
        (30, 70, 30): EmotionType.ANGRY,
        (30, 30, 30): EmotionType.SAD,
        (50, 50, 50): EmotionType.IDLE,
        (80, 80, 60): EmotionType.EXCITED,
        (40, 30, 60): EmotionType.THINKING,
        (60, 90, 40): EmotionType.SURPRISED,
    }
    
    @classmethod
    def calculate_emotion(cls, state: EmotionState) -> EmotionType:
        """根据情绪状态计算最终表情"""
        best_match = EmotionType.IDLE
        best_score = float('inf')
        
        for (p, a, i), emotion in cls.EMOTION_MAPPING.items():
            score = (
                abs(state.pleasure - p) +
                abs(state.activity - a) +
                abs(state.intimacy - i)
            )
            if score < best_score:
                best_score = score
                best_match = emotion
        
        return best_match
    
    @classmethod
    def get_action_for_event(cls, event_type: EventType, emotion: EmotionType) -> ActionType:
        """根据事件类型和情绪获取动作"""
        event_action_map = {
            EventType.USER_LOGIN: ActionType.WAVE,
            EventType.TASK_COMPLETE: ActionType.CONFETTI,
            EventType.TASK_FAIL: ActionType.HEAD_HOLD,
            EventType.INTEGRAL_GAINED: ActionType.CLAP,
            EventType.RISK_ALERT: ActionType.ALERT,
            EventType.NEW_FEATURE: ActionType.POINT,
            EventType.ACHIEVEMENT_UNLOCK: ActionType.SPIN,
            EventType.LEVEL_UP: ActionType.CONFETTI,
            EventType.SIGN_IN: ActionType.HEART,
            EventType.LONG_IDLE: ActionType.YAWN,
            EventType.USER_CLICK: ActionType.HEART,
            EventType.USER_FEED: ActionType.SPIN,
        }
        
        return event_action_map.get(event_type, ActionType.IDLE)


class DuduQuoteEngine:
    """嘟嘟语录引擎"""
    
    QUOTES = {
        "welcome": [
            "欢迎回来！今天也要加油哦~",
            "嘟嘟等你好久啦！",
            "主人来啦！今天想看什么？",
            "又见面啦，开心！",
        ],
        "task_complete": [
            "太棒啦！任务完成！",
            "厉害厉害！嘟嘟为你骄傲！",
            "完美！又完成一个任务~",
            "干得漂亮！",
        ],
        "task_fail": [
            "没关系，下次一定行！",
            "嘟嘟相信你可以的！",
            "别灰心，再试一次吧~",
            "失败是成功之母嘛！",
        ],
        "integral_gained": [
            "积分+1！继续加油！",
            "哇，积分增加了！",
            "攒积分换装扮咯~",
            "积分多多，快乐多多！",
        ],
        "risk_alert": [
            "注意！有风险预警！",
            "嘟嘟发现异常了！",
            "小心小心！",
            "这个需要注意一下哦~",
        ],
        "idle": [
            "嘟嘟在等你哦~",
            "有什么可以帮你的吗？",
            "今天天气真好~",
            "想看看新装扮吗？",
            "嘟嘟想你了~",
        ],
        "click": [
            "嘿嘿，被发现了！",
            "戳我干嘛~",
            "嘟嘟在这里！",
            "想我了吗？",
            "点击有惊喜哦~",
        ],
        "feed": [
            "好吃好吃！谢谢主人！",
            "嘟嘟吃饱啦~",
            "最喜欢主人了！",
            "再来再来！",
        ],
        "level_up": [
            "升级啦！嘟嘟变强了！",
            "等级提升！新技能解锁！",
            "成长快乐！",
        ],
        "sign_in": [
            "签到成功！积分到手！",
            "今天也签到啦~",
            "连续签到奖励更多哦！",
        ],
        "new_feature": [
            "新功能上线啦！快去看看！",
            "有新东西哦，嘟嘟带你去看！",
        ],
        "goodbye": [
            "下次见！嘟嘟会想你的！",
            "拜拜~记得回来哦！",
            "期待下次见面！",
        ],
    }
    
    @classmethod
    def get_quote(cls, category: str, context: Optional[Dict] = None) -> str:
        """获取语录"""
        quotes = cls.QUOTES.get(category, cls.QUOTES["idle"])
        return random.choice(quotes)
    
    @classmethod
    def get_random_idle_quote(cls) -> str:
        """获取随机空闲语录"""
        return cls.get_quote("idle")


class DuduAgent:
    """吉祥物嘟嘟智能体"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.agent_id = f"dudu_{user_id}"
        
        self.emotion_state = EmotionState()
        self.level_info = DuduLevel()
        
        self.current_emotion = EmotionType.IDLE
        self.current_action = ActionType.IDLE
        self.current_message = ""
        
        self.costumes: Dict[str, DuduCostume] = {}
        self.equipped_costumes: Dict[str, str] = {}
        
        self._event_listeners: Dict[EventType, Callable] = {}
        self._last_interaction = time.time()
        self._idle_check_task: Optional[asyncio.Task] = None
        self._decay_task: Optional[asyncio.Task] = None
        
        self._init_default_costumes()
        self._register_event_handlers()
    
    def _init_default_costumes(self):
        """初始化默认装扮"""
        default_costumes = [
            DuduCostume("default", "默认汉服", "outfit", "common", 1, 0, True),
            DuduCostume("zhouyu_hat", "周瑜纶巾", "hat", "rare", 5, 100),
            DuduCostume("luxun_hat", "陆逊武弁", "hat", "rare", 5, 100),
            DuduCostume("spring", "春日和服", "outfit", "epic", 10, 300),
            DuduCostume("summer", "夏日清凉装", "outfit", "rare", 8, 150),
            DuduCostume("autumn", "秋日枫叶装", "outfit", "rare", 8, 150),
            DuduCostume("winter", "冬日暖绒装", "outfit", "epic", 10, 300),
            DuduCostume("glasses", "小眼镜", "accessory", "common", 3, 50),
            DuduCostume("bowtie", "小领结", "accessory", "common", 3, 50),
            DuduCostume("crown", "小皇冠", "hat", "legendary", 20, 500),
        ]
        
        for costume in default_costumes:
            self.costumes[costume.costume_id] = costume
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        self._event_listeners = {
            EventType.USER_LOGIN: self._on_user_login,
            EventType.USER_LOGOUT: self._on_user_logout,
            EventType.TASK_COMPLETE: self._on_task_complete,
            EventType.TASK_FAIL: self._on_task_fail,
            EventType.INTEGRAL_GAINED: self._on_integral_gained,
            EventType.INTEGRAL_SPENT: self._on_integral_spent,
            EventType.RISK_ALERT: self._on_risk_alert,
            EventType.NEW_FEATURE: self._on_new_feature,
            EventType.ACHIEVEMENT_UNLOCK: self._on_achievement_unlock,
            EventType.LEVEL_UP: self._on_level_up,
            EventType.SIGN_IN: self._on_sign_in,
            EventType.INVITE_SUCCESS: self._on_invite_success,
            EventType.REPORT_GENERATED: self._on_report_generated,
            EventType.LONG_IDLE: self._on_long_idle,
            EventType.USER_CLICK: self._on_user_click,
            EventType.USER_FEED: self._on_user_feed,
        }
    
    async def handle_event(self, event_type: EventType, data: Optional[Dict] = None):
        """处理事件"""
        handler = self._event_listeners.get(event_type)
        if handler:
            await handler(data or {})
        
        self._last_interaction = time.time()
    
    async def _on_user_login(self, data: Dict):
        """用户登录"""
        self.emotion_state.pleasure += 10
        self.emotion_state.intimacy += 1
        
        leveled_up = self.level_info.add_exp(5)
        
        self.current_emotion = EmotionType.HAPPY
        self.current_action = ActionType.WAVE
        self.current_message = DuduQuoteEngine.get_quote("welcome")
        
        if leveled_up:
            await self._on_level_up({"new_level": self.level_info.level})
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_user_logout(self, data: Dict):
        """用户登出"""
        self.current_emotion = EmotionType.SAD
        self.current_action = ActionType.WAVE
        self.current_message = DuduQuoteEngine.get_quote("goodbye")
        
        await self._save_state()
    
    async def _on_task_complete(self, data: Dict):
        """任务完成"""
        self.emotion_state.pleasure += 15
        self.emotion_state.activity += 10
        
        exp_gain = data.get("exp", 10)
        leveled_up = self.level_info.add_exp(exp_gain)
        
        self.current_emotion = EmotionType.HAPPY
        self.current_action = ActionType.CONFETTI
        self.current_message = DuduQuoteEngine.get_quote("task_complete")
        
        if leveled_up:
            await self._on_level_up({"new_level": self.level_info.level})
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_task_fail(self, data: Dict):
        """任务失败"""
        self.emotion_state.pleasure -= 10
        
        self.current_emotion = EmotionType.SAD
        self.current_action = ActionType.HEAD_HOLD
        self.current_message = DuduQuoteEngine.get_quote("task_fail")
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_integral_gained(self, data: Dict):
        """获得积分"""
        amount = data.get("amount", 1)
        self.emotion_state.pleasure += amount // 5
        
        self.current_emotion = EmotionType.HAPPY
        self.current_action = ActionType.CLAP
        self.current_message = DuduQuoteEngine.get_quote("integral_gained")
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_integral_spent(self, data: Dict):
        """消耗积分"""
        self.current_emotion = EmotionType.THINKING
        self.current_action = ActionType.IDLE
        self.current_message = "积分使用成功~"
        
        await self._save_state()
    
    async def _on_risk_alert(self, data: Dict):
        """风险预警"""
        self.emotion_state.pleasure -= 20
        self.emotion_state.activity += 30
        
        self.current_emotion = EmotionType.SURPRISED
        self.current_action = ActionType.ALERT
        self.current_message = DuduQuoteEngine.get_quote("risk_alert")
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_new_feature(self, data: Dict):
        """新功能上线"""
        self.emotion_state.activity += 20
        
        self.current_emotion = EmotionType.EXCITED
        self.current_action = ActionType.POINT
        self.current_message = DuduQuoteEngine.get_quote("new_feature")
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_achievement_unlock(self, data: Dict):
        """成就解锁"""
        self.emotion_state.pleasure += 25
        self.emotion_state.intimacy += 5
        
        self.level_info.add_exp(20)
        
        self.current_emotion = EmotionType.EXCITED
        self.current_action = ActionType.SPIN
        self.current_message = f"恭喜解锁成就：{data.get('name', '神秘成就')}！"
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_level_up(self, data: Dict):
        """嘟嘟升级"""
        new_level = data.get("new_level", self.level_info.level)
        
        self.current_emotion = EmotionType.EXCITED
        self.current_action = ActionType.CONFETTI
        self.current_message = f"嘟嘟升级到{new_level}级啦！{DuduQuoteEngine.get_quote('level_up')}"
        
        await self._save_state()
    
    async def _on_sign_in(self, data: Dict):
        """签到"""
        self.emotion_state.pleasure += 5
        self.level_info.add_exp(3)
        
        self.current_emotion = EmotionType.CUTE
        self.current_action = ActionType.HEART
        self.current_message = DuduQuoteEngine.get_quote("sign_in")
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_invite_success(self, data: Dict):
        """邀请成功"""
        self.emotion_state.pleasure += 20
        self.emotion_state.intimacy += 3
        self.level_info.add_exp(15)
        
        self.current_emotion = EmotionType.HAPPY
        self.current_action = ActionType.CONFETTI
        self.current_message = "邀请成功！谢谢主人！"
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_report_generated(self, data: Dict):
        """报告生成"""
        self.emotion_state.pleasure += 10
        self.level_info.add_exp(8)
        
        self.current_emotion = EmotionType.HAPPY
        self.current_action = ActionType.CONFETTI
        self.current_message = "报告生成完毕！快去看看吧~"
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_long_idle(self, data: Dict):
        """长时间无操作"""
        self.emotion_state.activity -= 10
        
        self.current_emotion = EmotionType.IDLE
        self.current_action = ActionType.YAWN
        self.current_message = "主人去哪了...嘟嘟好无聊~"
        
        self.emotion_state.clamp()
    
    async def _on_user_click(self, data: Dict):
        """用户点击嘟嘟"""
        self.emotion_state.pleasure += 5
        self.emotion_state.intimacy += 2
        self.level_info.add_exp(1)
        
        self.current_emotion = EmotionType.CUTE
        self.current_action = ActionType.HEART
        self.current_message = DuduQuoteEngine.get_quote("click")
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _on_user_feed(self, data: Dict):
        """用户喂食"""
        food_value = data.get("value", 10)
        self.emotion_state.pleasure += food_value
        self.emotion_state.intimacy += food_value // 2
        self.level_info.add_exp(food_value // 2)
        
        self.current_emotion = EmotionType.HAPPY
        self.current_action = ActionType.SPIN
        self.current_message = DuduQuoteEngine.get_quote("feed")
        
        self.emotion_state.clamp()
        await self._save_state()
    
    async def _save_state(self):
        """保存状态到数据库"""
        try:
            from ..database import get_db_connection
            
            async for conn in get_db_connection():
                try:
                    await conn.execute("""
                        INSERT INTO dudu_state (user_id, emotion_state, level_info, current_emotion, current_action, current_message, equipped_costumes, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id) DO UPDATE SET
                            emotion_state = $2,
                            level_info = $3,
                            current_emotion = $4,
                            current_action = $5,
                            current_message = $6,
                            equipped_costumes = $7,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        self.user_id,
                        json.dumps(self.emotion_state.to_dict()),
                        json.dumps(self.level_info.to_dict()),
                        self.current_emotion.value,
                        self.current_action.value,
                        self.current_message,
                        json.dumps(self.equipped_costumes)
                    ))
                    await conn.commit()
                finally:
                    await conn.close()
        except Exception as e:
            print(f"保存嘟嘟状态失败: {e}")
    
    async def load_state(self):
        """从数据库加载状态"""
        try:
            from ..database import get_db_connection
            
            async for conn in get_db_connection():
                try:
                    row = await conn.fetchrow("""
                        SELECT emotion_state, level_info, current_emotion, current_action, current_message, equipped_costumes
                        FROM dudu_state
                        WHERE user_id = $1
                    """, self.user_id)
                    
                    if row:
                        emotion_data = json.loads(row["emotion_state"]) if row["emotion_state"] else {}
                        self.emotion_state = EmotionState(
                            pleasure=emotion_data.get("pleasure", 50),
                            activity=emotion_data.get("activity", 50),
                            intimacy=emotion_data.get("intimacy", 0)
                        )
                        
                        level_data = json.loads(row["level_info"]) if row["level_info"] else {}
                        self.level_info = DuduLevel(
                            level=level_data.get("level", 1),
                            exp=level_data.get("exp", 0),
                            total_interactions=level_data.get("total_interactions", 0)
                        )
                        
                        self.current_emotion = EmotionType(row["current_emotion"]) if row["current_emotion"] else EmotionType.IDLE
                        self.current_action = ActionType(row["current_action"]) if row["current_action"] else ActionType.IDLE
                        self.current_message = row["current_message"] or ""
                        
                        self.equipped_costumes = json.loads(row["equipped_costumes"]) if row["equipped_costumes"] else {}
                    
                    return True
                finally:
                    await conn.close()
        except Exception as e:
            print(f"加载嘟嘟状态失败: {e}")
            return False
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "user_id": self.user_id,
            "emotion_state": self.emotion_state.to_dict(),
            "level_info": self.level_info.to_dict(),
            "current_emotion": self.current_emotion.value,
            "current_action": self.current_action.value,
            "current_message": self.current_message,
            "equipped_costumes": self.equipped_costumes,
            "available_costumes": [c.to_dict() for c in self.costumes.values() if c.unlock_level <= self.level_info.level]
        }
    
    def equip_costume(self, costume_id: str) -> bool:
        """装备装扮"""
        if costume_id not in self.costumes:
            return False
        
        costume = self.costumes[costume_id]
        if costume.unlock_level > self.level_info.level:
            return False
        
        for c in self.costumes.values():
            if c.category == costume.category:
                c.equipped = False
        
        costume.equipped = True
        self.equipped_costumes[costume.category] = costume_id
        
        return True
    
    def buy_costume(self, costume_id: str, user_integral: int) -> Tuple[bool, int]:
        """购买装扮"""
        if costume_id not in self.costumes:
            return False, 0
        
        costume = self.costumes[costume_id]
        
        if costume.unlock_level > self.level_info.level:
            return False, 0
        
        if costume.price > user_integral:
            return False, 0
        
        return True, costume.price
    
    def get_random_action(self) -> Tuple[EmotionType, ActionType, str]:
        """获取随机动作（用于空闲时）"""
        emotions = [EmotionType.HAPPY, EmotionType.THINKING, EmotionType.CUTE, EmotionType.IDLE]
        actions = [ActionType.IDLE, ActionType.HEART, ActionType.POINT]
        
        emotion = random.choice(emotions)
        action = random.choice(actions)
        message = DuduQuoteEngine.get_random_idle_quote()
        
        return emotion, action, message
    
    async def start_background_tasks(self):
        """启动后台任务"""
        self._idle_check_task = asyncio.create_task(self._idle_check_loop())
        self._decay_task = asyncio.create_task(self._emotion_decay_loop())
    
    async def stop_background_tasks(self):
        """停止后台任务"""
        if self._idle_check_task:
            self._idle_check_task.cancel()
        if self._decay_task:
            self._decay_task.cancel()
    
    async def _idle_check_loop(self):
        """空闲检查循环"""
        while True:
            try:
                await asyncio.sleep(60)
                
                idle_time = time.time() - self._last_interaction
                if idle_time > 300:
                    await self.handle_event(EventType.LONG_IDLE)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"空闲检查错误: {e}")
    
    async def _emotion_decay_loop(self):
        """情绪衰减循环"""
        while True:
            try:
                await asyncio.sleep(300)
                self.emotion_state.decay(0.5)
                await self._save_state()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"情绪衰减错误: {e}")


class DuduManager:
    """嘟嘟管理器"""
    
    _instances: Dict[str, DuduAgent] = {}
    
    @classmethod
    async def get_dudu(cls, user_id: str) -> DuduAgent:
        """获取用户的嘟嘟实例"""
        if user_id not in cls._instances:
            dudu = DuduAgent(user_id)
            await dudu.load_state()
            await dudu.start_background_tasks()
            cls._instances[user_id] = dudu
        
        return cls._instances[user_id]
    
    @classmethod
    async def remove_dudu(cls, user_id: str):
        """移除嘟嘟实例"""
        if user_id in cls._instances:
            await cls._instances[user_id].stop_background_tasks()
            del cls._instances[user_id]
    
    @classmethod
    async def broadcast_event(cls, user_id: str, event_type: EventType, data: Optional[Dict] = None):
        """广播事件"""
        dudu = await cls.get_dudu(user_id)
        await dudu.handle_event(event_type, data)
        return dudu.get_state()


dudu_manager = DuduManager()
