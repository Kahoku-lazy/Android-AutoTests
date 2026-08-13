"""
Screenshot annotator — draws AI operation markers (red rects, text labels)
onto Web execution screenshots using PIL.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

# ── Colour palette (RGBA) ──
AI_RED = (244, 67, 54, 230)  # click / fail outline
AI_BLUE = (33, 150, 243, 230)  # fill input outline
AI_GREEN = (76, 175, 80, 230)  # assert outline
AI_LABEL_BG = (0, 0, 0, 190)  # label background
AI_PASS = (76, 175, 80, 240)
AI_FAIL = (244, 67, 54, 240)
AI_WHITE = (255, 255, 255, 240)
AI_TEXT_DIM = (255, 255, 255, 180)

# ── Font ──
_FONT_CACHE: dict[int, ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}


def _get_font(size: int = 14) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    for path in candidates:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                _FONT_CACHE[size] = font
                return font
            except OSError:
                pass
    font = ImageFont.load_default()
    _FONT_CACHE[size] = font
    return font


def annotate_screenshot(
    image_path: str,
    step_index: int,
    step_type: str,
    step_desc: str,
    result: str,
    element_bounds: dict | None = None,
    error_msg: str = "",
) -> str:
    """Annotate a screenshot and save back to the same path.

    - click steps:  red rectangle around the clicked element + label
    - fill steps:   blue rectangle around the input + label
    - assert steps: green border on the page
    - fail:         red failure banner below the title strip
    """
    if not os.path.exists(image_path):
        return image_path

    img = Image.open(image_path).convert("RGBA")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    font = _get_font(13)
    small_font = _get_font(11)
    label_pad = 6  # padding inside label box

    # ── 1. Element-specific annotation (rect + label) ──
    label_text = ""
    outline_color = AI_RED
    box = None  # the rect we draw

    if element_bounds:
        x, y, ew, eh = (
            element_bounds["x"],
            element_bounds["y"],
            element_bounds.get("width", 0),
            element_bounds.get("height", 0),
        )
        if ew > 0 and eh > 0:
            if step_type in ("web_click", "click", "long_click"):
                outline_color = AI_RED
                box = [x, y, x + ew, y + eh]
                label_text = f"AI 点击"
            elif step_type in ("web_fill", "web_type"):
                outline_color = AI_BLUE
                box = [x, y, x + ew, y + eh]
                label_text = "AI 输入"
    else:
        # web_assert — draw full-page green border
        if step_type == "web_assert":
            m = 4
            outline_color = AI_GREEN
            box = [m, m, w - m, h - m]
            label_text = "AI 验证"

    if box is not None:
        # Draw the outline rect
        draw.rectangle(box, outline=outline_color, width=3)

        # Place label: prefer above the rect, fall back to below if near top
        bx, by, bx2, by2 = box
        text_w, text_h = _text_size(draw, label_text, font)
        lbl_w = text_w + label_pad * 2
        lbl_h = text_h + label_pad

        if by - lbl_h - 2 > 4:
            # above
            ly = by - lbl_h - 2
        else:
            # below
            ly = by2 + 2
        lx = max(2, min(bx, w - lbl_w - 2))

        draw.rectangle([lx, ly, lx + lbl_w, ly + lbl_h], fill=AI_LABEL_BG)
        draw.text((lx + label_pad, ly + label_pad // 2), label_text, fill=AI_WHITE, font=font)

    # ── 2. Top-left status strip ──
    header = f"Step {step_index + 1} · {_type_label(step_type)} · {result.upper()}"
    h_color = AI_PASS if result == "pass" else AI_FAIL
    tw, th = _text_size(draw, header, font)
    hw = tw + 16
    draw.rectangle([2, 2, hw, th + 14], fill=AI_LABEL_BG)
    draw.text((10, 5), header, fill=h_color, font=font)

    # ── 3. Bottom description strip ──
    desc = step_desc[:120]
    if desc:
        draw.rectangle([2, h - 26, w - 2, h - 2], fill=AI_LABEL_BG)
        draw.text((8, h - 22), desc, fill=AI_TEXT_DIM, font=small_font)

    # ── 4. Failure banner ──
    if result == "fail":
        fail = f"FAIL: {error_msg[:150]}" if error_msg else "FAIL"
        ftw, fth = _text_size(draw, fail, small_font)
        draw.rectangle([2, 30, w - 2, 30 + fth + 14], fill=(244, 67, 54, 200))
        draw.text((8, 34), fail, fill=AI_WHITE, font=small_font)

    img.save(image_path, "PNG")
    return image_path


def _text_size(draw, text: str, font) -> tuple[int, int]:
    """Get text dimensions. Returns (width, height)."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def _type_label(step_type: str) -> str:
    return {
        "web_navigate": "NAV",
        "web_click": "CLICK",
        "web_fill": "FILL",
        "web_type": "TYPE",
        "web_wait": "WAIT",
        "web_assert": "ASSERT",
        "web_screenshot": "SHOT",
        "web_step": "STEP",
        "click": "CLICK",
        "wait": "WAIT",
        "sleep": "SLEEP",
        "screenshot": "SHOT",
        "long_click": "LONG",
        "swipe": "SWIPE",
    }.get(step_type, step_type[:8].upper())
