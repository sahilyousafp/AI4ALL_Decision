# External Integrations

**Analysis Date:** 2026-06-10

## APIs & External Services

**STAC Catalog (primary data source):**
- OpenLandMap STAC on Wasabi S3 — land-cover, surface temperature, NO2 datasets
  - Collection root: `https://s3.eu-central-1.wasabisys.com/stac/openlandmap/`
  - Land cover collection: `lc_glc.fcs30d` (GLC_FCS30D 30 m)
  - Surface temperature collection: `lst_mod11a2.daytime.annual` (MODIS MOD11A2)
  - Air quality collection: `no2_s5p.l3.trop.tmwm` (Sentinel-5P TROPOMI)
  - Auth: None (public S3 bucket)
  - Called by: `backend/server.py` — `_fetch_json()`, `_load_items_by_year()`, `_asset_href()`

**TiTiler (tile rendering service):**
- TiTiler public instance at `https://titiler.xyz`
  - Endpoint: `/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png`
  - Used for: rendering COG assets as XYZ tile layers consumed by Leaflet
  - Parameters: `url` (COG S3 href), `colormap` (JSON-encoded class→hex map for land cover), `colormap_name=turbo` + `resampling=cubic` for continuous datasets
  - Auth: None (public)
  - Called by: `backend/server.py` — `_build_tile_url()`, `_titiler_continuous()`
  - Tile URLs are **returned to the frontend** via `/api/map-config`; the browser requests tiles directly from titiler.xyz

**IGN España PNOA Histórico WMS (story orthophotos):**
- WMS endpoint: `https://www.ign.es/wms/pnoa-historico`
  - Layers fetched: `AMS_1956-1957`, `OLISTAT`, `SIGPAC`, `PNOA2008`, `PNOA2015`, `PNOA2021`
  - SRS: `EPSG:3857`, format `image/jpeg`, fixed 1600×900 px bbox
  - Auth: None (public WMS)
  - Called by: `backend/story_frames.py` — `fetch()` (offline pre-fetch script, not a live endpoint)
  - Output: JPEG frames saved to `frontend/public/assets/story/real/` + `bounds.json`

**Ollama (optional local LLM):**
- Ollama REST API at `http://localhost:11434` (hardcoded default)
  - Endpoint: `POST /api/generate`
  - Model: `llama2`
  - Used for: generating personalised ideology interpretations when `use_ollama=True`
  - Auth: None (localhost only)
  - Falls back to static text if Ollama is unavailable
  - Called by: `backend/ideology_agent_service.py` — `get_ollama_interpretation()`

## Data Storage

**Databases:**
- None — no database. All persistent data comes from remote STAC/COG files.

**In-process Cache:**
- `@lru_cache(maxsize=1)` on `_build_map_config()`, `_get_change_assets()`, `_compute_change()` in `backend/server.py`
- `@lru_cache(maxsize=64)` on `_asset_href()` in `backend/server.py`
- Cache is process-scoped and lost on restart

**File Storage:**
- Pre-fetched story orthophotos: `frontend/public/assets/story/real/*.jpg` (1956–2021, fetched by `backend/story_frames.py`)
- Cinematically restyled frames: `frontend/public/assets/story/cine/*.png` (1956–2021, generated externally via Higgsfield/flux_kontext)
- Artist's impression video clip: `frontend/public/assets/decay/delta_morph_geo.mp4` (used by `LoupeLens.tsx`)
- All static assets served via FastAPI `StaticFiles` mount or Vite dev server

**Caching:**
- No Redis, Memcached, or external cache. In-process `lru_cache` only (see above).

## Authentication & Identity

**Auth Provider:**
- None — no authentication system in place
- `IdeologyPanel.tsx` speculatively fetches `/api/user/profile` on mount (line 47–52) but this endpoint does not exist in `backend/server.py`; failures are silently swallowed

## Monitoring & Observability

**Error Tracking:**
- None detected — no Sentry, Datadog, or similar integration

**Health Check:**
- `GET /health` returns `{"status": "ok"}` (proxied in Vite dev config)

**Logs:**
- Python `print()` statements only (e.g., Ollama fallback message in `ideology_agent_service.py`)
- No structured logging framework

## CI/CD & Deployment

**Hosting:**
- Not configured — no `Dockerfile`, `docker-compose.yml`, `fly.toml`, `render.yaml`, `vercel.json`, etc. detected
- Intended deployment: single Uvicorn process serving both API and pre-built frontend static files

**CI Pipeline:**
- None detected

## Tile & Map Services (Frontend)

**Base Tile Layers:**

| Layer | URL template | Where used |
|---|---|---|
| CartoDB Light (Data mode default) | `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png` | `App.tsx` map initialisation |
| Esri World Imagery (Story mode) | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` | `MorphLayer.tsx` |
| TiTiler COG tiles (data layers) | `https://titiler.xyz/cog/tiles/...` | `App.tsx` left/right tile layers |

**Leaflet Plugins (CDN-loaded, not npm packages):**

| Plugin | Source | Usage |
|---|---|---|
| Leaflet 1.9.3 | `cdn.jsdelivr.net/npm/leaflet@1.9.3` | Core map in `index.html`; accessed as `window.L` |
| leaflet-side-by-side 2.0.0 | `cdn.jsdelivr.net/gh/digidem/leaflet-side-by-side@2.0.0` | Split-screen compare slider (`L.control.sideBySide`) |

Both plugins are loaded as synchronous `<script>` tags before the module bundle in `frontend/index.html`. The `window.L` compatibility shim (`L.Mixin.Events`) is also in `index.html`.

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Environment Configuration

**Required env vars:**
- None required — all external services use public unauthenticated endpoints

**Optional runtime config:**
- Ollama base URL: hardcoded `http://localhost:11434` in `backend/ideology_agent_service.py:97` — should be promoted to an env var if deploying to a non-local environment

**Secrets location:**
- No secrets detected in codebase

---

*Integration audit: 2026-06-10*
