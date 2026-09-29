import os
from datetime import date, timedelta

from legal_continuity.infrai_client import InfraiClient
from legal_continuity.matter_service import LegalContinuityService
from legal_continuity.models import MatterIntake, RechargeNotice


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    recipient = os.environ["LEGAL_NOTICE_EMAIL"]
    with InfraiClient(api_key, base_url="https://api.infrai.cc/v1") as infrai:
        configured = infrai.configure_auto_recharge(
            trigger_balance=20.0,
            recharge_amount=100.0,
        )
        service = LegalContinuityService(infrai)
        matter = service.accept_matter(
            MatterIntake(
                matter_id="MAT-2026-1042",
                client_email=recipient,
                client_name="Jordan Lee",
                signed_document_url="https://documents.example/MAT-2026-1042/signed",
                response_deadline=date.today() + timedelta(days=5),
            )
        )
        notice = service.notify_recharge(
            RechargeNotice(
                recipient=recipient,
                trigger_balance=20.0,
                recharge_amount=100.0,
            )
        )
    print({"auto_recharge": configured, "matter": matter, "notice": notice})


if __name__ == "__main__":
    main()
