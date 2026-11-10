import sys
import numpy as np
from PIL import Image
from collections import deque

SRC = sys.argv[1]
OUT = sys.argv[2]
base = np.array(Image.open(SRC).convert("RGB")).astype(np.int16)
H, W, _ = base.shape


def green_mask(box):
    x0, y0, x1, y1 = box
    r = base[y0:y1, x0:x1]
    R, G, B = r[..., 0], r[..., 1], r[..., 2]
    return ~((G > R + 15) & (G > B + 15))  # True = sprite


def flood_mask(box):
    x0, y0, x1, y1 = box
    r = base[y0:y1, x0:x1]
    h, w = r.shape[:2]
    passable = r.max(axis=2) > 90
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if passable[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if passable[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and passable[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    return ~seen


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


def inpaint(img, box, mask):
    """Fill masked pixels by horizontal interpolation between nearest unmasked neighbours."""
    x0, y0, x1, y1 = box
    reg = img[y0:y1, x0:x1]
    for y in range(reg.shape[0]):
        row = mask[y]
        if not row.any():
            continue
        xs = np.where(~row)[0]
        if len(xs) == 0:
            print("full row", box, y); continue
        for c in range(3):
            reg[y, row, c] = np.interp(np.where(row)[0], xs, reg[y, xs, c])


# --- sprite definitions (coordinates in the 1199x1312 source) ---
WP = dict(box=(172, 354, 312, 442))   # woodpecker upper body (above legs)
KF = dict(box=(530, 356, 676, 442))   # kingfisher upper body
EGG = dict(box=(890, 378, 1036, 465))  # egg incl. bottom on pedestal

clean = base.copy()
for s in (WP, KF):
    s["mask"] = largest(green_mask(s["box"]))
    s["fillmask"] = dilate(s["mask"], 4)
    x0, y0, x1, y1 = s["box"]
    s["pix"] = base[y0:y1, x0:x1].copy()
    inpaint(clean, s["box"], s["fillmask"])
_r = base[EGG["box"][1]:EGG["box"][3], EGG["box"][0]:EGG["box"][2]]
_m = largest(flood_mask(EGG["box"]) & ~((_r[..., 0] - _r[..., 2]) > 45))  # drop brown pedestal rim
for _y in range(_m.shape[0]):  # fill each row between the outline edges (cream lower half)
    _xs = np.where(_m[_y])[0]
    if len(_xs):
        _m[_y, _xs.min():_xs.max() + 1] = True
EGG["mask"] = _m
EGG["fillmask"] = dilate(EGG["mask"], 7)
x0, y0, x1, y1 = EGG["box"]
EGG["pix"] = base[y0:y1, x0:x1].copy()
inpaint(clean, EGG["box"], EGG["fillmask"])

# Keep the original pixels outside sprites (inpaint only where needed later)


def paste(frame, pix, mask, x, y):
    h, w = mask.shape
    sub = frame[y:y + h, x:x + w]
    sub[mask] = pix[mask]


def bob(frame, s, d):
    """Lift the upper body d px; the gap above the legs is filled by repeating the bottom row."""
    x0, y0, x1, y1 = s["box"]
    pix, mask = s["pix"], s["mask"]
    paste(frame, pix, mask, x0, y0 - d)
    if d > 0:
        lastp, lastm = pix[-1:], mask[-1:]
        for k in range(d):
            paste(frame, lastp, lastm, x0, y1 - 1 - k)


def egg(frame, lean, dy):
    """Pixel-art wobble: shift horizontal bands of the egg (top moves most, bottom stays)."""
    x0, y0, x1, y1 = EGG["box"]
    pix, mask = EGG["pix"], EGG["mask"]
    ys = np.where(mask.any(axis=1))[0]
    top, bot = ys.min(), ys.max() + 1
    hgt = bot - top
    for y in range(top, bot):
        gy = y0 + y   # band edges sit on the sprite's pixel grid so spots are never split
        band = 2 if gy < 421 else 1 if gy < 441 else 0
        off = lean * band // 2
        paste(frame, pix[y:y + 1], mask[y:y + 1], x0 + off, y0 + y - dy)


# 16 frames, 120ms each
wp_d = [0, 0, 7, 7] * 4
kf_d = [7, 7, 0, 0] * 4
egg_seq = [(0, 0)] * 4 + [(-8, 0), (0, 0), (8, 0), (0, 0), (-8, 0), (0, 0), (8, 0), (0, 0)] + [(0, 0), (0, 8), (0, 0), (0, 0)]

frames = []
for i in range(16):
    f = clean.copy()
    bob(f, WP, wp_d[i])
    bob(f, KF, kf_d[i])
    egg(f, *egg_seq[i])
    frames.append(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)))

# shared palette so the static parts never flicker
pal = frames[0].quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE)
q = [fr.quantize(palette=pal, dither=Image.NONE) for fr in frames]
q[0].save(OUT, save_all=True, append_images=q[1:], duration=120, loop=0, optimize=False, disposal=1)
for i, fr in enumerate(frames):
    fr.save(f"frame_{i:02d}.png")
print("ok")
