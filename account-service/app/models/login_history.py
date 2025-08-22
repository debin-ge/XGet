from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func
from ..db.database import Base
import uuid


class LoginHistory(Base):
    __tablename__ = "login_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String, ForeignKey("accounts.id"))
    proxy_id = Column(String, nullable=True)
    login_time = Column(DateTime, server_default=func.now())
    status = Column(String)  # SUCCESS, FAILED
    error_msg = Column(String, nullable=True)
    response_time = Column(Integer, nullable=True)  # 响应时间（毫秒） 