from typing import Literal

from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    plan_code: str | None = None
    plan: Literal["vip"] | None = "vip"
    cycle: Literal["monthly", "yearly"] | None = None


class CreateCheckoutData(BaseModel):
    payment_type: Literal["bank_transfer_webhook"]
    txn_ref: str
    amount: int
    transfer_content: str
    bank_name: str
    bank_account: str
    account_holder: str
    qr_image_url: str | None = None


class VnPayCallbackData(BaseModel):
    txn_ref: str
    amount: float
    status: Literal["pending", "completed", "failed", "cancelled"]
    response_code: str
