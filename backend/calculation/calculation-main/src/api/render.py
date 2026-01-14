from __future__ import annotations
import math
from typing import Dict, Any, List

def _lon_to_xy(abs_lon: float, cx: float, cy: float, r: float) -> tuple[float, float]:
    # Convert absolute longitude (0..360, Aries=0 at East?) to SVG coords.
    # We'll map 0° (Aries) to the right (east) and increase CCW so convert to radians with 90 - lon
    theta = math.radians(90.0 - (abs_lon % 360.0))
    x = cx + r * math.cos(theta)
    y = cy - r * math.sin(theta)
    return x, y


def chart_to_positions(chart: Any, size: int = 400) -> Dict[str, Any]:
    """Return simple positions for planets and house markers for a DivisionalChartOut-like object.
    This is minimal: uses absoluteLongitude when available, otherwise computes from houseAbs + rawLongitudeDeg.
    """
    cx = size / 2.0
    cy = size / 2.0
    r_planet = size * 0.36
    r_house = size * 0.48
    planets_out: List[Dict[str, Any]] = []
    houses_out: List[Dict[str, Any]] = []
    # Houses: use ascendant sign number as rotation base; place 12 ticks at sign centers
    try:
        asc_sign = getattr(chart, 'ascendantSignNumber', None)
        asc_abs = int(asc_sign) if asc_sign is not None else 1
    except Exception:
        asc_abs = 1

    # compute house angles: house i absolute sign number is (asc_abs-1 + i-1) % 12 -> center angle = signIndex*30 + 15
    for i in range(1, 13):
        sign_index = ((asc_abs - 1) + (i - 1)) % 12
        center_deg = sign_index * 30 + 15
        hx, hy = _lon_to_xy(center_deg, cx, cy, r_house)
        houses_out.append({'index': i, 'signNumber': sign_index + 1, 'x': hx, 'y': hy})

    # Planets
    for p in getattr(chart, 'planets', []) or []:
        abs_lon = None
        try:
            if getattr(p, 'absoluteLongitude', None) is not None:
                val = getattr(p, 'absoluteLongitude')
                if val is not None:
                    abs_lon = float(val)
            else:
                raw = getattr(p, 'rawLongitudeDeg', None)
                ha = getattr(p, 'houseAbs', None)
                if raw is not None:
                    rawf = float(raw)
                    if ha:
                        abs_lon = (int(ha) - 1) * 30.0 + rawf
                    else:
                        if rawf >= 30.0:
                            abs_lon = rawf
        except Exception:
            abs_lon = None
        if abs_lon is None:
            # fallback: place on outer circle evenly
            abs_lon = 360.0 * (len(planets_out) / max(1, len(getattr(chart,'planets',[]))))
        px, py = _lon_to_xy(abs_lon, cx, cy, r_planet)
        planets_out.append({'name': getattr(p, 'name', ''), 'x': px, 'y': py, 'abs_long': abs_lon})

    return {'size': size, 'center': {'x': cx, 'y': cy}, 'planets': planets_out, 'houses': houses_out}


