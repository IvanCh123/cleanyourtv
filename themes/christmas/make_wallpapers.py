#!/usr/bin/env python3
"""Draws themes/christmas/wallpapers/001-004.jpg from nothing but code, in the flat style of the Halloween
theme's haunted house: a log cabin with warm windows under the moon, a decorated tree on a snowy hill, a
village at night with a snowman, and a sleigh crossing the moon over a pine forest. No photos, artwork or
fonts are used, so the pictures are original (CC0, like the Halloween illustration) and anyone can redraw them.

    python3 make_wallpapers.py           # needs Pillow and NumPy; the seeds below give the same pictures
    python3 make_wallpapers.py <folder>  # write them somewhere else, to look before replacing

Kept dark where Home draws on top (see themes/README.md, Wallpapers): the clock sits top left and the dock
along the bottom, so the subject stands up and to the right and the bottom third fades toward black.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
S = 2                                   # draw at 2x, scale down for clean edges
w, h = W * S, H * S
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "wallpapers"

SNOW = (226, 234, 246)                  # moonlit snow on roofs, branches and the snowman
SNOW_SHADE = (176, 192, 220)
FAR = (104, 122, 166)                   # snowy ground at night: lighter far away, darker up close
MID = (78, 94, 136)
NEAR = (50, 62, 100)
PINE = (18, 52, 44)
PINE_DARK = (10, 32, 30)
WARM = (255, 204, 102)
WARM_DEEP = (247, 148, 60)
WOOD = (74, 44, 36)
WOOD_DARK = (52, 30, 26)
BULBS = [(255, 82, 82), (255, 210, 80), (110, 200, 255), (120, 230, 140), (255, 150, 220)]


def px(v):
    return int(round(v * S))


def sky(top, mid, bottom):
    ys = np.linspace(0, 1, h)[:, None]
    stops = [(0.0, top), (0.55, mid), (1.0, bottom)]
    img = np.zeros((h, w, 3))
    for c in range(3):
        col = np.interp(ys, [p for p, _ in stops], [s[c] for _, s in stops])
        img[:, :, c] = np.broadcast_to(col, (h, w))
    return Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")


def glow(base, cx, cy, radius, color, strength):
    """A soft round light: a blurred disc added on top."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = px(radius)
    d.ellipse([px(cx) - r, px(cy) - r, px(cx) + r, px(cy) + r], fill=color + (int(255 * strength),))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.6))
    base.alpha_composite(layer)


def stars(base, rng, n, y_max):
    d = ImageDraw.Draw(base)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, y_max) ** 1.15 / y_max ** 0.15
        r = rng.choice([1.5, 2.0, 2.8], p=[0.55, 0.32, 0.13])
        a = int(rng.uniform(150, 240))
        d.ellipse([px(x - r), px(y - r), px(x + r), px(y + r)], fill=(235, 240, 255, a))


def moon(base, cx, cy, r):
    glow(base, cx, cy, r * 2.6, (210, 225, 255), 0.22)
    d = ImageDraw.Draw(base)
    d.ellipse([px(cx - r), px(cy - r), px(cx + r), px(cy + r)], fill=(250, 246, 226, 255))
    for dx, dy, cr in [(-0.35, -0.2, 0.16), (0.2, 0.3, 0.22), (0.35, -0.35, 0.1)]:
        d.ellipse([px(cx + dx * r - cr * r), px(cy + dy * r - cr * r), px(cx + dx * r + cr * r),
                   px(cy + dy * r + cr * r)], fill=(232, 228, 206, 255))


def hill(base, y0, amp, phase, color, freq=1.0):
    """A rolling snowy ridge from y0 down to the bottom edge."""
    pts = []
    for i in range(0, W + 21, 20):
        t = i / W
        y = y0 + amp * math.sin(t * math.pi * 1.6 * freq + phase) + amp * 0.35 * math.sin(t * math.pi * 4.3 + phase * 2)
        pts.append((px(i), px(y)))
    pts += [(px(W + 20), h), (px(-20), h)]
    ImageDraw.Draw(base).polygon(pts, fill=color + (255,))


