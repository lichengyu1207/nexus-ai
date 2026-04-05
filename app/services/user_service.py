from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

from app.models.user import User, UserStatus
from app.core.database import get_db

# 加载环境变量
load_dotenv()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


class UserService:
    """用户服务类"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """获取密码哈希值"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str, full_name: Optional[str] = None, phone_number: Optional[str] = None) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        if UserService.get_user_by_username(db, username):
            raise ValueError("Username already registered")
        
        # 检查邮箱是否已存在
        if UserService.get_user_by_email(db, email):
            raise ValueError("Email already registered")
        
        # 创建用户
        hashed_password = UserService.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
            phone_number=phone_number
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """认证用户"""
        user = UserService.get_user_by_username(db, username)
        if not user:
            return None
        if not UserService.verify_password(password, user.password_hash):
            return None
        if user.status != UserStatus.ACTIVE:
            return None
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def update_user_status(db: Session, user_id: int, status: UserStatus) -> Optional[User]:
        """更新用户状态"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        user.status = status
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def update_user_profile(db: Session, user_id: int, full_name: Optional[str] = None, phone_number: Optional[str] = None) -> Optional[User]:
        """更新用户资料"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        if full_name is not None:
            user.full_name = full_name
        if phone_number is not None:
            user.phone_number = phone_number
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # 验证旧密码
        if not UserService.verify_password(old_password, user.password_hash):
            return False
        
        # 更新密码
        user.password_hash = UserService.get_password_hash(new_password)
        db.commit()
        
        return True


# 创建用户服务实例
user_service = UserService()
