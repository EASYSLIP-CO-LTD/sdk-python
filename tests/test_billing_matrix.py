"""Every billed operation sends once after a read timeout or HTTP 500."""

import asyncio
import copy
import httpx
import pytest
from easyslip import Client, AsyncClient
from easyslip.models import BatchSlip
from easyslip.errors import ApiError, NetworkError, BatchSubmitError
from test_conformance import CASES, invoke

CALLS = {}
# Take one canonical call per operation: the plain success or accepted fixture
# when there is one, so the choice never depends on the order fixtures load in.
for preferred in (True, False):
    for name, case in CASES:
        call = case.get("call", {})
        op = case.get("operation", "")
        stem = name.rsplit("/", 1)[-1].removesuffix(".json")
        if preferred and stem not in ("success", "accepted"):
            continue
        if call and (
            op.startswith("verify.") or op.startswith("v1.verify") or op.startswith("jobs.submit")
        ):
            CALLS.setdefault(op, copy.deepcopy(call["args"]))

CALLS["jobs.submitBankBatch"]["slips"] = [{"payload": "synthetic"}]
CALLS["jobs.submitBankMany"] = CALLS["jobs.submitBankBatch"]
assert len(CALLS) == 17


@pytest.mark.parametrize("operation", sorted(CALLS))
@pytest.mark.parametrize("failure", ["read", "500"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_billed_operation_never_replays(operation, failure, asynchronous):
    sends = 0

    def handler(request):
        nonlocal sends
        sends += 1
        if failure == "read":
            raise httpx.ReadTimeout("after send")
        return httpx.Response(500, json={"message": "server_error"})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            async with AsyncClient("synthetic", http=http) as client:
                with pytest.raises((ApiError, NetworkError, BatchSubmitError)):
                    await (
                        client.jobs.submit_bank_many([BatchSlip(payload="synthetic")])
                        if operation == "jobs.submitBankMany"
                        else invoke(client, operation, CALLS[operation])
                    )

    if asynchronous:
        asyncio.run(run())
    else:
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            with Client("synthetic", http=http) as client:
                with pytest.raises((ApiError, NetworkError, BatchSubmitError)):
                    if operation == "jobs.submitBankMany":
                        client.jobs.submit_bank_many([BatchSlip(payload="synthetic")])
                    else:
                        invoke(client, operation, CALLS[operation])
    assert sends == 1
