"""Still image of the sheet with each bird's name under it (for posting on X)."""
from PIL import Image, ImageDraw, ImageFont
from make_birds import LAYOUT, SLOT_W, SLOT_H, CELL

img = Image.open("preview.png").convert("RGB")
d = ImageDraw.Draw(img)
font = ImageFont.truetype("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", 22)
for r, row in enumerate(LAYOUT):
    for c, name in enumerate(row):
        cx = c * SLOT_W * CELL + SLOT_W * CELL // 2
        cy = r * SLOT_H * CELL + 182
        d.text((cx, cy), name, font=font, fill=(255, 255, 255), anchor="mm",
               stroke_width=3, stroke_fill=(52, 48, 110))
img.save("birds_names.png")
print("wrote birds_names.png")
