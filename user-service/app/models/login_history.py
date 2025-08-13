from sqlalchemy import Column, String, Boolean, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base
import uuid


class LoginHistory(Base):
    __tablename__ = "login_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    login_time = Column(DateTime, server_default=func.now())
    logout_time = Column(DateTime, nullable=True)
    
    # 登录信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    
    # 登录状态
    is_successful = Column(Boolean, default=True)
    failure_reason = Column(Text, nullable=True)
    
    # 会话信息
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=True)
    
    # 关系
    user = relationship("User", back_populates="login_history")
    session = relationship("UserSession")
    
    def __repr__(self):
        return f"<LoginHistory(id={self.id}, user_id={self.user_id}, is_successful={self.is_successful})>" 