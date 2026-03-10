#!/usr/bin/env python3
"""
Generate PNG frames for a simple modern hand-drawn Kanban animation:
- Columns: Backlog, WIP (overloaded), Done
- Too many cards in WIP
- Flashing red warning light (top-right) toggles on/off
Outputs: frames/frame_0000.png ... frame_N.png
"""

from __future__ import annotations
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080

FPS = 30
DURATION_S = 8
N_FRAMES = FPS * DURATION_S

OUT_DIR = "frames"

BG = (250, 248, 242)
INK = (25, 25, 28)
MUTED = (90, 90, 96)

COL_BACKLOG = (240, 246, 255)
COL_WIP = (255, 246, 238)
COL_DONE = (243, 255, 246)

CARD = (255, 255, 255)
WARN_RED = (220, 40, 50)

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _try_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Try a few common fonts; fall back to default.
    for name in ["DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttf"]:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            pass
    return ImageFont.load_default()

def jitter(i: int, amp: float) -> float:
    # Deterministic pseudo-jitter (hand-drawn wobble)
    return amp * math.sin(i * 1.618)

def hand_rect(draw: ImageDraw.ImageDraw, box, outline=INK, width=4, wobble=2, steps=18):
    x0, y0, x1, y1 = box
    pts = []
    # Build a slightly wobbly polyline rectangle
    for t in range(steps + 1):
        a = t / steps
        pts.append((x0 + (x1 - x0) * a, y0 + jitter(t, wobble)))
    for t in range(steps + 1):
        a = t / steps
        pts.append((x1 + jitter(t+11, wobble), y0 + (y1 - y0) * a))
    for t in range(steps + 1):
        a = t / steps
        pts.append((x1 - (x1 - x0) * a, y1 + jitter(t+23, wobble)))
    for t in range(steps + 1):
        a = t / steps
        pts.append((x0 + jitter(t+37, wobble), y1 - (y1 - y0) * a))
    draw.line(pts + [pts[0]], fill=outline, width=width, joint="curve")

