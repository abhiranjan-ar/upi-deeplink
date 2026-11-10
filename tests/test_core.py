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
        for bad in ("", "0", "0.00", "-5", "10.001", "abc", "1,000"):
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


if __name__ == "__main__":
    unittest.main()
