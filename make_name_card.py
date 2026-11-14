"""Name labels in pixel-art style under each bird (for posting on X).

Writes birds_names.png (still) and birds_names.gif (animated).
Text is drawn with anti-aliasing off at 12px, given a 1-dot outline,
then enlarged 2x with nearest-neighbour so it looks like dot lettering.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from make_birds import LAYOUT, SLOT_W, SLOT_H, CELL

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
SIZE = 12          # glyph size in text dots
SCALE = 2          # 1 text dot = 2px
TEXT = (255, 255, 255)
EDGE = (52, 48, 110)
LABEL_CY = 186     # vertical centre of the label inside each 200px slot


def label(name):
    font = ImageFont.truetype(FONT, SIZE)
    w = int(font.getlength(name)) + 4
    h = SIZE + 4
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    d.text((2, 2), name, font=font, fill=255)
    edge = mask.filter(ImageFilter.MaxFilter(3))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.paste(EDGE + (255,), (0, 0), edge)
    img.paste(TEXT + (255,), (0, 0), mask)
    return img.resize((w * SCALE, h * SCALE), Image.NEAREST)


LABELS = {n: label(n) for row in LAYOUT for n in row}


def overlay(frame):
    f = frame.convert("RGBA")
    for r, row in enumerate(LAYOUT):
        for c, name in enumerate(row):
            lb = LABELS[name]
            cx = c * SLOT_W * CELL + SLOT_W * CELL // 2
            cy = r * SLOT_H * CELL + LABEL_CY
            f.alpha_composite(lb, (cx - lb.width // 2, cy - lb.height // 2))
    return f.convert("RGB")


def main():
    overlay(Image.open("preview.png")).save("birds_names.png")

    gif = Image.open("birds.gif")
    frames, durs = [], []
    for i in range(gif.n_frames):
        gif.seek(i)
        frames.append(overlay(gif.convert("RGB")))
        durs.append(gif.info.get("duration", 90))
    cols = sorted({c for f in frames for _, c in f.getcolors(1 << 16)})
    assert len(cols) <= 256, len(cols)
    index = {c: i for i, c in enumerate(cols)}
    palette = [v for c in cols for v in c] + [0] * (768 - 3 * len(cols))
    out = []
    for f in frames:
        p = Image.new("P", f.size)
        p.putpalette(palette)
        p.putdata([index[c] for c in f.getdata()])
        out.append(p)
    out[0].save("birds_names.gif", save_all=True, append_images=out[1:],
                duration=durs, loop=0, disposal=1)
    print("wrote birds_names.png, birds_names.gif")


if __name__ == "__main__":
    main()
