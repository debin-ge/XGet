from sqlalchemy import Column, String, Integer, Float, DateTime, func
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
