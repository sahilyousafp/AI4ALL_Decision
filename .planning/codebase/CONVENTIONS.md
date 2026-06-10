# Coding Conventions

**Analysis Date:** 2026-06-10

## Naming Patterns

**Files:**
- React components: PascalCase `.tsx` files, one component per file (e.g., `IdeologyPanel.tsx`, `LossLayer.tsx`, `MorphLayer.tsx`, `LoupeLens.tsx`)
- Entry point: `main.tsx`, root component: `App.tsx`
- Stylesheet: single flat `styles.css` file (no CSS modules or styled-components)
- Python modules: `snake_case.py` (e.g., `ideology_agent_service.py`, `story_frames.py`)

**Functions:**
- TypeScript: camelCase for functions and event handlers (`handleSelectOption`, `submitResponses`, `resetQuiz`, `drawRadarChart`, `reorderQuestionsByProfile`)
- Python: `snake_case` for all functions, private helpers prefixed with `_` (e.g., `_fetch_json`, `_build_tile_url`, `_compute_change`, `_read_classes`)

**Variables:**
- TypeScript: camelCase locals and state names (`storyMode`, `hoverLegend`, `radarScores`, `leftLayerRef`)
- Python: `snake_case` locals; module-level constants in `UPPER_SNAKE_CASE` (e.g., `CHANGE_BBOX`, `YEAR_LEFT`, `COLLECTION_URL`, `MAP_CENTER`, `LANDCOVER_GROUPS`)

**Types:**
- TypeScript: PascalCase `type` aliases (not `interface`) for all shape definitions (e.g., `MapConfig`, `LayerInfo`, `LegendItem`, `Gradient`, `Props`)
- Python: PascalCase Pydantic `BaseModel` subclasses (e.g., `LegendItem`, `LayerConfig`, `MapConfig`, `Gradient`, `RadarScores`, `ScoringResult`, `IdeologyInterpretation`)
- Python `set[int]` used for GLC class code groupings (e.g., `CROP`, `FOREST`, `BUILT`)

**CSS Classes:**
- kebab-case BEM-adjacent naming, prefixed by component/feature area (e.g., `loss-panel`, `loss-bar-row`, `cine-controls`, `opinion-option`, `mode-btn`, `ds-btn`)
- Modifier state expressed with a short class suffix (e.g., `.active`, `.selected`, `.final`)

## Code Style

**Formatting:**
- No Prettier or ESLint config files are present in the repository (no `.eslintrc`, `.prettierrc`, `biome.json`, or `eslint.config.*`)
- TypeScript formatting follows Vite project defaults: single quotes for imports, 2-space indentation, trailing commas visible in JSX props
- Python formatting appears to follow PEP 8 by convention: 4-space indentation, blank lines between top-level definitions
- Python files use `from __future__ import annotations` at the top of every module

**Linting:**
- No linting toolchain configured; no `scripts.lint` in `frontend/package.json`
- `// eslint-disable-next-line react-hooks/exhaustive-deps` comments appear in three places (`frontend/src/App.tsx` lines 127, 156 and `frontend/src/components/IdeologyPanel.tsx` line 71), suggesting a react-hooks plugin was used historically or is implicitly enforced by the IDE but is not enforced in CI

## TypeScript Patterns

**Strictness:**
- `tsconfig.json` enables `"strict": true` — null-checks, no implicit any, strict function types all apply
- Despite strict mode, `any` is used extensively for the Leaflet map instance (`mapRef.current`, `leftLayerRef.current`, map prop types) because Leaflet is loaded as a CDN global: `const L = (window as any).L`. This is the primary source of `any` in the codebase.
- `any` also appears for Leaflet refs in `LossLayer.tsx` (`map: any | null`) and `MorphLayer.tsx` (`map: any | null`, `useRef<any[]>`)
- Non-Leaflet code avoids `any` — error catches use `catch (e: any)` as the only exception

**Type Declarations:**
- All local shape types are declared inline at the top of each file using `type` (not `interface`)
- No shared types file — types are not exported or shared between components
- Example pattern from `frontend/src/App.tsx`:
  ```typescript
  type LayerInfo = {
    year: number
    tiles: string
    label?: string | null
  }

  type MapConfig = {
    dataset_id: string
    dataset_label: string
    left: LayerInfo
    right: LayerInfo
    legend: LegendItem[]
    legend_kind: string
    gradient: Gradient | null
    center: [number, number]
    zoom: number
    source: string
  }
  ```

**Imports:**
- Named React hook imports (no `React.useState` style): `import { useEffect, useMemo, useRef, useState } from 'react'`
- `createPortal` imported from `react-dom` directly
- Component imports use relative paths without extensions: `import LossLayer from './components/LossLayer'`
- No path aliases configured in `tsconfig.json` or `vite.config.ts`
- CSS imported in `main.tsx` (`import './styles.css'`) and Leaflet CSS imported in `App.tsx` (`import 'leaflet/dist/leaflet.css'`)

## React Hooks Patterns

**useEffect:**
- Each `useEffect` has a single, clear responsibility — multiple effects are split by concern rather than combined
- Dependency arrays are explicit; when intentionally incomplete, suppressed with `// eslint-disable-next-line react-hooks/exhaustive-deps`
- The `hasConfig` boolean proxy pattern is used to prevent `config` from being a `useEffect` dep when only its truthiness matters:
  ```typescript
  const hasConfig = !!config
  useEffect(() => {
    if (!hasConfig || !L || mapRef.current || !config) return
    // create map once
  }, [hasConfig])
  ```
