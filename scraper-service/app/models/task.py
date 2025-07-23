from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, func
from ..db.database import Base
import uuid


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String)  # USER_INFO, USER_TWEETS, SEARCH, TOPIC, FOLLOWERS
    parameters = Column(JSON, nullable=False)
    account_id = Column(String)
    proxy_id = Column(String, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED, STOPPED
    progress = Column(Float, default=0.0)
    result_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
