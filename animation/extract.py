"""Cut the mockup into a clean background plate + animated sprite strips for the app.

usage: python3 extract.py base2.png OUTDIR
"""
import sys, json
import numpy as np
from PIL import Image
from collections import deque

SRC, OUT = sys.argv[1], sys.argv[2]
base = np.array(Image.open(SRC).convert("RGB")).astype(np.int16)
H, W, _ = base.shape
PLATE_H = 1236


def largest(m):
    h, w = m.shape
    lab = np.zeros((h, w), int)
    best, bestn, cur = 0, 0, 0
    for sy in range(h):
        for sx in range(w):
            if m[sy, sx] and not lab[sy, sx]:
                cur += 1; lab[sy, sx] = cur; q = deque([(sy, sx)]); n = 0
                while q:
                    y, x = q.popleft(); n += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not lab[ny, nx]:
                                lab[ny, nx] = cur; q.append((ny, nx))
                if n > bestn:
                    best, bestn = cur, n
    return lab == best


def dilate(m, n=1):
    for _ in range(n):
        p = np.pad(m, 1)
        m = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m


def interp_rows(img, mask):
    """Fill masked pixels of img (H,W,3) by horizontal interpolation, row by row."""
    out = img.copy()
    for y in range(mask.shape[0]):
        row = mask[y]
        if not row.any():
            continue
        xs = np.where(~row)[0]
        if len(xs) == 0:
            continue
        for c in range(3):
            out[y, row, c] = np.interp(np.where(row)[0], xs, img[y, xs, c])
    return out


def full_mask(box):
    x0, y0, x1, y1 = box
    m = np.zeros((H, W), bool)
    m[y0:y1, x0:x1] = True
    return m


# ---------- birds: upper body (on green) + legs/tail (on the pedestal) ----------
SPLIT = 442


def bird_mask(upper_box, leg_box):
    x0, y0, x1, y1 = upper_box
    r = base[y0:y1, x0:x1]
    R, G, B = r[..., 0], r[..., 1], r[..., 2]
    up = largest(~((G > R + 15) & (G > B + 15)))
    m = np.zeros((H, W), bool)
    m[y0:y1, x0:x1] = up
    # legs: difference from a horizontally-interpolated clean pedestal
    lx0, ly0, lx1, ly1 = leg_box
    reg = base[ly0:ly1, lx0:lx1]
    inner = np.zeros(reg.shape[:2], bool)
    inner[:, 1:-1] = True
    clean = interp_rows(reg, inner)
    diff = np.abs(reg.astype(int) - clean.astype(int)).sum(axis=2) > 70
    tan = (reg[..., 0] > 170) & (reg[..., 1] > 110) & (reg[..., 2] < 140)   # pedestal wood, not legs
    diff &= ~tan
    m[ly0:ly1, lx0:lx1] |= diff
    return largest(m)


BIRDS = {
    "akagera": dict(upper=(172, 354, 312, SPLIT), legs=(204, SPLIT, 314, 474), card=0),
    "kawasemi": dict(upper=(530, 356, 676, SPLIT), legs=(566, SPLIT, 682, 474), card=1),
}
CARD_X = [(69, 409), (440, 770), (801, 1131)]
CARD_Y = (302, 533)
cx_of = lambda i: (CARD_X[i][0] + CARD_X[i][1]) / 2

erase = np.zeros((H, W), bool)
meta = {}

for name, b in BIRDS.items():
    m = bird_mask(b["upper"], b["legs"])
    erase |= dilate(m, 3)
    ys, xs = np.where(m)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    LIFT = 7
    PAD = 6                                   # empty columns so frames never bleed into each other
    sw, fh = bx1 - bx0, by1 - by0 + LIFT
    fw = sw + 2 * PAD
    strip = np.zeros((fh, fw * 2, 4), np.uint8)
    sub = base[by0:by1, bx0:bx1].astype(np.uint8)
    sm = m[by0:by1, bx0:bx1]
    # frame 0: at rest
    f0 = strip[:, PAD:PAD + sw]
    f0[LIFT:][sm] = np.dstack([sub, np.full(sm.shape, 255, np.uint8)])[sm]
    # frame 1: upper body lifted LIFT px; the gap repeats the body's last row
    f1 = strip[:, fw + PAD:fw + PAD + sw]
    split = SPLIT - by0
    up_m = sm.copy(); up_m[split:] = False
    lo_m = sm.copy(); lo_m[:split] = False
    rgba = np.dstack([sub, np.full(sm.shape, 255, np.uint8)])
    f1[LIFT:][lo_m] = rgba[lo_m]
    shifted = np.zeros_like(f1)
    shifted[:fh - LIFT][up_m] = rgba[up_m]
    rowm = up_m[split - 1]
    for k in range(LIFT):
        shifted[split + k][rowm] = rgba[split - 1][rowm]
    sm2 = shifted[..., 3] > 0
    f1[sm2] = shifted[sm2]
    Image.fromarray(strip).save(f"{OUT}/{name}.png")
    c = b["card"]
    meta[name] = dict(w=int(fw), h=int(fh), frames=2,
                      dx=float(bx0 - PAD - cx_of(c)), bottom=int(by1))

