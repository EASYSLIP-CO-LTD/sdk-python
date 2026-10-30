"""Exercise an installed wheel without network access."""

import httpx
from easyslip import Client, EasySlip, EasySlipError
from easyslip.errors import ApiError


def respond(request: httpx.Request) -> httpx.Response:
    assert request.headers["Authorization"] == "Bearer synthetic-consumer-key"
    return httpx.Response(200, json={"data": []})


with httpx.Client(transport=httpx.MockTransport(respond)) as http:
    with Client("synthetic-consumer-key", http=http) as client:
        assert client.banks.list().items == []
assert EasySlip is Client
assert issubclass(ApiError, EasySlipError)
print("Installed artifact: offline request, alias and errors PASS")
