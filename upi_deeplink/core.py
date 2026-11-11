"""Core helpers for UPI deep links (NPCI UPI linking specification).

A UPI deep link has the shape::

    upi://pay?pa=payee@bank&pn=Payee%20Name&am=10.00&cu=INR&tn=Note

Mandatory parameters for ``pay`` are ``pa`` (payee VPA) and ``pn``
(payee name). ``am`` (amount) is optional but, when present, must be a
positive decimal with at most two fraction digits. ``cu`` defaults to
INR, currently the only currency UPI settles in.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional
from urllib.parse import quote, urlsplit, parse_qsl

UPI_SCHEME = "upi"
PAY_OPERATION = "pay"
DEFAULT_CURRENCY = "INR"

# VPA (virtual payment address): local-part @ PSP handle.
# The local part allows letters, digits, dot, hyphen and underscore.
_VPA_RE = re.compile(r"^[A-Za-z0-9._-]{1,}@[A-Za-z]{2,}[A-Za-z0-9]*$")

_AMOUNT_RE = re.compile(r"[0-9]+(\.[0-9]{1,2})?")

# Query keys defined by the NPCI linking spec for the pay operation.
_KNOWN_KEYS = {
    "pa",  # payee VPA (mandatory)
    "pn",  # payee name (mandatory)
    "mc",  # merchant code
    "tid", # transaction id
    "tr",  # transaction reference id
    "tn",  # transaction note
    "am",  # amount
    "mam", # minimum amount
    "cu",  # currency
    "url", # bill/invoice URL
    "mode",# mode (e.g. 04 for QR intent)
    "purpose",  # purpose code
}


class UpiLinkError(ValueError):
    """Raised when a UPI deep link or one of its fields is invalid."""


def validate_vpa(vpa: str) -> str:
    """Return the VPA unchanged if valid, else raise UpiLinkError."""
    if not isinstance(vpa, str) or not _VPA_RE.fullmatch(vpa):
        raise UpiLinkError(
            "invalid payee VPA %r: expected local@handle, e.g. name@okicici" % (vpa,)
        )
    return vpa


def validate_amount(amount: str) -> str:
    """Return the amount string if valid, else raise UpiLinkError.

    Amounts must be positive and carry at most two decimal places,
    matching how UPI apps render paisa.
    """
    if not isinstance(amount, str) or not _AMOUNT_RE.fullmatch(amount):
        raise UpiLinkError(
            "invalid amount %r: use up to two decimal places, e.g. '10.00'" % (amount,)
        )
    try:
        value = Decimal(amount)
    except InvalidOperation as exc:  # defensive; regex already gates this
        raise UpiLinkError("invalid amount %r" % (amount,)) from exc
    if value <= 0:
        raise UpiLinkError("amount must be positive, got %r" % (amount,))
    return amount


@dataclass
class UpiPayLink:
    """Structured form of a UPI ``pay`` deep link."""

    pa: str
    pn: str
    am: Optional[str] = None
    cu: str = DEFAULT_CURRENCY
    tn: Optional[str] = None
    tr: Optional[str] = None
    tid: Optional[str] = None
    mc: Optional[str] = None
    mam: Optional[str] = None
    url: Optional[str] = None
    mode: Optional[str] = None
    purpose: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)

    def to_url(self) -> str:
        return build_pay_link(
            pa=self.pa,
            pn=self.pn,
            am=self.am,
            cu=self.cu,
            tn=self.tn,
            tr=self.tr,
            tid=self.tid,
            mc=self.mc,
            mam=self.mam,
            url=self.url,
            mode=self.mode,
            purpose=self.purpose,
            extra=self.extra or None,
        )


def build_pay_link(
    *,
    pa: str,
    pn: str,
    am: Optional[str] = None,
    cu: str = DEFAULT_CURRENCY,
    tn: Optional[str] = None,
    tr: Optional[str] = None,
    tid: Optional[str] = None,
    mc: Optional[str] = None,
    mam: Optional[str] = None,
    url: Optional[str] = None,
    mode: Optional[str] = None,
    purpose: Optional[str] = None,
    extra: Optional[Dict[str, str]] = None,
) -> str:
    """Build a validated ``upi://pay`` deep link.

    Mandatory fields are ``pa`` (payee VPA) and ``pn`` (payee name).
    Values are URL-encoded per the linking spec; spaces become ``%20``.
    """
    validate_vpa(pa)
    if not isinstance(pn, str) or not pn.strip():
        raise UpiLinkError("payee name (pn) is mandatory")
    if am is not None:
        validate_amount(am)
    if mam is not None:
        validate_amount(mam)
    if cu != DEFAULT_CURRENCY:
        raise UpiLinkError("only INR is supported for UPI payments, got %r" % (cu,))

    params: Dict[str, str] = {"pa": pa, "pn": pn.strip(), "cu": cu}
    for key, value in (
        ("am", am),
        ("mam", mam),
        ("tn", tn),
        ("tr", tr),
        ("tid", tid),
        ("mc", mc),
        ("url", url),
        ("mode", mode),
        ("purpose", purpose),
    ):
        if value is not None:
            params[key] = value
    if extra:
        for key, value in extra.items():
            if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", key):
                raise UpiLinkError("extra parameter keys must be lowercase identifiers")
            if key in _KNOWN_KEYS:
                raise UpiLinkError("use the named argument for parameter %r" % (key,))
            if not isinstance(value, str):
                raise UpiLinkError("extra parameter %r must have a string value" % (key,))
            params[key] = value

    query = "&".join(
        "%s=%s" % (key, quote(value, safe="")) for key, value in params.items()
    )
    return "%s://%s?%s" % (UPI_SCHEME, PAY_OPERATION, query)


def parse_pay_link(link: str) -> UpiPayLink:
    """Parse and validate a ``upi://pay`` deep link into an UpiPayLink."""
    parts = urlsplit(link)
    scheme = parts.scheme.lower()
    if scheme != UPI_SCHEME:
        raise UpiLinkError("expected scheme 'upi', got %r" % (parts.scheme,))
    # urlsplit puts 'pay' in netloc for upi://pay?... links.
    operation = (parts.netloc or parts.path).lower()
    if operation != PAY_OPERATION:
        raise UpiLinkError("unsupported operation %r: only 'pay' is handled" % (operation,))

    params: Dict[str, str] = {}
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        key = key.lower()
        if key in params:
            raise UpiLinkError("duplicate parameter %r" % (key,))
        params[key] = value

    pa = params.pop("pa", None)
    pn = params.pop("pn", None)
    if not pa:
        raise UpiLinkError("missing mandatory parameter 'pa' (payee VPA)")
    if not pn or not pn.strip():
        raise UpiLinkError("missing mandatory parameter 'pn' (payee name)")
    validate_vpa(pa)

    am = params.pop("am", None)
    if am is not None:
        validate_amount(am)
    mam = params.pop("mam", None)
    if mam is not None:
        validate_amount(mam)

    cu = params.pop("cu", DEFAULT_CURRENCY)
    if cu != DEFAULT_CURRENCY:
        raise UpiLinkError("only INR is supported for UPI payments, got %r" % (cu,))

    known = {k: params.pop(k) for k in list(params) if k in _KNOWN_KEYS}
    return UpiPayLink(
        pa=pa,
        pn=pn,
        am=am,
        cu=cu,
        mam=mam,
        tn=known.get("tn"),
        tr=known.get("tr"),
        tid=known.get("tid"),
        mc=known.get("mc"),
        url=known.get("url"),
        mode=known.get("mode"),
        purpose=known.get("purpose"),
        # parse_qsl already decoded percent escapes exactly once. Preserve
        # extension values (including opaque PSP signatures) without decoding
        # them again or silently discarding them.
        extra=params,
    )
