import { useEffect, useRef, useState } from 'react'

/**
 * LossLayer — the honest, data-driven heart of the tool.
 *
 * Fetches /api/change (a real 1985->2022 diff of the GLC_FCS30D land cover:
 * where natural cover became impervious built-up) and renders it two ways:
 *   1. A red overlay marking exactly those lost cells, pinned to the delta
 *      bbox by projecting its corners each frame and revealed on the 2022 side
 *      of the divider — so swiping toward 2022 exposes the real loss in place.
 *   2. A stats panel with the measured hectares lost, by ecosystem type, cited.
 *
 * No AI, no projection — every red pixel and every number is the data.
 */

type Change = {
  bbox: [number, number, number, number] // [W,S,E,N]
  image: string
  hectares_lost: number
  breakdown: Record<string, number>
  resolution_m: number
  year_from: number
  year_to: number
  source: string
}

const LABELS: Record<string, string> = {
  cropland: 'Cropland',
  wetland: 'Wetland',
  forest: 'Forest',
  shrub_grass: 'Shrub & grass',
  water: 'Water',
}

const fmt = (n: number) => Math.round(n).toLocaleString('en-US')

type Props = {
  map: any | null
  hidden?: boolean
}

export default function LossLayer({ map, hidden = false }: Props) {
  const [data, setData] = useState<Change | null>(null)
  const [visible, setVisible] = useState(true)
  const imgRef = useRef<HTMLImageElement | null>(null)

  useEffect(() => {
    fetch('/api/change')
      .then(async (r) => {
        const payload = await r.json()
        if (!r.ok || payload?.detail) throw new Error(payload?.detail || 'change failed')
        setData(payload as Change)
      })
      .catch(() => setData(null))
  }, [])

  useEffect(() => {
    if (!map || !data) return
    const container: HTMLElement = map.getContainer()
    const [w, s, e, n] = data.bbox
    let raf = 0

    const readFraction = (): number => {
      const range = container.querySelector<HTMLInputElement>('.leaflet-sbs-range')
      if (!range) return 0.5
      const min = Number(range.min || 0)
      const max = Number(range.max || 1)
      const span = max - min || 1
      return (Number(range.value) - min) / span
    }

    const tick = () => {
      const img = imgRef.current
      // map._mapPane is torn down before our rAF stops during unmount/HMR;
      // projecting then throws (_leaflet_pos undefined). Skip that frame.
      if (img && map._loaded && map._mapPane && (map._mapPane as any)._leaflet_pos) {
        const nw = map.latLngToContainerPoint([n, w])
        const se = map.latLngToContainerPoint([s, e])
        const width = se.x - nw.x
        const height = se.y - nw.y
        img.style.left = `${nw.x}px`
        img.style.top = `${nw.y}px`
        img.style.width = `${width}px`
        img.style.height = `${height}px`
        // Reveal the loss only where 2022 is shown (right of the divider).
        const frac = Math.max(0, Math.min(1, readFraction()))
        const localLeft = Math.max(0, Math.min(width, frac * container.clientWidth - nw.x))
        img.style.clipPath = `inset(0 0 0 ${localLeft}px)`
      }
      raf = window.requestAnimationFrame(tick)
    }
    raf = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(raf)
  }, [map, data])

  if (!data || hidden) return null

  const rows = Object.entries(data.breakdown)
    .filter(([, ha]) => ha > 0)
    .sort((a, b) => b[1] - a[1])
  const maxHa = rows.length ? rows[0][1] : 1
  const km2 = data.hectares_lost / 100

  return (
    <>
      <div className="loss-root">
        {visible ? <img ref={imgRef} className="loss-img" src={data.image} alt="" /> : null}
      </div>

      <div className="panel loss-panel">
        <p className="eyebrow">Measured land-cover change</p>
        <h2 className="loss-headline">
          <strong>{fmt(data.hectares_lost)} ha</strong> of nature paved over
        </h2>
        <p className="loss-sub">
          Natural land cover → built-up, {data.year_from}–{data.year_to} · ≈{km2.toFixed(0)} km²
        </p>

        <div className="loss-bars">
          {rows.map(([key, ha]) => (
            <div className="loss-bar-row" key={key}>
              <span className="loss-bar-label">{LABELS[key] || key}</span>
              <span className="loss-bar-track">
                <span className="loss-bar-fill" style={{ width: `${Math.max(3, (ha / maxHa) * 100)}%` }} />
              </span>
              <span className="loss-bar-val">{fmt(ha)} ha</span>
            </div>
          ))}
        </div>

        <button type="button" className="loss-toggle" onClick={() => setVisible((v) => !v)}>
          {visible ? 'Hide loss on map' : 'Show loss on map'}
        </button>
        <p className="loss-source">{data.source} · sampled {data.resolution_m} m</p>
      </div>
    </>
  )
}
