from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from ..db.database import Base
import uuid


class TaskExecution(Base):
    __tablename__ = "task_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"))
    account_id = Column(String, nullable=True)
    proxy_id = Column(String, nullable=True)
    status = Column(String)  # RUNNING, COMPLETED, FAILED
    started_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # 执行时长（秒）
    error_message = Column(String, nullable=True)