"""upi-deeplink: build, parse and validate UPI payment deep links.

Implements the URL structure from the NPCI UPI linking specification
(upi://pay?...) with strict validation of payee VPA, amount and currency.
"""

from .core import (
    UpiLinkError,
    UpiPayLink,
    build_pay_link,
    parse_pay_link,
    validate_vpa,
    validate_amount,
)

__all__ = [
    "UpiLinkError",
    "UpiPayLink",
    "build_pay_link",
    "parse_pay_link",
    "validate_vpa",
    "validate_amount",
]

__version__ = "0.1.0"
