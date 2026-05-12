import { useEffect, useState, useRef } from 'react'

type IdeologyQuestion = {
  id: number
  text: string
  options: string[]
}

type RadarScores = {
  environment: number
  comfort: number
  economic: number
  social: number
}

type ScoringResult = {
  radar_scores: RadarScores
  lean: string
  responses: number[]
}

type IdeologyInterpretation = {
  radar_scores: RadarScores
  lean: string
  interpretation: string
}

const QUESTION_DELAY = 300

export default function IdeologyPanel() {
  const [questions, setQuestions] = useState<IdeologyQuestion[]>([])
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [responses, setResponses] = useState<number[]>([])
  const [showResults, setShowResults] = useState(false)
  const [interpretation, setInterpretation] = useState<IdeologyInterpretation | null>(null)
  const [radarScores, setRadarScores] = useState<RadarScores | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const [userProfile, setUserProfile] = useState<any | null>(null)

  useEffect(() => {
    // Try to fetch a user profile to tailor questions; ignore failures
    (async () => {
      try {
        const pRes = await fetch('/api/user/profile')
        if (pRes.ok) {
          const profile = await pRes.json()
          setUserProfile(profile)
        }
      } catch (e) {
        // no profile available; continue
      }

      try {
        const query = userProfile ? `?profile=${encodeURIComponent(JSON.stringify(userProfile))}` : ''
        const res = await fetch(`/api/ideology/questions${query}`)
        if (!res.ok) throw new Error('Failed to load questions')
        const data: IdeologyQuestion[] = await res.json()

        // If we have a profile, attempt a simple reordering by inferred category
        const reordered = reorderQuestionsByProfile(data, userProfile)
        setQuestions(reordered)
        setLoading(false)
      } catch (e: any) {
        setError(e.message)
        setLoading(false)
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function categorizeQuestion(text: string) {
    const t = text.toLowerCase()
    if (t.includes('environment') || t.includes('climate') || t.includes('nature')) return 'environment'
    if (t.includes('comfort') || t.includes('living') || t.includes('quality')) return 'comfort'
    if (t.includes('economic') || t.includes('jobs') || t.includes('growth')) return 'economic'
    if (t.includes('social') || t.includes('community') || t.includes('equity')) return 'social'
    return 'other'
  }

  function reorderQuestionsByProfile(qs: IdeologyQuestion[], profile: any | null) {
    if (!profile) return qs
    const pref = profile.preferred_category || profile.preference || null
    if (!pref) return qs
    const preferred = String(pref).toLowerCase()

    const matched: IdeologyQuestion[] = []
    const others: IdeologyQuestion[] = []
    for (const q of qs) {
      const cat = categorizeQuestion(q.text)
      if (cat === preferred) matched.push(q)
      else others.push(q)
    }
    return [...matched, ...others]
  }

  const handleSelectOption = (optionIndex: number) => {
    const newResponses = [...responses]
    newResponses[currentQuestion] = optionIndex
    setResponses(newResponses)

    if (currentQuestion < questions.length - 1) {
      setTimeout(() => {
        setCurrentQuestion(currentQuestion + 1)
      }, QUESTION_DELAY)
    } else {
      submitResponses(newResponses)
    }
  }

  const submitResponses = async (finalResponses: number[]) => {
    try {
      const scoreResult: ScoringResult = {
        radar_scores: { environment: 0, comfort: 0, economic: 0, social: 0 },
        lean: '',
        responses: finalResponses
      }

      const interpretResponse = await fetch('/api/ideology/interpret', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scoreResult),
      })

      if (!interpretResponse.ok) throw new Error('Failed to get interpretation')
      const result: IdeologyInterpretation = await interpretResponse.json()
      setInterpretation(result)
      setRadarScores(result.radar_scores)
      setShowResults(true)
    } catch (e: any) {
      setError(e.message)
    }
  }

  const resetQuiz = () => {
    setCurrentQuestion(0)
    setResponses([])
    setShowResults(false)
    setInterpretation(null)
    setRadarScores(null)
  }

  useEffect(() => {
    if (showResults && radarScores && canvasRef.current) {
      drawRadarChart(canvasRef.current, radarScores)
    }
  }, [showResults, radarScores])

  if (loading) {
    return (
      <div className="opinion-panel">
        <div className="opinion-content">
          <p className="opinion-text">Loading questionnaire...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="opinion-panel">
        <div className="opinion-content">
          <p className="opinion-text">Error: {error}</p>
        </div>
      </div>
    )
  }

  if (questions.length === 0) {
    return null
  }

  return (<>

    <div className="opinion-panel">
      {!showResults ? (
        <div className="opinion-content">
          <div className="opinion-progress">
            <div className="opinion-progress-bar" style={{ width: `${((currentQuestion) / questions.length) * 100}%` }} />
          </div>
          
          <div className="opinion-question-item">
            <div className="opinion-question-number">
              Question {currentQuestion + 1} of {questions.length}
            </div>
            <h3 className="opinion-question-text">
              {questions[currentQuestion]?.text}
            </h3>
            
            <div className="opinion-options">
              {questions[currentQuestion]?.options.map((option, idx) => (
                <button
                  key={idx}
                  className={`opinion-option ${responses[currentQuestion] === idx ? 'selected' : ''}`}
                  onClick={() => handleSelectOption(idx)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="opinion-content">
          <div className="opinion-results-header">
            <h3 className="opinion-results-title">Your Score</h3>
          </div>
          
          <div className="opinion-results-container">
            <div className="opinion-gauge-container">
              {/* Chart moved to bottom-left panel */}
            </div>
          </div>
          

          
          {interpretation && (
            <div className="opinion-interpretation final">
              <p>{interpretation.interpretation}</p>
            </div>
          )}
          
          <button className="opinion-retake-btn" onClick={resetQuiz}>
            Retake Quiz
          </button>
        </div>
      )}
    </div>

  {showResults && radarScores && (
    <div className="opinion-chart-panel">
      <canvas ref={canvasRef} width={320} height={320} className="opinion-gauge-canvas" />
    </div>
  )}
  </>)
}

function drawRadarChart(canvas: HTMLCanvasElement, scores: RadarScores) {
  // High-quality rendering using devicePixelRatio scaling
  const dpr = Math.max(1, window.devicePixelRatio || 1)
  const width = canvas.clientWidth || 280
  const height = canvas.clientHeight || 280
  canvas.width = Math.round(width * dpr)
  canvas.height = Math.round(height * dpr)
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`

  const ctx = canvas.getContext('2d')
  if (!ctx) return
  // Reset any transforms then scale for DPR
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, width, height)

  const centerX = width / 2
  const centerY = height / 2
  const maxRadius = Math.min(centerX, centerY) - 36

  // Styling defaults
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'

  // Draw 5 concentric circles (grid)
  ctx.strokeStyle = 'rgba(16, 18, 20, 0.08)'
  ctx.lineWidth = 1
  for (let i = 1; i <= 5; i++) {
    const gridRadius = (i * maxRadius) / 5
    ctx.beginPath()
    ctx.arc(centerX, centerY, gridRadius, 0, Math.PI * 2)
    ctx.stroke()
  }

  // Draw grid numbers (left)
  ctx.fillStyle = 'rgba(16, 18, 20, 0.45)'
  ctx.font = '11px system-ui, -apple-system, sans-serif'
  ctx.textAlign = 'right'
  for (let i = 1; i <= 5; i++) {
    const gridRadius = (i * maxRadius) / 5
    const labelValue = i * 20
    ctx.fillText(String(labelValue), centerX - 10, centerY - gridRadius + 4)
  }

  // Axis data
  const axes = [
    { name: 'Environment', angle: -90 }, // Up
    { name: 'Comfort', angle: 0 },       // Right
    { name: 'Economic', angle: 90 },     // Down
    { name: 'Social', angle: 180 },      // Left
  ]

  const scoreValues = [
    scores.environment,
    scores.comfort,
    scores.economic,
    scores.social,
  ]

  // Draw axis lines
  ctx.strokeStyle = 'rgba(16, 18, 20, 0.14)'
  ctx.lineWidth = 1
  axes.forEach((axis) => {
    const angle = (axis.angle * Math.PI) / 180
    const x = centerX + Math.cos(angle) * maxRadius
    const y = centerY + Math.sin(angle) * maxRadius
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.lineTo(x, y)
    ctx.stroke()
  })

  // Draw axis labels
  ctx.fillStyle = 'rgba(16, 18, 20, 0.75)'
  ctx.font = '12px system-ui, -apple-system, sans-serif'
  axes.forEach((axis) => {
    const angle = (axis.angle * Math.PI) / 180
    const labelRadius = maxRadius + 18
    const x = centerX + Math.cos(angle) * labelRadius
    const y = centerY + Math.sin(angle) * labelRadius

    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    // Draw subtle white background for legibility
    const text = axis.name
    const metrics = ctx.measureText(text)
    const padX = 8
    const padY = 6
    ctx.fillStyle = 'rgba(255,255,255,0.9)'
    ctx.fillRect(x - metrics.width / 2 - padX/2, y - 10, metrics.width + padX, 20)
    ctx.fillStyle = 'rgba(16, 18, 20, 0.85)'
    ctx.fillText(text, x, y)
  })

  // Calculate polygon points
  const polygonPoints: Array<{ x: number; y: number }> = []
  scoreValues.forEach((score, index) => {
    const angle = ((index * 360) / scoreValues.length - 90) * (Math.PI / 180)
    const radius = (score / 100) * maxRadius
    const x = centerX + radius * Math.cos(angle)
    const y = centerY + radius * Math.sin(angle)
    polygonPoints.push({ x, y })
  })

  // Draw filled polygon with subtle shadow
  ctx.save()
  ctx.shadowColor = 'rgba(0,0,0,0.08)'
  ctx.shadowBlur = 12
  ctx.fillStyle = 'rgba(102, 126, 234, 0.16)'
  ctx.strokeStyle = 'rgba(102, 126, 234, 0.95)'
  ctx.lineWidth = 2
  ctx.beginPath()
  polygonPoints.forEach((p, i) => {
    if (i === 0) ctx.moveTo(p.x, p.y)
    else ctx.lineTo(p.x, p.y)
  })
  ctx.closePath()
  ctx.fill()
  ctx.stroke()
  ctx.restore()

  // Draw data point circles with white border
  polygonPoints.forEach((point) => {
    ctx.beginPath()
    ctx.fillStyle = 'rgba(102, 126, 234, 1)'
    ctx.arc(point.x, point.y, 5, 0, Math.PI * 2)
    ctx.fill()
    ctx.lineWidth = 2
    ctx.strokeStyle = '#fff'
    ctx.stroke()
  })

  // Draw score labels beside each node
  ctx.fillStyle = 'rgba(16, 18, 20, 0.95)'
  ctx.font = '600 12px system-ui, -apple-system, sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  scoreValues.forEach((score, index) => {
    const point = polygonPoints[index]
    ctx.fillText(String(Math.round(score)), point.x, point.y - 14)
  })
}