def pine(base, x, ground, height, color=PINE, snow=True):
    d = ImageDraw.Draw(base)
    width = height * 0.52
    d.rectangle([px(x - height * 0.035), px(ground - height * 0.12), px(x + height * 0.035), px(ground)],
                fill=WOOD_DARK + (255,))
    tiers = 4
    for k in range(tiers):
        top = ground - height + k * height * 0.2
        bottom = top + height * 0.42
        half = width * (0.38 + 0.2 * k) / 1.0 * 0.62
        d.polygon([(px(x), px(top)), (px(x + half), px(bottom)), (px(x - half), px(bottom))], fill=color + (255,))
        if snow:
            # a snow cap along each tier's lower edge
            d.polygon([(px(x - half), px(bottom)), (px(x - half * 0.55), px(bottom - height * 0.045)),
                       (px(x), px(bottom - height * 0.01)), (px(x + half * 0.5), px(bottom - height * 0.05)),
                       (px(x + half), px(bottom))], fill=SNOW + (235,))
    if snow:
        d.polygon([(px(x), px(ground - height)), (px(x + width * 0.08), px(ground - height * 0.86)),
                   (px(x - width * 0.08), px(ground - height * 0.86))], fill=SNOW + (255,))


def window(base, x, y, ww, wh, cross=True):
    glow(base, x + ww / 2, y + wh / 2, max(ww, wh) * 1.3, WARM_DEEP, 0.28)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([px(x), px(y), px(x + ww), px(y + wh)], radius=px(min(ww, wh) * 0.18), fill=WARM + (255,))
    if cross:
        d.rectangle([px(x + ww / 2 - 1.6), px(y), px(x + ww / 2 + 1.6), px(y + wh)], fill=(196, 130, 60, 255))
        d.rectangle([px(x), px(y + wh / 2 - 1.6), px(x + ww), px(y + wh / 2 + 1.6)], fill=(196, 130, 60, 255))


def house(base, x, ground, bw, bh, body, roof, windows, chimney=False, door=True, wreath=False):
    d = ImageDraw.Draw(base)
    roof_h = bh * 0.7
    d.rectangle([px(x), px(ground - bh), px(x + bw), px(ground)], fill=body + (255,))
    if chimney:
        d.rectangle([px(x + bw * 0.68), px(ground - bh - roof_h * 0.85), px(x + bw * 0.8), px(ground - bh - roof_h * 0.3)],
                    fill=WOOD_DARK + (255,))
        d.rectangle([px(x + bw * 0.66), px(ground - bh - roof_h * 0.9), px(x + bw * 0.82), px(ground - bh - roof_h * 0.82)],
                    fill=SNOW + (255,))
    over = bw * 0.08
    d.polygon([(px(x - over), px(ground - bh)), (px(x + bw / 2), px(ground - bh - roof_h)),
               (px(x + bw + over), px(ground - bh))], fill=roof + (255,))
    # snow along the roof
    d.polygon([(px(x - over), px(ground - bh)), (px(x + bw / 2), px(ground - bh - roof_h)),
               (px(x + bw + over), px(ground - bh)), (px(x + bw + over * 0.4), px(ground - bh + bh * 0.06)),
               (px(x + bw / 2), px(ground - bh - roof_h * 0.82)), (px(x - over * 0.4), px(ground - bh + bh * 0.06))],
              fill=SNOW + (255,))
    for (fx, fy, fw, fh) in windows:
        window(base, x + fx * bw, ground - bh + fy * bh, fw * bw, fh * bh)
    if door:
        dw, dh = bw * 0.18, bh * 0.42
        dx = x + bw * 0.5 - dw / 2
        d = ImageDraw.Draw(base)
        d.rounded_rectangle([px(dx), px(ground - dh), px(dx + dw), px(ground)], radius=px(dw * 0.45),
                            fill=WARM_DEEP + (255,))
        if wreath:
            cx, cy, r = dx + dw / 2, ground - dh * 0.68, dw * 0.28
            d.ellipse([px(cx - r), px(cy - r), px(cx + r), px(cy + r)], outline=(30, 110, 60, 255), width=px(r * 0.45))
            d.ellipse([px(cx - 2.5), px(cy + r * 0.6), px(cx + 2.5), px(cy + r * 0.6 + 5)], fill=(220, 50, 50, 255))
    # snow drift at the foot of the wall
    d.ellipse([px(x - bw * 0.1), px(ground - bh * 0.06), px(x + bw * 1.1), px(ground + bh * 0.08)], fill=SNOW + (255,))


