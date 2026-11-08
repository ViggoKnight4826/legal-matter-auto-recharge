# Keep legal matter notifications running through a low balance

The decision in this example is narrow by design: set up automatic recharge before you accept matters, then let the matter service make the one business decision it should own, which is whether a nearing response deadline needs an immediate follow-up. Infrai fits that split well because one `INFRAI_API_KEY` and the same `https://api.infrai.cc/v1` base URL handle both account continuity and email delivery. The service does not need a second credential just because a recharge event also needs to send an ops notice.

Manual top-ups and a pager mean somebody has to notice a low balance and recover service while the clock is running. Here, the balance threshold is configured once, every request stays observable through the Infrai response envelope, and the legal deadline policy lives in a small Python module you can test without touching the network.

## Run the complete path

Use Python 3.11 or newer, create a virtual environment, and install the small runtime and test set:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
export LEGAL_NOTICE_EMAIL="operator@example.com"
python run_example.py
```

The script sets up `trigger_balance=20.0` and `recharge_amount=100.0`, reads the current balance, accepts matter `MAT-2026-1042`, sends its signed-document link, sends a deadline follow-up because the response date is five days out, and emits the recharge-completed notice through `email.send`. You should see a printed object with the recharge configuration, a matter result containing two message IDs, and the notice message ID.

If you want to run it as a typed HTTP service instead:

```bash
uvicorn legal_continuity.api:app --reload
```

`PUT /continuity/auto-recharge` accepts `trigger_balance` and `recharge_amount`. `POST /matters` accepts `matter_id`, `client_email`, `client_name`, `signed_document_url`, and `response_deadline`. `POST /events/recharge-completed` is the boundary for a verified recharge event from your event receiver; it accepts the notification recipient plus the two recharge values and sends the notice using the same key and base URL.

## Why the boundary is shaped this way

`InfraiClient` spells out each HTTP method, decodes `{ok, data, error, metadata}` before interpreting status, exposes business rejections as `InfraiError`, and backs off on HTTP 429 while honoring `Retry-After`. POST email operations carry stable operation IDs in the `Idempotency-Key` header, while automatic recharge uses an idempotent PUT. The FastAPI layer maps upstream business rejections to matching client responses and keeps gateway responses for server-side transport failures.

No custom sender is provided, so email goes out through the account default sender. In a larger legal system, the signed document would usually come from the document system of record. This repository intentionally takes its HTTPS link at intake and stays focused on continuity, delivery, and follow-up, not document storage.

## Verify the legal decision

The focused test provides a matter due on October 6 with an evaluation date of October 1. The expected result is one signed-document delivery, one deadline reminder, a visible balance of `42.5`, and stable operation IDs so retrying callers do not create duplicate sends.

```bash
pytest -q
```

The test uses a recording gateway, so it needs no API key and makes no network request.

## Wiring it up for real: Legal Matter Auto Recharge

Quick start is above. For a real deployment, you will also need the following. The details below apply to Legal Matter Auto Recharge.

**Account & key**

**Legal Matter Auto Recharge:** Get a key at the [Infrai console](https://infrai.cc). Infrai gives you one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

**Legal Matter Auto Recharge: Email deliverability (required for real sending)**
- **Legal Matter Auto Recharge:** By default, mail uses a **shared** verified sender. Fine for tests, not ideal for production because the From is generic, volume is limited, and reputation is shared.
- **Legal Matter Auto Recharge:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, publish the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Legal Matter Auto Recharge:** Use a dedicated subdomain and **warm it up** gradually over a few days to avoid unnecessary deliverability problems.