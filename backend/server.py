from __future__ import annotations

import json
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

app = FastAPI(title="AI4ALL Land Cover Viewer")

COLLECTION_URL = "https://s3.eu-central-1.wasabisys.com/stac/openlandmap/lc_glc.fcs30d/collection.json"
ASSET_KEY = "lc_glc.fcs30d_c_30m_s"
YEAR_LEFT = 1985
YEAR_RIGHT = 2022
MAP_CENTER = [41.2974, 2.0833]
DEFAULT_ZOOM = 12


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
