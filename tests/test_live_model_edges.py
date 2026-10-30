"""Sanitized model regressions found by cached dev sample smoke tests."""

from easyslip._codec import UNSET, decode
from easyslip.models import SlipReceiverBank


def test_receiver_bank_can_be_present_without_an_id():
    bank = decode(SlipReceiverBank, {})
    assert bank.id is UNSET
    assert bank.to_dict() == {}
