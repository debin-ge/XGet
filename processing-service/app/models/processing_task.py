import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base

class ProcessingTask(Base):
    """数据处理任务模型"""
    __tablename__ = "processing_tasks"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String(50), nullable=False)
    source_data_id = Column(String(36), nullable=False, index=True)
    parameters = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")
    priority = Column(String(50), default="normal")
    progress = Column(Float, default=0.0)
    error_message = Column(String(500), nullable=True)
    result_id = Column(String(36), nullable=True)
    callback_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关联处理结果
    result = relationship("ProcessingResult", back_populates="task", uselist=False) 