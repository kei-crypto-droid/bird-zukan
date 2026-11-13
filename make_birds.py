"""Bird pixel-art sheet generator.

- Reads the original sprites from source/original.gif (15 birds, side view)
- Erases the old stubby legs and draws proper legs (tarsus + toes)
- Replaces the Shima-enaga (row 2, col 3) with a normal Japanese Enaga
- Swaps 5 birds for front-facing versions of the same species
- Writes birds.gif (animated: birds crouch/bob with feet planted on the ground)
"""
from PIL import Image

SRC = "source/original.gif"
OUT = "birds.gif"
CELL = 10            # 1 pixel-art dot = 10px
SLOT_W, SLOT_H = 16, 20
COLS, ROWS = 5, 3
GROUND = 16          # toe row inside each slot
MAGENTA = (255, 0, 255)  # chroma key of the original sheet
BG_TOP = (92, 96, 196)     # blue-violet
BG_BOTTOM = (156, 132, 222)  # lighter lavender-violet

# ---------------------------------------------------------------- leg colours
PINK_BROWN = (184, 130, 110)   # sparrows, bush warbler etc.
SLATE = (78, 84, 100)          # tits, white-eye
NUT_LEG = (150, 118, 82)       # nuthatch
BLACK_LEG = (40, 36, 40)       # long-tailed tit


def shade(c, f=0.72):
    return tuple(int(v * f) for v in c)


# ------------------------------------------------- per-bird leg-fix settings
# key (row, col): (erase_from_y, erase_max_x, (leg_x1, leg_x2), leg colour, extra erase pixels)
SIDE = {
    (0, 0): (13, 11, (7, 10), PINK_BROWN, []),
    (0, 1): (13, 11, (6, 9), PINK_BROWN, []),
    (0, 2): (13, 11, (7, 10), PINK_BROWN, []),
    (0, 3): (13, 11, (7, 10), SLATE, []),
    (0, 4): (14, 11, (7, 10), NUT_LEG, []),
    (1, 0): (13, 11, (7, 10), SLATE, []),
    (1, 1): (13, 11, (6, 9), SLATE, []),
    (1, 3): (14, 11, (6, 9), SLATE, [(0, 13)]),
    (1, 4): (14, 11, (6, 9), SLATE, []),
    (2, 0): (12, 11, (7, 10), PINK_BROWN, []),
    (2, 1): (12, 11, (7, 10), PINK_BROWN, []),
    (2, 2): (12, 11, (7, 10), PINK_BROWN, []),
    (2, 3): (12, 11, (6, 9), PINK_BROWN, []),
    (2, 4): (12, 11, (6, 9), PINK_BROWN, []),
}


def load_original():
    im = Image.open(SRC)
    im.seek(0)
    f = im.convert("RGB").resize((80, 60), Image.NEAREST)
    sprites = {}
    for r in range(3):
        for c in range(5):
            g = {}
            for y in range(SLOT_H):
                for x in range(SLOT_W):
                    p = f.getpixel((c * 16 + x, r * 20 + y))
                    if p != MAGENTA:
                        g[(x, y)] = p
            sprites[(r, c)] = g
    return sprites


def from_ascii(rows, pal):
    g = {}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                g[(x, y)] = pal[ch]
    return g


def mirror_half(rows):
    """8-wide left halves -> 16-wide symmetric rows."""
    return [r + r[::-1] for r in rows]


# ------------------------------------------------------------ normal Enaga
# White crown, thick black brow-stripe to the nape, black back with
# wine-pink scapulars, pinkish belly, long black tail with white edges.
ENAGA_PAL = {
    "W": (246, 243, 241), "w": (226, 221, 222), "K": (30, 28, 31),
    "G": (74, 70, 76), "P": (232, 196, 200), "p": (196, 138, 152),
    "E": (16, 14, 16), "Y": (236, 196, 92), "b": (36, 34, 36),
}
ENAGA = [
    "................",
    "................",
    "................",
    ".....WWWW.......",
    "....WWWWWKK.....",
    "...KKKKKKKKK....",
    "..bWEYWWKKKK....",
    "...WWWWWWKpp....",
    "...WWWWWWKppK...",
    "...wWWWWPKKWKK..",
    "....wWWPPPKKWKK.",
    ".....wPPPPpKKKWK",
    "......wPPp...KKW",
    "..............KK",
]


