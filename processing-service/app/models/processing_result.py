import uuid
from datetime import datetime
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base

class ProcessingResult(Base):
    """数据处理结果模型"""
    __tablename__ = "processing_results"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("processing_tasks.id"), nullable=False)
    data = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    storage_location = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联处理任务
    task = relationship("ProcessingTask", back_populates="result") 