# EasySlip Python SDK

[![CI](https://github.com/EASYSLIP-CO-LTD/sdk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/EASYSLIP-CO-LTD/sdk-python/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

SDK สำหรับตรวจสลิปธนาคารและ TrueMoney Wallet ผ่าน EasySlip API พร้อมชนิดข้อมูลสำหรับ Python

[English](README.md)

## ความสามารถ

เรียก API ได้ทั้งแบบ sync และ async จัดการบัญชีรับเงิน ส่งงานตรวจเบื้องหลัง และตรวจลายเซ็น webhook รองรับ API v2 และ v1 เดิม ข้อมูลตอบกลับเก็บ field เพิ่มเติมไว้ได้ ส่วนข้อผิดพลาดมี code และ request id เมื่อ API ส่งมา

## สิ่งที่ต้องมี

Python 3.11 ถึง 3.15 ที่ยังได้รับการสนับสนุน และ API key จาก [หน้าจัดการนักพัฒนา](https://developer.easyslip.com)

## ติดตั้ง

```sh
python -m pip install easyslip-sdk
```

## เริ่มใช้งาน

ตั้ง `EASYSLIP_API_KEY` ใน environment หรือใช้ `EASYSLIP_API_KEY_FILE` ชี้ไปยังไฟล์ส่วนตัวที่เก็บ key เตรียม `payload.txt`, `slip.png` และรูปสลิปวอลเล็ทสำหรับคำสั่งที่ต้องการใช้ เปลี่ยน URL ตัวอย่างเป็น URL รูปสลิปที่เข้าถึงได้จากอินเทอร์เน็ต คำสั่งตรวจแต่ละบรรทัดส่งคำขอแยกกันและอาจใช้โควต้า

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

`bank_by_image` รับ path, bytes หรือไฟล์ที่เปิดแบบ binary ถ้าส่ง string SDK จะอ่านเป็น path ในเครื่อง จึงไม่ควรส่ง string จากผู้ใช้โดยตรง `bank_by_payload` ใช้ข้อความ QR ของสลิป ไม่ใช่เลขอ้างอิงรายการ ส่วนคำสั่ง URL ให้ API ดาวน์โหลดรูปจาก URL สาธารณะ `generate_qr` ใช้สร้าง QR รับเงิน ไม่ได้ตรวจสลิป เรียก API v1 เดิมได้ผ่าน `client.v1`

แอป async ใช้ `AsyncClient` และ await เมธอดชื่อเดียวกัน:

```python
import asyncio
from easyslip import AsyncClient


async def main() -> None:
    async with AsyncClient() as client:
        await client.get_info()


asyncio.run(main())
```

## ตั้งค่า

| ตัวเลือก | ค่าเริ่มต้น | การใช้งาน |
| --- | --- | --- |
| `api_key` | `EASYSLIP_API_KEY` แล้วจึง `EASYSLIP_API_KEY_FILE` | ใช้ key ที่ส่งโดยตรงก่อนค่า environment |
| `timeout` | 30 วินาที | เวลารอของคำขอ HTTP แต่ละครั้ง |
| `max_retries` | 2 | จำนวนครั้งที่ลองเพิ่มตามเงื่อนไขด้านล่าง |
| `v2_base_url` | `EASYSLIP_V2_BASE_URL` หรือ `https://api.easyslip.com/v2` | เปลี่ยน URL ของ API v2 |
| `v1_base_url` | `EASYSLIP_V1_BASE_URL` หรือ `https://api.easyslip.com/v1` | เปลี่ยน URL ของ API v1 |
| `http` | HTTPX client ที่ SDK สร้าง | ส่ง `httpx.Client` หรือ `httpx.AsyncClient` เองได้ และต้องปิดเอง |

```python
import httpx
from easyslip import Client

with httpx.Client(trust_env=False, follow_redirects=False) as http:
    with Client(timeout=15, max_retries=1, http=http) as client:
        client.get_info()
```

ใช้ context manager เพื่อปิดการเชื่อมต่อที่ SDK สร้าง ถ้าส่ง HTTP client เอง ให้ปิดเมื่อใช้งานเสร็จ `jobs.wait_for_job(job_id, timeout=600)` ตรวจสถานะทุกหนึ่งวินาทีเป็นค่าเริ่มต้น และนับ timeout รวมทั้งคำขอและเวลารอก่อนลองใหม่

## จัดการข้อผิดพลาด

ข้อผิดพลาดทั้งหมดของ SDK สืบทอดจาก `EasySlipError` ควรดักชนิดที่เฉพาะเจาะจงก่อนชนิดแม่

| Error class | HTTP status | เกิดเมื่อ | วิธีจัดการ |
| --- | --- | --- | --- |
| `AuthenticationError` | 401 | API key ไม่ถูกต้องหรือไม่ได้ส่งมา | ตรวจสอบ key ของแอปพลิเคชัน |
| `PermissionDeniedError / QuotaExceededError` | 403 | ไม่มีสิทธิ์หรือโควต้าหมด | ตรวจสอบสิทธิ์และโควต้า |
| `InvalidRequestError / InvalidImageError / InvalidUrlError` | 400 | ข้อมูล รูปภาพ หรือ URL ไม่ผ่านเงื่อนไข | แก้ข้อมูลก่อนส่งใหม่ |
| `DuplicateSlipError` | 400 (v1) | สลิปเคยถูกตรวจแล้วใน v1 | อ่าน error.slip และอย่าเพิ่มยอดซ้ำ |
| `NotFoundError / SlipNotFoundError / SlipPendingError` | 404 | ไม่พบข้อมูลหรือธนาคารยังไม่พร้อมให้ตรวจสลิป | ตรวจสอบรหัสหรือรอข้อมูลจากธนาคาร |
| `ConflictError` | 409 | บัญชีรับเงินซ้ำกับบัญชีที่มีอยู่ | ใช้บัญชีเดิมหรือแก้ข้อมูลบัญชี |
| `RateLimitError` | 429 | ส่งคำขอถี่เกินไป | รอตาม retry_after ถ้ามี |
| `ServerError / ServiceUnavailableError` | 5xx | API หรือระบบที่เกี่ยวข้องทำงานไม่สำเร็จ | เก็บ request id ไว้ติดต่อทีมงาน |
| `InputError` | None | SDK ปฏิเสธข้อมูลก่อนส่งคำขอ | แก้ข้อมูลตาม code ที่ได้รับ |
| `NetworkError / RequestTimeoutError` | None | เชื่อมต่อไม่ได้หรือหมดเวลารอ | ตรวจสอบการเชื่อมต่อและระวังการส่งคำขอตรวจซ้ำ |
| `JobWaitTimeoutError` | None | หมดเวลารอผลของงาน | ดู last_job แล้วรอผลต่อเมื่อต้องการ |
| `BatchSubmitError` | None | ส่งงานบางชุดไม่สำเร็จหลังจากรับชุดก่อนหน้าแล้ว | ดู submitted และ failed_chunk เพื่อไม่ส่งชุดที่รับแล้วซ้ำ |
| `WebhookSignatureError` | None | ลายเซ็น webhook ไม่ตรงกับ body | ปฏิเสธ webhook และตรวจสอบ signing secret |

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

คำสั่งที่ส่งซ้ำได้จะลองใหม่เมื่อเชื่อมต่อไม่สำเร็จหรือพบ 5xx บางสถานะ และอาจลองใหม่เมื่อได้ HTTP 429 คำสั่งตรวจสลิปและส่งงานจะไม่ส่งซ้ำหลัง read timeout หรือ 5xx เพราะอาจใช้โควต้าซ้ำ การลองใหม่เพิ่มเวลารอแบบ exponential backoff พร้อม jitter และใช้ `Retry-After` เมื่อไม่เกิน 60 วินาที

ข้อความผิดพลาด body, header และสาเหตุการเชื่อมต่อจะปิดบัง API key รวมถึงรูปแบบ percent-encoded และ JSON-escaped ส่วน Authorization header จะถูกปิดบังเสมอ `sensitive_raw_body()` คืน body เดิมโดยตั้งใจ จึงไม่ควรส่งลง log ผลตรวจสลิปอาจมีข้อมูลส่วนบุคคล แอปของคุณต้องควบคุมสิทธิ์การเข้าถึงด้วย

## ลายเซ็น webhook

ตรวจลายเซ็นจาก bytes เดิมก่อนแปลง JSON ห้าม serialize ใหม่ก่อนตรวจ อ่าน header `X-EasySlip-Signature` จากคำขอและเก็บ webhook secret ใน environment

```python
import os
from easyslip.webhooks import construct_event

raw_body = b'{"status":"success"}'
signature = None  # Replace with the incoming X-EasySlip-Signature header.
event = construct_event(raw_body, signature, os.environ["EASYSLIP_WEBHOOK_SECRET"])
```

ตัวอย่างนี้จะปฏิเสธคำขอที่ไม่มีลายเซ็น ใน HTTP handler ให้คืนข้อผิดพลาดเมื่อเกิด `WebhookSignatureError`

## ตัวอย่างและเอกสาร

[ตัวอย่างที่รันได้](examples/README.md) ครอบคลุมทุกคำสั่ง รวม pagination บัญชีรับเงิน และงานเบื้องหลัง ดูชนิดข้อมูลได้ใน [คู่มือ Python SDK](https://document.easyslip.com/th/sdk/python) และดูเงื่อนไข endpoint ได้ใน [เอกสาร API](https://document.easyslip.com)

## ติดต่อทีมงาน

แจ้งบั๊ก SDK ผ่าน GitHub issue พร้อม request id และตัวอย่างที่ทำให้เกิดปัญหา เรื่องบัญชีและโควต้าให้ติดต่อผ่าน [หน้าจัดการนักพัฒนา](https://developer.easyslip.com) อย่าใส่ API key หรือสลิปที่ยังมีข้อมูลลูกค้าลงใน issue สาธารณะ อ่านช่องทางแจ้งปัญหาความปลอดภัยแบบส่วนตัวใน [SECURITY.md](SECURITY.md)

## สัญญาอนุญาต

[MIT](LICENSE), Copyright (c) 2026 EasySlip Co., Ltd.
