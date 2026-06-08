import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import 'leaflet/dist/leaflet.css'
import IdeologyPanel from './components/IdeologyPanel'
import LossLayer from './components/LossLayer'
import MorphLayer from './components/MorphLayer'

const L = (window as any).L

type LayerInfo = {
  year: number
  tiles: string
  label?: string | null
}

type LegendItem = {
  quantity: string
  label: string
  color: string
}

type Gradient = {
  colors: string[]
  min_label: string
  max_label: string
  unit: string
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

type DatasetMeta = { id: string; label: string; subtitle: string }

export default function App() {
  const mapRef = useRef<any>(null)
  const leftLayerRef = useRef<any>(null)
  const rightLayerRef = useRef<any>(null)
  const compareControlRef = useRef<any>(null)
  const [uiRoot, setUiRoot] = useState<HTMLElement | null>(null)
  const [datasets, setDatasets] = useState<DatasetMeta[]>([])
  const [dataset, setDataset] = useState('landcover')
  const [config, setConfig] = useState<MapConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [opacity, setOpacity] = useState(1)
  const [storyMode, setStoryMode] = useState(false)
  const [mapInstance, setMapInstance] = useState<any>(null)
  const [hoverLegend, setHoverLegend] = useState<{ item: LegendItem; x: number; y: number } | null>(null)

  useEffect(() => {
    let root = document.getElementById('ui-root')
    if (!root) {
      root = document.createElement('div')
      root.id = 'ui-root'
      document.body.appendChild(root)
    }
    setUiRoot(root)
  }, [])

  // Dataset list for the switcher.
  useEffect(() => {
    fetch('/api/datasets')
      .then((r) => r.json())
      .then((d: DatasetMeta[]) => setDatasets(d))
      .catch(() => setDatasets([]))
  }, [])

  // (Re)load the map config whenever the selected dataset changes.
  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`/api/map-config?dataset=${dataset}`)
      .then(async (response) => {
        const payload = await response.json()
        if (!response.ok || payload?.detail) {
          throw new Error(payload?.detail || 'Failed to load map configuration.')
        }
        setConfig(payload as MapConfig)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [dataset])

  // Create the Leaflet map exactly once (after the first config arrives).
  const hasConfig = !!config
  useEffect(() => {
    if (!hasConfig || !L || mapRef.current || !config) return
    const initialZoom = Math.min(24, Math.round(config.zoom * 1.2))
    const map = L.map('map', {
      center: config.center,
      zoom: initialZoom,
      zoomControl: false,
      worldCopyJump: true,
    })
    L.control.zoom({ position: 'bottomright' }).addTo(map)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 24,
    }).addTo(map)
    mapRef.current = map
    setMapInstance(map)

    return () => {
      setMapInstance(null)
      if (compareControlRef.current) {
        compareControlRef.current.remove()
        compareControlRef.current = null
      }
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
      leftLayerRef.current = null
      rightLayerRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasConfig])

  // (Re)build the side-by-side data layers whenever the dataset/config changes —
  // the map itself is preserved (Story mode, basemap, view all stay put).
  useEffect(() => {
    const map = mapRef.current
    if (!map || !config || !L) return
    if (compareControlRef.current) {
      compareControlRef.current.remove()
      compareControlRef.current = null
    }
    if (leftLayerRef.current) {
      map.removeLayer(leftLayerRef.current)
      leftLayerRef.current = null
    }
    if (rightLayerRef.current) {
      map.removeLayer(rightLayerRef.current)
      rightLayerRef.current = null
    }
    const eff = storyMode ? 0 : opacity
    // Continuous datasets (temp, pollution) are coarse 1-2 km rasters — smooth the
    // hard pixel blocks into a legible field. Categorical land cover stays crisp.
    const cls = config.legend_kind === 'gradient' ? 'smooth-raster' : ''
    const left = L.tileLayer(config.left.tiles, { opacity: eff, maxZoom: 24, className: cls, attribution: 'OpenLandMap' }).addTo(map)
    const right = L.tileLayer(config.right.tiles, { opacity: eff, maxZoom: 24, className: cls, attribution: 'OpenLandMap' }).addTo(map)
    leftLayerRef.current = left
    rightLayerRef.current = right
    compareControlRef.current = L.control.sideBySide(left, right).addTo(map)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config, mapInstance])

  // Opacity + Story mode hide/show the data layers.
  useEffect(() => {
    const eff = storyMode ? 0 : opacity
    if (leftLayerRef.current) leftLayerRef.current.setOpacity(eff)
    if (rightLayerRef.current) rightLayerRef.current.setOpacity(eff)
  }, [opacity, storyMode])

  const leftLabel = config?.left.label ?? String(config?.left.year ?? '')
  const rightLabel = config?.right.label ?? String(config?.right.year ?? '')

  const legendTitle = useMemo(() => {
    if (!config) return 'Legend'
    if (config.legend_kind === 'gradient' && config.gradient) return config.gradient.unit
    return `Land cover (${leftLabel} vs ${rightLabel})`
  }, [config, leftLabel, rightLabel])

  const panels = () => {
    if (loading && !config) {
      return (
        <div className="panel shell">
          <div className="title">Loading map data...</div>
        </div>
      )
    }

    if (error) {
      return (
        <div className="panel shell">
          <div className="title">Unable to load map</div>
          <p className="subtitle">{error}</p>
        </div>
      )
    }

    if (!config) {
      return (
        <div className="panel shell">
          <div className="title">No map configuration found.</div>
        </div>
      )
    }

    const isGradient = config.legend_kind === 'gradient' && config.gradient

    return (
      <>
        <div className="mode-switch" role="group" aria-label="Map view mode">
          <button
            type="button"
            className={`mode-btn ${storyMode ? '' : 'active'}`}
            onClick={() => setStoryMode(false)}
          >
            🛰 Data
          </button>
          <button
            type="button"
            className={`mode-btn ${storyMode ? 'active' : ''}`}
            onClick={() => setStoryMode(true)}
          >
            🌱 Story
          </button>
        </div>

        {/* Dataset switcher — only meaningful in Data mode */}
        {!storyMode && datasets.length > 0 && (
          <div className="dataset-switch" role="group" aria-label="Dataset">
            {datasets.map((d) => (
              <button
                key={d.id}
                type="button"
                className={`ds-btn ${dataset === d.id ? 'active' : ''}`}
                onClick={() => setDataset(d.id)}
                title={d.subtitle}
              >
                <span className="ds-label">{d.label}</span>
                <span className="ds-sub">{d.subtitle}</span>
              </button>
            ))}
          </div>
        )}

        <div className="panel shell" style={storyMode ? { display: 'none' } : undefined}>
          <p className="eyebrow">AI4ALL Participatory Motivation</p>
          <h1 className="title">{config.dataset_label}</h1>
          <p className="subtitle">
            Drag the vertical slider to compare {leftLabel} and {rightLabel} side by side.
          </p>
          <div className="opacity-control">
            <label htmlFor="opacity-range">Layer opacity</label>
            <input
              id="opacity-range"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={opacity}
              onChange={(event) => setOpacity(Number(event.target.value))}
            />
            <span>{opacity.toFixed(2)}</span>
          </div>
          <p className="source">Source: {config.source}</p>
        </div>

        {!storyMode && <div className="year-chip left">{leftLabel}</div>}
        {!storyMode && <div className="year-chip right">{rightLabel}</div>}

        <div className="panel legend-panel" style={storyMode ? { display: 'none' } : undefined}>
          <h2>{legendTitle}</h2>
          {isGradient ? (
            <>
              <p className="legend-help">Continuous scale — same range on both sides, so the change is comparable.</p>
              <div
                className="gradient-bar"
                style={{ background: `linear-gradient(90deg, ${config.gradient!.colors.join(', ')})` }}
              />
              <div className="gradient-labels">
                <span>{config.gradient!.min_label}</span>
                <span>{config.gradient!.max_label}</span>
              </div>
            </>
          ) : (
            <>
              <p className="legend-help">Simplified into a few clear land types.</p>
              <div className="legend-list">
                {config.legend.map((item) => (
                  <button
                    type="button"
                    className="legend-row"
                    key={item.quantity}
                    onMouseEnter={(event) => setHoverLegend({ item, x: event.clientX + 12, y: event.clientY + 18 })}
                    onMouseMove={(event) => setHoverLegend({ item, x: event.clientX + 12, y: event.clientY + 18 })}
                    onMouseLeave={() => setHoverLegend(null)}
                  >
                    <span className="legend-swatch" style={{ backgroundColor: item.color }} />
                    <span className="legend-text">{item.label}</span>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </>
    )
  }

  return (
    <div className="app-root">
      <div id="map" className="map-container" />
      {uiRoot
        ? createPortal(<LossLayer map={mapInstance} hidden={storyMode || dataset !== 'landcover'} />, uiRoot)
        : <LossLayer map={mapInstance} hidden={storyMode || dataset !== 'landcover'} />}
      {uiRoot ? createPortal(<MorphLayer map={mapInstance} active={storyMode} />, uiRoot) : <MorphLayer map={mapInstance} active={storyMode} />}
      {uiRoot ? createPortal(panels(), uiRoot) : panels()}
      {!storyMode && (uiRoot ? createPortal(<IdeologyPanel />, uiRoot) : <IdeologyPanel />)}

      {uiRoot && hoverLegend
        ? createPortal(
            <div className="legend-popup" style={{ left: hoverLegend.x, top: hoverLegend.y }}>
              <div className="popup-swatch" style={{ backgroundColor: hoverLegend.item.color }} />
              <div className="popup-body">
                <div className="popup-title">{hoverLegend.item.label}</div>
              </div>
            </div>,
            uiRoot,
          )
        : null}
    </div>
  )
}
