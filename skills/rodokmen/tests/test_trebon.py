import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

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


class RejstrikOutputTests(unittest.TestCase):
    def test_empty_result_does_not_claim_the_name_is_absent(self):
        output = StringIO()
        with redirect_stdout(output):
            _print_rejstrik([])

        self.assertIn("není důkaz, že jméno chybí", output.getvalue())


if __name__ == "__main__":
    unittest.main()