# ------------------------------------------------------ front-facing birds
# Left halves (8 columns), mirrored.  Legs drawn separately.
FRONT = []

# Sized to match the side-view birds: about 8-10 dots wide, 10 dots tall.
# スズメ (tree sparrow)
FRONT.append((mirror_half([
    "......cc",
    ".....ccc",
    "....cccc",
    "....WEcc",
    "....WWWB",
    "....KWWK",
    "...bwWww",
    "...bwwww",
    "....bwww",
    ".....www",
]), {
    "c": (140, 84, 42), "W": (240, 232, 220), "E": (20, 18, 18),
    "K": (36, 30, 28), "B": (78, 72, 70), "b": (112, 72, 38),
    "w": (214, 200, 182),
}, PINK_BROWN))

# シジュウカラ (Japanese tit)
FRONT.append((mirror_half([
    "......KK",
    ".....KKK",
    "....KKKK",
    "....WEKK",
    "....WWWB",
    "....KWWK",
    "...gwWWK",
    "...gwWWK",
    "....gwWK",
    ".....wwK",
]), {
    "K": (28, 26, 30), "W": (246, 244, 238), "E": (8, 8, 8),
    "B": (84, 84, 90), "g": (128, 138, 96), "w": (222, 220, 212),
}, SLATE))

# メジロ (Japanese white-eye)
FRONT.append((mirror_half([
    "......GG",
    ".....GGG",
    "....GWGG",
    "....WEWG",
    "....GWGB",
    "....GYYY",
    "...gYYYY",
    "...gwYWW",
    "....gwWW",
    ".....www",
]), {
    "G": (126, 150, 56), "W": (248, 246, 240), "E": (14, 14, 14),
    "B": (50, 50, 54), "Y": (230, 210, 70), "g": (104, 124, 48),
    "w": (214, 208, 190),
}, SLATE))

# エナガ (long-tailed tit)
FRONT.append((mirror_half([
    "......WW",
    ".....WWW",
    "....KKWW",
    "....KEYW",
    "....WWWB",
    "....WWWW",
    "...KWWWW",
    "...KPWWW",
    "....PPPW",
    ".....PPP",
]), {
    "W": (246, 243, 241), "K": (30, 28, 31), "E": (14, 12, 14),
    "Y": (236, 196, 92), "B": (36, 34, 36), "P": (232, 196, 200),
}, BLACK_LEG))

# ヤマガラ (varied tit)
FRONT.append((mirror_half([
    "......KK",
    ".....KKK",
    "....CKKK",
    "....CECC",
    "....CCCB",
    "....CCCK",
    "...gOCKK",
    "...gOOOO",
    "....gOOO",
    ".....OOO",
]), {
    "K": (30, 28, 32), "C": (240, 226, 196), "E": (12, 12, 12),
    "B": (84, 82, 88), "O": (196, 110, 52), "g": (110, 116, 130),
}, SLATE))


# FRONT index -> slot (row, col) of the same species in the side-view sheet
FRONT_POS = {
    0: (2, 3),  # スズメ
    1: (1, 1),  # シジュウカラ
    2: (0, 3),  # メジロ
    3: (1, 2),  # エナガ
    4: (1, 0),  # ヤマガラ
}


# slot rearrangement: front birds end up at (0,1) (0,4) (1,2) (2,0) (2,3)
SWAP = {
    (0, 3): (0, 1), (0, 1): (0, 3),  # メジロ <-> olive side bird
    (1, 1): (0, 4), (0, 4): (1, 1),  # シジュウカラ <-> nuthatch
    (1, 0): (2, 0), (2, 0): (1, 0),  # ヤマガラ <-> crested lark-ish bird
}


def body_bottom(g, x):
    ys = [y for (px, y) in g if px == x]
    return max(ys) if ys else None


def draw_side_legs(g, legs, color, ground, crouch):
    """Side view: tarsus straight down, toes pointing forward (left).

    Both legs use the same darker tone; the toes are kept 2 dots wide so a
    gap stays between the two feet instead of merging into one bar.
    """
    out = dict(g)
    col = shade(color)
    for x in legs:
        top = body_bottom(out, x)
        top = (top + 1) if top is not None else ground - 2
        for y in range(top, ground):
            out.setdefault((x, y), col)
        for tx in (x - 1, x):
            out[(tx, ground)] = col
    return out


