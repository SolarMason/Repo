#!/usr/bin/env python3
"""
Solar Mason brand asset generator.

Generates everything from a single design spec:
  - icon-180.png             (Apple touch icon, full-bleed for iOS)
  - icon-192.png             (PWA icon, manifest)
  - icon-512.png             (PWA large icon, manifest)
  - icon-maskable-512.png    (Android adaptive icon with safe zone)
  - favicon-32.png           (browser tab favicon)
  - favicon.ico              (multi-size legacy favicon)
  - og-image.png             (1200x630 social share card)

Run: python3 build-assets.py
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT_DIR = os.path.join(os.path.dirname(__file__), '.')

# =====================================================================
# Brand palette (Solar Mason)
# =====================================================================
ORANGE   = (255, 159, 10)   # warm accent
RED      = (255, 59, 48)    # deep accent
DARKEN   = (180, 30, 25)    # bottom-right shade for the gradient
WHITE    = (255, 255, 255)
SOFT_W   = (255, 255, 255, 235)
DIM_W    = (255, 255, 255, 160)


# =====================================================================
# Helpers
# =====================================================================

def load_font(size, weight='bold'):
    """Try Inter (preferred), fall back to DejaVu Sans."""
    candidates = {
        'bold':     ['Inter-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'],
        'semibold': ['Inter-SemiBold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'],
        'medium':   ['Inter-Medium.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],
        'regular':  ['Inter-Regular.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],
    }
    for path in candidates.get(weight, []):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def make_gradient(size, c1, c2, c3=None):
    """Diagonal three-stop gradient: c1 (top-left) -> c2 (mid) -> c3 (bottom-right)."""
    w, h = size
    img = Image.new('RGB', size, c1)
    px = img.load()

    if c3 is None:
        c3 = c2
        c2 = tuple((a + b) // 2 for a, b in zip(c1, c3))

    diag = math.sqrt(w*w + h*h)
    for y in range(h):
        for x in range(w):
            # 0 at top-left, 1 at bottom-right
            t = (x + y) / (w + h)
            if t < 0.5:
                # interpolate c1 -> c2
                u = t * 2
                r = int(c1[0] * (1-u) + c2[0] * u)
                g = int(c1[1] * (1-u) + c2[1] * u)
                b = int(c1[2] * (1-u) + c2[2] * u)
            else:
                # interpolate c2 -> c3
                u = (t - 0.5) * 2
                r = int(c2[0] * (1-u) + c3[0] * u)
                g = int(c2[1] * (1-u) + c3[1] * u)
                b = int(c2[2] * (1-u) + c3[2] * u)
            px[x, y] = (r, g, b)
    return img


def rounded_mask(size, radius):
    """Solid alpha mask with rounded corners."""
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0]-1, size[1]-1), radius=radius, fill=255)
    return mask


def draw_sun_with_panels(canvas, cx, cy, sun_radius, ray_len, panel_width, stroke):
    """Draw the Solar Mason brand mark: sun above three solar-panel slats.
       canvas: ImageDraw on an RGBA image with transparent background sublayer."""

    # ---- Rays (8 rays around the sun) -----------------------------------
    ray_inner = sun_radius + sun_radius * 0.30  # gap between sun and ray start
    ray_outer = ray_inner + ray_len
    # Rays at compass + diagonal positions (skip bottom — panels go there)
    ray_angles_deg = [-90, -45, 0, 45, 90 + 30, 90 - 30, 180, 180 + 45]  # 8 rays, biased upward
    ray_angles_deg = [0, 45, 90, 135, 180, 225, 270, 315]  # cleaner: even distribution
    # Hide the two bottom-pointing rays so they don't conflict with panels
    hidden = {90}  # straight down

    for ang in ray_angles_deg:
        if ang in hidden:
            continue
        rad = math.radians(ang - 90)  # 0 = up
        x1 = cx + ray_inner * math.cos(rad)
        y1 = cy + ray_inner * math.sin(rad)
        x2 = cx + ray_outer * math.cos(rad)
        y2 = cy + ray_outer * math.sin(rad)
        canvas.line([(x1, y1), (x2, y2)], fill=WHITE, width=stroke)

    # ---- Sun body --------------------------------------------------------
    canvas.ellipse(
        [cx - sun_radius, cy - sun_radius, cx + sun_radius, cy + sun_radius],
        fill=WHITE
    )

    # ---- Solar panel slats below the sun --------------------------------
    panel_top = cy + sun_radius + ray_len + sun_radius * 0.20
    slat_h = stroke
    slat_gap = stroke * 1.4
    for i in range(3):
        y = panel_top + i * (slat_h + slat_gap)
        # Tapered slats: middle one widest (perspective hint)
        taper = 1.0 - abs(i - 1) * 0.10
        half = panel_width * taper / 2
        canvas.rounded_rectangle(
            [cx - half, y, cx + half, y + slat_h],
            radius=slat_h / 2,
            fill=WHITE
        )


def render_icon(size_px, corner_radius_ratio=0.225, safe_zone_ratio=0.0):
    """
    Render the master Solar Mason icon at any pixel size.
    safe_zone_ratio: 0 = full bleed (Apple touch / Android any),
                     0.10 = 10% inset for adaptive maskable icons.
    """
    # Render at 2x for supersampling, then downscale for clean edges
    SS = 2
    W = size_px * SS
    radius = int(W * corner_radius_ratio)

    # Build the gradient background
    bg = make_gradient((W, W), ORANGE, RED, DARKEN)

    # Subtle inner highlight for premium feel — a top-left soft ellipse
    highlight = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.ellipse(
        [-W * 0.4, -W * 0.6, W * 0.7, W * 0.4],
        fill=(255, 220, 180, 70)
    )
    highlight = highlight.filter(ImageFilter.GaussianBlur(W * 0.06))
    bg = bg.convert('RGBA')
    bg = Image.alpha_composite(bg, highlight)

    # Brand mark layer
    mark_layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    md = ImageDraw.Draw(mark_layer)

    cx = cy = W / 2
    # If maskable, the inner content must fit in the safe zone (centered ~80%)
    content_scale = 1.0 - (safe_zone_ratio * 2)

    sun_radius  = W * 0.13 * content_scale
    ray_len     = W * 0.07 * content_scale
    panel_width = W * 0.42 * content_scale
    stroke      = max(2, int(W * 0.024 * content_scale))

    # Pull the whole composition slightly upward so the panels sit balanced
    cy_offset = -W * 0.03 * content_scale
    draw_sun_with_panels(md, cx, cy + cy_offset, sun_radius, ray_len, panel_width, stroke)

    # Soft glow behind the sun for warmth
    glow = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    glow_r = sun_radius * 1.8
    gd.ellipse(
        [cx - glow_r, cy + cy_offset - glow_r, cx + glow_r, cy + cy_offset + glow_r],
        fill=(255, 240, 200, 90)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(W * 0.04))

    composite = Image.alpha_composite(bg, glow)
    composite = Image.alpha_composite(composite, mark_layer)

    # Apply rounded corners (only for non-maskable icons; maskable must be square)
    if safe_zone_ratio == 0.0:
        mask = rounded_mask((W, W), radius)
        rounded = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        rounded.paste(composite, (0, 0), mask)
        composite = rounded

    # Downscale with high-quality filter
    return composite.resize((size_px, size_px), Image.LANCZOS)


# =====================================================================
# Assets
# =====================================================================

def build_icons():
    print("\n→ Icons")

    # Apple touch icon — iOS adds its own rounding, so we ship rounded too
    # (works fine; iOS just ignores its own rounding if image already round)
    img = render_icon(180, corner_radius_ratio=0.225)
    img.save(os.path.join(OUT_DIR, 'icon-180.png'), 'PNG', optimize=True)
    print(f"  icon-180.png         {os.path.getsize(os.path.join(OUT_DIR, 'icon-180.png')):>7} bytes")

    img = render_icon(192, corner_radius_ratio=0.225)
    img.save(os.path.join(OUT_DIR, 'icon-192.png'), 'PNG', optimize=True)
    print(f"  icon-192.png         {os.path.getsize(os.path.join(OUT_DIR, 'icon-192.png')):>7} bytes")

    img = render_icon(512, corner_radius_ratio=0.225)
    img.save(os.path.join(OUT_DIR, 'icon-512.png'), 'PNG', optimize=True)
    print(f"  icon-512.png         {os.path.getsize(os.path.join(OUT_DIR, 'icon-512.png')):>7} bytes")

    # Maskable: full bleed square, content in 80% safe zone
    img = render_icon(512, corner_radius_ratio=0.0, safe_zone_ratio=0.10)
    img.save(os.path.join(OUT_DIR, 'icon-maskable-512.png'), 'PNG', optimize=True)
    print(f"  icon-maskable-512.png{os.path.getsize(os.path.join(OUT_DIR, 'icon-maskable-512.png')):>7} bytes")

    # Favicon
    img = render_icon(32, corner_radius_ratio=0.20)
    img.save(os.path.join(OUT_DIR, 'favicon-32.png'), 'PNG', optimize=True)
    print(f"  favicon-32.png       {os.path.getsize(os.path.join(OUT_DIR, 'favicon-32.png')):>7} bytes")

    # ICO (multi-size)
    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    base = render_icon(48, corner_radius_ratio=0.20)
    base.save(os.path.join(OUT_DIR, 'favicon.ico'), format='ICO', sizes=ico_sizes)
    print(f"  favicon.ico          {os.path.getsize(os.path.join(OUT_DIR, 'favicon.ico')):>7} bytes")


def build_og_image():
    print("\n→ OG share card (1200x630)")

    W, H = 1200, 630
    bg = make_gradient((W, H), ORANGE, RED, DARKEN)
    bg = bg.convert('RGBA')

    # Subtle vignette
    vignette = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    vd.ellipse([-W * 0.2, -H * 0.4, W * 1.2, H * 1.2], fill=(0, 0, 0, 60))
    vignette = vignette.filter(ImageFilter.GaussianBlur(80))
    bg = Image.alpha_composite(bg, vignette)

    # Top-left highlight
    hl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([-200, -300, 700, 400], fill=(255, 220, 180, 80))
    hl = hl.filter(ImageFilter.GaussianBlur(120))
    bg = Image.alpha_composite(bg, hl)

    # Subtle solar-panel grid overlay (very faint white lines, lower-right)
    grid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    grid_origin_x = W - 380
    grid_origin_y = H - 320
    grid_w, grid_h = 360, 280
    # 6x4 grid of cells
    cols, rows = 6, 4
    cell_w = grid_w / cols
    cell_h = grid_h / rows
    for c in range(cols + 1):
        x = grid_origin_x + c * cell_w
        gd.line([(x, grid_origin_y), (x, grid_origin_y + grid_h)], fill=(255, 255, 255, 30), width=1)
    for r in range(rows + 1):
        y = grid_origin_y + r * cell_h
        gd.line([(grid_origin_x, y), (grid_origin_x + grid_w, y)], fill=(255, 255, 255, 30), width=1)
    bg = Image.alpha_composite(bg, grid)

    # ----- Compose icon on the left -----
    icon = render_icon(280, corner_radius_ratio=0.225)
    icon_x = 80
    icon_y = (H - 280) // 2
    bg.paste(icon, (icon_x, icon_y), icon)

    # ----- Text on the right -----
    canvas = ImageDraw.Draw(bg)

    text_x = icon_x + 280 + 50
    title_font    = load_font(96, 'bold')
    subtitle_font = load_font(40, 'medium')
    meta_font     = load_font(26, 'regular')
    url_font      = load_font(28, 'semibold')

    # Title: "Solar Mason"
    title = "Solar Mason"
    title_bbox = canvas.textbbox((0, 0), title, font=title_font)
    title_h = title_bbox[3] - title_bbox[1]

    # Subtitle: "Repository Dashboard"
    subtitle = "Repository Dashboard"
    sub_bbox = canvas.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_h = sub_bbox[3] - sub_bbox[1]

    # Meta: small descriptor
    meta = "Live · Auto-updating · 5-minute refresh"
    meta_bbox = canvas.textbbox((0, 0), meta, font=meta_font)
    meta_h = meta_bbox[3] - meta_bbox[1]

    # URL pill at the bottom
    url = "repo.nepa-pro.com"

    total_h = title_h + 14 + sub_h + 30 + meta_h
    text_y = (H - total_h) // 2 - 10  # nudge up slightly

    # Drop shadow for the title (subtle, for legibility)
    shadow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    sd.text((text_x + 3, text_y + 3), title, font=title_font, fill=(0, 0, 0, 80))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(4))
    bg = Image.alpha_composite(bg, shadow_layer)
    canvas = ImageDraw.Draw(bg)

    canvas.text((text_x, text_y), title, font=title_font, fill=WHITE)
    canvas.text((text_x, text_y + title_h + 14), subtitle, font=subtitle_font, fill=(255, 255, 255, 230))
    canvas.text((text_x, text_y + title_h + 14 + sub_h + 30), meta, font=meta_font, fill=(255, 255, 255, 180))

    # URL pill — bottom right
    pill_padding_x = 22
    pill_padding_y = 12
    url_bbox = canvas.textbbox((0, 0), url, font=url_font)
    url_w = url_bbox[2] - url_bbox[0]
    url_h = url_bbox[3] - url_bbox[1]
    pill_w = url_w + pill_padding_x * 2
    pill_h = url_h + pill_padding_y * 2
    pill_x = W - pill_w - 60
    pill_y = H - pill_h - 50

    # Draw pill background (rounded, semi-transparent white)
    pill_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill_layer)
    pd.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=pill_h // 2,
        fill=(255, 255, 255, 36),
        outline=(255, 255, 255, 100),
        width=1
    )
    bg = Image.alpha_composite(bg, pill_layer)
    canvas = ImageDraw.Draw(bg)
    canvas.text((pill_x + pill_padding_x, pill_y + pill_padding_y - 2), url, font=url_font, fill=WHITE)

    # Top-left brand tag
    tag_font = load_font(22, 'medium')
    tag = "NEPA-PRO · GITHUB"
    canvas.text((80, 60), tag, font=tag_font, fill=(255, 255, 255, 170))

    # Convert to RGB and save (OG cards should not have transparency)
    final = bg.convert('RGB')
    final.save(os.path.join(OUT_DIR, 'og-image.png'), 'PNG', optimize=True)
    print(f"  og-image.png         {os.path.getsize(os.path.join(OUT_DIR, 'og-image.png')):>7} bytes")


if __name__ == '__main__':
    build_icons()
    build_og_image()
    print("\n✓ All assets generated.")
