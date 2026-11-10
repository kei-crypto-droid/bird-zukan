"""Map label fixes: separate 西目屋村 / 白神山地, make 白神山地 a badge, add 藤里町."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC, OUT, FONTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(SRC).convert("RGB")
a = np.array(im)

BG = np.array([157, 230, 132], np.uint8)   # map land green
NAVY = (0, 0, 28)                          # other place names
WHITE = (255, 255, 255)

# 1) grab the mountain icon (non-green pixels only) before erasing
mx0, my0, mx1, my1 = 662, 792, 744, 832
mt = a[my0:my1, mx0:mx1].copy()
mt_mask = np.abs(mt.astype(int) - BG.astype(int)).sum(axis=2) > 12

# 2) erase old labels + mountain
a[733:796, 652:757] = BG
a[my0:my1, mx0:mx1][mt_mask] = BG

# 3) mountain moved down a little
SHIFT = 10
a[my0 + SHIFT:my1 + SHIFT, mx0:mx1][mt_mask] = mt[mt_mask]

im = Image.fromarray(a)
d = ImageDraw.Draw(im)
f_name = ImageFont.truetype(f"{FONTDIR}/MPLUSRounded1c-800.ttf", 23)
f_name_big = ImageFont.truetype(f"{FONTDIR}/MPLUSRounded1c-800.ttf", 26)
f_badge = ImageFont.truetype(f"{FONTDIR}/MPLUSRounded1c-900.ttf", 25)


def label(text, cx, top, font, fill=NAVY, sw=3):
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, top), text, font=font, fill=fill, stroke_width=sw, stroke_fill=WHITE)


# 西目屋村: ordinary place name, same colour as the other towns
label("西目屋村", 705, 731, f_name)

# 白神山地: badge (deep forest green, yellow lettering, white rim)
text = "白神山地"
tw = d.textlength(text, font=f_badge)
bw, bh = tw + 26, 38
bx0, by0 = 705 - bw / 2, 764
d.rounded_rectangle((bx0 - 2, by0 - 2, bx0 + bw + 2, by0 + bh + 2), radius=13, fill=(10, 60, 20))
d.rounded_rectangle((bx0, by0, bx0 + bw, by0 + bh), radius=11, fill=(255, 255, 255))
d.rounded_rectangle((bx0 + 3, by0 + 3, bx0 + bw - 3, by0 + bh - 3), radius=9, fill=(30, 110, 45))
d.text((705 - tw / 2, by0 + 3), text, font=f_badge, fill=(255, 226, 60))

# 藤里町: new town label, upper part of the yellow area
label("藤里町", 655, 868, f_name_big)

im.save(OUT)
print("ok")
