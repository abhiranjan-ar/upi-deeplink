import unittest

from upi_deeplink import (
    UpiLinkError,
    build_pay_link,
    parse_pay_link,
    validate_amount,
    validate_vpa,
)

class TestValidateVpa(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_vpa("abhishek@okicici"), "abhishek@okicici")
        self.assertEqual(validate_vpa("shop.01@ybl"), "shop.01@ybl")

    def test_invalid(self):
        for bad in ("", "noatsign", "@ybl", "a@", "x y@ybl", "name@"):
            with self.assertRaises(UpiLinkError, msg=bad):
                validate_vpa(bad)

class TestValidateAmount(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_amount("10"), "10")
        self.assertEqual(validate_amount("10.00"), "10.00")
        self.assertEqual(validate_amount("0.01"), "0.01")

    def test_invalid(self):
        for bad in ("", "0", "0.00", "-5", "10.001", "abc", "1,000", ".5", "10.", "1 0"):
            with self.assertRaises(UpiLinkError, msg=bad):
                validate_amount(bad)

class TestBuildPayLink(unittest.TestCase):
    def test_minimal(self):
        link = build_pay_link(pa="abhishek@okicici", pn="Abhishek Ranjan")
        self.assertTrue(link.startswith("upi://pay?"))
        self.assertIn("pa=abhishek%40okicici", link)
        self.assertIn("pn=Abhishek%20Ranjan", link)
        self.assertIn("cu=INR", link)
        self.assertNotIn("am=", link)

    def test_full(self):
        link = build_pay_link(
            pa="merchant@okhdfcbank",
            pn="Corner Store",
            am="199.50",
            tn="Order 1234",
            tr="ORD1234",
        )
        self.assertIn("am=199.50", link)
        self.assertIn("tn=Order%201234", link)
        self.assertIn("tr=ORD1234", link)

    def test_mam_validated_and_included(self):
        link = build_pay_link(pa="m@okhdfcbank", pn="M", am="50.00", mam="50.00")
        self.assertIn("mam=50.00", link)
        with self.assertRaises(UpiLinkError):
            build_pay_link(pa="m@okhdfcbank", pn="M", mam="10.001")

    def test_extra_params_included(self):
        link = build_pay_link(pa="a@okicici", pn="N", extra={"xref": "123"})
        self.assertIn("xref=123", link)

    def test_extra_cannot_shadow_known_keys(self):
        with self.assertRaises(UpiLinkError):
            build_pay_link(pa="a@okicici", pn="N", extra={"pa": "b@okicici"})
        with self.assertRaises(UpiLinkError):
            build_pay_link(pa="a@okicici", pn="N", am="1", extra={"am": "2"})

    def test_round_trip(self):
        link = build_pay_link(
            pa="a.b-c_d@okaxis", pn="Round Trip", am="42.42", tn="t n"
        )
        parsed = parse_pay_link(link)
        self.assertEqual(parsed.pa, "a.b-c_d@okaxis")
        self.assertEqual(parsed.pn, "Round Trip")
        self.assertEqual(parsed.am, "42.42")
        self.assertEqual(parsed.cu, "INR")
        self.assertEqual(parsed.tn, "t n")

    def test_round_trip_special_characters(self):
        link = build_pay_link(pa="cafe@okicici", pn="Cafe & Sons (Main)")
        parsed = parse_pay_link(link)
        self.assertEqual(parsed.pn, "Cafe & Sons (Main)")

    def test_merchant_fields_round_trip(self):
        link = build_pay_link(
            pa="merchant@okhdfcbank",
            pn="Merchant",
            tid="TID123",
            mc="5411",
            tr="ORD9",
            url="https://shop.example/invoice/9",
            mode="04",
            purpose="00",
        )
        parsed = parse_pay_link(link)
        self.assertEqual(parsed.tid, "TID123")
        self.assertEqual(parsed.mc, "5411")
        self.assertEqual(parsed.tr, "ORD9")
        self.assertEqual(parsed.url, "https://shop.example/invoice/9")
        self.assertEqual(parsed.mode, "04")
        self.assertEqual(parsed.purpose, "00")

    def test_rejects_bad_inputs(self):
        with self.assertRaises(UpiLinkError):
            build_pay_link(pa="bad", pn="Name")
        with self.assertRaises(UpiLinkError):
            build_pay_link(pa="name@okicici", pn=" ")
        with self.assertRaises(UpiLinkError):
            build_pay_link(pa="name@okicici", pn="Name", am="0")
        with self.assertRaises(UpiLinkError):
            build_pay_link(pa="name@okicici", pn="Name", cu="USD")

