from __future__ import annotations

import base64
import io
import json
import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urljoin
from xml.etree import ElementTree as ET

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ideology_agent_service import get_ideology_service, IdeologyQuestion, ScoringResult, IdeologyInterpretation

# Faster remote COG access for the change-detection endpoint.
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_MULTIPLEX", "YES")
os.environ.setdefault("VSI_CACHE", "TRUE")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif,.TIF")

app = FastAPI(title="AI4ALL Land Cover Viewer")

COLLECTION_URL = "https://s3.eu-central-1.wasabisys.com/stac/openlandmap/lc_glc.fcs30d/collection.json"
ASSET_KEY = "lc_glc.fcs30d_c_30m_s"
YEAR_LEFT = 1985
YEAR_RIGHT = 2022
MAP_CENTER = [41.2974, 2.0833]
DEFAULT_ZOOM = 12

# Delta bounding box for change detection: (west, south, east, north).
# Covers El Prat airport + the Llobregat delta wetlands and farmland.
CHANGE_BBOX = (1.980, 41.250, 2.220, 41.360)

# GLC_FCS30D class groupings.
CROP = {10, 11, 12, 20}
FOREST = {51, 52, 61, 62, 71, 72, 81, 82, 91, 92}
SHRUB_GRASS = {120, 121, 122, 130, 140, 150, 151, 152, 153}
WETLAND = {180, 181, 182, 183, 184, 185, 186, 187}
WATER = {210}
NATURE = CROP | FOREST | SHRUB_GRASS | WETLAND | WATER
BUILT = {190}  # impervious surfaces


class LegendItem(BaseModel):
    quantity: str
    label: str
    color: str


class LayerConfig(BaseModel):
    year: int
    tiles: str


class MapConfig(BaseModel):
    dataset_id: str
    dataset_label: str
    left: LayerConfig
    right: LayerConfig
    legend: list[LegendItem]
    center: list[float]
    zoom: int
    source: str


def _fetch_json(url: str, timeout: int = 45) -> dict[str, Any]:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _fetch_text(url: str, timeout: int = 60) -> str:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def _load_items_by_year() -> dict[int, dict[str, Any]]:
    collection = _fetch_json(COLLECTION_URL)
    items: dict[int, dict[str, Any]] = {}
    for link in collection.get("links", []):
        if link.get("rel") != "item":
            continue
        href = urljoin(COLLECTION_URL, link.get("href", ""))
        item = _fetch_json(href)
        match = re.search(r"(19|20)\d{2}", item.get("id", ""))
        if match:
            items[int(match.group(0))] = item
    return items


def _parse_sld(sld_url: str) -> list[LegendItem]:
    sld_xml = _fetch_text(sld_url)
    root = ET.fromstring(sld_xml)

    entries: list[LegendItem] = []
    for node in root.iter():
        if not node.tag.endswith("ColorMapEntry"):
            continue
        quantity = (node.attrib.get("quantity") or "").strip()
        color = (node.attrib.get("color") or "").strip()
        if not quantity or not color:
            continue
        label = (node.attrib.get("label") or quantity).strip()
        entries.append(LegendItem(quantity=quantity, label=label, color=color))

    entries.sort(key=lambda x: float(x.quantity))
    return entries


def _build_tile_url(asset_href: str, legend: list[LegendItem]) -> str:
    colormap = {entry.quantity: entry.color for entry in legend}
    url = f"https://titiler.xyz/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?url={quote_plus(asset_href)}"
    if colormap:
        encoded_colormap = quote_plus(json.dumps(colormap, separators=(",", ":")))
        url += f"&colormap={encoded_colormap}"
    return url


@lru_cache(maxsize=1)
def _build_map_config() -> MapConfig:
    items_by_year = _load_items_by_year()
    missing_years = [year for year in (YEAR_LEFT, YEAR_RIGHT) if year not in items_by_year]
    if missing_years:
        raise RuntimeError(f"Missing required year(s): {', '.join(str(y) for y in missing_years)}")

    left_item = items_by_year[YEAR_LEFT]
    right_item = items_by_year[YEAR_RIGHT]

    left_asset = left_item.get("assets", {}).get(ASSET_KEY, {}).get("href")
    right_asset = right_item.get("assets", {}).get(ASSET_KEY, {}).get("href")
    if not left_asset or not right_asset:
        raise RuntimeError(f"Asset '{ASSET_KEY}' missing in selected years.")

    sld_url = left_item.get("assets", {}).get("sld", {}).get("href")
    if not sld_url:
        raise RuntimeError("SLD legend asset was not found.")

    legend = _parse_sld(sld_url)
    return MapConfig(
        dataset_id="glc_fcs30d",
        dataset_label=f"Global Land Cover (GLC_FCS30D) {YEAR_LEFT} vs {YEAR_RIGHT}",
        left=LayerConfig(year=YEAR_LEFT, tiles=_build_tile_url(left_asset, legend)),
        right=LayerConfig(year=YEAR_RIGHT, tiles=_build_tile_url(right_asset, legend)),
        legend=legend,
        center=MAP_CENTER,
        zoom=DEFAULT_ZOOM,
        source="OpenLandMap / TiTiler / STAC",
    )


