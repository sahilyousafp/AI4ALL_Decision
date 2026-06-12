# Codebase Structure

**Analysis Date:** 2026-06-10

## Directory Layout

```
AI4ALL_Decision/                    # Repo root
├── backend/                        # FastAPI Python server
│   ├── server.py                   # App, all API routes, COG/STAC/TiTiler logic
│   ├── ideology_agent_service.py   # Questionnaire, scoring, optional Ollama integration
│   ├── story_frames.py             # Offline utility: fetch IGN WMS frames to public/
│   ├── requirements.txt            # Python dependencies
│   └── __init__.py
├── frontend/                       # Vite + React SPA
│   ├── index.html                  # HTML shell: CDN Leaflet + leaflet-side-by-side bootstrap
│   ├── vite.config.ts              # Vite config: dev proxy /api -> :8000, build outDir=dist
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── main.tsx                # React root mount, global CSS import
│   │   ├── App.tsx                 # Map init, dataset/mode state, portal orchestration
│   │   ├── styles.css              # All CSS — single file, plain CSS, CSS custom properties
│   │   └── components/
│   │       ├── IdeologyPanel.tsx   # 5-question quiz, radar chart canvas, ideology scoring
│   │       ├── LossLayer.tsx       # Change mask overlay + stats panel
│   │       ├── MorphLayer.tsx      # Story mode: cinematic cross-dissolve image overlays
│   │       └── LoupeLens.tsx       # Story mode: draggable video loupe lens
│   ├── public/
│   │   └── assets/
│   │       ├── decay/
│   │       │   └── delta_morph_geo.mp4   # Loupe lens video clip
│   │       └── story/
│   │           ├── cine/           # Cinematically restyled PNG frames (1956-2021)
│   │           │   ├── 1956.png
│   │           │   ├── 1997.png
│   │           │   ├── 2002.png
│   │           │   ├── 2008.png
│   │           │   ├── 2015.png
│   │           │   └── 2021.png
│   │           └── real/           # Raw IGN PNOA orthophotos + geo metadata
│   │               ├── 1956.jpg ... 2021.jpg
│   │               └── bounds.json # Geo bbox + year list for MorphLayer
│   └── dist/                       # Vite build output (committed, served by FastAPI)
├── .planning/
│   └── codebase/                   # GSD mapping documents (this directory)
├── Knowledge/                      # Project reference/background documents
├── graphify-out/                   # Generated graph outputs (exploratory)
├── GEMINI.md                       # Project notes
└── backend_run.log
```

## Directory Purposes

**`backend/`:**
- Purpose: All server-side Python. FastAPI app, data proxy, computation
- Contains: Route handlers, Pydantic models, COG/STAC helpers, ideology service
- Key files: `backend/server.py` (main), `backend/ideology_agent_service.py`

**`frontend/src/`:**
- Purpose: All TypeScript/React source
- Contains: One top-level component (`App.tsx`), four leaf components, one CSS file, entry point
- Key files: `frontend/src/App.tsx`, `frontend/src/styles.css`

**`frontend/src/components/`:**
- Purpose: Self-contained React components, each responsible for a distinct map feature
- Contains: Four files, no subdirectories, no barrel index
- Key files: `IdeologyPanel.tsx`, `LossLayer.tsx`, `MorphLayer.tsx`, `LoupeLens.tsx`

**`frontend/public/assets/story/cine/`:**
- Purpose: Cinematically restyled orthophoto frames for `MorphLayer` dissolve
- Contains: 6 PNG images named `{year}.png` (1956, 1997, 2002, 2008, 2015, 2021)
- Generated: Yes — by external Higgsfield restyle pass on raw IGN frames
- Committed: Yes

**`frontend/public/assets/story/real/`:**
- Purpose: Raw geo-registered IGN PNOA source orthophotos + registration metadata
- Contains: 6 JPEG images + `bounds.json`
- Generated: Yes — by running `python backend/story_frames.py`
- Committed: Yes

**`frontend/public/assets/decay/`:**
- Purpose: Loupe lens video for `LoupeLens` component
- Contains: `delta_morph_geo.mp4`
- Committed: Yes

**`frontend/dist/`:**
- Purpose: Vite production build output, served by FastAPI as static files via `StaticFiles`
- Generated: Yes — by `npm run build` in `frontend/`
- Committed: Yes (present in repo; FastAPI checks for its existence at startup)

## Key File Locations

**Entry Points:**
- `backend/server.py` line 449: `uvicorn.run("backend.server:app", ...)` — Python direct entry
- `frontend/src/main.tsx`: React DOM mount
- `frontend/index.html`: HTML shell loaded by browser

