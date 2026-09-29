from datetime import date
from typing import Protocol

from .models import MatterIntake, MatterResult, RechargeNotice, RechargeNoticeResult


class ContinuityGateway(Protocol):
    def get_balance(self) -> dict[str, object]:
        raise AssertionError("Protocol declaration")

    def send_email(
        self, to: str, subject: str, *, text: str, operation_id: str
    ) -> dict[str, object]:
        raise AssertionError("Protocol declaration")


class LegalContinuityService:
    def __init__(self, gateway: ContinuityGateway, reminder_window_days: int = 7) -> None:
        self._gateway = gateway
        self._reminder_window_days = reminder_window_days

    def accept_matter(self, intake: MatterIntake, today: date | None = None) -> MatterResult:
        current_day = today or date.today()
        balance_data = self._gateway.get_balance()
        delivery = self._gateway.send_email(
            str(intake.client_email),
            f"Signed document for matter {intake.matter_id}",
            text=(
                f"Hello {intake.client_name}, your signed document is ready: "
                f"{intake.signed_document_url}"
            ),
            operation_id=f"{intake.matter_id}-signed-delivery",
        )

        days_remaining = (intake.response_deadline - current_day).days
        should_follow_up = 0 <= days_remaining <= self._reminder_window_days
        follow_up_id: str | None = None
        if should_follow_up:
            follow_up = self._gateway.send_email(
                str(intake.client_email),
                f"Deadline reminder for matter {intake.matter_id}",
                text=(
                    f"Your response deadline is {intake.response_deadline.isoformat()}. "
                    f"Please review the signed document before that date."
                ),
                operation_id=f"{intake.matter_id}-deadline-{intake.response_deadline.isoformat()}",
            )
            follow_up_id = str(follow_up["message_id"])

        return MatterResult(
            matter_id=intake.matter_id,
            balance=float(balance_data["balance"]),
            delivery_message_id=str(delivery["message_id"]),
            follow_up_message_id=follow_up_id,
            follow_up_scheduled=should_follow_up,
        )

    def notify_recharge(self, notice: RechargeNotice) -> RechargeNoticeResult:
        sent = self._gateway.send_email(
            str(notice.recipient),
            "Infrai auto recharge completed",
            text=(
                f"The balance reached {notice.trigger_balance:.2f}; "
                f"an automatic recharge of {notice.recharge_amount:.2f} completed."
            ),
            operation_id=(
                f"recharge-{notice.recipient}-{notice.trigger_balance}-"
                f"{notice.recharge_amount}"
            ),
        )
        return RechargeNoticeResult(message_id=str(sent["message_id"]))
