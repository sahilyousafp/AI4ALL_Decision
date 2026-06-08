import { useEffect, useMemo, useRef, useState } from 'react'

/**
 * MorphLayer — Story mode: a cinematic SCRUB slider over the real land change at
 * El Prat airport / Llobregat delta, Barcelona.
 *
 * Every frame is a REAL IGN PNOA orthophoto of the same fixed bbox, in exact
 * registration (1956 → 1997 → 2002 → 2008 → 2015 → 2021), then restyled by
 * Higgsfield (flux_kontext) into one consistent photoreal film-grade palette —
 * the geography is untouched, only the rendering is unified and cinematic.
 *
 * Drag the slider: adjacent real frames cross-dissolve in place, so you watch the
 * delta get paved into the airport, on the true map, with no fakery.
 */

const L = (window as any).L

type Bounds = { south: number; west: number; north: number; east: number; years: number[] }

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v))

type Props = { map: any | null; active: boolean }

export default function MorphLayer({ map, active }: Props) {
  const baseRef = useRef<any>(null)
  const overlaysRef = useRef<any[]>([])
  const [bounds, setBounds] = useState<Bounds | null>(null)
  const [frac, setFrac] = useState(0) // 0 = oldest frame, 1 = newest
  const [ready, setReady] = useState(false)

  // Load the registration bbox + year list written by backend/story_frames.py.
  useEffect(() => {
    fetch('/assets/story/real/bounds.json')
      .then((r) => r.json())
      .then((d: Bounds) => setBounds(d))
      .catch(() => setBounds(null))
  }, [])

  const years = bounds?.years ?? []
  const n = years.length

  // Add the real cinematic frames as geo-pinned overlays when Story mode opens.
  useEffect(() => {
    if (!map || !L || !active || !bounds || n === 0) return
    const saved = { center: map.getCenter(), zoom: map.getZoom() }
    const llBounds: [[number, number], [number, number]] = [
      [bounds.south, bounds.west],
      [bounds.north, bounds.east],
    ]

    // Real satellite context for everything outside the framed delta.
    const base = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 24, zIndex: 400, attribution: 'Esri World Imagery' },
    ).addTo(map)
    baseRef.current = base

    overlaysRef.current = years.map((year, i) =>
      L.imageOverlay(`/assets/story/cine/${year}.png`, llBounds, {
        opacity: i === 0 ? 1 : 0,
        zIndex: 500 + i,
        interactive: false,
        className: 'cine-frame',
      }).addTo(map),
    )

    setFrac(0)
    setReady(true)

    // hide any leftover side-by-side compare chrome from Data mode
    const container: HTMLElement = map.getContainer()
    const divider = container.querySelector<HTMLElement>('.leaflet-sbs-divider')
    const range = container.querySelector<HTMLElement>('.leaflet-sbs-range')
    if (divider) divider.style.display = 'none'
    if (range) range.style.display = 'none'

    map.flyToBounds(llBounds, { duration: 1.1, padding: [20, 20] })

    return () => {
      setReady(false)
      if (baseRef.current) map.removeLayer(baseRef.current)
      overlaysRef.current.forEach((o) => map.removeLayer(o))
      baseRef.current = null
      overlaysRef.current = []
      if (divider) divider.style.display = ''
      if (range) range.style.display = ''
      map.setView(saved.center, saved.zoom)
    }
  }, [map, active, bounds, n])

  // Cross-dissolve: find the segment the slider sits in and blend its two frames.
  const { k, f } = useMemo(() => {
    if (n < 2) return { k: 0, f: 0 }
    const pos = frac * (n - 1)
    const kk = clamp(Math.floor(pos), 0, n - 2)
    return { k: kk, f: pos - kk }
  }, [frac, n])

  useEffect(() => {
    if (!ready) return
    overlaysRef.current.forEach((o, i) => {
      if (!o) return
      const op = i < k ? 0 : i === k ? 1 : i === k + 1 ? f : 0
      o.setOpacity(op)
    })
  }, [k, f, ready])

  if (!active) return null

  const displayYear = n === 0 ? '' : f < 0.5 ? years[k] : years[Math.min(k + 1, n - 1)]
  const firstYear = years[0]
  const lastYear = years[n - 1]

  return (
    <div className="morph-ui">
      <div className="cine-head">
        <p className="cine-place">El Prat airport · Llobregat delta</p>
        <p className="cine-year">{displayYear}</p>
      </div>

      <div className="cine-controls">
        <span className="cine-end-label">{firstYear}</span>
        <input
          className="cine-range"
          type="range"
          min={0}
          max={1000}
          value={Math.round(frac * 1000)}
          onChange={(e) => setFrac(Number(e.target.value) / 1000)}
          aria-label={`Scrub real aerial imagery from ${firstYear} to ${lastYear}`}
        />
        <span className="cine-end-label">{lastYear}</span>
      </div>

      <p className="cine-tag">
        Real aerial imagery · IGN España (PNOA histórico) · {firstYear}–{lastYear} · cinematically rendered
      </p>
    </div>
  )
}