@lru_cache(maxsize=1)
def _get_change_assets() -> tuple[str, str]:
    """COG hrefs for the two years used by change detection."""
    items_by_year = _load_items_by_year()
    left = items_by_year.get(YEAR_LEFT, {}).get("assets", {}).get(ASSET_KEY, {}).get("href")
    right = items_by_year.get(YEAR_RIGHT, {}).get("assets", {}).get(ASSET_KEY, {}).get("href")
    if not left or not right:
        raise RuntimeError("Land-cover COG asset missing for change detection.")
    return left, right


def _read_classes(href: str, bbox: tuple[float, float, float, float], width: int, height: int):
    """Read a COG window over bbox (WGS84) as a 2D array of class codes."""
    from rio_tiler.io import Reader

    with Reader(href) as reader:
        img = reader.part(
            bbox,
            bounds_crs="epsg:4326",
            dst_crs="epsg:4326",
            width=width,
            height=height,
            resampling_method="nearest",
        )
    return img.data[0]


@lru_cache(maxsize=1)
def _compute_change() -> dict[str, Any]:
    """Where 1985 natural land cover became 2022 built-up, with hectares lost."""
    import numpy as np
    from PIL import Image

    west, south, east, north = CHANGE_BBOX
    mean_lat = (south + north) / 2.0
    m_per_deg_lat = 111_320.0
    m_per_deg_lng = 111_320.0 * math.cos(math.radians(mean_lat))
    width_m = (east - west) * m_per_deg_lng
    height_m = (north - south) * m_per_deg_lat
    # ~40 m sampling resolution.
    cols = max(64, min(900, int(round(width_m / 40.0))))
    rows = max(64, min(900, int(round(height_m / 40.0))))

    left_href, right_href = _get_change_assets()
    a85 = _read_classes(left_href, CHANGE_BBOX, cols, rows)
    a22 = _read_classes(right_href, CHANGE_BBOX, cols, rows)

    nature_85 = np.isin(a85, list(NATURE))
    built_22 = np.isin(a22, list(BUILT))
    loss = nature_85 & built_22

    cell_area_ha = (width_m / cols) * (height_m / rows) / 10_000.0

    def _ha_where(mask) -> float:
        return round(float(np.count_nonzero(loss & mask)) * cell_area_ha, 1)

    breakdown = {
        "cropland": _ha_where(np.isin(a85, list(CROP))),
        "wetland": _ha_where(np.isin(a85, list(WETLAND))),
        "forest": _ha_where(np.isin(a85, list(FOREST))),
        "shrub_grass": _ha_where(np.isin(a85, list(SHRUB_GRASS))),
        "water": _ha_where(np.isin(a85, list(WATER))),
    }
    total_ha = round(float(np.count_nonzero(loss)) * cell_area_ha, 1)

    # Render the loss mask as a translucent red RGBA PNG (transparent elsewhere).
    rgba = np.zeros((rows, cols, 4), dtype=np.uint8)
    # Vivid magenta so newly-lost land stands out from the GLC palette
    # (which already paints built-up as red).
    rgba[loss] = (255, 0, 200, 205)
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    return {
        "bbox": [west, south, east, north],
        "image": data_url,
        "hectares_lost": total_ha,
        "breakdown": breakdown,
        "resolution_m": round(width_m / cols),
        "year_from": YEAR_LEFT,
        "year_to": YEAR_RIGHT,
        "source": "GLC_FCS30D 30 m land cover (OpenLandMap); nature→impervious change",
    }


@app.get("/api/change")
def get_change() -> JSONResponse:
    """Real 1985->2022 ecosystem-to-built-up change over the delta."""
    try:
        return JSONResponse(_compute_change())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Change detection failed: {exc}") from exc


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/api/map-config", response_model=MapConfig)
def get_map_config() -> MapConfig:
    try:
        return _build_map_config()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to build map config: {exc}") from exc


@app.get("/api/ideology/questions", response_model=list[IdeologyQuestion])
def get_ideology_questions() -> list[IdeologyQuestion]:
    """Get all ideology questionnaire questions"""
    service = get_ideology_service()
    return service.get_questions()


@app.post("/api/ideology/score", response_model=ScoringResult)
def score_ideology_responses(responses: ScoringResult) -> ScoringResult:
    """Calculate ideology score from user responses"""
    try:
        service = get_ideology_service()
        return service.calculate_score(responses.responses)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/ideology/interpret", response_model=IdeologyInterpretation)
def interpret_ideology_score(score_result: ScoringResult, use_ollama: bool = False) -> IdeologyInterpretation:
    """Get interpretation of ideology score with optional Ollama generation"""
    try:
        service = get_ideology_service()
        return service.interpret_score(score_result.responses, use_ollama=use_ollama)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


repo_root = Path(__file__).resolve().parents[1]
dist_dir = repo_root / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")
else:

    @app.get("/")
    def frontend_not_built() -> JSONResponse:
        return JSONResponse(
            {
                "message": "Frontend is not built yet.",
                "build": "Run `npm run build` from the frontend directory.",
                "api": "/api/map-config",
            }
        )


if __name__ == "__main__":
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
