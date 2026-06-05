import { useEffect, useRef, useState } from 'react'

/**
 * MorphLayer — the "Story" view: the real map morphing into the real airport.
 *
 * Base reality (no AI, true coordinates, IGN PNOA histórico orthophotos):
 *   • 1956 — the delta + the tiny early El Prat airport.
 *   • 2015 — today's Barcelona (BCN) airport over that same ground.
 * Cross-dissolved in place on the Leaflet map.
 *
 * Exaggerated animation blended ON TOP of that reality:
 *   • the live imagery is colour-graded cold + desaturated as it dies into concrete
 *   • a glowing magenta "scar" (the REAL nature→built loss mask from /api/change),
 *     geo-pinned and pulsing, swells in over the exact ground that was paved
 *   • a vignette closes in; a shockwave ring fires when you hit play.
 */

const L = (window as any).L
const WMS = 'https://www.ign.es/wms/pnoa-historico?'
const BEFORE = { layer: 'AMS_1956-1957', year: 1956 }
const AFTER = { layer: 'PNOA2015', year: 2015 }

// Frame on the El Prat airport itself.
const CENTER: [number, number] = [41.2974, 2.0785]
const AIRPORT_BOUNDS: [[number, number], [number, number]] = [
  [41.272, 2.035],
  [41.318, 2.122],
]
const PUSH_ZOOM = 15
const MORPH_MS = 6500

type Change = {
  hectares_lost: number
  image?: string
  bbox?: [number, number, number, number] // [W,S,E,N]
}
// A realistic distant flock — tiny gull silhouettes scattered over the delta sky,
// each flapping + drifting slightly. Reads as real far-off birds, not sticker emoji.
// Deterministic spread (no Math.random) across the upper-left delta region.
const FLOCK = Array.from({ length: 26 }, (_, i) => {
  const gx = (i * 53) % 100 // 0..100 pseudo-spread
  const gy = (i * 31) % 100
  return {
    left: `${6 + (gx / 100) * 58}%`, // cluster over the delta, not the open sea
    top: `${8 + (gy / 100) * 34}%`,
    scale: 0.95 + ((i * 17) % 100) / 110, // 0.95..1.86
    flapDur: `${0.7 + ((i * 13) % 60) / 100}s`, // 0.7..1.3s wingbeat
    driftDur: `${9 + ((i * 7) % 80) / 10}s`, // 9..17s drift
    delay: `-${(i * 0.37).toFixed(2)}s`,
  }
})

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v))
const fmt = (n: number) => Math.round(n).toLocaleString('en-US')
const ease = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2)

type Props = { map: any | null; active: boolean }