- Cleanup functions are returned from effects that acquire resources (rAF loops, Leaflet layers, event listeners):
  ```typescript
  useEffect(() => {
    let raf = 0
    const tick = () => { ...; raf = window.requestAnimationFrame(tick) }
    raf = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(raf)
  }, [map, data])
  ```

**useRef:**
- Used for imperative Leaflet handles that must not trigger re-renders (`mapRef`, `leftLayerRef`, `rightLayerRef`, `compareControlRef`)
- Used for DOM element handles (`canvasRef`, `imgRef`, `videoRef`)
- Used for drag state that must not trigger re-renders (`dragging`, `offset`) in `LoupeLens.tsx`

**useState:**
- State initializers are typed explicitly when needed: `useState<MapConfig | null>(null)`, `useState<DatasetMeta[]>([])`
- State is kept at the component that owns it; no state lifted above `App` or shared via context

**useMemo:**
- Used sparingly: one instance in `App.tsx` for `legendTitle` (derived from config and labels), one in `MorphLayer.tsx` for cross-dissolve frame math (`k`, `f`)

**createPortal:**
- All UI panels are portalled into a manually-created `#ui-root` div appended to `document.body`, to layer above the Leaflet map. Pattern in `App.tsx`:
  ```typescript
  {uiRoot ? createPortal(<Component />, uiRoot) : <Component />}
  ```
  The fallback renders inline when `uiRoot` is null during the first render tick.

## Error Handling

**TypeScript/Frontend:**
- Fetch errors use `.catch()` returning `null` or setting an error state string (never throws)
- User-visible error states are rendered as fallback UI panels (e.g., `if (error) return <div className="panel shell">...`)
- No error boundary components (`react-error-boundary` is not installed)

**Python/Backend:**
- Route handlers wrap all external calls in `try/except Exception as exc` and re-raise as `HTTPException(status_code=502, detail=...)`
- `ValueError` from service layer is caught separately and raises `HTTPException(status_code=400, ...)`
- Helper functions (`_fetch_json`, `_fetch_text`) allow `requests` exceptions to propagate naturally up to the route handler
- `@lru_cache` is used on expensive operations (`_build_map_config`, `_compute_change`, `_get_change_assets`, `_asset_href`) to avoid repeat external calls

## FastAPI Patterns

**Route Definitions:**
- Routes declared with `@app.get` / `@app.post` decorators, returning either typed Pydantic models or `JSONResponse`
- `response_model=` used on endpoints that return Pydantic models
- Query parameters typed directly in function signatures: `def get_map_config(dataset: str = "landcover")`
- No APIRouter — all routes defined directly on the `app` instance in `backend/server.py`

**Pydantic Models:**
- `from __future__ import annotations` enables forward references
- All models inherit from `BaseModel`
- Optional fields use `field: Type | None = None` syntax (Python 3.10+ union shorthand)
- Inline docstrings on model classes explain domain context (e.g., `Gradient`, `IdeologyAgentService`)
- Example pattern from `backend/server.py`:
  ```python
  class MapConfig(BaseModel):
      dataset_id: str
      dataset_label: str
      left: LayerConfig
      right: LayerConfig
      legend: list[LegendItem]
      legend_kind: str = "classes"  # "classes" | "gradient"
      gradient: Gradient | None = None
      center: list[float]
      zoom: int
      source: str
  ```

**Service Layer:**
- Business logic lives in `backend/ideology_agent_service.py` as a class (`IdeologyAgentService`), not inline in route handlers
- A module-level singleton is accessed via `get_ideology_service()` (lazy init, not dependency injection)
- QUESTIONS are stored as a class-level list of Pydantic models

## Logging

- No structured logging framework used in either frontend or backend
- Python backend uses `print()` for operational output (e.g., `print(f"Ollama inference failed: {e}...")` in `ideology_agent_service.py`)
- Frontend uses no console logging in production paths

## Comments

**When to Comment:**
- Inline comments explain non-obvious algorithmic choices and domain context, not what the code does literally
- Module-level docstrings on Python files explain the what and why (e.g., `story_frames.py`, `LossLayer.tsx` has a JSDoc-style block comment at the top)
- Inline `# noqa: BLE001` used once in `story_frames.py` to suppress blind exception catch

**Comment style in TypeScript:**
- Multi-line JSDoc block comments used at the top of component files to describe purpose and design decisions
- Single-line `//` comments inline for non-obvious logic
- Sections in `styles.css` are delimited with `/* ---- Section title ---- */` banners

## CSS Conventions

**Architecture:**
- Single stylesheet `frontend/src/styles.css` — no CSS modules, Tailwind, or component-scoped styles
- CSS custom properties (variables) defined in `:root` for the design tokens:
  ```css
  :root {
    --apple-text: #101214;
    --apple-muted: #5e656e;
    --apple-panel: rgba(255, 255, 255, 0.8);
    --apple-border: rgba(255, 255, 255, 0.65);
    --apple-shadow: 0 26px 60px rgba(18, 30, 52, 0.2);
    --apple-radius: 22px;
  }
  ```
- Variable names prefixed `--apple-` indicating an Apple-inspired glassmorphism design system

**Layout:**
- Panels use `position: fixed` with explicit `z-index` stacking values (600–1500 range)
- `backdrop-filter: blur(16px) saturate(135%)` on all panel elements for the frosted-glass effect
- `min()` / `clamp()` used for responsive sizing without media queries where possible
- Responsive breakpoints at `max-width: 900px` and `max-width: 720px`
- `prefers-reduced-motion` media query honoured for all CSS animations

**Buttons:**
- Interactive buttons use `all: unset` to reset browser defaults, then explicit re-styling
- Active state expressed with `.active` class, hover with `:hover` pseudo-class

---

*Convention analysis: 2026-06-10*
