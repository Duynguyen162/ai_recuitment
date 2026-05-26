import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.enum import RoleEnum
from app.crud import crud_company
from app.db.database import get_db
from app.models.companies import Company
from app.models.payment_transactions import PaymentTransaction
from app.models.subscription_plans import SubscriptionPlan
from app.models.user import User
from app.services.ngrok_service import public_url
from app.schemas.base_schema import ResponseSchema
from app.schemas.payment_schema import CreateCheckoutData, CreateCheckoutRequest, VnPayCallbackData

router = APIRouter(prefix="/payment", tags=["Payment"])


def _add_days(base_time: datetime, days: int) -> datetime:
    from datetime import timedelta

    return base_time + timedelta(days=days)


@router.get("/plans", response_model=ResponseSchema[list[dict]])
def list_active_plans(db: Session = Depends(get_db)):
    plans = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.cycle.asc())
        .all()
    )
    data = [
        {
            "code": p.code,
            "name": p.name,
            "cycle": p.cycle,
            "price_vnd": p.price_vnd,
            "vip_duration_days": p.vip_duration_days,
        }
        for p in plans
    ]
    return ResponseSchema(success=True, data=data, error=None, meta=None)


@router.post("/create-checkout", response_model=ResponseSchema[CreateCheckoutData])
def create_checkout(
    payload: CreateCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chi nha tuyen dung moi duoc su dung tinh nang nay")

    company = crud_company.get_company_by_hr(db, current_user.id)
    if not company:
        raise HTTPException(status_code=404, detail="Ban chua dang ky cong ty")

    if not settings.SEPAY_BANK_NAME.strip() or not settings.SEPAY_BANK_ACCOUNT.strip():
        raise HTTPException(status_code=500, detail="Thieu cau hinh SEPAY_BANK_NAME/SEPAY_BANK_ACCOUNT")

    plan_code = (payload.plan_code or "").strip()
    if not plan_code:
        if not payload.plan or not payload.cycle:
            raise HTTPException(status_code=400, detail="Thieu plan_code hoac cap plan + cycle")
        plan_code = f"{payload.plan}_{payload.cycle}"

    plan = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.code == plan_code, SubscriptionPlan.is_active.is_(True))
        .first()
    )
    if not plan:
        raise HTTPException(status_code=400, detail="Goi dang ky khong ton tai hoac da tat")

    amount = plan.price_vnd
    txn_ref = f"SP{company.id}{int(datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).timestamp())}"
    transfer_content = f"VIP {txn_ref}"

    transaction = PaymentTransaction(
        company_id=company.id,
        created_by=current_user.id,
        txn_ref=txn_ref,
        plan=(payload.plan or "vip"),
        plan_code=plan.code,
        cycle=plan.cycle,
        vip_duration_days=plan.vip_duration_days,
        amount=amount,
        amount_subunit=amount,
        status="pending",
    )
    db.add(transaction)
    webhook_base = public_url or settings.BASE_URL.rstrip("/")
    transaction.raw_payload = json.dumps(
        {
            "transfer_content": transfer_content,
            "webhook_url": f"{webhook_base}/api/v1/payment/sepay-ipn",
        },
        ensure_ascii=True,
    )
    db.commit()

    return ResponseSchema(
        success=True,
        data=CreateCheckoutData(
            payment_type="bank_transfer_webhook",
            txn_ref=txn_ref,
            amount=amount,
            transfer_content=transfer_content,
            bank_name=settings.SEPAY_BANK_NAME,
            bank_account=settings.SEPAY_BANK_ACCOUNT,
            account_holder=settings.SEPAY_ACCOUNT_HOLDER,
            qr_image_url=settings.SEPAY_QR_IMAGE_URL or None,
        ),
        error=None,
        meta=None,
    )