class TestParsePayLink(unittest.TestCase):
    def test_parse_typical_app_link(self):
        parsed = parse_pay_link(
            "upi://pay?pa=merchant@okhdfcbank&pn=Corner%20Store&am=10.00&cu=INR"
        )
        self.assertEqual(parsed.pa, "merchant@okhdfcbank")
        self.assertEqual(parsed.pn, "Corner Store")
        self.assertEqual(parsed.am, "10.00")

    def test_unknown_params_preserved_in_extra(self):
        parsed = parse_pay_link("upi://pay?pa=a@okicici&pn=N&xref=123")
        self.assertEqual(parsed.extra, {"xref": "123"})

    def test_blank_mandatory_params_rejected(self):
        with self.assertRaises(UpiLinkError):
            parse_pay_link("upi://pay?pa=&pn=N")
        with self.assertRaises(UpiLinkError):
            parse_pay_link("upi://pay?pa=a@okicici&pn=")

    def test_invalid_amount_rejected(self):
        with self.assertRaises(UpiLinkError):
            parse_pay_link("upi://pay?pa=a@okicici&pn=N&am=10.001")
        with self.assertRaises(UpiLinkError):
            parse_pay_link("upi://pay?pa=a@okicici&pn=N&mam=0")

    def test_rejects_bad_links(self):
        for bad in (
            "https://pay?pa=a@okicici&pn=N",
            "upi://collect?pa=a@okicici&pn=N",
            "upi://pay?pn=N",
            "upi://pay?pa=a@okicici",
            "upi://pay?pa=a@okicici&pn=N&am=0",
            "upi://pay?pa=a@okicici&pn=N&cu=USD",
            "upi://pay?pa=a@okicici&pn=N&pa=b@okicici",
        ):
            with self.assertRaises(UpiLinkError, msg=bad):
                parse_pay_link(bad)

class TestValidationRegressions(unittest.TestCase):
    def test_extra_cannot_bypass_optional_field_validation(self):
        for key, value in (("am", "-5"), ("mam", "0"), ("cu", "USD"),
                           ("tn", "note"), ("mode", "04")):
            with self.subTest(key=key), self.assertRaises(UpiLinkError):
                build_pay_link(pa="a@okicici", pn="A", extra={key: value})

    def test_extra_keys_cannot_inject_query_parameters(self):
        for key in ("Cu", "AM", "x&am", "x=1", "", "x#fragment", "x%26am"):
            with self.subTest(key=key), self.assertRaises(UpiLinkError):
                build_pay_link(pa="a@okicici", pn="A", extra={key: "-5"})

    def test_extra_values_must_be_strings(self):
        for value in (None, 10, True):
            with self.subTest(value=value), self.assertRaises(UpiLinkError):
                build_pay_link(pa="a@okicici", pn="A", extra={"xref": value})

    def test_extension_values_are_decoded_exactly_once(self):
        for value in ("literal%2F", "%26am%3D999", "a+b", "100% done", "A&B=1"):
            with self.subTest(value=value):
                link = build_pay_link(pa="a@okicici", pn="A", extra={"xref": value})
                parsed = parse_pay_link(link)
                self.assertEqual(parsed.extra["xref"], value)
                self.assertEqual(parse_pay_link(parsed.to_url()).extra["xref"], value)

    def test_psp_signature_preserved_as_opaque_extra(self):
        parsed = parse_pay_link("upi://pay?pa=a@okicici&pn=A&sign=abc%2Bdef%2F%3D")
        self.assertEqual(parsed.extra["sign"], "abc+def/=")
        self.assertEqual(parse_pay_link(parsed.to_url()).extra["sign"], "abc+def/=")

    def test_amount_rejects_trailing_newline_and_non_ascii_digits(self):
        for amount in ("10\n", "10\r", "١٠", "１２.５０", 10, None):
            with self.subTest(amount=amount), self.assertRaises(UpiLinkError):
                validate_amount(amount)

    def test_vpa_rejects_trailing_newline(self):
        with self.assertRaises(UpiLinkError):
            validate_vpa("a@okicici\n")

    def test_whitespace_only_payee_name_rejected(self):
        with self.assertRaises(UpiLinkError):
            parse_pay_link("upi://pay?pa=a@okicici&pn=%20%20")

if __name__ == "__main__":
    unittest.main()
