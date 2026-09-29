from datetime import date

from pydantic import BaseModel, Field, HttpUrl


class MatterIntake(BaseModel):
    matter_id: str = Field(min_length=1)
    client_email: str = Field(min_length=3, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    client_name: str = Field(min_length=1)
    signed_document_url: HttpUrl
    response_deadline: date


class MatterResult(BaseModel):
    matter_id: str
    balance: float
    delivery_message_id: str
    follow_up_message_id: str | None
    follow_up_scheduled: bool


class AutoRechargeRequest(BaseModel):
    trigger_balance: float = Field(gt=0)
    recharge_amount: float = Field(gt=0)


class RechargeNotice(BaseModel):
    recipient: str = Field(min_length=3, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    trigger_balance: float = Field(gt=0)
    recharge_amount: float = Field(gt=0)


class RechargeNoticeResult(BaseModel):
    message_id: str
