# upi-deeplink

Build, parse and validate UPI payment deep links (`upi://pay?...`) per the
NPCI UPI linking specification. Pure Python, zero dependencies.

UPI apps (Google Pay, PhonePe, Paytm, BHIM, bank apps) respond to these
links: scanning a QR or opening the URL pre-fills a payment. This library
gives backend and tooling code a safe way to generate those links and to
check links received from elsewhere.

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

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Scope and roadmap

- `pay` operation only (request-money `collect` is deprecated in apps)
- Planned: QR payload helpers (`upi://pay` inside Bharat QR), amount
  limits per NPCI circulars, stricter `mode`/`purpose` code tables

## License

MIT - see [LICENSE](LICENSE).
