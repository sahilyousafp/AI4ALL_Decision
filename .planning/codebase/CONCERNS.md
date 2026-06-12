# Codebase Concerns

**Analysis Date:** 2026-06-10

---

## Known Console Errors (Confirmed in backend_run.log)

**`/api/user/profile` returns 404 on every page load:**
- Symptoms: Every browser session logs a 404 from this endpoint. The error is silently swallowed in `IdeologyPanel.tsx` but the failed fetch still appears in devtools.
- Files: `frontend/src/components/IdeologyPanel.tsx` lines 47–52, `backend/server.py` (endpoint does not exist)
- Trigger: Automatic on component mount — `IdeologyPanel` fetches `/api/user/profile` on render, always fails
- Impact: The `userProfile` state always stays `null`, making the `reorderQuestionsByProfile` logic permanently dead code
- Fix approach: Either implement the `/api/user/profile` endpoint, or remove the fetch + dead reorder logic entirely. For the redesign, if IdeologyPanel is replaced, delete both.

---

## Tech Debt

**`IdeologyPanel.tsx` is scheduled for full replacement but remains wired up:**
- Issue: The component is explicitly called out as "to be replaced" in the redesign brief. It is still imported and rendered in `App.tsx` line 312 in Data mode.
- Files: `frontend/src/components/IdeologyPanel.tsx`, `frontend/src/App.tsx` line 312
- Impact: Any redesign work risks conflict if this component is left in place. Its CSS classes (`opinion-panel`, `opinion-content`, etc.) overlap with `ideology-*` class names defined in the same `styles.css`, creating confusion.
- Fix approach: Remove the import and render call from `App.tsx` before redesign work begins, then delete the file.

**`LoupeLens.tsx` is implemented but never rendered:**
- Issue: The component file exists at `frontend/src/components/LoupeLens.tsx` and is fully functional, but it is not imported or used anywhere in `App.tsx` or any other component.
- Files: `frontend/src/components/LoupeLens.tsx`
- Impact: Dead code shipped in the bundle. The loupe lens experience (draggable cinematic magnifier in Story mode) is not accessible to users despite being built.
- Fix approach: Either wire it into `App.tsx` in Story mode (alongside `MorphLayer`), or delete it and remove the `delta_morph_geo.mp4` asset if the feature is not wanted.

**Duplicate CSS class definitions for `opinion-content` and related results classes:**
- Issue: `.opinion-content` is defined twice in `styles.css` (lines 796 and 963). `.opinion-results-container` is defined twice (lines 801 and 1050). `.opinion-gauge-canvas` is defined twice (lines 807 and 1062). The second definition silently wins in cascade.
- Files: `frontend/src/styles.css`
- Impact: Unpredictable layout — which rule wins depends on specificity and order. If either block is removed during redesign, the remaining block may not be the intended one.
- Fix approach: Audit and merge duplicates before the redesign CSS pass. The first block (lines 791–810) appears to be an early draft of what was later expanded (lines 944–1164).

**`opinion-gauge-container` div is empty with a comment explaining the chart moved:**
- Issue: `IdeologyPanel.tsx` line 212–214 renders an empty `<div className="opinion-gauge-container">` with the comment `{/* Chart moved to bottom-left panel */}`. The container is never removed.
- Files: `frontend/src/components/IdeologyPanel.tsx` lines 211–215
- Impact: An invisible empty div in the results view. No visible bug, but dead markup that will confuse redesign work.
- Fix approach: Remove the empty container div when replacing IdeologyPanel.

**`ideology-*` CSS classes defined in `styles.css` but not used by any current component:**
- Issue: `styles.css` contains `.ideology-panel`, `.ideology-results-container`, `.ideology-score-panel`, and `.score-item` (with `.environment`, `.comfort`, `.economic`, `.social` modifiers) at lines 919–942. No TSX file uses these class names — the working component uses `opinion-*` names instead.
- Files: `frontend/src/styles.css` lines 919–942
- Impact: Stale CSS that inflates the bundle and creates naming confusion — two parallel naming systems for the same conceptual component.
- Fix approach: Delete the `ideology-*` block from `styles.css` when redesigning or removing IdeologyPanel.

