"""App icons: the double dash that opens every Midjourney parameter.

Drawn from primitives so there's no font dependency and it stays crisp at
every size. Dark ground, light bars.
"""

import os

from PIL import Image, ImageDraw

OUT = "/home/claude/mjref/icons"
GROUND = (14, 14, 14)
MARK = (236, 235, 231)
SS = 4  # supersample factor


def draw(size, pad_ratio, rounded):
    s = size * SS
    img = Image.new("RGB", (s, s), GROUND)
    d = ImageDraw.Draw(img)

    if rounded:
        # rounded-square ground, transparent corners baked to ground colour
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=GROUND + (255,))

    pad = s * pad_ratio
    bar_w = s - pad * 2
    bar_h = s * 0.085
    gap = s * 0.105
    cy = s / 2
    top = cy - gap / 2 - bar_h
    bot = cy + gap / 2

    for y in (top, bot):
        d.rounded_rectangle(
            [pad, y, pad + bar_w, y + bar_h],
            radius=bar_h / 2,
            fill=MARK + ((255,) if rounded else ()),
        )

    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)

    jobs = [
        ("icon-192.png", 192, 0.22, True),
        ("icon-512.png", 512, 0.22, True),
        ("apple-touch-icon.png", 180, 0.22, False),   # iOS masks its own corners
        ("icon-maskable-512.png", 512, 0.30, False),  # extra safe-zone padding
    ]

    for name, size, pad, rounded in jobs:
        img = draw(size, pad, rounded)
        if img.mode == "RGBA":
            flat = Image.new("RGB", img.size, GROUND)
            flat.paste(img, mask=img.split()[3])
            img = flat
        path = os.path.join(OUT, name)
        img.save(path, "PNG", optimize=True)
        print("%-26s %3dpx  %5.1f KB" % (name, size, os.path.getsize(path) / 1024))


if __name__ == "__main__":
    main()
