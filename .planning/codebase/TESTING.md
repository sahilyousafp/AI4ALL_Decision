# Testing Patterns

**Analysis Date:** 2026-06-10

## Test Framework

**Runner:**
- None — no test framework is installed or configured
- `frontend/package.json` has no test runner (no Vitest, Jest, or similar) and no `scripts.test` entry
- `backend/requirements.txt` lists no pytest, httpx, or test-related packages
- No `jest.config.*`, `vitest.config.*`, or `pytest.ini` files exist anywhere in the repository

**Assertion Library:**
- None

**Run Commands:**
```bash
# No test commands exist
# The only scripts in package.json are:
npm run dev        # Start Vite dev server on port 5173
npm run build      # Build to frontend/dist/
npm run preview    # Preview production build
```

## Test File Organization

**Location:**
- No test files exist in the project source tree
- A single test file was found at `frontend/node_modules/gensync/test/index.test.js` — this is a transitive dependency file, not a project test

**Naming:**
- No established naming convention (nothing to observe)

## CI/CD

**CI Pipeline:**
- No `.github/` directory exists — GitHub Actions is not configured
- No CI configuration of any kind (CircleCI, GitLab CI, Bitbucket Pipelines, etc.) detected

## What Exists Instead of Tests

**Manual verification:**
- Screenshots of the running app (`app-launch.png`, `app-loaded.png`, `app-wide.png` at the repo root) indicate manual browser testing is the current verification approach

**Backend validation via Pydantic:**
- All API request/response shapes are validated by Pydantic `BaseModel` at the FastAPI layer — this provides some runtime contract enforcement at the boundary between frontend and backend
- `IdeologyAgentService.calculate_score()` performs explicit input validation with `ValueError` (checks response count and valid values 0/1/2) — this is the closest thing to tested logic in the codebase:
  ```python
  def calculate_score(self, responses: list[int]) -> ScoringResult:
      if not responses or len(responses) != len(self.QUESTIONS):
          raise ValueError(f"Expected {len(self.QUESTIONS)} responses, got {len(responses)}")
      for resp in responses:
          if resp not in [0, 1, 2]:
              raise ValueError(f"Response values must be 0, 1, or 2, got {resp}")
  ```

**`@lru_cache` as implicit smoke test:**
- `_build_map_config()`, `_compute_change()`, and `_get_change_assets()` in `backend/server.py` are cached with `@lru_cache(maxsize=1)`. These will raise `RuntimeError` on first call if STAC assets are missing — this surfaces integration failures at startup time rather than silently serving bad data.

## Test Coverage Gaps

**Untested areas (entire codebase):**

- `IdeologyAgentService.calculate_score()` scoring math — option 0/1/2 weighting, normalization to 0-100, lean determination logic — all untested
- `IdeologyAgentService.get_static_interpretation()` branching logic — thresholds (80, +10) for `high_environmental` / `high_comfort` / `balanced` are untested
- `_simplified_colormap()` and `_simplified_legend()` in `backend/server.py` — GLC class code → group colour mapping is unchecked
- `_compute_change()` change detection logic — the numpy masking and hectare math is not tested with known inputs
- `_bbox_3857()` and Mercator projection helpers in `backend/story_frames.py` — geometric calculations are untested
- All React components — no component rendering, prop-passing, or user interaction tests
- All API endpoints — no integration or contract tests with a test client (e.g., FastAPI's `TestClient`)
- `drawRadarChart()` canvas rendering function in `frontend/src/components/IdeologyPanel.tsx`
- The `LossLayer` rAF animation loop and `readFraction()` divider parsing logic

## Recommendations for Adding Tests

**Highest priority (pure logic, easiest to test):**
- `backend/ideology_agent_service.py` — `calculate_score()` and `get_static_interpretation()` have zero external dependencies; add `pytest` and write parametrized unit tests
- `backend/story_frames.py` — `_bbox_3857()`, `_merc_x()`, `_merc_y()`, `_inv_merc_y()` are pure math functions; verify round-trip accuracy

**Medium priority (integration):**
- FastAPI endpoints via `fastapi.testclient.TestClient` — mock `requests.get` to avoid live STAC calls; test 200 responses and 502 error paths for `/api/map-config`, `/api/change`, `/api/ideology/questions`, `/api/ideology/interpret`

**Frontend:**
- Add Vitest + `@testing-library/react` — test `IdeologyPanel` question progression, option selection, and results rendering
- Test `LossLayer` render with `hidden=true` returns null
- Test `MorphLayer` renders null when `active=false`

**CI:**
- No CI pipeline is present; adding a GitHub Actions workflow would be the first step to enforcing any tests on push

---

*Testing analysis: 2026-06-10*