def draw_front_legs(g, color, ground):
    out = dict(g)
    for x, toes in ((5, (4, 5, 6)), (10, (9, 10, 11))):
        top = body_bottom(out, x)
        top = (top + 1) if top is not None else ground - 2
        for y in range(top, ground):
            out.setdefault((x, y), color)
        for tx in toes:
            out[(tx, ground)] = color
    return out


def shift(g, dy):
    return {(x, y + dy): c for (x, y), c in g.items()}


def build_side(sprite, cfg, crouch):
    ey, ex, legs, color, extra = cfg
    g = {k: v for k, v in sprite.items() if not (k[1] >= ey and k[0] <= ex)}
    for k in extra:
        g.pop(k, None)
    # align so the body bottom sits 3 rows above GROUND
    bottom = max(body_bottom(g, x) or 0 for x in legs)
    dy = (GROUND - 3) - bottom + (1 if crouch else 0)
    g = shift(g, dy)
    return draw_side_legs(g, legs, color, GROUND, crouch)


def build_enaga(crouch):
    g = from_ascii(ENAGA, ENAGA_PAL)
    legs = (6, 9)
    bottom = max(body_bottom(g, x) or 0 for x in legs)
    dy = (GROUND - 3) - bottom + (1 if crouch else 0)
    g = shift(g, dy)
    return draw_side_legs(g, legs, BLACK_LEG, GROUND, crouch)


def build_front(spec, crouch):
    rows, pal, color = spec
    g = from_ascii(rows, pal)
    bottom = max(body_bottom(g, x) or 0 for x in (5, 10))
    dy = (GROUND - 3) - bottom + (1 if crouch else 0)
    g = shift(g, dy)
    return draw_front_legs(g, color, GROUND)


def render(crouch):
    sprites = load_original()
    W, H = COLS * SLOT_W * CELL, ROWS * SLOT_H * CELL
    img = Image.new("RGB", (W, H))
    # blue-violet vertical gradient, stepped per dot row to stay pixel-art
    rows = H // CELL
    for r in range(rows):
        t = r / (rows - 1)
        col = tuple(round(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM))
        img.paste(col, (0, r * CELL, W, (r + 1) * CELL))
    grid = {}
    for key, cfg in SIDE.items():
        grid[key] = build_side(sprites[key], cfg, crouch)
    grid[(1, 2)] = build_enaga(crouch)
    # front-facing birds replace the side-view bird of the same species
    for i, pos in FRONT_POS.items():
        grid[pos] = build_front(FRONT[i], crouch)
    # spread front-facing birds out so they don't cluster (no two side by side)
    grid = {SWAP.get(k, k): v for k, v in grid.items()}
    px = img.load()
    for (r, c), g in grid.items():
        for (x, y), col in g.items():
            if 0 <= x < SLOT_W and 0 <= y < SLOT_H:
                for yy in range(CELL):
                    for xx in range(CELL):
                        px[(c * SLOT_W + x) * CELL + xx, (r * SLOT_H + y) * CELL + yy] = col
    return img


def main():
    up, down = render(False), render(True)

    def bob(columns):
        """Frame where only the given columns are crouched."""
        f = up.copy()
        w = SLOT_W * CELL
        for c in columns:
            f.paste(down.crop((c * w, 0, (c + 1) * w, f.height)), (c * w, 0))
        return f

    # columns 1/3/5 and columns 2/4 take turns:
    # while one group hops 3 times, the other group rests, then they swap
    odd, even = bob((0, 2, 4)), bob((1, 3))
    seq = [up, odd, up, odd, up, odd, up, even, up, even, up, even]
    durs = [90] * len(seq)
    # exact shared palette (total colours < 256), so nothing gets merged
    cols = sorted({c for f in (up, down) for _, c in f.getcolors(1 << 16)})
    assert len(cols) <= 256, len(cols)
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette([v for c in cols for v in c] + [0] * (768 - 3 * len(cols)))
    index = {c: i for i, c in enumerate(cols)}

    def to_p(f):
        p = Image.new("P", f.size)
        p.putpalette(pal_img.getpalette())
        p.putdata([index[c] for c in f.getdata()])
        return p

    frames = [to_p(f) for f in seq]
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1)
    up.save("preview.png")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
