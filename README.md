# EasySlip Python SDK

[![CI](https://github.com/EASYSLIP-CO-LTD/sdk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/EASYSLIP-CO-LTD/sdk-python/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Verify bank transfer slips and TrueMoney Wallet receipts with typed Python clients for the EasySlip API.

[ภาษาไทย](README.th.md)

## Features

Use synchronous or asynchronous requests, manage receiving accounts, submit background jobs and verify webhook signatures. Both API v2 and legacy v1 are supported. Responses preserve extra fields, and errors include the API code and request id when available.

## Requirements

Python 3.11 through 3.15. Use a currently supported Python release and an EasySlip API key from [the developer portal](https://developer.easyslip.com).

## Installation

```sh
python -m pip install easyslip-sdk
```

## Quick start

Set `EASYSLIP_API_KEY` in your environment, or set `EASYSLIP_API_KEY_FILE` to a private file containing the key. Prepare `payload.txt`, `slip.png` and a wallet receipt for the operations you want to use. Replace the example image URL with your public slip image URL. Each verification is a separate request and can consume quota.

```python
import base64
from pathlib import Path
from easyslip import Client
from easyslip.models import QrRequest

with Client() as client:
    payload = Path("payload.txt").read_text().strip()
    result = client.verify.bank_by_payload(payload)
    print(result.meta.request_id if result.meta else None)
    client.verify.bank_by_image(Path("slip.png"))
    client.verify.bank_by_url("https://example.com/slip.png")
    client.verify.bank_by_base64(base64.b64encode(Path("slip.png").read_bytes()).decode())
    client.verify.truewallet_by_image(Path("wallet-slip.png"))
    info = client.get_info()
    qr = client.v1.generate_qr(QrRequest(type="PROMPTPAY", msisdn="0812345678", amount=100))
    legacy = client.v1.verify_bank_by_payload(payload)
```

`bank_by_image` accepts a path, bytes or a binary file object. Treat strings as trusted local paths; do not pass user-supplied strings to file methods. `bank_by_payload` reads a slip's QR payload, not its transaction reference. The URL method asks the API to fetch a publicly reachable image. `generate_qr` returns payment QR data rather than verifying a slip. Legacy v1 methods remain under `client.v1`.

For an async application, use `AsyncClient` and await the same resource methods:

```python
import asyncio
from easyslip import AsyncClient


async def main() -> None:
    async with AsyncClient() as client:
        await client.get_info()


asyncio.run(main())
```

## Configuration

| Option | Default | Purpose |
| --- | --- | --- |
| `api_key` | `EASYSLIP_API_KEY`, then `EASYSLIP_API_KEY_FILE` | Select the application key; an explicit value takes precedence. |
| `timeout` | 30 seconds | Bound each HTTP request. |
| `max_retries` | 2 | Allow up to two additional attempts under the retry rules below. |
| `v2_base_url` | `EASYSLIP_V2_BASE_URL` or `https://api.easyslip.com/v2` | Override the v2 API URL. |
| `v1_base_url` | `EASYSLIP_V1_BASE_URL` or `https://api.easyslip.com/v1` | Override the legacy API URL. |
| `http` | An SDK-owned HTTPX client | Supply `httpx.Client` or `httpx.AsyncClient`; you remain responsible for closing it. |

```python
import httpx
from easyslip import Client

with httpx.Client(trust_env=False, follow_redirects=False) as http:
    with Client(timeout=15, max_retries=1, http=http) as client:
        client.get_info()
```

Use a context manager to close connections created by the SDK. Custom clients remain yours to close. `jobs.wait_for_job(job_id, timeout=600)` polls with a default interval of two seconds and applies its timeout to the whole wait, including requests and retry delays.

## Error handling

All SDK failures inherit from `EasySlipError`. Catch specific errors before their parent classes.

| Error class | HTTP status | When it happens | What to do |
| --- | --- | --- | --- |
| `AuthenticationError` | 401 | The API key is missing or invalid. | Check the key for this application. |
| `PermissionDeniedError / QuotaExceededError` | 403 | Access is denied or quota is exhausted. | Check permissions and quota. |
| `InvalidRequestError / InvalidImageError / InvalidUrlError` | 400 | The API refuses an argument, image or URL. | Correct the input before resending. |
| `DuplicateSlipError` | 400 (v1) | The slip has already been verified. | Read error.slip; avoid crediting it twice. |
| `NotFoundError / SlipNotFoundError / SlipPendingError` | 404 | A resource or slip is unavailable; a pending slip may need time. | Check the identifier or wait for the bank. |
| `ConflictError` | 409 | A receiving account conflicts with an existing account. | Use the existing account or change the identity. |
| `RateLimitError` | 429 | The request rate is too high. | Wait for retry_after when supplied. |
| `ServerError / ServiceUnavailableError` | 5xx | The API or a dependency could not complete the request. | Keep the request id when contacting support. |
| `InputError` | None | The SDK rejects an argument before sending. | Fix the argument; code identifies the reason. |
| `NetworkError / RequestTimeoutError` | None | The connection fails or the request times out. | Check connectivity; do not blindly repeat billed calls. |
| `JobWaitTimeoutError` | None | The polling deadline expires. | Keep last_job and resume polling if appropriate. |
| `BatchSubmitError` | None | A later batch chunk fails. | Use submitted and failed_chunk to avoid resubmitting accepted chunks. |
| `WebhookSignatureError` | None | A webhook signature does not match the original body. | Reject the webhook and check the signing secret. |

```python
from easyslip import Client
from easyslip.errors import ApiError, AuthenticationError, RateLimitError, NetworkError

try:
    with Client() as client:
        client.get_info()
except AuthenticationError:
    print("Check the API key configured for this application.")
except RateLimitError as error:
    print("Wait before trying again:", error.retry_after)
except ApiError as error:
    print(error.status, error.code, error.request_id)
except NetworkError:
    print("The request could not complete. Check your connection.")
```

Safe operations retry connection failures and selected 5xx responses; requests may also retry HTTP 429. Verification and job submissions do not retry read timeouts or 5xx after sending, because another attempt could consume quota twice. Retries use exponential backoff with jitter and respect `Retry-After` up to 60 seconds.

Public error messages, bodies, headers and transport causes redact the configured API key, including percent-encoded and JSON-escaped forms. Authorization headers are always redacted. `sensitive_raw_body()` deliberately returns the original API error body; keep it out of logs. Slip responses can contain personal data and need your own access controls.

## Webhook signatures

Verify the original request bytes before parsing. Do not re-serialize JSON first. Read `X-EasySlip-Signature` from the incoming request and keep the webhook secret in your environment.

```python
import os
from easyslip.webhooks import construct_event

raw_body = b'{"status":"success"}'
signature = None  # Replace with the incoming X-EasySlip-Signature header.
event = construct_event(raw_body, signature, os.environ["EASYSLIP_WEBHOOK_SECRET"])
```

This example rejects a missing signature. In your HTTP handler, return an error when `WebhookSignatureError` is raised.

## Examples and documentation

[Runnable examples](examples/README.md) cover every operation, including pagination, receiving accounts and background jobs. The [Python SDK guide](https://document.easyslip.com/en/sdk/python) documents inputs and response models; the [API reference](https://document.easyslip.com) describes endpoint behavior.

## Support

Open a GitHub issue for SDK bugs, with a request id and a small reproduction. For account and quota questions, contact EasySlip through [the developer portal](https://developer.easyslip.com). Never include API keys or unmasked customer slips in public issues. See [SECURITY.md](SECURITY.md) for private security reports.

## License

[MIT](LICENSE), Copyright (c) 2026 EasySlip Co., Ltd.
