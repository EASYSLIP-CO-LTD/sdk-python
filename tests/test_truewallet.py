"""TrueMoney Wallet answers with and without names or parties, and verify by QR payload."""

import json
import httpx
import pytest
from easyslip import AsyncClient, Client, models as m
from easyslip._codec import UNSET, decode
from easyslip.errors import DuplicateSlipError, InputError

BASE = {"transactionId": "50012345678902", "date": "2026-12-03T22:05:00+07:00", "amount": 200.25}
WITH_NAMES = {
    **BASE,
    "sender": {"name": "นาย ผู้โอน ทดสอบ"},
    "receiver": {"name": "นาย รับเงิน ทดสอบ", "phone": "08-xxx-4567"},
}
WITH_PHONES = {
    **BASE,
    "sender": {"phone": "08-xxx-2345"},
    "receiver": {"phone": "08-xxx-9876"},
}
SHAPES = {
    "names": WITH_NAMES,
    "phones": WITH_PHONES,
    "receiver phone only": {**BASE, "receiver": {"phone": "08-xxx-9876"}},
    "no parties": BASE,
}


@pytest.mark.parametrize("raw", SHAPES.values(), ids=SHAPES.keys())
def test_slip_decodes_and_round_trips(raw):
    slip = decode(m.TrueWalletSlip, raw)
    assert slip.to_dict() == raw
    assert (slip.sender is UNSET) == ("sender" not in raw)
    assert (slip.receiver is UNSET) == ("receiver" not in raw)


def test_phone_only_party_has_no_name():
    slip = decode(m.TrueWalletSlip, WITH_PHONES)
    assert slip.sender.name is UNSET
    assert slip.sender.phone == "08-xxx-2345"
    assert slip.receiver.phone == "08-xxx-9876"


def client_for(handler):
    return Client(
        "fixture-secret",
        http=httpx.Client(transport=httpx.MockTransport(handler)),
        v1_base_url="https://api.test/v1",
        v2_base_url="https://api.test/v2",
    )


def test_v2_by_payload_sends_json_and_reads_no_parties():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            200, json={"success": True, "data": {"amountInSlip": 200.25, "rawSlip": BASE}}
        )

    with client_for(handler) as c:
        result = c.verify.truewallet_by_payload(
            "wallet-qr", m.VerifyOptions(remark="r", check_duplicate=True)
        )
    assert seen[0].url.path == "/v2/verify/truewallet"
    assert json.loads(seen[0].content) == {
        "payload": "wallet-qr",
        "remark": "r",
        "checkDuplicate": True,
    }
    assert result.raw_slip.sender is UNSET


def test_v1_by_payload_sends_a_json_boolean_and_reads_phones():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"status": 200, "data": WITH_PHONES})

    with client_for(handler) as c:
        slip = c.v1.verify_truemoney_by_payload(
            "wallet-qr", m.V1VerifyOptions(check_duplicate=False)
        )
    assert seen[0].url.path == "/v1/verify/truewallet"
    assert json.loads(seen[0].content) == {"payload": "wallet-qr", "checkDuplicate": False}
    assert slip.receiver.phone == "08-xxx-9876"


def test_v1_duplicate_without_names_keeps_the_slip():
    def handler(request):
        return httpx.Response(
            400, json={"status": 400, "message": "duplicate_slip", "data": WITH_PHONES}
        )

    with client_for(handler) as c:
        with pytest.raises(DuplicateSlipError) as caught:
            c.v1.verify_truemoney_by_payload("wallet-qr", m.V1VerifyOptions(check_duplicate=True))
    assert caught.value.slip.to_dict() == WITH_PHONES


@pytest.mark.parametrize("payload", ["", "x" * 257, None])
def test_empty_or_long_payload_is_refused_before_any_request(payload):
    def handler(request):
        raise AssertionError("no request expected")

    with client_for(handler) as c:
        with pytest.raises(InputError):
            c.verify.truewallet_by_payload(payload)
        with pytest.raises(InputError):
            c.v1.verify_truemoney_by_payload(payload)


async def test_async_by_payload():
    seen = []

    def handler(request):
        seen.append(request)
        if request.url.path.startswith("/v1"):
            return httpx.Response(200, json={"status": 200, "data": BASE})
        return httpx.Response(
            200, json={"success": True, "data": {"amountInSlip": 200.25, "rawSlip": WITH_PHONES}}
        )

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncClient(
        "fixture-secret",
        http=http,
        v1_base_url="https://api.test/v1",
        v2_base_url="https://api.test/v2",
    ) as c:
        v2 = await c.verify.truewallet_by_payload("wallet-qr")
        v1 = await c.v1.verify_truemoney_by_payload("wallet-qr")
    assert v2.raw_slip.sender.phone == "08-xxx-2345"
    assert v1.sender is UNSET