export default function MorphLayer({ map, active }: Props) {
  const baseRef = useRef<any>(null)
  const beforeRef = useRef<any>(null)
  const afterRef = useRef<any>(null)
  const scarRef = useRef<HTMLImageElement | null>(null)
  const [frac, setFrac] = useState(0) // 0 = 1956 delta, 1 = 2015 airport
  const [playing, setPlaying] = useState(false)
  const [change, setChange] = useState<Change | null>(null)
  const [ready, setReady] = useState(false)
  const [shockKey, setShockKey] = useState(0)

  useEffect(() => {
    fetch('/api/change')
      .then((r) => r.json())
      .then((d) => setChange(d?.detail ? null : d))
      .catch(() => setChange(null))
  }, [])

  // Add / remove the real IGN aerial layers when Story mode toggles.
  useEffect(() => {
    if (!map || !L || !active) return
    const container: HTMLElement = map.getContainer()
    const saved = { center: map.getCenter(), zoom: map.getZoom() }

    // PNOA orthophotos are land-only — request transparent PNG so sea / coverage
    // gaps fall through to a real satellite base instead of rendering as white.
    const common = {
      format: 'image/png',
      version: '1.1.1',
      transparent: true,
      maxZoom: 24,
      attribution: 'Imagery © Instituto Geográfico Nacional de España (PNOA)',
    }
    const base = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 24, zIndex: 499, attribution: 'Esri World Imagery' },
    ).addTo(map)
    const before = L.tileLayer.wms(WMS, { ...common, layers: BEFORE.layer, zIndex: 500 }).addTo(map)
    const after = L.tileLayer.wms(WMS, { ...common, layers: AFTER.layer, opacity: 0, zIndex: 501 }).addTo(map)
    baseRef.current = base
    beforeRef.current = before
    afterRef.current = after
    setFrac(0)
    setPlaying(false)
    setReady(true)

    // hide the side-by-side wipe divider — Story mode blends instead of wipes
    const divider = container.querySelector<HTMLElement>('.leaflet-sbs-divider')
    const range = container.querySelector<HTMLElement>('.leaflet-sbs-range')
    if (divider) divider.style.display = 'none'
    if (range) range.style.display = 'none'

    map.flyToBounds(AIRPORT_BOUNDS, { duration: 1.1 })

    return () => {
      setReady(false)
      if (baseRef.current) map.removeLayer(baseRef.current)
      if (beforeRef.current) map.removeLayer(beforeRef.current)
      if (afterRef.current) map.removeLayer(afterRef.current)
      baseRef.current = null
      beforeRef.current = null
      afterRef.current = null
      if (divider) divider.style.display = ''
      if (range) range.style.display = ''
      container.style.filter = ''
      map.setView(saved.center, saved.zoom)
    }
  }, [map, active])

  // Blend fraction -> layer opacities + a cold/desaturated grade on the live map
  // (the exaggeration: the real imagery visibly loses its life as concrete wins).
  useEffect(() => {
    if (beforeRef.current) beforeRef.current.setOpacity(1 - frac)
    if (afterRef.current) afterRef.current.setOpacity(frac)
    if (map && active) {
      const c = map.getContainer() as HTMLElement
      // warm golden vintage on the 1956 side (beautiful, not clinical) -> cold grey 2015
      const sepia = (0.4 * (1 - frac)).toFixed(3)
      const sat = (1 - 0.5 * frac).toFixed(3)
      const bri = (1.02 - 0.14 * frac).toFixed(3)
      const con = (1 + 0.12 * frac).toFixed(3)
      c.style.filter = `sepia(${sepia}) saturate(${sat}) brightness(${bri}) contrast(${con})`
    }
    // keep the scar a translucent accent — it should glow over the airport, not bury it
    if (scarRef.current) scarRef.current.style.opacity = `${clamp((frac - 0.35) / 0.5, 0, 1) * 0.4}`
  }, [frac, ready, map, active])

  // Geo-pin the loss scar each frame so it tracks pan/zoom (it marks the real
  // nature→built cells from /api/change, glowing over the airport that ate them).
  useEffect(() => {
    if (!map || !active || !change?.image || !change?.bbox) return
    const [w, s, e, n] = change.bbox
    let raf = 0
    const tick = () => {
      const img = scarRef.current
      if (img && map._loaded && map._mapPane && (map._mapPane as any)._leaflet_pos) {
        const nw = map.latLngToContainerPoint([n, w])
        const se = map.latLngToContainerPoint([s, e])
        img.style.left = `${nw.x}px`
        img.style.top = `${nw.y}px`
        img.style.width = `${se.x - nw.x}px`
        img.style.height = `${se.y - nw.y}px`
      }
      raf = window.requestAnimationFrame(tick)
    }
    raf = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(raf)
  }, [map, active, change])

  // Auto-play: cross-fade while the camera pushes in + a shockwave ring fires.
  useEffect(() => {
    if (!playing || !map) return
    let raf = 0
    let start = 0
    if (frac >= 0.999) setFrac(0)
    setShockKey((k) => k + 1)
    map.flyTo(CENTER, PUSH_ZOOM, { duration: MORPH_MS / 1000 })
    const step = (ts: number) => {
      if (!start) start = ts
      const t = clamp((ts - start) / MORPH_MS, 0, 1)
      setFrac(ease(t))
      if (t >= 1) {
        setPlaying(false)
        return
      }
      raf = window.requestAnimationFrame(step)
    }
    raf = window.requestAnimationFrame(step)
    return () => window.cancelAnimationFrame(raf)
  }, [playing, map])

  if (!active) return null

  const year = Math.round(BEFORE.year + frac * (AFTER.year - BEFORE.year))
  const statOpacity = clamp((frac - 0.4) / 0.4, 0, 1)
  // nature life is full on the 1956 delta, gone by ~60% of the morph
  const lifeOpacity = clamp(1 - frac / 0.6, 0, 1)

  return (
    <div className="morph-ui">
      {/* glowing real-loss scar, geo-pinned (position set imperatively) */}
      {change?.image ? <img ref={scarRef} className="morph-scar" src={change.image} alt="" style={{ opacity: 0 }} /> : null}

      {/* living delta: a realistic distant flock, scattering away as concrete wins */}
      <div className="morph-flock" style={{ opacity: lifeOpacity }}>
        {FLOCK.map((b, i) => (
          <span
            key={i}
            className="gull"
            style={{
              left: b.left,
              top: b.top,
              transform: `scale(${b.scale})`,
              animationDuration: b.driftDur,
              animationDelay: b.delay,
            }}
          >
            <svg viewBox="0 0 24 10" width="34" height="14" aria-hidden="true">
              <path
                className="gull-wing"
                d="M1 7 Q6 1 12 6 Q18 1 23 7"
                fill="none"
                stroke="rgba(22,26,32,0.92)"
                strokeWidth="1.9"
                strokeLinecap="round"
                style={{ animationDuration: b.flapDur, animationDelay: b.delay }}
              />
            </svg>
          </span>
        ))}
      </div>

      {/* vignette that closes in as the delta dies */}
      <div className="morph-fx" style={{ opacity: 0.15 + 0.6 * frac }} />

      {/* shockwave ring on play */}
      {playing ? <div key={shockKey} className="morph-shock" /> : null}

      <div className="cine-head">
        <p className="cine-place">El Prat airport · Llobregat delta</p>
        <p className="cine-year">{year}</p>
      </div>

      {change ? (
        <div className="cine-stat" style={{ opacity: statOpacity }}>
          <strong>{fmt(change.hectares_lost)} ha</strong>
          <span>of delta nature paved into the airport &amp; city</span>
        </div>
      ) : null}

      <div className="cine-controls">
        <button
          type="button"
          className="cine-play"
          onClick={() => setPlaying((p) => !p)}
          aria-label={playing ? 'Pause' : 'Play morph'}
        >
          {playing ? '❚❚' : '▶'}
        </button>
        <span className="cine-end-label">{BEFORE.year}</span>
        <input
          className="cine-range"
          type="range"
          min={0}
          max={1000}
          value={Math.round(frac * 1000)}
          onChange={(e) => setFrac(Number(e.target.value) / 1000)}
          onMouseDown={() => setPlaying(false)}
          aria-label="Blend from 1956 delta to 2015 airport"
        />
        <span className="cine-end-label">{AFTER.year}</span>
      </div>

      <p className="cine-tag">Real aerial imagery · IGN España (PNOA) · 1956 &amp; 2015 · loss measured from GLC</p>
    </div>
  )
}
