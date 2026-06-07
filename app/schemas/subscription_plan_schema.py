from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SubscriptionPlanBase(BaseModel):
    code: str
    name: str
    cycle: Literal["monthly", "yearly"]
    price_vnd: int
    vip_duration_days: int
    is_active: bool = True


class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass


class SubscriptionPlanUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
