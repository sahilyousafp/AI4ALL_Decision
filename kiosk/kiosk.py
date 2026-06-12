"""
Mock voting kiosk for the AI4ALL exhibition.

Runs on port 8000 and feeds the map app (frontend, port 5173) over SSE:
the map listens to GET /events and switches its data layer to match the
leading scenario (expand -> landcover, balance -> NO2, protect -> LST).

Endpoints:
  GET  /        - kiosk touch UI (three vote buttons + live tally)
  GET  /events  - SSE stream of {"type": "tally_update", expand, balance, protect}
  POST /vote    - body {"scenario": "expand" | "balance" | "protect"}
  POST /reset   - zero the tally
  GET  /tally   - current tally as JSON

Run:  python kiosk/kiosk.py
"""
from __future__ import annotations

import asyncio
import json

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="AI4ALL Voting Kiosk")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SCENARIOS = ("expand", "balance", "protect")

tally: dict[str, int] = {s: 0 for s in SCENARIOS}
subscribers: set[asyncio.Queue] = set()


class Vote(BaseModel):
    scenario: str


def tally_message() -> str:
    return json.dumps({"type": "tally_update", **tally})


async def broadcast() -> None:
    msg = tally_message()
    for q in list(subscribers):
        await q.put(msg)


@app.get("/events")
async def events():
    queue: asyncio.Queue = asyncio.Queue()
    subscribers.add(queue)

    async def stream():
        try:
            # Send the current state immediately so late joiners sync up.
            yield {"data": tally_message()}
            while True:
                yield {"data": await queue.get()}
        finally:
            subscribers.discard(queue)

    return EventSourceResponse(stream(), ping=15)


@app.post("/vote")
async def vote(v: Vote):
    if v.scenario not in SCENARIOS:
        raise HTTPException(status_code=422, detail=f"scenario must be one of {SCENARIOS}")
    tally[v.scenario] += 1
    await broadcast()
    return tally


@app.post("/reset")
async def reset():
    for s in SCENARIOS:
        tally[s] = 0
    await broadcast()
    return tally


@app.get("/tally")
def get_tally():
    return tally


KIOSK_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Llobregat Delta — Cast Your Vote</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: "Segoe UI", system-ui, sans-serif;
    min-height: 100vh;
    background: radial-gradient(ellipse at top, #16261c 0%, #0a120d 70%);
    color: #e8f0e8;
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 2.2rem; padding: 2rem;
  }
  h1 { font-size: 1.9rem; font-weight: 600; letter-spacing: 0.04em; text-align: center; }
  p.sub { color: #9db8a4; text-align: center; max-width: 34rem; line-height: 1.5; }
  .buttons { display: flex; gap: 1.4rem; flex-wrap: wrap; justify-content: center; }
  button.vote {
    width: 14rem; padding: 1.6rem 1rem; border: 2px solid transparent;
    border-radius: 1.2rem; cursor: pointer; color: inherit;
    font-size: 1.15rem; font-weight: 600; line-height: 1.4;
    transition: transform 0.12s, border-color 0.12s;
  }
  button.vote:active { transform: scale(0.96); }
  button.vote .emoji { display: block; font-size: 2.6rem; margin-bottom: 0.5rem; }
  button.vote small { display: block; font-weight: 400; font-size: 0.82rem; opacity: 0.75; margin-top: 0.35rem; }
  #b-expand  { background: #3a2a20; } #b-expand:hover  { border-color: #d99a6c; }
  #b-balance { background: #2a3038; } #b-balance:hover { border-color: #8fb4d9; }
  #b-protect { background: #1f3526; } #b-protect:hover { border-color: #7fce8f; }
  .tally { display: flex; gap: 2.4rem; font-size: 1.05rem; }
  .tally span b { font-size: 1.6rem; display: block; text-align: center; }
  .leader { color: #9fe8af; font-size: 0.95rem; min-height: 1.4em; }
  .toast {
    position: fixed; bottom: 1.4rem; background: #1e3326; border: 1px solid #3f6b4c;
    padding: 0.6rem 1.2rem; border-radius: 2rem; opacity: 0; transition: opacity 0.3s;
  }
  .toast.show { opacity: 1; }
</style>
</head>
<body>
  <h1>🌍 The Llobregat Delta — You Decide</h1>
  <p class="sub">The airport wants to grow. The wetlands want to breathe.
     Cast your vote and watch the big map react.</p>

  <div class="buttons">
    <button class="vote" id="b-expand"  onclick="vote('expand')">
      <span class="emoji">🏗️</span> Expand the Airport
      <small>growth first — see the land-cover footprint</small>
    </button>
    <button class="vote" id="b-balance" onclick="vote('balance')">
      <span class="emoji">⚖️</span> Balance Both
      <small>compromise — see the air-quality tradeoff</small>
    </button>
    <button class="vote" id="b-protect" onclick="vote('protect')">
      <span class="emoji">🌿</span> Protect the Wetlands
      <small>nature first — see the cooling benefit</small>
    </button>
  </div>

  <div class="tally">
    <span>🏗️ <b id="t-expand">0</b></span>
    <span>⚖️ <b id="t-balance">0</b></span>
    <span>🌿 <b id="t-protect">0</b></span>
  </div>
  <div class="leader" id="leader"></div>
  <div class="toast" id="toast">Vote counted ✓</div>

<script>
  const NAMES = { expand: "Expand the Airport", balance: "Balance Both", protect: "Protect the Wetlands" };

  async function vote(scenario) {
    await fetch("/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario }),
    });
    const toast = document.getElementById("toast");
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 1200);
  }

  function render(t) {
    for (const s of ["expand", "balance", "protect"]) {
      document.getElementById("t-" + s).textContent = t[s] ?? 0;
    }
    const entries = Object.entries(NAMES).map(([k, v]) => [k, t[k] ?? 0, v]);
    entries.sort((a, b) => b[1] - a[1]);
    const [topKey, topVotes, topName] = entries[0];
    document.getElementById("leader").textContent =
      topVotes > 0 && topVotes > entries[1][1] ? `Leading: ${topName}` : "";
  }

  const es = new EventSource("/events");
  es.onmessage = (e) => { try { render(JSON.parse(e.data)); } catch {} };
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def kiosk_page():
    return KIOSK_HTML


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
