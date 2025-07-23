from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..models.processing_rule import ProcessingRule
from ..schemas.processing_rule import (
    ProcessingRuleCreate,
    ProcessingRuleUpdate,
    ProcessingRuleResponse,
    ProcessingRuleList,
)
from ..services.rule_service import RuleService

router = APIRouter()

@router.post("", response_model=ProcessingRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_processing_rule(
    rule_data: ProcessingRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的数据处理规则
    """
    service = RuleService()
    rule = await service.create_rule(db, rule_data)
    return rule

@router.get("", response_model=ProcessingRuleList)
async def get_processing_rules(
    skip: int = 0,
    limit: int = 100,
    task_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取处理规则列表，支持分页和过滤
    """
    service = RuleService()
    rules, total = await service.get_rules(db, skip, limit, task_type, is_active)
    return {
        "rules": rules,
        "total": total,
    }

@router.get("/{rule_id}", response_model=ProcessingRuleResponse)
async def get_processing_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定ID的处理规则
    """
    service = RuleService()
    rule = await service.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="处理规则未找到")
    return rule

@router.put("/{rule_id}", response_model=ProcessingRuleResponse)
async def update_processing_rule(
    rule_id: str, rule_data: ProcessingRuleUpdate, db: AsyncSession = Depends(get_db)
):
    """
    更新处理规则信息
    """
    service = RuleService()
    rule = await service.update_rule(db, rule_id, rule_data)
    if not rule:
        raise HTTPException(status_code=404, detail="处理规则未找到")
    return rule

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_processing_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除处理规则
    """
    service = RuleService()
    success = await service.delete_rule(db, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="处理规则未找到")

@router.get("/by-task-type/{task_type}", response_model=List[ProcessingRuleResponse])
async def get_rules_by_task_type(task_type: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定任务类型的活跃处理规则
    """
    service = RuleService()
    rules = await service.get_rules_by_task_type(db, task_type)
    return rules 