@router.post("/sepay-ipn")
async def sepay_ipn(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    ipn_api_key = settings.SEPAY_IPN_API_KEY.strip()
    if ipn_api_key:
        normalized = (authorization or "").strip()
        accepted = {
            f"Apikey {ipn_api_key}",
            f"ApiKey {ipn_api_key}",
            f"Bearer {ipn_api_key}",
            ipn_api_key,
        }
        if normalized not in accepted:
            return {"success": False, "message": "Unauthorized"}

    payload = await request.json()
    order_code = payload.get("order_code") or payload.get("orderCode")
    status = (
        payload.get("status")
        or payload.get("payment_status")
        or payload.get("transferType")
        or payload.get("result")
        or ""
    ).lower()
    transfer_type = str(payload.get("transferType") or "").lower()
    amount = (
        payload.get("order_amount")
        or payload.get("amount")
        or payload.get("transferAmount")
        or payload.get("value")
    )

    # Fallback: nhận diện txn_ref từ content nếu SePay webhook biến động số dư.
    if not order_code:
        content = str(
            payload.get("content")
            or payload.get("transaction_content")
            or payload.get("description")
            or ""
        )
        matched = re.search(r"\bSP\d+\b", content)
        if matched:
            order_code = matched.group(0)

    if not order_code:
        return {"success": False, "message": "order_code not found"}

    transaction = db.query(PaymentTransaction).filter(PaymentTransaction.txn_ref == order_code).first()
    if not transaction:
        return {"success": False, "message": "order not found"}

    if transaction.status == "completed":
        return {"success": True}

    paid_amount = None
    if amount is not None:
        try:
            paid_amount = int(float(amount))
        except Exception:
            paid_amount = None

    is_success = (
        status in {"success", "paid", "completed"}
        or transfer_type == "in"
        or str(payload.get("result_code", "")) == "00"
    )
    if is_success:
        if paid_amount is None or paid_amount < transaction.amount:
            transaction.status = "pending"
            transaction.response_code = "amount_mismatch"
        else:
            transaction.status = "completed"
            transaction.paid_amount = paid_amount
            company = db.query(Company).filter(Company.id == transaction.company_id).first()
            if company:
                now_utc = datetime.now(timezone.utc)
                base_start = now_utc
                if company.vip_expire_at and company.vip_expire_at > now_utc:
                    base_start = company.vip_expire_at

                duration_days = transaction.vip_duration_days or (365 if transaction.cycle == "yearly" else 30)
                new_expire = _add_days(base_start, duration_days)
                transaction.vip_started_at = base_start
                transaction.vip_expire_at = new_expire
                company.is_vip = True
                company.vip_expire_at = new_expire
    else:
        # Keep pending for ambiguous webhook statuses; only mark failed on explicit fail/cancel.
        if status in {"failed", "cancelled", "canceled", "error"}:
            transaction.status = "failed"
        else:
            transaction.status = "pending"

    transaction.response_code = str(payload.get("result_code") or payload.get("status") or "")
    transaction.bank_code = str(payload.get("gateway") or "")
    transaction.pay_date = str(payload.get("transaction_date") or payload.get("paid_at") or "")
    transaction.raw_payload = json.dumps(payload, ensure_ascii=True)

    if paid_amount is not None:
        transaction.paid_amount = paid_amount

    db.commit()
    return {"success": True}


@router.get("/sepay-status", response_model=ResponseSchema[VnPayCallbackData])
def sepay_status(
    txn_ref: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chi nha tuyen dung moi duoc su dung tinh nang nay")

    transaction = db.query(PaymentTransaction).filter(PaymentTransaction.txn_ref == txn_ref).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Khong tim thay giao dich")

    company = crud_company.get_company_by_hr(db, current_user.id)
    if not company or company.id != transaction.company_id:
        raise HTTPException(status_code=403, detail="Ban khong co quyen xem giao dich nay")

    status = transaction.status if transaction.status in {"pending", "completed", "failed", "cancelled"} else "pending"
    success = status == "completed"
    return ResponseSchema(
        success=success,
        data=VnPayCallbackData(
            txn_ref=transaction.txn_ref,
            amount=float(transaction.amount),
            status=status,
            response_code=transaction.response_code or "",
        ),
        error=None if success else "Thanh toan chua duoc xac nhan",
        meta=None,
    )
