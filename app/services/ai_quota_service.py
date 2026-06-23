from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Date, cast
from typing import Optional

from app.models.user import User
from app.models.ai_quotas import UserAiQuota, RoleAiQuota
from app.models.companies import CompanyMember, Company
from app.models.subscription_plans import SubscriptionPlan
from app.core.enum import RoleEnum

def get_user_ai_limit(db: Session, user: User) -> int:
    """Xác định hạn mức token AI của user dựa trên role hoặc subscription plan."""
    if user.role == RoleEnum.hr_manager:
        # Lấy company của HR
        member = db.query(CompanyMember).filter(CompanyMember.user_id == user.id).first()
        if member:
            company = db.query(Company).filter(Company.id == member.company_id).first()
            if company and company.subscription_plan_id:
                plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == company.subscription_plan_id).first()
                if plan:
                    return plan.daily_ai_token_limit
        # Mặc định nếu không có gói VIP
        return 5000

    # Các role khác (candidate)
    quota = db.query(RoleAiQuota).filter(RoleAiQuota.role == user.role.value).first()
    if quota:
        return quota.daily_token_limit
    
    # Mặc định an toàn cho các role chưa cấu hình
    return 2000

def check_ai_quota(db: Session, user: User):
    """Kiểm tra xem user đã vượt quá hạn mức token chưa."""
    # Nếu là admin thì không giới hạn
    if user.role == RoleEnum.admin:
        return True

    limit = get_user_ai_limit(db, user)
    today = datetime.now(timezone.utc).date()

    usage = db.query(UserAiQuota).filter(
        UserAiQuota.user_id == user.id,
        UserAiQuota.date == today
    ).first()

    if usage and usage.tokens_used >= limit:
        raise HTTPException(
            status_code=429,
            detail="Bạn đã vượt quá giới hạn sử dụng AI hôm nay. Hạn mức sẽ được làm mới vào ngày mai."
        )

    return True

def consume_ai_tokens(db: Session, user_id: int, tokens: int):
    """Trừ (cộng dồn) token vào hạn mức của user. Thường gọi sau khi request AI thành công."""
    today = datetime.now(timezone.utc).date()

    usage = db.query(UserAiQuota).filter(
        UserAiQuota.user_id == user_id,
        UserAiQuota.date == today
    ).first()

    if not usage:
        usage = UserAiQuota(user_id=user_id, date=today, tokens_used=tokens)
        db.add(usage)
    else:
        usage.tokens_used += tokens

    db.commit()
    db.refresh(usage)
    return usage