def christmas_tree(base, x, ground, height, rng):
    pine(base, x, ground, height, color=(24, 84, 58), snow=False)
    d = ImageDraw.Draw(base)
    # garland of bulbs in loose swoops down the tree
    for k in range(5):
        y0 = ground - height * (0.78 - k * 0.15)
        half = height * 0.52 * (0.2 + 0.15 * k) * 0.95
        for j in range(9 + k * 2):
            t = j / (8 + k * 2)
            bx = x - half + 2 * half * t
            by = y0 + height * 0.05 * math.sin(t * math.pi) + height * 0.06 * t
            col = BULBS[(j + k) % len(BULBS)]
            glow(base, bx, by, 10, col, 0.55)
            d = ImageDraw.Draw(base)
            d.ellipse([px(bx - 3.2), px(by - 3.2), px(bx + 3.2), px(by + 3.2)], fill=col + (255,))
    # the star on top
    sx, sy, r = x, ground - height - 6, height * 0.06
    glow(base, sx, sy, r * 5, (255, 220, 120), 0.45)
    d = ImageDraw.Draw(base)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((px(sx + rr * math.cos(a)), px(sy + rr * math.sin(a))))
    d.polygon(pts, fill=(255, 222, 110, 255))


def present(base, x, ground, bw, bh, color, ribbon):
    d = ImageDraw.Draw(base)
    d.rectangle([px(x), px(ground - bh), px(x + bw), px(ground)], fill=color + (255,))
    d.rectangle([px(x + bw * 0.43), px(ground - bh), px(x + bw * 0.57), px(ground)], fill=ribbon + (255,))
    d.rectangle([px(x), px(ground - bh * 0.62), px(x + bw), px(ground - bh * 0.5)], fill=ribbon + (255,))
    d.ellipse([px(x + bw * 0.25), px(ground - bh - bh * 0.28), px(x + bw * 0.5), px(ground - bh + 2)], fill=ribbon + (255,))
    d.ellipse([px(x + bw * 0.5), px(ground - bh - bh * 0.28), px(x + bw * 0.75), px(ground - bh + 2)], fill=ribbon + (255,))


def snowman(base, x, ground, size):
    d = ImageDraw.Draw(base)
    for (dy, r) in [(0.0, 0.5), (0.72, 0.36), (1.25, 0.25)]:
        cy = ground - size * (r + dy)
        d.ellipse([px(x - size * r), px(cy - size * r), px(x + size * r), px(cy + size * r)], fill=SNOW + (255,))
        d.chord([px(x - size * r), px(cy - size * r), px(x + size * r), px(cy + size * r)], -60, 60,
                fill=SNOW_SHADE + (255,))
    hy = ground - size * 1.5
    d.ellipse([px(x - size * 0.06), px(hy - size * 0.02), px(x + size * 0.0), px(hy + size * 0.04)], fill=(30, 30, 40, 255))
    d.ellipse([px(x + size * 0.07), px(hy - size * 0.02), px(x + size * 0.13), px(hy + size * 0.04)], fill=(30, 30, 40, 255))
    d.polygon([(px(x + size * 0.03), px(hy + size * 0.07)), (px(x + size * 0.28), px(hy + size * 0.11)),
               (px(x + size * 0.03), px(hy + size * 0.14))], fill=(240, 130, 50, 255))
    d.rectangle([px(x - size * 0.3), px(ground - size * 1.25), px(x + size * 0.3), px(ground - size * 1.16)],
                fill=(200, 50, 60, 255))
    d.rectangle([px(x + size * 0.12), px(ground - size * 1.2), px(x + size * 0.22), px(ground - size * 0.95)],
                fill=(200, 50, 60, 255))
    d.rectangle([px(x - size * 0.22), px(ground - size * 1.84), px(x + size * 0.22), px(ground - size * 1.74)],
                fill=(26, 26, 34, 255))
    d.rectangle([px(x - size * 0.15), px(ground - size * 2.1), px(x + size * 0.15), px(ground - size * 1.76)],
                fill=(26, 26, 34, 255))


