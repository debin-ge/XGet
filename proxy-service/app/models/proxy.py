from sqlalchemy import Column, String, Integer, Float, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base
import uuid


class Proxy(Base):
    __tablename__ = "proxies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String)  # SOCKS5, HTTP, HTTPS
    ip = Column(String)
    port = Column(Integer)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    isp = Column(String, nullable=True)
    latency = Column(Integer, nullable=True)  # 毫秒
    success_rate = Column(Float, default=0.0)
    last_check = Column(DateTime, nullable=True)
    status = Column(String, default="INACTIVE")  # ACTIVE, INACTIVE, CHECKING
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联质量监控记录
    quality = relationship("ProxyQuality", back_populates="proxy", uselist=False)
    # 关联使用历史记录
    usage_history = relationship("ProxyUsageHistory", back_populates="proxy", cascade="all, delete-orphan")


class ProxyQuality(Base):
    __tablename__ = "proxy_qualities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    proxy_id = Column(String, ForeignKey("proxies.id", ondelete="CASCADE"), unique=True)
    total_usage = Column(Integer, default=0)  # 总使用次数
    success_count = Column(Integer, default=0)  # 成功次数
    quality_score = Column(Float, default=0.8)  # 质量得分
    last_used = Column(DateTime, nullable=True)  # 上次使用时间
    cooldown_time = Column(Integer, default=0)  # 冷却时间（秒）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联到代理
    proxy = relationship("Proxy", back_populates="quality")


class ProxyUsageHistory(Base):
    __tablename__ = "proxy_usage_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    proxy_id = Column(String, ForeignKey("proxies.id", ondelete="CASCADE"))
    account_id = Column(String, nullable=True)  # 使用账户ID
    task_id = Column(String, nullable=True)  # 任务ID
    service_name = Column(String, nullable=True)  # 使用服务名称
    success = Column(String, default="SUCCESS")  # SUCCESS, FAILED, TIMEOUT
    response_time = Column(Integer, nullable=True)  # 响应时间（毫秒）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联到代理
    proxy = relationship("Proxy", back_populates="usage_history")