**Several Story mode CSS classes are defined but the features they style do not exist in the current TSX:**
- Issue: The following CSS classes are defined in `styles.css` but are referenced by no current TSX component: `.morph-scar`, `.morph-flock`, `.gull`, `.gull-wing`, `.morph-fx`, `.morph-shock`, `.cine-stat`, `.cine-play`. These appear to be from an earlier, richer version of `MorphLayer`.
- Files: `frontend/src/styles.css` lines 315–506 and 533–559 and 579–592
- Impact: ~120 lines of dead CSS. The animations (gull flock, shockwave, vignette fx) were removed from `MorphLayer.tsx` but their styles remain.
- Fix approach: Remove these CSS blocks, or reimplement the removed features during the cinematic redesign.

---

## Security Considerations

**No CORS middleware on the FastAPI backend:**
- Risk: Any origin can call the API in production if the backend is exposed directly (not behind the static file serving).
- Files: `backend/server.py` — no `CORSMiddleware` added to `app`
- Current mitigation: In production the backend serves the built frontend as static files, so same-origin applies. In dev, the Vite proxy handles origin. No explicit CORS protection exists.
- Recommendations: Add `CORSMiddleware` with a locked `allow_origins` list before any external/public deployment.

**Leaflet and leaflet-side-by-side loaded from CDN in HTML, not from npm:**
- Risk: Build integrity is not enforced — no Subresource Integrity (SRI) hashes on the CDN `<script>` and `<link>` tags.
- Files: `frontend/index.html` lines 5–13
- Current mitigation: None.
- Recommendations: Either add SRI hashes to the CDN tags, or bundle Leaflet through npm (already listed in `package.json` as a dep but the CDN version is what actually runs).

**Leaflet is loaded as both a CDN global AND as an npm package:**
- Risk: There are two copies of Leaflet in play. `package.json` lists `"leaflet": "^1.9.3"` and the CSS is imported via `import 'leaflet/dist/leaflet.css'` in `App.tsx`, but the actual `L` object is read from `window.L` (the CDN global) via `const L = (window as any).L`. If the CDN is blocked or loads a different version, the app silently breaks.
- Files: `frontend/src/App.tsx` line 8, `frontend/src/components/MorphLayer.tsx` line 16, `frontend/index.html` lines 5–12
- Fix approach: Commit to one approach: import Leaflet from npm fully (remove CDN tags), or remove the npm dep and accept the CDN. Do not do both.

---

## Performance Bottlenecks

**Six uncompressed PNG cinematic frames totalling ~15 MB loaded into the browser at Story mode entry:**
- Problem: The six cinematic aerial frames in `/assets/story/cine/` are stored as lossless PNGs averaging ~2.5 MB each (total ~15 MB). They are loaded as `L.imageOverlay` on top of the map simultaneously when Story mode opens.
- Files: `frontend/public/assets/story/cine/` (1956.png through 2021.png), `frontend/src/components/MorphLayer.tsx` lines 57–65
- Cause: PNG format was likely chosen for quality; no lazy-loading or progressive decode is used.
- Improvement path: Convert to WebP (typically 60–70% smaller for photographic aerials). Add a loading state before revealing overlays. Lazy-load non-adjacent frames.

**`/api/change` is fetched independently by both `LossLayer` and `LoupeLens`, firing two identical requests:**
- Problem: Both `LossLayer.tsx` (line 48) and `LoupeLens.tsx` (line 33) independently `fetch('/api/change')` on mount. Because LoupeLens is not currently wired up this is not actively firing, but if it is re-added, two identical heavy requests will fire simultaneously.
- Files: `frontend/src/components/LossLayer.tsx` line 48, `frontend/src/components/LoupeLens.tsx` line 33
- Cause: No shared data context or caching layer for the change result.
- Improvement path: Lift the `/api/change` fetch to `App.tsx` and pass `data` as a prop, or use a simple module-level cache.

