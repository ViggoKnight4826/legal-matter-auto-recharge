from datetime import date

from legal_continuity.matter_service import LegalContinuityService
from legal_continuity.models import MatterIntake


class RecordingGateway:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def get_balance(self) -> dict[str, object]:
        return {"balance": 42.5}

    def send_email(
        self, to: str, subject: str, *, text: str, operation_id: str
    ) -> dict[str, object]:
        self.sent.append(
            {"to": to, "subject": subject, "text": text, "operation_id": operation_id}
        )
        return {"message_id": f"msg-{len(self.sent)}"}


def test_imminent_deadline_sends_delivery_and_follow_up() -> None:
    gateway = RecordingGateway()
    service = LegalContinuityService(gateway, reminder_window_days=7)
    intake = MatterIntake(
        matter_id="MAT-17",
        client_email="client@example.com",
        client_name="Avery",
        signed_document_url="https://documents.example/MAT-17/signed",
        response_deadline=date(2026, 10, 6),
    )

    result = service.accept_matter(intake, today=date(2026, 10, 1))

    assert result.follow_up_scheduled is True
    assert result.follow_up_message_id == "msg-2"
    assert result.balance == 42.5
    assert [message["operation_id"] for message in gateway.sent] == [
        "MAT-17-signed-delivery",
        "MAT-17-deadline-2026-10-06",
    ]