def render_chart_svg(chart: Any, style: str = 'South', theme: str = 'Light', size: int = 400) -> str:
    """Render a minimal SVG for the given chart. Only implements South (circular) style for D1.
    Output is intentionally simple and safe to embed.
    """
    pos = chart_to_positions(chart, size=size)
    cx = pos['center']['x']
    cy = pos['center']['y']
    r_outer = size * 0.46
    r_inner = size * 0.18
    bg = '#ffffff' if theme == 'Light' else '#0b1220'
    fg = '#111827' if theme == 'Light' else '#e6eef8'
    accent = '#4f46e5'
    accent2 = '#059669'

    def avoid_collisions(labels: List[Dict[str, Any]], min_dist: float = 14.0):
        # Simple pairwise shift: if two labels are too close, shift the later label down
        placed: List[Dict[str, Any]] = []
        for lab in labels:
            x = lab['x']; y = lab['y'];
            for p in placed:
                dx = x - p['x']; dy = y - p['y'];
                d2 = dx*dx + dy*dy
                if d2 < (min_dist*min_dist):
                    # shift down by min_dist
                    y += min_dist
            placed.append({'x': x, 'y': y})
            lab['y'] = y
        return labels

    parts: List[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img" aria-label="Kundli chart">')
    parts.append(f'<rect width="100%" height="100%" fill="{bg}"/>')
    if style.lower() == 'south':
        # main circle
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" stroke="{fg}" stroke-width="1"/>')
        # inner circle
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" fill="none" stroke="{fg}" stroke-width="1"/>')
        # houses ticks and labels
        for h in pos['houses']:
            parts.append(f"<text x=\"{h['x']:.1f}\" y=\"{h['y']:.1f}\" fill=\"{fg}\" font-size=\"10\" text-anchor=\"middle\" dominant-baseline=\"middle\">{h['index']}</text>")
        # planets with collision avoidance
        labels = []
        for pl in pos['planets']:
            labels.append({'x': pl['x'], 'y': pl['y'] - 0, 'text': pl.get('name','')})
        labels = avoid_collisions(labels, min_dist=14.0)
        for i,pl in enumerate(pos['planets']):
            lx = pl['x']; ly = pl['y'];
            parts.append(f"<g class=\"planet\" data-name=\"{pl['name']}\">")
            parts.append(f"<circle cx=\"{lx:.1f}\" cy=\"{ly:.1f}\" r=\"8\" fill=\"{accent}\" stroke=\"{fg}\" stroke-width=\"0.8\"/>")
            lab = labels[i]
            parts.append(f"<text x=\"{lab['x']:.1f}\" y=\"{lab['y']+4:.1f}\" fill=\"white\" font-size=\"9\" text-anchor=\"middle\" dominant-baseline=\"middle\">{lab['text']}</text>")
            parts.append('</g>')
    else:
        # North-style: simple boxed 12-house layout
        pad = 12
        box = (size - pad*2) / 4.0
        # map house indices 1..12 to positions (visual North kundli ordering)
        # We'll arrange 3 rows x 4 cols and map houses in a common North layout order
        # Using a common mapping: index -> (col,row)
        mapping = {
            1: (1,0), 2: (0,1), 3: (1,1), 4: (2,1), 5: (3,1), 6: (0,2),
            7: (1,2), 8: (2,2), 9: (3,2), 10: (0,3), 11: (1,3), 12: (2,3)
        }
        # adjust for visual spacing
        for h in pos['houses']:
            idx = h['index']
            if idx not in mapping:
                # fallback: place around center
                x = cx + (idx-6)*20
                y = cy
            else:
                col,row = mapping[idx]
                x = pad + col*box + box/2
                y = pad + row*box + box/2
            parts.append(f"<rect x=\"{x-box/2:.1f}\" y=\"{y-box/2:.1f}\" width=\"{box:.1f}\" height=\"{box:.1f}\" fill=\"none\" stroke=\"{fg}\" stroke-width=\"1\"/>")
            parts.append(f"<text x=\"{x:.1f}\" y=\"{y- box/2 + 10:.1f}\" fill=\"{fg}\" font-size=\"11\" text-anchor=\"start\">{h['index']}</text>")
        # place planets inside their house boxes if possible
        for pl in pos['planets']:
            # find house center from houses list
            hidx = None
            try:
                hidx = int(getattr(pl, 'house', pl.get('house', None)))
            except Exception:
                hidx = None
            # fallback to nearest house by absolute longitude
            px = pl['x']; py = pl['y']
            # simple placement: draw small circle and label near a computed box
            parts.append(f"<circle cx=\"{px:.1f}\" cy=\"{py:.1f}\" r=\"6\" fill=\"{accent2}\" stroke=\"{fg}\" stroke-width=\"0.8\"/>")
            parts.append(f"<text x=\"{px+8:.1f}\" y=\"{py+3:.1f}\" fill=\"{fg}\" font-size=\"10\">{pl['name']}</text>")
    parts.append('</svg>')
    return '\n'.join(parts)
