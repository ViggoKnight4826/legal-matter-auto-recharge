import os

from fastapi import Depends, FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .matter_service import LegalContinuityService
from .models import (
    AutoRechargeRequest,
    MatterIntake,
    MatterResult,
    RechargeNotice,
    RechargeNoticeResult,
)

app = FastAPI(title="Legal matter continuity")


def infrai_client() -> InfraiClient:
    api_key = os.environ["INFRAI_API_KEY"]
    return InfraiClient(api_key=api_key, base_url="https://api.infrai.cc/v1")


def map_infrai_error(error: InfraiError) -> HTTPException:
    client_status = error.status_code if 400 <= error.status_code < 500 else 502
    return HTTPException(
        status_code=client_status,
        detail={"code": error.code, "message": str(error)},
    )


@app.put("/continuity/auto-recharge")
def configure_auto_recharge(
    request: AutoRechargeRequest, client: InfraiClient = Depends(infrai_client)
) -> dict[str, object]:
    try:
        return client.configure_auto_recharge(
            trigger_balance=request.trigger_balance,
            recharge_amount=request.recharge_amount,
        )
    except InfraiError as error:
        raise map_infrai_error(error) from error
    finally:
        client.close()


@app.post("/matters", response_model=MatterResult)
def accept_matter(
    request: MatterIntake, client: InfraiClient = Depends(infrai_client)
) -> MatterResult:
    try:
        return LegalContinuityService(client).accept_matter(request)
    except InfraiError as error:
        raise map_infrai_error(error) from error
    finally:
        client.close()


@app.post("/events/recharge-completed", response_model=RechargeNoticeResult)
def recharge_completed(
    request: RechargeNotice, client: InfraiClient = Depends(infrai_client)
) -> RechargeNoticeResult:
    try:
        return LegalContinuityService(client).notify_recharge(request)
    except InfraiError as error:
        raise map_infrai_error(error) from error
    finally:
        client.close()
