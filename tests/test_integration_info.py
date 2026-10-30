"""Read-only account connectivity check, enabled explicitly by the caller."""

import os
import pytest
from easyslip import Client, AsyncClient

pytestmark = pytest.mark.skipif(
    os.environ.get("EASYSLIP_INTEGRATION") != "1", reason="EASYSLIP_INTEGRATION is not enabled"
)


def test_account_info():
    with Client() as client:
        assert client.get_info().meta.status == 200


async def test_async_account_info():
    async with AsyncClient() as client:
        assert (await client.get_info()).meta.status == 200