def sleigh(base, cx, cy, size):
    """Santa's sleigh and four reindeer in silhouette, flying left to right."""
    d = ImageDraw.Draw(base)
    ink = (14, 18, 34, 255)
    s = size
    d.polygon([(px(cx - s), px(cy)), (px(cx + s * 0.2), px(cy)), (px(cx + s * 0.35), px(cy - s * 0.35)),
               (px(cx - s * 0.75), px(cy - s * 0.45)), (px(cx - s * 1.05), px(cy - s * 0.25))], fill=ink)
    d.line([(px(cx - s * 1.1), px(cy + s * 0.15)), (px(cx + s * 0.4), px(cy + s * 0.15))], fill=ink, width=px(s * 0.06))
    d.ellipse([px(cx - s * 0.6), px(cy - s * 0.85), px(cx - s * 0.2), px(cy - s * 0.4)], fill=ink)
    d.ellipse([px(cx - s * 0.95), px(cy - s * 0.75), px(cx - s * 0.6), px(cy - s * 0.38)], fill=ink)
    for k in range(4):
        rx = cx + s * (0.9 + k * 0.75)
        ry = cy - s * (0.25 + k * 0.12)
        d.ellipse([px(rx - s * 0.32), px(ry - s * 0.12), px(rx + s * 0.32), px(ry + s * 0.12)], fill=ink)
        d.polygon([(px(rx + s * 0.22), px(ry - s * 0.05)), (px(rx + s * 0.38), px(ry - s * 0.32)),
                   (px(rx + s * 0.48), px(ry - s * 0.28)), (px(rx + s * 0.34), px(ry))], fill=ink)
        for lx, dx in [(-0.22, -0.12), (-0.1, 0.05), (0.15, -0.05), (0.25, 0.12)]:
            d.line([(px(rx + s * lx), px(ry + s * 0.05)), (px(rx + s * (lx + dx)), px(ry + s * 0.32))], fill=ink,
                   width=px(s * 0.05))
        d.line([(px(rx + s * 0.4), px(ry - s * 0.3)), (px(rx + s * 0.32), px(ry - s * 0.48))], fill=ink, width=px(s * 0.04))
        d.line([(px(rx + s * 0.44), px(ry - s * 0.3)), (px(rx + s * 0.55), px(ry - s * 0.46))], fill=ink, width=px(s * 0.04))
    d.line([(px(cx + s * 0.3), px(cy - s * 0.3)), (px(cx + s * 3.2), px(cy - s * 0.6))], fill=ink, width=px(s * 0.025))


