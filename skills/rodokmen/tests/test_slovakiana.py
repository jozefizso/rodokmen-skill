import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

_STAV = tempfile.mkdtemp(prefix="slusne_test_")
os.environ["SLUSNE_STAV"] = _STAV
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import slovakiana  # noqa: E402
import slusne  # noqa: E402


class SlovakianaParsingTests(unittest.TestCase):
    def test_house_number_from_street(self):
        self.assertEqual(slovakiana.cislo_domu("-, -/68"), "68")
        self.assertEqual(slovakiana.cislo_domu("-, -/-"), "")
        self.assertEqual(slovakiana.cislo_domu("Hlavná, 12/345"), "345 (Hlavná 12)")

    def test_box_and_sheet_from_name(self):
        self.assertEqual(slovakiana.skatule_harek("Sčítací hárok 556/464, Stará Turá"), ("556", "464"))

    def test_municipality_match_ignores_diacritics(self):
        self.assertEqual(slovakiana.bez_diakritiky("Stará Turá"), slovakiana.bez_diakritiky("stara tura"))


class SlusneRateLimitTests(unittest.TestCase):
    def test_retry_after_seconds_and_http_date(self):
        self.assertEqual(slusne._sekundy("120"), 120)
        ted = time.time()
        self.assertAlmostEqual(slusne._sekundy(str(int(ted) + 300), ted), 300, delta=1)
        self.assertGreater(slusne._sekundy(time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(ted + 7200))), 7000)
        self.assertEqual(slusne._sekundy("nesmysl"), 0)

    def test_retry_after_extends_stop(self):
        with self.assertRaises(slusne.Zastaveno):
            slusne.kontroluj_odpoved("retry.example.org", 429, False, retry_after="10800")
        st = slusne._nacti(slusne._cesta("retry.example.org"))
        self.assertGreater(st["stop"] - time.time(), 10000)

    def test_low_remaining_delays_next_request(self):
        hlavicky = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "45"}
        slusne._hlavicky_limitu("limit.example.org", hlavicky.get)
        st = slusne._nacti(slusne._cesta("limit.example.org"))
        self.assertGreater(st["dalsi_dotaz"] - time.time(), 40)

    def test_slovakiana_uses_crawl_delay(self):
        self.assertEqual(slusne._skupina("content.slovakiana.sk"), ("slovakiana.sk", (10.0, 10.0)))


if __name__ == "__main__":
    unittest.main()
