from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class ProcessingRuleBase(BaseModel):
    """处理规则基础模型"""
    name: str
    description: Optional[str] = None
    task_type: str
    rule_definition: Dict[str, Any]
    is_active: bool = True

class ProcessingRuleCreate(ProcessingRuleBase):
    """创建处理规则的请求模型"""
    pass

class ProcessingRuleUpdate(BaseModel):
    """更新处理规则的请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    rule_definition: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ProcessingRuleInDB(ProcessingRuleBase):
    """数据库中的处理规则模型"""
    id: str
    version: int = 1
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProcessingRuleResponse(ProcessingRuleInDB):
    """处理规则响应模型"""
    pass

class ProcessingRuleList(BaseModel):
    """处理规则列表响应模型"""
    rules: List[ProcessingRuleResponse]
    total: int 