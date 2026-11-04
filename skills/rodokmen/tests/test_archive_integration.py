import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import mza
import soal_zoomify


class MzaLimiterTests(unittest.TestCase):
    def test_curl_is_wrapped_without_custom_write_out(self):
        command = mza.slusne._prepis(["curl", "-sS", "--fail", "https://www.mza.cz/iipsrv/test"])
        self.assertIn("slusne.py", command[4])
        self.assertNotIn("-w", command)

    def test_http_429_stops_before_retry(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_response(429)
                self.end_headers()
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp, \
                 patch.object(mza.slusne, "STAV", tmp), \
                 patch.object(mza.slusne, "VOLNE", ()), \
                 patch.object(mza.slusne, "_slozka_", []):
                with self.assertRaises(mza.slusne.Zastaveno):
                    mza.get(f"http://127.0.0.1:{server.server_port}/archive")
                self.assertEqual(requests, ["/archive"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_curl_stop_code_is_not_retried(self):
        result = subprocess.CompletedProcess([], 3, b"", b"stopped")
        with patch.object(mza.shutil, "which", return_value="curl"), patch.object(mza.subprocess, "run", return_value=result) as run:
            with self.assertRaises(SystemExit) as error:
                mza.curl_get("https://www.mza.cz/iipsrv/test")
        self.assertEqual(error.exception.code, 3)
        run.assert_called_once()
        self.assertNotIn("-w", run.call_args.args[0])


@unittest.skipUnless(shutil.which("magick") or (os.name != "nt" and shutil.which("convert")), "ImageMagick required")
class ZoomifyCropTests(unittest.TestCase):
    def test_crop_downloads_only_required_tile(self):
        command = soal_zoomify.magick()
        tile = subprocess.run([command, "-size", "2x2", "xc:red", "jpg:-"], check=True, capture_output=True).stdout
        urls = []
        def get(url):
            urls.append(url)
            if url.endswith("ImageProperties.xml"):
                return b'<IMAGE_PROPERTIES WIDTH="4" HEIGHT="4" TILESIZE="2" />'
            return tile
        with tempfile.TemporaryDirectory() as tmp, patch.object(soal_zoomify, "get", side_effect=get):
            output = str(Path(tmp) / "crop.jpg")
            soal_zoomify.stahni("https://vademecum.nacr.cz/image", 0, output, (0, 0, 0.5, 0.5))
            size = subprocess.run([command, output, "-format", "%wx%h", "info:"], check=True, capture_output=True, text=True).stdout
            self.assertEqual(size, "2x2")
            self.assertEqual(len([url for url in urls if "TileGroup" in url]), 1)


if __name__ == "__main__":
    unittest.main()