def finish(base, name, lift, rng):
    """Lift the scene by {@code lift} px so it ends where Home's dock begins (the ground below is stretched from
    the last row), darken the bottom (dock) and the top-left corner (clock), save 1920x1080."""
    cut = px(lift)
    lifted = Image.new("RGBA", base.size)
    lifted.paste(base.crop((0, cut, w, h)), (0, 0))
    lifted.paste(base.crop((0, h - 1, w, h)).resize((w, cut)), (0, h - cut))
    base = lifted
    ys = np.linspace(0, 1, h)[:, None]
    xs = np.linspace(0, 1, w)[None, :]
    bottom = np.clip((ys - 0.62) / 0.38, 0, 1) ** 1.4 * 0.72
    corner = np.clip(1 - np.hypot(xs / 0.42, ys / 0.34), 0, 1) ** 1.2 * 0.5
    shade = np.clip(1 - np.maximum(bottom, corner), 0, 1)
    arr = np.asarray(base.convert("RGB")).astype(np.float64) * shade[:, :, None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    # about one level of noise, so the moon's glow and the dark sky do not band into rings
    noisy = np.asarray(img).astype(np.float64) + rng.normal(0, 0.9, (H, W, 1))
    img = Image.fromarray(np.clip(np.round(noisy), 0, 255).astype(np.uint8), "RGB")
    OUT.mkdir(exist_ok=True)
    img.save(OUT / name, quality=92, subsampling=0, optimize=True, progressive=True)
    print(name, (OUT / name).stat().st_size, "B")


def cabin_scene():
    rng = np.random.default_rng(2512)
    b = sky((6, 10, 30), (16, 26, 58), (40, 52, 92))
    stars(b, rng, 90, 640)
    moon(b, 1470, 480, 95)
    hill(b, 700, 30, 0.6, FAR)
    for x, g, hh in [(980, 730, 170), (1060, 712, 220), (1790, 705, 230), (1860, 720, 180)]:
        pine(b, x, g, hh, PINE_DARK)
    hill(b, 760, 40, 2.1, MID)
    house(b, 1240, 800, 330, 170, WOOD, (58, 34, 30), [(0.1, 0.25, 0.2, 0.3), (0.7, 0.25, 0.2, 0.3)],
          chimney=True, wreath=True)
    for x, g, hh in [(1150, 812, 200), (1660, 806, 260), (1730, 830, 190)]:
        pine(b, x, g, hh)
    hill(b, 860, 25, 4.0, NEAR)
    finish(b, "001.jpg", 140, rng)


def tree_scene():
    rng = np.random.default_rng(2412)
    b = sky((4, 8, 24), (12, 22, 50), (30, 44, 82))
    stars(b, rng, 100, 700)
    glow(b, 1380, 600, 340, (90, 120, 200), 0.18)
    hill(b, 740, 22, 1.3, FAR)
    for x, hh in [(860, 160), (930, 120), (1830, 190), (1890, 150)]:
        pine(b, x, 760, hh, PINE_DARK)
    hill(b, 820, 30, 3.0, MID)
    christmas_tree(b, 1380, 790, 400, rng)
    for x, bw, bh, col, rib in [(1240, 70, 54, (200, 50, 60), (255, 210, 90)), (1316, 56, 70, (40, 120, 200), (240, 240, 255)),
                                (1430, 78, 48, (40, 150, 90), (230, 60, 60)), (1512, 52, 60, (240, 190, 70), (200, 40, 60))]:
        present(b, x, 805, bw, bh, col, rib)
    hill(b, 900, 18, 1.1, NEAR)
    snowman(b, 1660, 850, 105)
    finish(b, "002.jpg", 120, rng)


def village_scene():
    rng = np.random.default_rng(2612)
    b = sky((8, 8, 32), (26, 22, 64), (64, 46, 96))
    stars(b, rng, 90, 600)
    moon(b, 950, 430, 60)
    hill(b, 640, 35, 0.2, (96, 98, 150), 0.8)
    # church on the far hill
    d = ImageDraw.Draw(b)
    d.rectangle([px(1700), px(520), px(1760), px(660)], fill=(44, 40, 78, 255))
    d.polygon([(px(1690), px(520)), (px(1730), px(420)), (px(1770), px(520))], fill=(44, 40, 78, 255))
    window(b, 1720, 560, 20, 34, cross=False)
    hill(b, 720, 20, 1.5, MID)
    for x, bw, bh, body, roof, chimney in [(1000, 200, 120, (86, 56, 70), (60, 36, 52), True),
                                            (1220, 160, 150, (70, 60, 96), (48, 40, 74), False),
                                            (1400, 230, 110, (96, 60, 52), (66, 40, 36), True),
                                            (1650, 170, 135, (60, 74, 96), (40, 52, 74), False)]:
        house(b, x, 790, bw, bh, body, roof, [(0.12, 0.25, 0.22, 0.3), (0.66, 0.25, 0.22, 0.3)], chimney=chimney,
              wreath=bw > 190)
    # a string of lights across the street
    d = ImageDraw.Draw(b)
    for k in range(34):
        t = k / 33
        lx = 1000 + t * 820
        ly = 620 + 40 * math.sin(t * math.pi * 3) ** 2
        col = BULBS[k % len(BULBS)]
        glow(b, lx, ly, 9, col, 0.5)
        d = ImageDraw.Draw(b)
        d.ellipse([px(lx - 3), px(ly - 3), px(lx + 3), px(ly + 3)], fill=col + (255,))
    hill(b, 800, 18, 3.3, NEAR)
    for x, hh in [(930, 210), (1880, 240)]:
        pine(b, x, 860, hh)
    finish(b, "003.jpg", 120, rng)


def sleigh_scene():
    rng = np.random.default_rng(2312)
    b = sky((4, 6, 22), (10, 20, 50), (24, 40, 80))
    stars(b, rng, 110, 720)
    moon(b, 1380, 540, 150)
    sleigh(b, 1080, 560, 58)
    hill(b, 720, 40, 2.4, FAR)
    for i in range(16):
        x = 780 + i * 80 + rng.uniform(-20, 20)
        pine(b, x, 760 + rng.uniform(-10, 20), rng.uniform(150, 260), PINE_DARK)
    hill(b, 820, 30, 0.9, MID)
    for i in range(8):
        x = 820 + i * 150 + rng.uniform(-30, 30)
        pine(b, x, 860 + rng.uniform(-10, 10), rng.uniform(220, 320))
    hill(b, 900, 20, 2.0, NEAR)
    finish(b, "004.jpg", 140, rng)


if __name__ == "__main__":
    cabin_scene()
    tree_scene()
    village_scene()
    sleigh_scene()
