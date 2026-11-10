# upi-deeplink

[![CI](https://github.com/abhiranjan-ar/upi-deeplink/actions/workflows/ci.yml/badge.svg)](https://github.com/abhiranjan-ar/upi-deeplink/actions/workflows/ci.yml)

Build, parse and validate UPI payment deep links (`upi://pay?...`) following
the `pay` operation of the NPCI UPI linking specification (v1.6). Pure Python,
zero dependencies.

UPI apps (Google Pay, PhonePe, Paytm, BHIM, bank apps) respond to these
links: scanning a QR or opening the URL pre-fills a payment. This library
gives backend and tooling code a safe way to generate those links and to
check links received from elsewhere.

## Why not string formatting

Hand-built links (`f"upi://pay?pa={vpa}&pn={name}"`) silently break on
unencoded spaces and `&` in payee names, accept malformed VPAs, and let
amounts like `10.001` or `0` through to a payment app. This library validates
every field before a link is built or trusted, and refuses links it cannot
validate.

## Install

```bash
pip install git+https://github.com/abhiranjan-ar/upi-deeplink.git
```

## Usage

```python
from upi_deeplink import build_pay_link, parse_pay_link

link = build_pay_link(
    pa="merchant@okhdfcbank",   # payee VPA (mandatory)
    pn="Corner Store",          # payee name (mandatory)
    am="199.50",                # optional amount, max 2 decimals
    tn="Order 1234",            # optional note
    tr="ORD1234",               # optional reference id
)
# upi://pay?pa=merchant%40okhdfcbank&pn=Corner%20Store&cu=INR&am=199.50&tn=Order%201234&tr=ORD1234

parsed = parse_pay_link(link)
assert parsed.pa == "merchant@okhdfcbank"
assert parsed.am == "199.50"
```

Validation rejects malformed VPAs, non-positive or over-precise amounts,
non-INR currencies, missing mandatory fields, duplicate parameters and
non-`pay` operations. Unknown query parameters round-trip through
`UpiPayLink.extra` instead of being silently dropped.

See `examples/invoice_link.py` for a small end-to-end example.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

CI runs the suite on every push and pull request across Python 3.9-3.12
(GitHub Actions).

## Scope and roadmap

- `pay` operation only (request-money `collect` is deprecated in apps)
- Enforces the spec's mandatory fields (`pa`, `pn`), INR-only currency and
  decimal amounts; merchant/PSP tags (`orgid`, `mid`, `msid`, `mtid`,
  `sign`) round-trip through `UpiPayLink.extra` and are never generated
- Planned: QR payload helpers (`upi://pay` inside Bharat QR), amount
  limits per NPCI circulars, stricter `mode`/`purpose` code tables

## License

MIT - see LICENSE.
