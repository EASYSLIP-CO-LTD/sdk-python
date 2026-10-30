"""Typed sync and async clients for the public slip API."""

from .client import Client as Client, AsyncClient as AsyncClient
from ._codec import UNSET as UNSET
from ._base_error import SDKError as SDKError

__version__ = "1.0.0"  # x-release-please-version

from ._base_error import EasySlipError as EasySlipError

EasySlip = Client
