"""Draws Clubhouse's app icon (a baseball on a dark tile) and writes packaging/clubhouse.ico."""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).with_name("clubhouse.ico")
S = 1024


def draw(size: int = S) -> Image.Image:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = size * 0.2
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=(14, 18, 28, 255))
    d.rounded_rectangle([size * .04, size * .04, size * .96, size * .96], radius=r * .85, outline=(196, 32, 50, 255), width=int(size * .025))
    c, br = size / 2, size * .34
    d.ellipse([c - br, c - br, c + br, c + br], fill=(246, 244, 238, 255))
    # two curved seams with stitches
    red, w = (200, 30, 45, 255), int(size * .022)
    for side in (-1, 1):
        cx = c + side * br * 1.55
        box = [cx - br * 1.08, c - br * 1.08, cx + br * 1.08, c + br * 1.08]
        start, end = (140, 220) if side > 0 else (-40, 40)
        d.arc(box, start, end, fill=red, width=w)
        import math
        for k in range(7):
            a = math.radians(start + (end - start) * (k + .5) / 7)
            px, py = cx + br * 1.08 * math.cos(a), c + br * 1.08 * math.sin(a)
            nx, ny = math.cos(a), math.sin(a)
            tx, ty = -ny, nx
            L = size * .028
            d.line([px - nx * L + tx * L * .6, py - ny * L + ty * L * .6, px + nx * L + tx * L * .6, py + ny * L + ty * L * .6], fill=red, width=int(w * .7))
    return im


if __name__ == "__main__":
    big = draw()
    big.save(OUT, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    big.resize((256, 256), Image.LANCZOS).save(OUT.with_suffix(".png"))
    print("wrote", OUT)
