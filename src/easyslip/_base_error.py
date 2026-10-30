"""Root error for this distribution."""


class EasySlipError(Exception):
    """Base class for API and transport failures."""


SDKError = EasySlipError
