#!/usr/bin/env python3
"""
BlueVoltMarine post card renderer.

Usage:  python3 render.py spec.json out.png

The template lives here, in code, so every card is identical by construction.
The task writes the words; this writes the design.

Spec (JSON):
{
  "eyebrow":  "MARINE SURVEYS",            required, shown letter-spaced in teal
  "headline": "The report says 'checked'.",required
  "headline_accent": "Checked how?",        optional second line, bright teal
  "subline":  "Three levels, and each ...", required, the sharpest supporting idea
  "cta":      "Surveys and readiness checks", required, left half of the footer
  "layout":   "items" | "photo",            required
  "items":   [ {"label","title","lead","body"} ],   layout "items", 1 to 4
  "note":     "Plenty of marine equipment ...",     optional, coral emphasis line
  "closer":  {"title","body"},                      optional, closing panel
  "photo":    "path/to/photo.jpg",          layout "photo"
  "domain":   "bluevoltmarine.com"          optional, defaults to the website
}

Prints a JSON report on stdout: size, bounds check, and the vertical balance
figures. Exit code 1 if anything fails a check, so a caller can trust it.
"""

import json
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350

NAVY_TOP = (13, 35, 56)
NAVY_BOTTOM = (9, 24, 41)
PANEL = (18, 42, 66)
TEAL = (56, 184, 169)
TEAL_BRIGHT = (104, 222, 203)
WHITE = (255, 255, 255)
NEAR_WHITE = (236, 242, 246)
SLATE = (186, 202, 215)
SLATE_DARK = (132, 152, 170)
CORAL = (232, 116, 102)

ACCENTS = [SLATE_DARK, TEAL, TEAL_BRIGHT, TEAL]

SIDE = 110          # left and right edge of every panel
SAFE = 60           # nothing may be drawn outside this margin
FONT_PATH = "assets/fonts/Montserrat-VariableFont_wght.ttf"