# ---------- egg ----------
EGG_BOX = (890, 378, 1036, 465)


def egg_mask():
    x0, y0, x1, y1 = EGG_BOX
    r = base[y0:y1, x0:x1]
    h, w = r.shape[:2]
    passable = (r.max(axis=2) > 90) | ((r[..., 0] - r[..., 2]) > 45)
    seen = np.zeros((h, w), bool)
    q = deque([(y, x) for x in range(w) for y in (0, h - 1)] + [(y, x) for y in range(h) for x in (0, w - 1)])
    q = deque([(y, x) for (y, x) in q if passable[y, x]])
    for y, x in q:
        seen[y, x] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and passable[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    mm = largest(~seen & ~((r[..., 0] - r[..., 2]) > 45))
    for yy in range(h):
        xs = np.where(mm[yy])[0]
        if len(xs):
            mm[yy, xs.min():xs.max() + 1] = True
    m = np.zeros((H, W), bool)
    m[y0:y1, x0:x1] = mm
    return m


em = egg_mask()
erase |= dilate(em, 6)
ys, xs = np.where(em)
ex0, ey0, ex1, ey1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
PADX, HOP = 10, 8
ew, eh = ex1 - ex0 + 2 * PADX, ey1 - ey0 + HOP
esub = np.dstack([base[ey0:ey1, ex0:ex1].astype(np.uint8), np.full((ey1 - ey0, ex1 - ex0), 255, np.uint8)])
esm = em[ey0:ey1, ex0:ex1]
SEQ = [(0, 0)] * 4 + [(-8, 0), (0, 0), (8, 0), (0, 0), (-8, 0), (0, 0), (8, 0), (0, 0)] + [(0, 0), (0, 8), (0, 0), (0, 0)]
estrip = np.zeros((eh, ew * len(SEQ), 4), np.uint8)
for i, (lean, dy) in enumerate(SEQ):
    fr = estrip[:, i * ew:(i + 1) * ew]
    for yy in range(ey1 - ey0):
        gy = ey0 + yy
        band = 2 if gy < 421 else 1 if gy < 441 else 0
        off = lean * band // 2
        rm = esm[yy]
        if not rm.any():
            continue
        ty = HOP + yy - dy
        cols = np.where(rm)[0]
        fr[ty, cols + PADX + off] = esub[yy, cols]
Image.fromarray(estrip).save(f"{OUT}/egg.png")
meta["egg"] = dict(w=int(ew), h=int(eh), frames=len(SEQ), dx=float(ex0 - PADX - cx_of(2)), bottom=int(ey1))

# ---------- text areas that become live ----------
regions = [
    (139 - 4, 303, 353 + 5, 352 + 3),    # おなかすいた (card 1)
    (502 - 4, 303, 720 + 5, 352 + 3),    # おなかすいた (card 2)
    (150, 483, 345, 527),                # アカゲラ
    (500, 483, 714, 527),                # カワセミ
    (880, 483, 1052, 527),               # ？の卵
    (96, 209, 252, 263),                 # 2,400
    (290, 603, 1112, 646),               # speech bubble text
]
for r in regions:
    erase |= full_mask(r)

plate = interp_rows(base, erase)
# field above the pedestals: replace the fill with a smooth fitted surface (no streaks)
for (cx0, cx1) in CARD_X:
    x0, x1, y0, y1 = cx0 + 8, cx1 - 8, 312, 446
    reg = base[y0:y1, x0:x1].astype(float)
    er = erase[y0:y1, x0:x1]
    G = reg[..., 1]
    known = (~dilate(er, 4)) & (G > 222)            # light field only (spots and borders excluded)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    X = np.stack([np.ones_like(xx), xx, yy, xx * xx, yy * yy, xx * yy], -1).astype(float)
    Xs = X[known] / [1, 1e3, 1e3, 1e6, 1e6, 1e6]
    fill = er & True
    Xf = X[fill] / [1, 1e3, 1e3, 1e6, 1e6, 1e6]
    sub = plate[y0:y1, x0:x1]
    for c in range(3):
        coef, *_ = np.linalg.lstsq(Xs, reg[..., c][known], rcond=None)
        sub[..., c][fill] = Xf @ coef
    plate[y0:y1, x0:x1] = sub
plate = plate[:PLATE_H].astype(np.uint8)
Image.fromarray(plate).save(f"{OUT}/plate.png")
Image.fromarray(plate).save(f"{OUT}/plate.jpg", quality=90, optimize=True, progressive=True)
meta["plate"] = dict(w=W, h=PLATE_H)
json.dump(meta, open(f"{OUT}/sprites.json", "w"), indent=1)
print(json.dumps(meta))
