# Architecture

**Analysis Date:** 2026-06-10

## Pattern Overview

**Overall:** Full-stack exhibition app — React SPA frontend + FastAPI backend, communicating via a JSON REST API. The frontend is an imperative Leaflet map with React UI panels overlaid via portals; the backend is a data proxy and computation engine over remote COG/STAC sources.

**Key Characteristics:**
- Leaflet map is created imperatively in a `useRef`, never re-created; React controls its data layers separately
- All UI panels are injected into a dynamically-created `#ui-root` DOM node via `createPortal`, keeping them above the Leaflet pane z-stack
- Two mutually exclusive view modes ("Data" and "Story") toggle which components are visible and control whether Leaflet data layers are opaque or hidden
- Backend is a pure data proxy: it fetches remote COG assets, computes a one-time change mask, and builds TiTiler tile URLs — no database, no auth
- Leaflet is loaded from CDN via `<script>` tag and accessed as `(window as any).L`; it is NOT a npm package

## Layers

**Backend — FastAPI:**
- Purpose: Resolve STAC asset hrefs, compute the land-cover change mask, build TiTiler tile URLs, serve ideology questionnaire
- Location: `backend/server.py`, `backend/ideology_agent_service.py`
- Contains: REST endpoints, Pydantic models, `@lru_cache` computation functions
- Depends on: Remote STAC catalog (Wasabi S3), TiTiler cloud service, optional Ollama at `localhost:11434`
- Used by: React frontend via `/api/*` fetch calls

**Frontend — React App shell:**
- Purpose: Owns Leaflet map lifecycle, dataset selection state, mode toggle (Data/Story)
- Location: `frontend/src/App.tsx`
- Contains: Map init/teardown, layer swap effects, panel rendering, portal injection into `#ui-root`
- Depends on: window.L (Leaflet CDN), backend `/api/map-config`, `/api/datasets`
- Used by: Rendered as React root in `frontend/src/main.tsx`

**Frontend — Map overlay components:**
- Purpose: React components that operate on or alongside the Leaflet map instance
- Location: `frontend/src/components/`
- Contains: `LossLayer.tsx`, `MorphLayer.tsx`, `LoupeLens.tsx`, `IdeologyPanel.tsx`
- Depends on: `map` prop (Leaflet instance passed down from App), `/api/change`, `/assets/story/*`
- Used by: `App.tsx` via portals into `#ui-root`

**Static assets — Story mode frames:**
- Purpose: Pre-rendered cinematic image frames and loupe video, served as static files
- Location: `frontend/public/assets/story/cine/` (6 × PNG), `frontend/public/assets/story/real/` (6 × JPG + `bounds.json`), `frontend/public/assets/decay/`
- Contains: `{year}.png` (cinematic restyle), `{year}.jpg` (raw IGN orthophoto), `bounds.json` (geo-registration bbox)
- Used by: `MorphLayer.tsx`, `LoupeLens.tsx`

## Data Flow

**Dataset load flow:**
1. App mounts → `GET /api/datasets` → populates dataset switcher buttons
2. User selects dataset (or default `landcover`) → `GET /api/map-config?dataset=<id>`
3. Backend resolves STAC item hrefs, builds TiTiler tile URL strings, returns `MapConfig` JSON
4. App stores `MapConfig` in `config` state, triggers layer-swap effect
5. Effect removes old `L.tileLayer` instances, creates new left/right layers, re-attaches `L.control.sideBySide`

**Change detection overlay flow:**
1. `LossLayer` mounts → `GET /api/change`
2. Backend: reads two COG windows via `rio_tiler` into numpy arrays, computes boolean loss mask, renders RGBA PNG, base64-encodes it, returns `{bbox, image, hectares_lost, breakdown}`
3. `LossLayer` creates an `<img>` element; a `requestAnimationFrame` loop re-projects the `bbox` corners each frame via `map.latLngToContainerPoint()`, positions the `<img>` with CSS, and clips it to the right (2022) half of the divider using `clipPath: inset(0 0 0 Xpx)`

**Story mode flow:**
1. Mode toggle → `storyMode=true` → data layers set to opacity 0, Data panels hidden
2. `MorphLayer` mounts → `GET /assets/story/real/bounds.json` → loads geo bbox + year list
3. Adds Esri World Imagery base layer + 6 `L.imageOverlay` instances (one per year) all geo-pinned to the same `bounds`
4. User drags `<input type="range">` → `frac` state → cross-dissolve computed via `useMemo` → `setOpacity` called on the two bracketing overlays
5. `LoupeLens` runs a parallel `requestAnimationFrame` loop reading the same `.cine-range` input to sync a CSS filter (sepia/saturation/brightness/contrast) graded from warm to cold