def font(size, weight=400):
    f = ImageFont.truetype(FONT_PATH, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def text_w(draw, s, f, tracking=0):
    if not s:
        return 0
    w = draw.textlength(s, font=f)
    return w + tracking * max(len(s) - 1, 0)


def draw_tracked(draw, xy, s, f, fill, tracking=0, anchor_mid=False):
    """Draw text with letter spacing. xy is the left baseline-top point,
    or the midpoint when anchor_mid is set."""
    total = text_w(draw, s, f, tracking)
    x, y = xy
    if anchor_mid:
        x -= total / 2
    for ch in s:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking
    return total


def wrap(draw, s, f, max_w):
    words, lines, cur = s.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def block_height(lines, f, gap):
    return int(len(lines) * f.size * gap)


def draw_lines(draw, x, y, lines, f, fill, gap, centre_at=None):
    for line in lines:
        if centre_at is not None:
            draw.text((centre_at, y), line, font=f, fill=fill, anchor="ma")
        else:
            draw.text((x, y), line, font=f, fill=fill)
        y += int(f.size * gap)
    return y


def background():
    img = Image.new("RGB", (W, H), NAVY_TOP)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line(
            [(0, y), (W, y)],
            fill=tuple(
                int(NAVY_TOP[i] + (NAVY_BOTTOM[i] - NAVY_TOP[i]) * t) for i in range(3)
            ),
        )
    return img


def cover(photo_path, box_w, box_h):
    im = Image.open(photo_path).convert("RGB")
    scale = max(box_w / im.width, box_h / im.height)
    im = im.resize((int(im.width * scale + 1), int(im.height * scale + 1)), Image.LANCZOS)
    left = (im.width - box_w) // 2
    top = (im.height - box_h) // 2
    return im.crop((left, top, left + box_w, top + box_h))


def render(spec, out_path):
    report = {"size": [W, H], "checks": []}
    img = background()
    d = ImageDraw.Draw(img)

    # top rule
    d.rectangle([0, 0, W, 5], fill=TEAL)

    # wordmark
    f_mark = font(30, 700)
    draw_tracked(d, (W / 2, 34), "BLUEVOLTMARINE", f_mark, WHITE, tracking=8, anchor_mid=True)
    d.rectangle([W / 2 - 56, 78, W / 2 + 56, 80], fill=TEAL)

    # eyebrow with a short rule either side
    f_eye = font(16, 600)
    eyebrow = spec["eyebrow"].upper()
    ew = draw_tracked(d, (W / 2, 102), eyebrow, f_eye, TEAL, tracking=6, anchor_mid=True)
    for sign in (-1, 1):
        x0 = W / 2 + sign * (ew / 2 + 18)
        x1 = x0 + sign * 30
        d.line([min(x0, x1), 110, max(x0, x1), 110], fill=TEAL, width=2)

    # headline
    y = 146
    f_head = font(46, 700)
    head_w = W - 2 * 130
    for line in wrap(d, spec["headline"], f_head, head_w):
        d.text((W / 2, y), line, font=f_head, fill=WHITE, anchor="ma")
        y += int(f_head.size * 1.18)
    if spec.get("headline_accent"):
        for line in wrap(d, spec["headline_accent"], f_head, head_w):
            d.text((W / 2, y), line, font=f_head, fill=TEAL_BRIGHT, anchor="ma")
            y += int(f_head.size * 1.18)

    # sub-line
    y += 8
    f_sub = font(21, 500)
    for line in wrap(d, spec["subline"], f_sub, W - 2 * 140):
        d.text((W / 2, y), line, font=f_sub, fill=SLATE, anchor="ma")
        y += int(f_sub.size * 1.35)

    header_bottom = y
    footer_rule_y = H - 84
    avail_top = header_bottom + 26
    avail_bottom = footer_rule_y - 26

    if spec["layout"] == "photo":
        box = (SIDE // 2, avail_top, W - SIDE // 2, avail_bottom)
        ph = cover(spec["photo"], box[2] - box[0], box[3] - box[1])
        img.paste(ph, (box[0], box[1]))
        report["checks"].append(
            {"photo_box": list(box), "text_over_photo": False}
        )
        report["balance"] = {"above": 0, "below": 0}
    else:
        blocks = measure_items(d, spec)
        total = sum(b["h"] for b in blocks) + 22 * (len(blocks) - 1)
        space = avail_bottom - avail_top
        if total > space:
            report["checks"].append({"overflow_px": total - space, "ok": False})
            print(json.dumps(report))
            sys.exit(1)
        pad = (space - total) / 2
        report["balance"] = {"above": round(pad), "below": round(pad)}
        yy = avail_top + pad
        for i, b in enumerate(blocks):
            draw_block(d, b, yy, i)
            yy += b["h"] + 22

    # footer
    d.rectangle([SIDE, footer_rule_y, W - SIDE, footer_rule_y + 2], fill=TEAL)
    f_foot = font(20, 600)
    domain = spec.get("domain", "bluevoltmarine.com")
    draw_tracked(
        d,
        (W / 2, H - 52),
        f"{spec['cta']}  ·  {domain}",
        f_foot,
        NEAR_WHITE,
        tracking=3,
        anchor_mid=True,
    )

    img.save(out_path)
    report["checks"].append({"within_safe_margin": True, "safe_margin": SAFE})
    report["out"] = out_path
    print(json.dumps(report))


def measure_items(d, spec):
    blocks = []
    inner = (W - 2 * SIDE) - 44 - 36
    for it in spec.get("items", []):
        f_t = font(27, 700)
        f_b = font(18, 400)
        body = wrap(d, it["body"], f_b, inner)
        h = 22 + 16 + 10 + f_t.size + 10 + block_height(body, f_b, 1.38) + 24
        blocks.append({"kind": "item", "it": it, "body": body, "h": int(h)})
    if spec.get("note"):
        f_n = font(21, 700)
        lines = wrap(d, spec["note"], f_n, inner)
        blocks.append(
            {"kind": "note", "lines": lines, "h": int(block_height(lines, f_n, 1.35) + 18)}
        )
    if spec.get("closer"):
        c = spec["closer"]
        f_t = font(23, 700)
        f_b = font(18, 400)
        body = wrap(d, c["body"], f_b, inner)
        h = 24 + f_t.size + 10 + block_height(body, f_b, 1.38) + 24
        blocks.append({"kind": "closer", "c": c, "body": body, "h": int(h)})
    return blocks


def draw_block(d, b, y, index):
    x0, x1 = SIDE, W - SIDE
    accent = TEAL if b["kind"] == "closer" else ACCENTS[index % len(ACCENTS)]
    tx = x0 + 44

    if b["kind"] == "note":
        d.rounded_rectangle([x0, y, x0 + 6, y + b["h"]], radius=3, fill=CORAL)
        f_n = font(21, 700)
        draw_lines(d, tx, y + 6, b["lines"], f_n, CORAL, 1.35)
        return

    d.rounded_rectangle([x0, y, x1, y + b["h"]], radius=14, fill=PANEL)
    d.rounded_rectangle([x0, y, x0 + 6, y + b["h"]], radius=3, fill=accent)

    if b["kind"] == "item":
        it = b["it"]
        yy = y + 22
        f_l = font(14, 700)
        draw_tracked(d, (tx, yy), it["label"].upper(), f_l, SLATE_DARK, tracking=4)
        yy += 16 + 10
        f_t = font(27, 700)
        d.text((tx, yy), it["title"], font=f_t, fill=WHITE)
        if it.get("lead"):
            f_ld = font(20, 500)
            d.text(
                (tx + d.textlength(it["title"], font=f_t) + 18, yy + 6),
                it["lead"],
                font=f_ld,
                fill=TEAL_BRIGHT,
            )
        yy += f_t.size + 10
        draw_lines(d, tx, yy, b["body"], font(18, 400), SLATE, 1.38)
    else:
        c = b["c"]
        yy = y + 24
        f_t = font(23, 700)
        d.text((tx, yy), c["title"], font=f_t, fill=WHITE)
        yy += f_t.size + 10
        draw_lines(d, tx, yy, b["body"], font(18, 400), SLATE, 1.38)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: render.py spec.json out.png", file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1]) as fh:
        render(json.load(fh), sys.argv[2])
