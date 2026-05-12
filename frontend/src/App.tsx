import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import 'leaflet/dist/leaflet.css'
import IdeologyPanel from './components/IdeologyPanel'

const L = (window as any).L

type LayerInfo = {
  year: number
  tiles: string
}

type LegendItem = {
  quantity: string
  label: string
  color: string
}

type MapConfig = {
  dataset_id: string
  dataset_label: string
  left: LayerInfo
  right: LayerInfo
  legend: LegendItem[]
  center: [number, number]
  zoom: number
  source: string
}

export default function App() {
  const mapRef = useRef<any>(null)
  const leftLayerRef = useRef<any>(null)
  const rightLayerRef = useRef<any>(null)
  const compareControlRef = useRef<any>(null)
  const [uiRoot, setUiRoot] = useState<HTMLElement | null>(null)
  const [config, setConfig] = useState<MapConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [opacity, setOpacity] = useState(1)
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

  useEffect(() => {
    fetch('/api/map-config')
      .then(async (response) => {
        const payload = await response.json()
        if (!response.ok || payload?.detail) {
          throw new Error(payload?.detail || 'Failed to load map configuration.')
        }
        setConfig(payload as MapConfig)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!config || !L || mapRef.current) return

    // Increase default zoom by 20%, capped at 24
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

    const leftLayer = L.tileLayer(config.left.tiles, {
      opacity,
      maxZoom: 24,
      attribution: 'OpenLandMap',
    }).addTo(map)
    const rightLayer = L.tileLayer(config.right.tiles, {
      opacity,
      maxZoom: 24,
      attribution: 'OpenLandMap',
    }).addTo(map)

    mapRef.current = map
    leftLayerRef.current = leftLayer
    rightLayerRef.current = rightLayer
    compareControlRef.current = L.control.sideBySide(leftLayer, rightLayer).addTo(map)

    return () => {
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
  }, [config, opacity])

  useEffect(() => {
    if (leftLayerRef.current) leftLayerRef.current.setOpacity(opacity)
    if (rightLayerRef.current) rightLayerRef.current.setOpacity(opacity)
  }, [opacity])

  const legendTitle = useMemo(() => {
    if (!config) return 'Legend'
    return `Land Cover Legend (${config.left.year} vs ${config.right.year})`
  }, [config])

  const panels = () => {
    if (loading) {
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

    return (
      <>
        <div className="panel shell">
          <p className="eyebrow">AI4ALL Participatory Motivation</p>
          <h1 className="title">{config.dataset_label}</h1>
          <p className="subtitle">Drag the vertical slider to compare historical land-cover classes side by side.</p>
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

        <div className="year-chip left">{config.left.year}</div>
        <div className="year-chip right">{config.right.year}</div>

        <div className="panel legend-panel">
          <h2>{legendTitle}</h2>
          <p className="legend-help">Hover any color to preview the class information.</p>
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
                <span className="legend-text">
                  <strong>{item.quantity}</strong> - {item.label}
                </span>
              </button>
            ))}
          </div>
        </div>
      </>
    )
  }

  return (
    <div className="app-root">
      <div id="map" className="map-container" />
      {uiRoot ? createPortal(panels(), uiRoot) : panels()}
      {uiRoot ? createPortal(<IdeologyPanel />, uiRoot) : <IdeologyPanel />}

      {uiRoot && hoverLegend
        ? createPortal(
            <div className="legend-popup" style={{ left: hoverLegend.x, top: hoverLegend.y }}>
              <div className="popup-swatch" style={{ backgroundColor: hoverLegend.item.color }} />
              <div className="popup-body">
                <div className="popup-title">Class {hoverLegend.item.quantity}</div>
                <div className="popup-label">{hoverLegend.item.label}</div>
              </div>
            </div>,
            uiRoot,
          )
        : null}
    </div>
  )
}