def filled_hand_panel(img: Image.Image, box, fill, outline=INK):
    d = ImageDraw.Draw(img)
    # soft shadow
    shadow = Image.new("RGBA", img.size, (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    x0,y0,x1,y1 = box
    sd.rounded_rectangle((x0+6,y0+8,x1+6,y1+8), radius=18, fill=(0,0,0,40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(shadow)

    d.rounded_rectangle(box, radius=18, fill=fill)
    hand_rect(d, box, outline=outline, width=5, wobble=2.2)

def draw_scribble(draw, x, y, w, h, color=(120,120,125), width=3, lines=3, phase=0.0):
    for k in range(lines):
        pts=[]
        n=14
        for i in range(n):
            a=i/(n-1)
            xx=x + a*w
            yy=y + (k+1)*h/(lines+1) + 6*math.sin(phase + a*6.2 + k*1.7) * 0.3
            yy += 2*math.sin(phase*0.5 + a*10 + k)
            pts.append((xx,yy))
        draw.line(pts, fill=color, width=width)

def main():
    _ensure_dir(OUT_DIR)

    font_title = _try_font(56)
    font_col = _try_font(42)
    font_small = _try_font(26)

    # Layout
    pad = 70
    top = 140
    board_h = 820
    col_gap = 34
    col_w = (W - 2*pad - 2*col_gap) // 3
    col_h = board_h

    cols = [
        ("Backlog", COL_BACKLOG),
        ("WIP", COL_WIP),
        ("Done", COL_DONE),
    ]

    # Card counts (WIP intentionally overloaded)
    backlog_n = 6
    wip_n = 12
    done_n = 5

    # Precompute card positions per column
    card_pad_x = 26
    card_pad_y = 24
    card_h = 78
    card_gap = 14

    def col_box(idx):
        x0 = pad + idx*(col_w + col_gap)
        y0 = top
        x1 = x0 + col_w
        y1 = y0 + col_h
        return (x0,y0,x1,y1)

    for f in range(N_FRAMES):
        t = f / FPS

        img = Image.new("RGBA", (W, H), BG + (255,))
        d = ImageDraw.Draw(img)

        # Title
        d.text((pad, 48), "Delivery Flow", font=font_title, fill=INK)

        # Draw columns
        for i, (name, fill) in enumerate(cols):
            x0,y0,x1,y1 = col_box(i)
            filled_hand_panel(img, (x0,y0,x1,y1), fill=fill, outline=INK)

            # Column header
            d.text((x0+26, y0+18), name, font=font_col, fill=INK)
            # underline (hand-ish)
            d.line([(x0+26, y0+70), (x0+200, y0+70 + jitter(i, 2))], fill=INK, width=4)

        # Cards helper
        def draw_cards(col_i, n, overflow=False, phase=0.0):
            x0,y0,x1,y1 = col_box(col_i)
            cx0 = x0 + card_pad_x
            cy = y0 + 105 + card_pad_y

            for k in range(n):
                yy = cy + k*(card_h + card_gap)
                # If overflowing, compress visually and clip at bottom
                if overflow and yy + card_h > y1 - 26:
                    # stack into a "pile" near bottom to show too many cards
                    pile_y = y1 - 160
                    yy = pile_y + (k - (n-4)) * 10  # slight stacking
                # subtle bob animation
                yy += 2.2*math.sin(phase + k*0.9)

                card_box = (cx0, yy, x1 - card_pad_x, yy + card_h)

                # shadow
                sh = Image.new("RGBA", img.size, (0,0,0,0))
                sd = ImageDraw.Draw(sh)
                sd.rounded_rectangle((card_box[0]+4,card_box[1]+6,card_box[2]+4,card_box[3]+6),
                                     radius=14, fill=(0,0,0,40))
                sh = sh.filter(ImageFilter.GaussianBlur(5))
                img.alpha_composite(sh)

                d.rounded_rectangle(card_box, radius=14, fill=CARD)
                hand_rect(d, card_box, outline=INK, width=4, wobble=1.8)

                # scribble text
                draw_scribble(d, card_box[0]+18, card_box[1]+16, (card_box[2]-card_box[0])-36, 42,
                             color=(105,105,112), width=3, lines=2, phase=phase + k*0.6)

                # WIP stress indicator on some cards
                if col_i == 1 and k >= 7:
                    d.ellipse((card_box[2]-48, card_box[1]+14, card_box[2]-22, card_box[1]+40),
                              fill=(255, 214, 214), outline=WARN_RED, width=3)

        # Animate phases
        phase = t * 2.2
        draw_cards(0, backlog_n, overflow=False, phase=phase)
        draw_cards(1, wip_n, overflow=True, phase=phase + 0.7)  # overloaded WIP
        draw_cards(2, done_n, overflow=False, phase=phase + 1.2)

        # Red warning light (flashes)
        # Flash pattern: 2Hz for last ~6 seconds, always visible but toggles fill/brightness
        flash = 0.0
        if t >= 1.5:
            flash = 0.5 + 0.5 * math.sin(2 * math.pi * 2.0 * (t - 1.5))
        on = flash > 0.55

        lx, ly = W - 180, 52
        # base housing
        d.rounded_rectangle((lx-18, ly-10, lx+120, ly+86), radius=18, fill=(255,255,255), outline=INK, width=4)
        hand_rect(d, (lx-18, ly-10, lx+120, ly+86), outline=INK, width=4, wobble=1.5)

        # light
        if on:
            d.ellipse((lx+10, ly+10, lx+66, ly+66), fill=WARN_RED, outline=INK, width=4)
            # glow
            glow = Image.new("RGBA", img.size, (0,0,0,0))
            gd = ImageDraw.Draw(glow)
            gd.ellipse((lx-10, ly-10, lx+86, ly+86), fill=(220, 40, 50, 90))
            glow = glow.filter(ImageFilter.GaussianBlur(14))
            img.alpha_composite(glow)
        else:
            d.ellipse((lx+10, ly+10, lx+66, ly+66), fill=(255, 230, 232), outline=INK, width=4)

        d.text((lx+74, ly+22), "WIP", font=font_small, fill=INK)
        d.text((lx+74, ly+48), "HIGH", font=font_small, fill=WARN_RED if on else MUTED)

        # Add a subtle paper grain
        # (Cheap deterministic noise)
        px = img.load()
        for y in range(0, H, 2):
            for x in range(0, W, 2):
                n = int(6 * (0.5 + 0.5*math.sin((x*0.013) + (y*0.021) + t*0.7)))
                r,g,b,a = px[x,y]
                px[x,y] = (max(0, r-n), max(0, g-n), max(0, b-n), a)

        out_path = os.path.join(OUT_DIR, f"frame_{f:04d}.png")
        img.convert("RGB").save(out_path, "PNG")

    print(f"Generated {N_FRAMES} frames in {OUT_DIR}/")

if __name__ == "__main__":
    main()
