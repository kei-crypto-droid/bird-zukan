"""Name labels in coarse dot lettering under each bird (for posting on X).

Writes birds_names.png (still) and birds_names.gif (animated).
Letters come from the hand-made 5x7 dot katakana in dot_font.py;
each letter dot is drawn as a 4px square.
"""
from PIL import Image
from make_birds import LAYOUT, SLOT_W, SLOT_H, CELL
from dot_font import text_dots

DOT = 4            # 1 letter dot = 4px
TEXT = (255, 255, 255)
LABEL_CY = 184     # vertical centre of the label inside each 200px slot


def label(name):
    dots, w, h = text_dots(name)
    img = Image.new("RGBA", (w * DOT, h * DOT), (0, 0, 0, 0))
    for x, y in dots:
        img.paste(TEXT + (255,), (x * DOT, y * DOT, (x + 1) * DOT, (y + 1) * DOT))
    return img


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