**`_compute_change()` is decorated with `@lru_cache(maxsize=1)` but `_config_lst()` and `_config_no2()` are not cached at all:**
- Problem: Every dataset switch to `lst` or `no2` fires fresh `_asset_href()` calls that resolve STAC items from remote URLs. `_asset_href` is cached at `maxsize=64`, so individual URLs are cached, but the full config assembly (including the TiTiler URL construction) happens on every request.
- Files: `backend/server.py` lines 317–364, lines 297–304
- Impact: Unnecessary latency on every dataset switch in a multi-user exhibition context.
- Fix approach: Apply `@lru_cache(maxsize=1)` to `_config_lst()` and `_config_no2()` the same way `_build_map_config()` is cached.

---

## Fragile Areas

**`(window as any).L` — global Leaflet dependency with no null guard at render time:**
- Files: `frontend/src/App.tsx` line 8, `frontend/src/components/MorphLayer.tsx` line 16
- Why fragile: If the CDN `<script>` in `index.html` fails to load (network issue, exhibition offline mode, ad blocker), `L` is `undefined`. The map creation `useEffect` at `App.tsx` line 97 checks `!L` and silently returns — the map never renders, with no user-visible error.
- Safe modification: Add an error boundary or an explicit check with a visible fallback message. For offline exhibition use, bundle Leaflet via npm.

**`mapRef.current` vs `mapInstance` state: two references to the same map object with unclear ownership:**
- Files: `frontend/src/App.tsx` lines 46, 57, 96–128
- Why fragile: `mapRef.current` is the authoritative reference for imperative Leaflet operations. `mapInstance` is a React state copy of the same object, used only to trigger re-renders (e.g., passing to `LossLayer` and `MorphLayer`). These can briefly diverge during the `useEffect` that initialises the map — `mapRef.current` is set synchronously but `setMapInstance` schedules a re-render. If any child component reads `map` prop before the state update flushes, it receives `null`.
- Safe modification: Consider storing the map only in a ref and exposing it to children via a React context rather than prop drilling the stale state value.

**MorphLayer cleanup: Leaflet `divider` and `range` elements are hidden via `style.display` and restored in the cleanup function — if the component unmounts abnormally, these DOM elements remain hidden:**
- Files: `frontend/src/components/MorphLayer.tsx` lines 72–87
- Why fragile: The `return () => { ... }` cleanup restores `divider.style.display = ''`. If the effect reruns before cleanup completes (fast mode toggle), the references may point to detached DOM elements.
- Safe modification: Track visibility state in React rather than mutating Leaflet DOM directly.

**`_compute_change()` imports `numpy` and `PIL` inside the function body, not at module top:**
- Files: `backend/server.py` lines 231–232
- Why fragile: Import errors (missing package) will only surface at request time, not at startup. If `pillow` or `numpy` is missing from the environment, the `/api/change` endpoint returns a 502 with no early warning.
- Safe modification: Move imports to module top level so missing dependencies cause a startup crash rather than a runtime 502.

---

## Missing Critical Features

**No offline / kiosk mode for exhibition use:**
- Problem: The app depends on four external live services: the Wasabi S3 STAC collection (`s3.eu-central-1.wasabisys.com`), TiTiler (`titiler.xyz`), the IGN WMS (`ign.es/wms/pnoa-historico`), and the CartoCDN base tiles. At an exhibition venue with restricted internet, any of these can fail silently — the map loads but shows blank tiles or a loading spinner indefinitely.
- Blocks: Reliable operation at the AI4ALL exhibition.
- Files: `backend/server.py` lines 32–33, 162–163, 307–314; `frontend/src/App.tsx` lines 106–110

**No loading state when Story mode opens — frames appear blank until all 6 PNGs load:**
- Problem: `MorphLayer.tsx` sets `ready = true` immediately after `addTo(map)` calls, before browser has actually decoded the PNG data. The `setFrac(0)` and opacity logic run but display nothing until network completes.
- Files: `frontend/src/components/MorphLayer.tsx` lines 57–68
- Fix: Listen to `imageoverlay load` events or use a `Promise.all` over Image preloads before setting `ready = true`.

**`/api/ideology/score` endpoint exists but the frontend never calls it:**
- Problem: `backend/server.py` defines `POST /api/ideology/score` (line 412) which returns a `ScoringResult`. The frontend skips this step and posts directly to `POST /api/ideology/interpret`, which internally calls `calculate_score()` anyway. The dedicated score endpoint is dead.
- Files: `backend/server.py` lines 412–419, `frontend/src/components/IdeologyPanel.tsx` lines 113–135
- Blocks: Nothing currently; it's unused API surface that could confuse future contributors.

