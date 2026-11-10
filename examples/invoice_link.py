"""Generate a UPI payment link for an invoice and verify a received link.

Run from the repository root:  python examples/invoice_link.py
"""

from upi_deeplink import UpiLinkError, build_pay_link, parse_pay_link


def main():
    link = build_pay_link(
        pa="merchant@okhdfcbank",
        pn="Corner Store",
        am="199.50",
        tn="Invoice INV-2026-0091",
        tr="INV-2026-0091",
        url="https://shop.example/invoices/INV-2026-0091",
    )
    print("Payment link:", link)

    # Later: a link received from a customer or another system.
    received = (
        "upi://pay?pa=merchant%40okhdfcbank&pn=Corner%20Store"
        "&am=199.50&cu=INR&tr=INV-2026-0091"
    )
    try:
        parsed = parse_pay_link(received)
    except UpiLinkError as exc:
        print("Rejected invalid link:", exc)
        return
    print("Payee:", parsed.pn, "<" + parsed.pa + ">")
    print("Amount: INR", parsed.am, "| Reference:", parsed.tr)


if __name__ == "__main__":
    main()
