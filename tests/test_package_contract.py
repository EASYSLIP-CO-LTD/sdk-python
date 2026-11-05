"""The installed package exposes the documented defaults and error hierarchy."""

from pathlib import Path
import tomllib
from easyslip import Client, EasySlip, EasySlipError
from easyslip.errors import ApiError, InputError, NetworkError
from easyslip.webhooks import SIGNATURE_HEADER

ROOT = Path(__file__).parents[1]


def test_defaults_and_environment(monkeypatch, tmp_path):
    for name in ("EASYSLIP_API_KEY", "EASYSLIP_V1_BASE_URL", "EASYSLIP_V2_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    key = tmp_path / "key"
    key.write_text("fixture-key\n")
    monkeypatch.setenv("EASYSLIP_API_KEY_FILE", str(key))
    with Client() as client:
        assert client._v1._base == "https://api.easyslip.com/v1"
        assert client._v2._base == "https://api.easyslip.com/v2"
        assert client._v2._agent.startswith("easyslip-python/") and " python/" in client._v2._agent
        assert "fixture-key" not in repr(client)
    assert EasySlip is Client
    assert SIGNATURE_HEADER == "X-EasySlip-Signature"
    for error in (ApiError, InputError, NetworkError):
        assert issubclass(error, EasySlipError)


def test_package_metadata_and_license():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert data["name"] == "easyslip-sdk"
    assert data["license"] == "MIT"
    assert data["authors"] == [{"name": "EasySlip Co., Ltd."}]
    assert "Copyright (c) 2026 EasySlip Co., Ltd." in (ROOT / "LICENSE").read_text()
    url = "https://github.com/EASYSLIP-CO-LTD/sdk-python"
    assert data["urls"] == {"Repository": url, "Homepage": url, "Issues": url + "/issues"}
    for name in ("README.md", "README.th.md"):
        text = (ROOT / name).read_text()
        assert "pip install easyslip-sdk" in text
        assert "from easyslip import Client" in text
        assert url in text
    assert (ROOT / "src/easyslip/py.typed").exists()
