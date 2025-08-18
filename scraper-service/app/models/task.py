from sqlalchemy import Column, String, DateTime, JSON, func, Text
from ..db.database import Base
import uuid


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name = Column(String, nullable=False)  # 任务名称
    describe = Column(Text, nullable=True)  # 任务描述
    task_type = Column(String, nullable=False)  # USER_INFO, USER_TWEETS, SEARCH, TOPIC, FOLLOWERS, FOLLOWING
    parameters = Column(JSON, nullable=False)  # 任务参数
    account_id = Column(String, nullable=True)  # 关联的账户ID
    proxy_id = Column(String, nullable=True)  # 关联的代理ID
    status = Column(String, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED, STOPPED
    error_message = Column(Text, nullable=True)  # 错误信息
    user_id = Column(String, nullable=False)  # 创建任务的用户ID
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