**No favicon or app metadata for exhibition browser:**
- Problem: `frontend/index.html` has no `<link rel="icon">`, no `<meta name="description">`, no Open Graph tags. Title is `"AI4ALL Land Cover Viewer"` — likely not the final exhibition name ("Beneath the Flight Path" is referenced in the project brief).
- Files: `frontend/index.html`
- Blocks: Polished exhibition presentation; browser tab shows a generic icon.

**`GEMINI.md` describes a Jupyter Notebook workflow that no longer reflects the current app:**
- Problem: The root `GEMINI.md` describes building a Folium/Jupyter map and has nothing to do with the current React/FastAPI codebase. It will mislead any AI agent or contributor reading it as project documentation.
- Files: `GEMINI.md`
- Fix approach: Update or replace with accurate project description for the redesign phase.

---

## Test Coverage Gaps

**Zero test files exist for either frontend or backend:**
- What's not tested: All backend endpoints (`/api/map-config`, `/api/change`, `/api/datasets`, `/api/ideology/*`), the scoring/interpretation logic in `ideology_agent_service.py`, the React components, the radar chart canvas drawing function.
- Files: Entire `frontend/src/` and `backend/` directories
- Risk: Refactoring during the redesign has no safety net. The scoring algorithm in `ideology_agent_service.py` `calculate_score()` has non-obvious normalisation logic (max possible per category is 125, not 100) that is untested.
- Priority: High — especially for `ideology_agent_service.py` since it contains business logic.

---

## Stale / Leftover Assets

**`delta_morph_geo.mp4` duplicated in both `public/assets/decay/` and `public/assets/story/real/`:**
- Files: `frontend/public/assets/decay/delta_morph_geo.mp4`, `frontend/public/assets/story/real/delta_morph_geo.mp4`
- The video file (2.4 MB) exists in two locations. `LoupeLens.tsx` references `/assets/decay/delta_morph_geo.mp4`. The copy in `story/real/` appears to be a leftover from a directory reorganisation (the prior commit message references "Remove unused rejected Option-B decay assets").
- Fix approach: Delete `public/assets/story/real/delta_morph_geo.mp4`. Keep only `public/assets/decay/`.

**Root-level debug screenshots committed to the repo:**
- Files: `app-launch.png`, `app-loaded.png`, `app-wide.png` (1.6 MB combined) in the project root
- These are Playwright-captured debugging screenshots, not project assets. They are not `.gitignore`'d and were committed.
- Fix approach: Add `*.png` to `.gitignore` at root level (or specifically these three filenames), then remove them from the tree.

**`backend_run.log` committed to the repo root:**
- Files: `backend_run.log`
- A runtime log file with uvicorn request history is present in the repo root and not gitignored.
- Fix approach: Add `*.log` to `.gitignore` and remove from tree.

**`graphify-out/` directory contains generated analysis artifacts:**
- Files: `graphify-out/graph.html`, `graphify-out/graph.json`, `graphify-out/cache/`, etc.
- These are AI agent analysis outputs, not source code or assets. They are not gitignored.
- Fix approach: Add `graphify-out/` to `.gitignore`.

---

## Scaling Limits

**titiler.xyz is a free public instance with no SLA:**
- Current capacity: Unknown — public shared service
- Limit: Rate limiting or downtime will cause all map tiles to fail silently. The app shows no fallback when tiles return non-200 responses — Leaflet simply leaves tiles blank.
- Scaling path: Self-host TiTiler in a Docker container for exhibition use, or pre-render and cache the required tile sets.

**`@lru_cache` on `_build_map_config()` and `_compute_change()` is process-scoped:**
- If the backend runs with multiple worker processes (e.g., `uvicorn --workers 4`), each process maintains its own cache. The first request to each worker fires a cold STAC+COG fetch.
- Files: `backend/server.py` lines 170, 227
- Scaling path: Use a shared Redis cache or pre-warm all workers at startup.

---

*Concerns audit: 2026-06-10*
