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

  useEffect(() => {
    fetch('/api/ideology/questions')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load questions')
        return res.json()
      })
      .then((data: IdeologyQuestion[]) => {
        setQuestions(data)
        setLoading(false)
      })
      .catch((e: Error) => {
        setError(e.message)
        setLoading(false)
      })
  }, [])

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
      <div className="ideology-panel">
        <div className="ideology-content">
          <p className="ideology-text">Loading questionnaire...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="ideology-panel">
        <div className="ideology-content">
          <p className="ideology-text">Error: {error}</p>
        </div>
      </div>
    )
  }

  if (questions.length === 0) {
    return null
  }

  return (<>

    <div className="ideology-panel">
      {!showResults ? (
        <div className="ideology-content">
          <div className="ideology-progress">
            <div className="ideology-progress-bar" style={{ width: `${((currentQuestion) / questions.length) * 100}%` }} />
          </div>
          
          <div className="ideology-question-item">
            <div className="ideology-question-number">
              Question {currentQuestion + 1} of {questions.length}
            </div>
            <h3 className="ideology-question-text">
              {questions[currentQuestion]?.text}
            </h3>
            
            <div className="ideology-options">
              {questions[currentQuestion]?.options.map((option, idx) => (
                <button
                  key={idx}
                  className={`ideology-option ${responses[currentQuestion] === idx ? 'selected' : ''}`}
                  onClick={() => handleSelectOption(idx)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="ideology-content">
          <div className="ideology-results-header">
            <h3 className="ideology-results-title">Your Score</h3>
          </div>
          
          <div className="ideology-results-container">
            <div className="ideology-gauge-container">
              <canvas ref={canvasRef} width={280} height={280} className="ideology-gauge-canvas" />
            </div>
          </div>
          

          
          {interpretation && (
            <div className="ideology-interpretation">
              <p>{interpretation.interpretation}</p>
            </div>
          )}
          
          <button className="ideology-retake-btn" onClick={resetQuiz}>
            Retake Quiz
          </button>
        </div>
      )}
    </div>
    {showResults && radarScores && (
      <div className="panel ideology-score-floating">
        <div className="ideology-score-panel">
          <div className="score-item environment">
            <span className="score-label">Environment</span>
            <span className="score-value">{radarScores.environment}</span>
          </div>
          <div className="score-item comfort">
            <span className="score-label">Comfort</span>
            <span className="score-value">{radarScores.comfort}</span>
          </div>
          <div className="score-item economic">
            <span className="score-label">Economic</span>
            <span className="score-value">{radarScores.economic}</span>
          </div>
          <div className="score-item social">
            <span className="score-label">Social</span>
            <span className="score-value">{radarScores.social}</span>
          </div>
        </div>
      </div>
    )}
  </>)
}

function drawRadarChart(canvas: HTMLCanvasElement, scores: RadarScores) {
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const centerX = 140
  const centerY = 140
  const maxRadius = 70

  // Clear canvas
  ctx.fillStyle = 'transparent'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  // Draw 5 concentric circles (grid)
  ctx.strokeStyle = 'rgba(16, 18, 20, 0.1)'
  ctx.lineWidth = 1
  for (let i = 1; i <= 5; i++) {
    const gridRadius = (i * maxRadius) / 5
    ctx.beginPath()
    ctx.arc(centerX, centerY, gridRadius, 0, Math.PI * 2)
    ctx.stroke()
  }

  // Draw grid numbers
  ctx.fillStyle = 'rgba(16, 18, 20, 0.4)'
  ctx.font = '10px system-ui, -apple-system, sans-serif'
  ctx.textAlign = 'right'
  for (let i = 1; i <= 5; i++) {
    const gridRadius = (i * maxRadius) / 5
    const labelValue = i * 20
    ctx.fillText(String(labelValue), centerX - 8, centerY - gridRadius + 4)
  }

  // Axis data
  const axes = [
    { name: 'Environment', angle: 0 },     // Top
    { name: 'Comfort', angle: 90 },        // Right
    { name: 'Economic', angle: 180 },      // Bottom
    { name: 'Social', angle: 270 },        // Left
  ]

  const scoreValues = [
    scores.environment,
    scores.comfort,
    scores.economic,
    scores.social,
  ]

  // Draw 4 axis lines
  ctx.strokeStyle = 'rgba(16, 18, 20, 0.2)'
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
  ctx.fillStyle = 'rgba(16, 18, 20, 0.6)'
  ctx.font = '11px system-ui, -apple-system, sans-serif'
  axes.forEach((axis, index) => {
    const angle = (axis.angle * Math.PI) / 180
    const labelRadius = maxRadius + 18
    const x = centerX + Math.cos(angle) * labelRadius
    const y = centerY + Math.sin(angle) * labelRadius

    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(axis.name, x, y)
  })

  // Calculate polygon points
  const polygonPoints: Array<{ x: number; y: number }> = []
  scoreValues.forEach((score, index) => {
    const angle = (index * 90 * Math.PI) / 180
    const radius = (score / 100) * maxRadius
    const x = centerX + radius * Math.cos(angle)
    const y = centerY + radius * Math.sin(angle)
    polygonPoints.push({ x, y })
  })

  // Draw filled polygon
  ctx.fillStyle = 'rgba(102, 126, 234, 0.2)'
  ctx.strokeStyle = 'rgba(102, 126, 234, 0.8)'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(polygonPoints[0].x, polygonPoints[0].y)
  for (let i = 1; i < polygonPoints.length; i++) {
    ctx.lineTo(polygonPoints[i].x, polygonPoints[i].y)
  }
  ctx.closePath()
  ctx.fill()
  ctx.stroke()

  // Draw data point circles
  ctx.fillStyle = 'rgba(102, 126, 234, 1)'
  polygonPoints.forEach((point) => {
    ctx.beginPath()
    ctx.arc(point.x, point.y, 5, 0, Math.PI * 2)
    ctx.fill()
  })

  // Draw score labels at each node
  ctx.fillStyle = 'rgba(16, 18, 20, 0.9)'
  ctx.font = 'bold 12px system-ui, -apple-system, sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  scoreValues.forEach((score, index) => {
    const point = polygonPoints[index]
    ctx.fillText(String(Math.round(score)), point.x, point.y)
  })
}
