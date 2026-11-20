"""Builds Clubhouse's brand images from the emblem in packaging/brand/clubhouse-emblem.webp.

Writes:
  packaging/clubhouse.ico + .png   app and window icon: the emblem on its own dark tile
  app/ui/brand/emblem.png          transparent cut-out for the top bar (dark background keyed out)
  app/ui/brand/emblem-lg.png       larger cut-out for the welcome and loading screens
  docs/logo.png                    README logo (emblem on its dark background)
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).with_name("brand") / "clubhouse-emblem.webp"
OUT = Path(__file__).with_name("clubhouse.ico")
UI = ROOT / "app" / "ui" / "brand"


def cutout(src: Image.Image) -> Image.Image:
    """Key out the near-black background: alpha from brightness, so dark textured backdrop disappears while the
    orange and silver strokes stay solid. Cropped to the emblem."""
    rgb = src.convert("RGB")
    lum = ImageChops.lighter(ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")), rgb.getchannel("B"))
    alpha = lum.point(lambda v: 0 if v < 46 else 255 if v > 86 else int((v - 46) * 255 / 40))
    alpha = alpha.filter(ImageFilter.MedianFilter(3))
    im = rgb.convert("RGBA"); im.putalpha(alpha)
    return im.crop(alpha.point(lambda v: 255 if v > 40 else 0).getbbox())


def tile(src: Image.Image, size: int) -> Image.Image:
    """The emblem, centered on its own dark background in a rounded square (the app icon)."""
    rgb = src.convert("RGB")
    lum = ImageChops.lighter(ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")), rgb.getchannel("B"))
    l, t, r, b = lum.point(lambda v: 255 if v > 70 else 0).getbbox()
    side = int(max(r - l, b - t) * 1.04)
    cx, cy = (l + r) // 2, (t + b) // 2
    sq = rgb.crop((cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2)).resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * .18), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(sq, (0, 0), mask)
    return out


def fit(im: Image.Image, h: int) -> Image.Image:
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


if __name__ == "__main__":
    src = Image.open(SRC)
    big = tile(src, 1024)
    big.save(OUT, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    big.resize((256, 256), Image.LANCZOS).save(OUT.with_suffix(".png"))
    UI.mkdir(parents=True, exist_ok=True)
    cut = cutout(src)
    fit(cut, 120).save(UI / "emblem.png", optimize=True)        # shown at ~52 px tall, sharp on high-DPI screens
    fit(cut, 420).save(UI / "emblem-lg.png", optimize=True)
    (ROOT / "docs").mkdir(exist_ok=True)
    src.convert("RGB").resize((420, 420), Image.LANCZOS).save(ROOT / "docs" / "logo.png", optimize=True)
    print("wrote", OUT, UI / "emblem.png", UI / "emblem-lg.png", ROOT / "docs" / "logo.png")
