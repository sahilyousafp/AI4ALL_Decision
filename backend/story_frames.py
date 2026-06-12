"""
Fetch the REAL georeferenced aerial keyframes for Story mode.

Pulls El Prat airport + Llobregat delta from IGN PNOA histórico WMS at ONE fixed
web-mercator bbox (16:9), identical pixel size per year, so every frame is in
exact registration. These are the real conditioning images for the Higgsfield
cinematic restyle pass — no AI here, just true orthophotos.

Run from repo root:  python backend/story_frames.py
"""
from __future__ import annotations

import math
from pathlib import Path

import requests

WMS = "https://www.ign.es/wms/pnoa-historico?"

# Real IGN historical layers covering the delta, oldest -> newest.
# (label_year, wms_layer)
FRAMES: list[tuple[int, str]] = [
    (1956, "AMS_1956-1957"),
    (1997, "OLISTAT"),
    (2002, "SIGPAC"),
    (2008, "PNOA2008"),
    (2015, "PNOA2015"),
    (2021, "PNOA2021"),
]

# Frame centred on El Prat airport + the Llobregat delta wetlands/farmland.
CENTER_LON = 2.0775
CENTER_LAT = 41.2940
LON_HALF = 0.0520          # ~ +/- 4.3 km E-W
PX_W, PX_H = 1600, 900     # 16:9

R = 6378137.0


def _merc_x(lon: float) -> float:
    return R * math.radians(lon)


def _merc_y(lat: float) -> float:
    return R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def _inv_merc_y(y: float) -> float:
    return math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)


def _bbox_3857() -> tuple[float, float, float, float, float, float, float, float]:
    """Return (minx,miny,maxx,maxy) in mercator + (W,S,E,N) in lon/lat, 16:9."""
    w_lon = CENTER_LON - LON_HALF
    e_lon = CENTER_LON + LON_HALF
    minx, maxx = _merc_x(w_lon), _merc_x(e_lon)
    width_m = maxx - minx
    height_m = width_m * PX_H / PX_W            # lock to 16:9
    cy = _merc_y(CENTER_LAT)
    miny, maxy = cy - height_m / 2, cy + height_m / 2
    s_lat, n_lat = _inv_merc_y(miny), _inv_merc_y(maxy)
    return minx, miny, maxx, maxy, w_lon, s_lat, e_lon, n_lat


def fetch() -> None:
    minx, miny, maxx, maxy, w, s, e, n = _bbox_3857()
    out = Path(__file__).resolve().parents[1] / "frontend" / "public" / "assets" / "story" / "real"
    out.mkdir(parents=True, exist_ok=True)

    print(f"latlng bounds  S,W = {s:.5f},{w:.5f}   N,E = {n:.5f},{e:.5f}")
    print(f"mercator bbox  {minx:.1f},{miny:.1f},{maxx:.1f},{maxy:.1f}\n")

    for year, layer in FRAMES:
        params = {
            "service": "WMS",
            "request": "GetMap",
            "version": "1.1.1",
            "layers": layer,
            "styles": "",
            "srs": "EPSG:3857",
            "bbox": f"{minx},{miny},{maxx},{maxy}",
            "width": PX_W,
            "height": PX_H,
            "format": "image/jpeg",
        }
        url = WMS + "&".join(f"{k}={v}" for k, v in params.items())
        try:
            r = requests.get(url, timeout=90)
            r.raise_for_status()
            ctype = r.headers.get("content-type", "")
            if "image" not in ctype:
                print(f"  {year} {layer:28} -> NOT IMAGE ({ctype}): {r.text[:160]}")
                continue
            path = out / f"{year}.jpg"
            path.write_bytes(r.content)
            print(f"  {year} {layer:28} -> {path.name}  {len(r.content)//1024} KB")
        except Exception as exc:  # noqa: BLE001
            print(f"  {year} {layer:28} -> FAILED: {exc}")

    # Write the bbox so the frontend can geo-pin the overlay exactly.
    meta = out / "bounds.json"
    meta.write_text(
        f'{{"south": {s:.6f}, "west": {w:.6f}, "north": {n:.6f}, "east": {e:.6f}, '
        f'"years": {[y for y, _ in FRAMES]}}}\n'
    )
    print(f"\nwrote {meta}")


if __name__ == "__main__":
    fetch()
