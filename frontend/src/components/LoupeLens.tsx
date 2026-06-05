import { useEffect, useRef, useState } from 'react'

/**
 * LoupeLens — a draggable cinematic magnifier for Story mode.
 *
 * The user drags a circular glass across the real map; inside the glass the
 * Higgsfield/Seedance delta→airport clip plays on a loop, graded to match the
 * map's warm→cold morph. It's an honest "ghost of the wetland" peek — framed and
 * labelled as an artist's impression, never pretending to be the literal ground —
 * sitting beside the real geo-morph + the real measured loss figure.
 *
 * The clip plays independently (not pixel-locked to the terrain), which both reads
 * as a cinematic loupe and avoids the jank of masking video to a panning map.
 */

const VIDEO = '/assets/decay/delta_morph_geo.mp4'
const LENS = 264 // diameter px

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v))
const fmt = (n: number) => Math.round(n).toLocaleString('en-US')

type Props = { active: boolean }

export default function LoupeLens({ active }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const dragging = useRef(false)
  const offset = useRef({ x: 0, y: 0 })
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null)
  const [ha, setHa] = useState<number | null>(null)
  const [hint, setHint] = useState(true)

  useEffect(() => {
    fetch('/api/change')
      .then((r) => r.json())
      .then((d) => setHa(d?.detail ? null : d.hectares_lost))
      .catch(() => setHa(null))
  }, [])

  // Drop the lens just below the airport when Story mode opens.
  useEffect(() => {
    if (active) {
      setPos({ x: window.innerWidth * 0.5, y: window.innerHeight * 0.54 })
      setHint(true)
    } else {
      dragging.current = false
    }
  }, [active])

  // Drag handling (screen-space; the lens floats over the map).
  useEffect(() => {
    if (!active) return
    const onMove = (e: PointerEvent) => {
      if (!dragging.current) return
      setPos({
        x: clamp(e.clientX - offset.current.x, LENS / 2, window.innerWidth - LENS / 2),
        y: clamp(e.clientY - offset.current.y, LENS / 2, window.innerHeight - LENS / 2),
      })
    }
    const onUp = () => (dragging.current = false)
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [active])

  // Match the lens grade to the morph slider (warm 1956 → cold 2015). Cheap rAF,
  // only touches a CSS filter string.
  useEffect(() => {
    if (!active) return
    let raf = 0
    const tick = () => {
      const r = document.querySelector<HTMLInputElement>('.cine-range')
      let frac = 0
      if (r) {
        const min = Number(r.min || 0)
        const max = Number(r.max || 1000)
        frac = (Number(r.value) - min) / (max - min || 1)
      }
      const v = videoRef.current
      if (v) {
        const sepia = (0.4 * (1 - frac)).toFixed(3)
        const sat = (1 - 0.5 * frac).toFixed(3)
        const bri = (1.02 - 0.14 * frac).toFixed(3)
        const con = (1 + 0.12 * frac).toFixed(3)
        v.style.filter = `sepia(${sepia}) saturate(${sat}) brightness(${bri}) contrast(${con})`
      }
      raf = window.requestAnimationFrame(tick)
    }
    raf = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(raf)
  }, [active])

  if (!active || !pos) return null

  const onPointerDown = (e: React.PointerEvent) => {
    dragging.current = true
    offset.current = { x: e.clientX - pos.x, y: e.clientY - pos.y }
    setHint(false)
  }

  return (
    <div className="loupe-root">
      <div
        className="loupe"
        style={{ left: pos.x, top: pos.y, width: LENS, height: LENS }}
        onPointerDown={onPointerDown}
      >
        <video ref={videoRef} className="loupe-video" src={VIDEO} autoPlay loop muted playsInline />
        <div className="loupe-glass" />
        <div className="loupe-label">
          Artist's impression{ha ? ` · ~${fmt(ha)} ha lost here` : ''}
        </div>
      </div>
      {hint ? (
        <div className="loupe-hint" style={{ left: pos.x, top: pos.y + LENS / 2 + 16 }}>
          ⟵ drag the lens across the airport ⟶
        </div>
      ) : null}
    </div>
  )
}
