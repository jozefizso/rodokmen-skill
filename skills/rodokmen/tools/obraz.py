"""Společné pomocné funkce pro práci s obrázky (hledání ImageMagicku).

Ostatní nástroje ho importují takto (`python3 -I` nepřidává složku skriptu do cesty, proto ji přidáme sami):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from obraz import magick
"""
import glob, os, shutil, sys


def najdi_magick():
    """Cesta k ImageMagicku, nebo None. ImageMagick 7 (magick), jinak 6 (convert) – ten ale ne na Windows, kde je convert.exe jiný program."""
    return (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
            or (os.name != "nt" and shutil.which("convert")) or None)


def magick():
    """Cesta k ImageMagicku; když chybí, skončí hned (před stahováním) srozumitelnou hláškou."""
    m = najdi_magick()
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, "
                 "Windows: winget install ImageMagick.ImageMagick a restart Claude Code) a spusť nástroj znovu.")
    return m
