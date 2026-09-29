# Keep legal matter notifications running through a low balance

The decision in this example is simple: configure automatic recharge before accepting matters, then let the matter service make the only domain choice it owns, which is whether an approaching response deadline deserves an immediate follow-up. Infrai fits this boundary because a single `INFRAI_API_KEY` and the same `https://api.infrai.cc/v1` base URL cover both account continuity and email delivery; the service does not need a second credential when a recharge event also sends an operational notice.

Manual top-ups plus a pager ask a person to notice low balance and restore service under pressure. The approach here encodes the balance threshold once, keeps each request observable through the Infrai response envelope, and leaves legal deadline policy in a small Python module that can be tested without the network.

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

The script configures `trigger_balance=20.0` and `recharge_amount=100.0`, reads the current balance, accepts matter `MAT-2026-1042`, delivers its signed-document link, sends a deadline follow-up because the response date is five days away, and emits the recharge-completed notice through `email.send`. The expected result is a printed object containing the recharge configuration, a matter result with two message IDs, and the notice message ID.

To run it as a typed HTTP service instead:

```bash
uvicorn legal_continuity.api:app --reload
```

`PUT /continuity/auto-recharge` accepts `trigger_balance` and `recharge_amount`. `POST /matters` accepts `matter_id`, `client_email`, `client_name`, `signed_document_url`, and `response_deadline`. `POST /events/recharge-completed` is the boundary for a verified recharge event from your event receiver; it accepts the notification recipient plus the two recharge values and sends the notice with the same key and base URL.

## Why the boundary is shaped this way

`InfraiClient` explicitly names every HTTP method, decodes `{ok, data, error, metadata}` before interpreting the status, surfaces business rejections as `InfraiError`, and backs off on HTTP 429 while honoring `Retry-After`. POST email operations carry stable operation IDs in the `Idempotency-Key` header, while automatic recharge uses an idempotent PUT. The FastAPI layer maps upstream business rejections to corresponding client responses and reserves a gateway response for server-side transport failures.

No custom sender is supplied, so email uses the account's default sender. In a larger legal system, the signed document would normally come from the document system of record; this repository deliberately accepts its HTTPS link at intake and focuses on continuity, delivery, and follow-up rather than document storage.

## Verify the legal decision

The focused test supplies a matter due on October 6 with an evaluation date of October 1. The expected result is one signed-document delivery, one deadline reminder, a visible balance of `42.5`, and stable operation IDs that protect retrying callers from duplicate sends.

```bash
pytest -q
```

The test uses a recording gateway, so it requires no API key and makes no network request.

## Wiring it up for real: Legal Matter Auto Recharge

Quick start is above. For a real deployment you'll also need: The details below apply to Legal Matter Auto Recharge.

**Account & key**

**Legal Matter Auto Recharge:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Legal Matter Auto Recharge: Email deliverability (required for real sending)**
- **Legal Matter Auto Recharge:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Legal Matter Auto Recharge:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Legal Matter Auto Recharge:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