**Configuration:**
- `frontend/vite.config.ts`: Dev proxy (`/api` → `localhost:8000`), build output dir
- `frontend/package.json`: npm scripts (`dev`, `build`, `preview`), dependency versions
- `frontend/tsconfig.json`: TypeScript compiler options
- `backend/requirements.txt`: Python package list (no pinned versions)

**Core Logic:**
- `backend/server.py` `_build_map_config()`: Land cover STAC → TiTiler tile URL pipeline
- `backend/server.py` `_compute_change()`: COG window read → numpy change mask → base64 PNG
- `backend/server.py` `_config_lst()`, `_config_no2()`: Surface temp / air quality layer builders
- `backend/ideology_agent_service.py` `IdeologyAgentService.calculate_score()`: 4-axis scoring
- `frontend/src/App.tsx` lines 96-128: Leaflet map creation effect (runs once)
- `frontend/src/App.tsx` lines 132-157: Layer swap effect (runs on each dataset change)
- `frontend/src/components/LossLayer.tsx` lines 57-93: rAF geo-pin loop

**Static Assets:**
- `frontend/public/assets/story/real/bounds.json`: Geo bbox consumed by `MorphLayer.tsx`
- `frontend/public/assets/story/cine/{year}.png`: Loaded as `L.imageOverlay` in `MorphLayer.tsx`
- `frontend/public/assets/decay/delta_morph_geo.mp4`: Loaded in `<video>` in `LoupeLens.tsx`

## Naming Conventions

**Files:**
- React components: PascalCase, `.tsx` — e.g., `IdeologyPanel.tsx`, `LossLayer.tsx`
- Utility scripts: snake_case, `.py` — e.g., `story_frames.py`, `ideology_agent_service.py`
- Story frame images: numeric year as filename — e.g., `1956.png`, `2021.jpg`

**Directories:**
- Backend: flat, no subdirectories
- Frontend components: flat `components/` directory, no feature-based nesting
- Public assets: grouped by feature (`story/`, `decay/`) then by variant (`cine/`, `real/`)

**TypeScript types:**
- Defined inline in each file (no shared `types/` directory)
- PascalCase type aliases mirroring backend Pydantic model names: `MapConfig`, `LayerInfo`, `LegendItem`, `Gradient`

**Python:**
- Private helpers prefixed with `_`: `_build_tile_url()`, `_compute_change()`, `_asset_href()`
- Public route handlers use the FastAPI decorator pattern directly on module-level functions

## Where to Add New Code

**New data layer (new dataset like a new environmental metric):**
- Backend: Add a `_config_<name>()` function in `backend/server.py` following the pattern of `_config_lst()` or `_config_no2()`, then add the dataset entry to `DATASETS` list and a branch in `get_map_config()`
- Frontend: No code change needed — the dataset switcher auto-populates from `/api/datasets`

**New map overlay component (new visual feature on the map):**
- Create `frontend/src/components/NewFeature.tsx` accepting `{ map: any | null, active?: boolean }` props
- Import and portal-mount in `frontend/src/App.tsx` using the `createPortal(..., uiRoot)` pattern
- Add CSS to `frontend/src/styles.css`

**New UI panel (non-map information panel):**
- Add inline in `App.tsx` `panels()` function, or create a new component in `frontend/src/components/` and portal-mount it

**New backend endpoint:**
- Add a route function in `backend/server.py` with a `@app.get` or `@app.post` decorator
- Add corresponding Pydantic request/response models in the same file or `ideology_agent_service.py` if ideology-related

**New static asset (new video, image set):**
- Place in `frontend/public/assets/<feature-name>/`
- Reference in components as `/assets/<feature-name>/file.ext` (served at root by Vite / FastAPI StaticFiles)

## Special Directories

**`frontend/dist/`:**
- Purpose: Production build output; FastAPI serves this as the SPA shell + bundled assets
- Generated: Yes (via `npm run build`)
- Committed: Yes (unusual — keeps the repo self-contained for exhibition deployment)

**`frontend/public/assets/story/real/`:**
- Purpose: Raw IGN WMS orthophotos + geo bounds metadata
- Generated: Yes (via `python backend/story_frames.py`)
- Committed: Yes

**`backend/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No (gitignored)

**`.planning/codebase/`:**
- Purpose: GSD codebase mapping documents
- Generated: Yes (by this agent)
- Committed: Expected yes

---

*Structure analysis: 2026-06-10*
