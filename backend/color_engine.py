"""
RoomRatio Color Engine
======================
Core AI logic for extracting colors from room images
and mapping them to the 60-30-10 interior design rule.
"""

import io
import math
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans


# ─── Color Utilities ───────────────────────────────────────────────────────────

def rgb_to_hex(rgb: tuple) -> str:
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hsl(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    cmax, cmin = max(r, g, b), min(r, g, b)
    delta = cmax - cmin
    l = (cmax + cmin) / 2
    s = 0 if delta == 0 else delta / (1 - abs(2 * l - 1))
    if delta == 0:
        h = 0
    elif cmax == r:
        h = 60 * (((g - b) / delta) % 6)
    elif cmax == g:
        h = 60 * (((b - r) / delta) + 2)
    else:
        h = 60 * (((r - g) / delta) + 4)
    return h, s * 100, l * 100


def color_distance(c1: tuple, c2: tuple) -> float:
    """Euclidean distance in RGB space."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def get_color_name(rgb: tuple) -> str:
    """Map an RGB value to a human-readable color name."""
    r, g, b = rgb
    h, s, l = rgb_to_hsl(r, g, b)

    if l < 15:
        return "Near Black"
    if l > 88:
        return "Near White"
    if s < 12:
        if l < 35:
            return "Dark Gray"
        if l < 60:
            return "Medium Gray"
        return "Light Gray"

    if h < 15 or h >= 345:
        return "Red" if s > 50 else "Dusty Rose"
    if h < 40:
        return "Orange" if s > 60 else "Terracotta"
    if h < 65:
        return "Yellow" if s > 60 else "Warm Beige"
    if h < 80:
        return "Yellow-Green"
    if h < 150:
        return "Green" if s > 50 else "Sage Green"
    if h < 175:
        return "Teal"
    if h < 210:
        return "Cyan"
    if h < 260:
        return "Blue" if s > 50 else "Steel Blue"
    if h < 290:
        return "Indigo"
    if h < 330:
        return "Purple" if s > 50 else "Mauve"
    return "Pink"


def get_color_role(rgb: tuple) -> str:
    """Classify color as warm, cool, or neutral for design guidance."""
    r, g, b = rgb
    h, s, l = rgb_to_hsl(r, g, b)
    if s < 15 or l > 85 or l < 10:
        return "neutral"
    if 30 <= h <= 200:
        return "cool"
    return "warm"


# ─── Main Color Extraction ──────────────────────────────────────────────────────

def extract_colors_from_image(image_bytes: bytes, n_colors: int = 7) -> list[dict]:
    """
    Extract dominant colors from a room image using K-Means clustering.
    Returns colors sorted by visual dominance (percentage of image).
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Resize for speed — 300px wide is plenty for color analysis
    max_size = 300
    ratio = max_size / max(img.size)
    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
    img = img.resize(new_size, Image.LANCZOS)

    # Convert to numpy array and reshape for clustering
    pixels = np.array(img).reshape(-1, 3).astype(float)

    # Remove near-white and near-black pixels (background/shadows)
    mask = (
        (pixels.max(axis=1) < 245) &   # not near-white
        (pixels.min(axis=1) > 10)       # not near-black
    )
    filtered = pixels[mask]

    # Fall back to all pixels if too few remain
    if len(filtered) < 100:
        filtered = pixels

    # K-Means clustering to find dominant colors
    k = min(n_colors, len(filtered) // 10)
    k = max(k, 3)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=200)
    kmeans.fit(filtered)

    centers = kmeans.cluster_centers_
    labels = kmeans.labels_
    counts = np.bincount(labels)
    total = counts.sum()

    colors = []
    for i, (center, count) in enumerate(zip(centers, counts)):
        rgb = tuple(int(c) for c in center)
        pct = round(float(count) / total * 100, 1)
        colors.append({
            "rgb": rgb,
            "hex": rgb_to_hex(rgb),
            "percentage": pct,
            "name": get_color_name(rgb),
            "role": get_color_role(rgb),
        })

    # Sort by percentage descending
    colors.sort(key=lambda x: x["percentage"], reverse=True)
    return colors


# ─── 60-30-10 Ratio Engine ──────────────────────────────────────────────────────

def assign_ratio_zones(colors: list[dict]) -> dict:
    """
    Map extracted colors to 60-30-10 zones.
    
    Strategy:
    - 60% (Dominant): Largest color cluster — walls, floors, large furniture
    - 30% (Secondary): Mid-size clusters — sofas, bed, curtains  
    - 10% (Accent): Smallest clusters — doors, trims, accessories
    """
    if not colors:
        return {"dominant": [], "secondary": [], "accent": []}

    total_colors = len(colors)

    if total_colors == 1:
        return {"dominant": colors, "secondary": [], "accent": []}

    if total_colors == 2:
        return {"dominant": [colors[0]], "secondary": [colors[1]], "accent": []}

    # Dynamically split based on cumulative percentage
    dominant, secondary, accent = [], [], []
    cumulative = 0.0

    for color in colors:
        cumulative += color["percentage"]
        if cumulative <= 62:
            dominant.append(color)
        elif cumulative <= 92:
            secondary.append(color)
        else:
            accent.append(color)

    # Ensure at least one color per zone
    if not dominant and colors:
        dominant = [colors[0]]
    if not secondary and len(colors) > 1:
        secondary = [colors[1]]
    if not accent and len(colors) > 2:
        accent = [colors[2]]

    return {"dominant": dominant, "secondary": secondary, "accent": accent}


def calculate_ratio_score(zones: dict) -> dict:
    """
    Score how closely the room matches the ideal 60-30-10 rule.
    Returns a score from 0-100 and a breakdown.
    """
    def zone_pct(zone_colors):
        return sum(c["percentage"] for c in zone_colors)

    dom_pct = zone_pct(zones["dominant"])
    sec_pct = zone_pct(zones["secondary"])
    acc_pct = zone_pct(zones["accent"])

    # Ideal targets
    targets = {"dominant": 60, "secondary": 30, "accent": 10}

    # Calculate deviation from ideal
    dom_dev = abs(dom_pct - targets["dominant"])
    sec_dev = abs(sec_pct - targets["secondary"])
    acc_dev = abs(acc_pct - targets["accent"])

    # Score: 100 = perfect, deductions for deviation
    score = max(0, 100 - (dom_dev * 0.8) - (sec_dev * 0.6) - (acc_dev * 0.4))

    return {
        "score": round(score),
        "dominant_pct": round(dom_pct, 1),
        "secondary_pct": round(sec_pct, 1),
        "accent_pct": round(acc_pct, 1),
        "targets": targets,
        "grade": "Excellent" if score >= 85 else "Good" if score >= 65 else "Fair" if score >= 45 else "Needs Work",
    }


# ─── Palette Suggestions ────────────────────────────────────────────────────────

def generate_suggestions(zones: dict, score: dict) -> list[str]:
    """Generate actionable design suggestions based on ratio analysis."""
    suggestions = []

    dom = score["dominant_pct"]
    sec = score["secondary_pct"]
    acc = score["accent_pct"]

    if dom < 50:
        suggestions.append(
            f"Your dominant color covers only {dom}% of the room. "
            "Consider painting more wall area or adding a larger area rug in your base color to hit the 60% target."
        )
    elif dom > 72:
        suggestions.append(
            f"Your dominant color is overwhelming at {dom}%. "
            "Introduce more secondary color through curtains or a sofa to bring it closer to 60%."
        )

    if sec < 20:
        suggestions.append(
            f"Your secondary color is under-represented at {sec}%. "
            "Add a statement sofa, bed frame, or curtains in your secondary color to reach 30%."
        )
    elif sec > 42:
        suggestions.append(
            f"Your secondary color is too strong at {sec}%. "
            "Swap some furniture pieces to your dominant color to restore balance."
        )

    if acc < 5:
        suggestions.append(
            "Your accent is barely visible. Add bold accessories — cushions, artwork, "
            "plants, or a feature door — in your accent color for that 10% pop."
        )
    elif acc > 18:
        suggestions.append(
            f"Your accent color is taking up {acc}% — more than it should. "
            "Reduce bold accessories or repaint trim/doors in a more neutral tone."
        )

    if score["score"] >= 85:
        suggestions.append(
            "Your room is beautifully balanced! Minor tweaks to accent placement could make it perfect."
        )

    return suggestions


# ─── Complementary Palette Generator ───────────────────────────────────────────

def generate_complementary_palette(dominant_hex: str) -> dict:
    """
    Given a dominant color, suggest secondary and accent colors
    using color theory (complementary, analogous, triadic).
    """
    r, g, b = hex_to_rgb(dominant_hex)
    h, s, l = rgb_to_hsl(r, g, b)

    def hsl_to_rgb(h, s, l):
        s, l = s / 100, l / 100
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c / 2
        if h < 60:   r1, g1, b1 = c, x, 0
        elif h < 120: r1, g1, b1 = x, c, 0
        elif h < 180: r1, g1, b1 = 0, c, x
        elif h < 240: r1, g1, b1 = 0, x, c
        elif h < 300: r1, g1, b1 = x, 0, c
        else:         r1, g1, b1 = c, 0, x
        return (int((r1 + m) * 255), int((g1 + m) * 255), int((b1 + m) * 255))

    # Analogous secondary: +30° on color wheel, slightly desaturated
    secondary_h = (h + 30) % 360
    secondary_rgb = hsl_to_rgb(secondary_h, max(s * 0.8, 20), min(l * 1.1, 75))

    # Triadic accent: +120°, more saturated
    accent_h = (h + 120) % 360
    accent_rgb = hsl_to_rgb(accent_h, min(s * 1.2, 90), max(l * 0.85, 25))

    return {
        "dominant": {"hex": dominant_hex, "name": get_color_name(hex_to_rgb(dominant_hex))},
        "secondary": {"hex": rgb_to_hex(secondary_rgb), "name": get_color_name(secondary_rgb)},
        "accent": {"hex": rgb_to_hex(accent_rgb), "name": get_color_name(accent_rgb)},
    }


# ─── Full Analysis Pipeline ─────────────────────────────────────────────────────

def analyze_room(image_bytes: bytes) -> dict:
    """
    Full RoomRatio analysis pipeline.
    1. Extract colors from image
    2. Assign to 60-30-10 zones
    3. Score the balance
    4. Generate suggestions
    5. Suggest complementary palette
    """
    colors = extract_colors_from_image(image_bytes)
    zones = assign_ratio_zones(colors)
    score = calculate_ratio_score(zones)
    suggestions = generate_suggestions(zones, score)
    
    # Use top dominant color to generate ideal palette
    dominant_hex = zones["dominant"][0]["hex"] if zones["dominant"] else "#C8A882"
    ideal_palette = generate_complementary_palette(dominant_hex)

    # Flatten zones for response with element hints
    element_map = {
        "dominant": ["Walls", "Flooring", "Large Furniture"],
        "secondary": ["Sofa / Bed", "Curtains", "Cabinets"],
        "accent": ["Doors & Trims", "Cushions", "Accessories"],
    }

    zones_output = {}
    for zone_name, zone_colors in zones.items():
        zones_output[zone_name] = {
            "colors": zone_colors,
            "target_pct": {"dominant": 60, "secondary": 30, "accent": 10}[zone_name],
            "actual_pct": score[f"{zone_name}_pct"],
            "elements": element_map[zone_name],
        }

    return {
        "colors_extracted": colors,
        "zones": zones_output,
        "score": score,
        "suggestions": suggestions,
        "ideal_palette": ideal_palette,
        "total_colors_found": len(colors),
    }
