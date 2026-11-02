import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import cache
import trebon
from trebon import _compose_tiles, _print_rejstrik, magick


HAS_IMAGEMAGICK = bool(shutil.which("magick") or (os.name != "nt" and shutil.which("convert")))


@unittest.skipUnless(HAS_IMAGEMAGICK, "ImageMagick is required by trebon.py")
class ComposeTilesTests(unittest.TestCase):
    def test_composes_variable_size_tiles_without_cropping(self):
        command = magick()
        with tempfile.TemporaryDirectory() as tmp:
            tile_rows = []
            for y, tiles in enumerate(((("5x3", "red"), ("2x2", "blue")),
                                       (("4x1", "green"), ("3x2", "yellow")))):
                row = []
                for x, (geometry, color) in enumerate(tiles):
                    path = os.path.join(tmp, f"tile_{y}_{x}.png")
                    subprocess.run(
                        [command, "-size", geometry, f"xc:{color}", path],
                        check=True,
                    )
                    row.append(path)
                tile_rows.append(row)

            output = os.path.join(tmp, "output.png")
            _compose_tiles(tile_rows, output, tmp, command)

            result = subprocess.run(
                [command, output, "-format", "%wx%h", "info:"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.stdout, "7x5")

    def test_downloaded_tiles_are_cached_and_reused(self):
        command = magick()
        with tempfile.TemporaryDirectory() as tmp:
            tile = subprocess.run(
                [command, "-size", "5x3", "xc:red", "jpg:-"],
                check=True, capture_output=True,
            ).stdout

            def get(path, referer=None, binary=False):
                if "view.php" in path:
                    return 'showImage("image","token"', path
                if "isrv8.cgi" in path:
                    return (tile if path.endswith(".0.1-0-0") else b""), path
                return "", path

            first = os.path.join(tmp, "first.jpg")
            second = os.path.join(tmp, "second.jpg")
            with patch.object(cache, "KOREN", os.path.join(tmp, "cache")), \
                 patch.object(trebon, "get", side_effect=get) as request:
                with redirect_stdout(StringIO()):
                    trebon.snimek("123", "1", first)
                self.assertGreater(request.call_count, 0)
                request.reset_mock()
                with redirect_stdout(StringIO()) as output:
                    trebon.snimek("123", "1", second)
                request.assert_not_called()
                self.assertIn("z cache", output.getvalue())
                self.assertEqual(Path(first).read_bytes(), Path(second).read_bytes())
                self.assertIn("5x3", output.getvalue())


class RejstrikOutputTests(unittest.TestCase):
    def test_empty_result_does_not_claim_the_name_is_absent(self):
        output = StringIO()
        with redirect_stdout(output):
            _print_rejstrik([])

        self.assertIn("není důkaz, že jméno chybí", output.getvalue())


if __name__ == "__main__":
    unittest.main()
