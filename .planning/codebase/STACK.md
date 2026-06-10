# Technology Stack

**Analysis Date:** 2026-06-10

## Languages

**Primary:**
- TypeScript 5.x — all frontend source (`frontend/src/**/*.tsx`, `frontend/src/styles.css`)
- Python 3.11 — all backend source (`backend/server.py`, `backend/ideology_agent_service.py`, `backend/story_frames.py`)

**Secondary:**
- CSS — single stylesheet at `frontend/src/styles.css` (no CSS-in-JS, no preprocessor)
- HTML — single entry template at `frontend/index.html`

## Runtime

**Environment:**
- Node.js 22.x (frontend dev toolchain only; no Node server in production)
- Python 3.11 (backend runtime; confirmed by system Python)

**Package Manager:**
- npm 10.9.x
- Lockfile: `frontend/package.json` present; no `package-lock.json` detected (private package, lock file may exist but not committed)

## Frameworks

**Frontend Core:**
- React 18.2.0 — UI component tree; `frontend/src/main.tsx` bootstraps via `createRoot`
- React DOM 18.2.0 — `createPortal` used extensively in `App.tsx` to float UI panels over Leaflet's DOM

**Frontend Build / Dev:**
- Vite 5.0 — dev server (port 5173), HMR, production build to `frontend/dist/`
- `@vitejs/plugin-react` 4.0 — Babel/React Fast Refresh plugin for Vite

**Backend Core:**
- FastAPI — REST API server; all routes in `backend/server.py`
- Uvicorn (standard extras) — ASGI runner; started with `uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)`
- Pydantic — request/response models (`MapConfig`, `LayerConfig`, `Gradient`, `LegendItem`, `IdeologyQuestion`, etc.)

**Backend Data Processing:**
- rio-tiler — reads Cloud Optimised GeoTIFFs over HTTP; used in `_read_classes()` for change-detection window reads
- NumPy (implicit dependency of rio-tiler) — array masks in `_compute_change()`
- Pillow — renders the loss-mask RGBA PNG from a NumPy array in `_compute_change()`

**Testing:**
- Not detected — no test runner config found (`jest.config.*`, `vitest.config.*`, `pytest.ini`, etc.)

## Key Dependencies

**Critical (frontend):**
- `leaflet` 1.9.3 — mapping engine; loaded via CDN in `frontend/index.html` as a global `window.L`, **not** a module import
- `leaflet-side-by-side` 2.0.0 — split-screen compare slider; loaded from jsDelivr CDN (`gh/digidem/leaflet-side-by-side@2.0.0`) via `<script>` tag in `frontend/index.html`

**Critical (backend):**
- `requests` — HTTP client; fetches STAC collection JSON, STAC item JSON, SLD XML, WMS orthophotos
- `rio-tiler` — COG reader for change detection; reads GeoTIFF windows over VSICURL
- `fastapi` / `uvicorn[standard]` — web framework and ASGI runner
- `pillow` — PNG rendering for change-overlay image returned as base64 data URL

**Infrastructure:**
- `python-multipart` — FastAPI form body support (included in requirements, not currently used by any endpoint)

## Configuration

**Environment:**
- No `.env` file detected; no `python-dotenv` dependency
- GDAL environment variables set programmatically at startup in `backend/server.py` (lines 25-28):
  `GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR`, `GDAL_HTTP_MULTIPLEX=YES`, `VSI_CACHE=TRUE`, `CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif,.TIF`
- No secrets required for current operation (all data sources are public HTTP endpoints)
- Optional: `OLLAMA_BASE_URL` is hardcoded to `http://localhost:11434` in `IdeologyAgentService.__init__()` — not an env var

**Build:**
- `frontend/vite.config.ts` — dev proxy routes `/api/*` and `/health` to `http://localhost:8000`; production build outputs to `frontend/dist/`
- `backend/server.py` serves `frontend/dist/` as a static mount at `/` when the build directory exists
- `frontend/tsconfig.json` — not read but expected by TypeScript 5.x; standard Vite scaffold

**TypeScript:**
- `tsconfig.json` present (not read); strict mode assumed from `@types/react` and `@types/leaflet` devDependencies

## Platform Requirements

**Development:**
- Node.js 22+, npm 10+ (frontend build)
- Python 3.11+ with pip (backend)
- GDAL shared libraries available to rio-tiler (comes bundled with `rasterio` wheel on most platforms)
- Optional: Ollama running locally at port 11434 for LLM-generated ideology interpretations

**Production:**
- Single process: `uvicorn backend.server:app --host 0.0.0.0 --port 8000`
- Frontend must be pre-built (`npm run build` from `frontend/`) so `frontend/dist/` exists
- Internet access required: backend fetches STAC catalog from Wasabi S3, tiles served by titiler.xyz, optional IGN WMS for story-frame refresh
- No containerisation config detected (no `Dockerfile`, `docker-compose.yml`)

---

*Stack analysis: 2026-06-10*
