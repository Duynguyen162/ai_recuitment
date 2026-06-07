from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.enum import RoleEnum
from app.db.database import get_db
from app.models.subscription_plans import SubscriptionPlan
from app.models.user import User
from app.schemas.base_schema import ResponseSchema
from app.schemas.subscription_plan_schema import (
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdate,
)

router = APIRouter(prefix="/subscription-plans", tags=["Admin Subscription Plans"])


@router.get("", response_model=ResponseSchema[list[SubscriptionPlanResponse]])
def list_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Chi Admin moi co quyen truy cap")

    plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.id.asc()).all()
    return ResponseSchema(success=True, data=[SubscriptionPlanResponse.model_validate(p) for p in plans], error=None, meta=None)


@router.post("", response_model=ResponseSchema[SubscriptionPlanResponse])
def create_plan(
    payload: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Chi Admin moi co quyen truy cap")

    existing = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plan code da ton tai")

    plan = SubscriptionPlan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return ResponseSchema(success=True, data=SubscriptionPlanResponse.model_validate(plan), error=None, meta=None)


@router.put("/{plan_id}", response_model=ResponseSchema[SubscriptionPlanResponse])
def update_plan(
    plan_id: int,
    payload: SubscriptionPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Chi Admin moi co quyen truy cap")

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Khong tim thay plan")

    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(plan, k, v)

    db.commit()
    db.refresh(plan)
    return ResponseSchema(success=True, data=SubscriptionPlanResponse.model_validate(plan), error=None, meta=None)