**Ideology questionnaire flow:**
1. `IdeologyPanel` mounts → `GET /api/user/profile` (graceful ignore on failure) → `GET /api/ideology/questions`
2. Questions optionally reordered client-side by profile preference category
3. User picks options one at a time → on last answer `POST /api/ideology/interpret` with all responses
4. Backend: `IdeologyAgentService.calculate_score()` computes 4-axis radar scores → `get_static_interpretation()` (or optional Ollama call) → returns `IdeologyInterpretation`
5. Results displayed with a Canvas-drawn radar chart (`drawRadarChart()` in `IdeologyPanel.tsx`)

**State Management:**
- All state lives in `App.tsx` (no Redux, no context API)
- `mapRef` and layer refs are mutable `useRef` values — mutations do not trigger re-renders
- `mapInstance` state variable is the React-reactive copy of the map, used only to pass as a prop to child components after map creation

## Key Abstractions

**MapConfig (shared contract):**
- Purpose: The data shape that bridges backend dataset selection to frontend tile rendering
- Backend Pydantic model: `backend/server.py` lines 104-114
- Frontend TypeScript type: `frontend/src/App.tsx` lines 29-40
- Fields: `left`/`right` `LayerInfo` (year + TiTiler tile URL), `legend`, `legend_kind` (`"classes"` or `"gradient"`), `gradient`, `center`, `zoom`, `source`

**TiTiler tile URL builder:**
- Purpose: Turn a remote COG href into an XYZ tile URL Leaflet can consume
- Location: `backend/server.py` `_build_tile_url()` (line 162), `_titiler_continuous()` (line 307)
- Pattern: Encodes colormap as URL-encoded JSON query param for categorical data; uses `colormap_name=turbo&resampling=cubic` for continuous rasters

**STAC item resolver:**
- Purpose: Traverse a remote STAC collection to find the COG `href` for a given year/asset key
- Location: `backend/server.py` `_load_items_by_year()` (line 129), `_asset_href()` (line 298)
- Pattern: Fetches collection JSON, iterates item links, regex-extracts year from item ID, caches result with `@lru_cache`

**LossLayer overlay technique:**
- Purpose: Pixel-perfect geo-pinning of a precomputed PNG onto a panning/zooming Leaflet map without using `L.imageOverlay` (to support the side-by-side clip)
- Location: `frontend/src/components/LossLayer.tsx` lines 57-93
- Pattern: `requestAnimationFrame` loop reading `map.latLngToContainerPoint()` each frame, setting CSS `left`/`top`/`width`/`height` on a fixed-position `<img>`, plus `clipPath: inset(0 0 0 Xpx)` calculated from the `leaflet-sbs-range` input value

## Entry Points

**Backend:**
- Location: `backend/server.py`
- Triggers: `uvicorn backend.server:app` or `python backend/server.py` (direct run)
- Responsibilities: FastAPI app definition, all `/api/*` route registration, frontend `dist/` static mount

**Frontend dev:**
- Location: `frontend/src/main.tsx`
- Triggers: Vite dev server (`npm run dev`) or bundled by `npm run build` into `frontend/dist/`
- Responsibilities: Creates React root, imports global CSS

**Frontend HTML bootstrap:**
- Location: `frontend/index.html`
- Responsibilities: Loads Leaflet CSS + JS from CDN, loads `leaflet-side-by-side` plugin from CDN, provides `#root` div

**Story frame fetcher (offline utility):**
- Location: `backend/story_frames.py`
- Triggers: `python backend/story_frames.py` (run once manually, not imported by server)
- Responsibilities: Requests WMS GetMap from IGN PNOA histórico, writes 6 JPEG frames + `bounds.json` to `frontend/public/assets/story/real/`

## Error Handling

**Strategy:** Fail gracefully and show inline UI messages; backend raises `HTTPException(502)` for upstream failures.

**Patterns:**
- Backend: `@lru_cache` computation functions throw `RuntimeError` on missing upstream data; routes catch and re-raise as `HTTPException(502, detail=...)`
- Frontend API calls: `.catch()` on all `fetch()` chains; error stored in `error` state and rendered as a panel message
- `LossLayer`/`LoupeLens`: `.catch(() => setData(null))` — silently hides overlay if `/api/change` fails
- `IdeologyPanel`: optional `/api/user/profile` call is fire-and-forget with silent catch
- `LossLayer` rAF loop: guards against `map._mapPane._leaflet_pos` being undefined during unmount

## Cross-Cutting Concerns

**Logging:** `console.log` / `console.error` in frontend; `print()` in Python scripts; no structured logging framework
**Validation:** Pydantic models on all backend request/response bodies; frontend has no form validation layer
**Authentication:** None — unauthenticated public exhibition app
**Caching:** `@lru_cache(maxsize=1)` on `_build_map_config()`, `_get_change_assets()`, `_compute_change()` — results are frozen for server lifetime; `@lru_cache(maxsize=64)` on `_asset_href()` for STAC lookups
**Z-index stack:** CSS `z-index` is the only layering mechanism — Leaflet panes use 400-599; `.loss-root` uses 600; portaled panels float on top of everything

---

*Architecture analysis: 2026-06-10*
