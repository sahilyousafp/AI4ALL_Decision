"""
Ideology Agent Service for FastAPI Backend
Manages questionnaire logic, scoring, and optional Ollama integration
"""

from __future__ import annotations

from typing import Any
import requests
from pydantic import BaseModel


class IdeologyQuestion(BaseModel):
    id: int
    text: str
    options: list[str]


class RadarScores(BaseModel):
    environment: int  # 0-100
    comfort: int      # 0-100
    economic: int     # 0-100
    social: int       # 0-100


class ScoringResult(BaseModel):
    radar_scores: RadarScores
    lean: str  # environmental|balanced|comfort
    responses: list[int]  # 0, 1, or 2 for each question


class IdeologyInterpretation(BaseModel):
    radar_scores: RadarScores
    lean: str
    interpretation: str


class IdeologyAgentService:
    """Manages ideology questionnaire logic and Ollama integration"""

    QUESTIONS: list[IdeologyQuestion] = [
        IdeologyQuestion(
            id=1,
            text="When considering land-use development (like airport expansion), what matters most?",
            options=[
                "Economic growth and job creation",
                "Balanced growth with environmental safeguards",
                "Environmental preservation and biodiversity"
            ]
        ),
        IdeologyQuestion(
            id=2,
            text="How do you view climate change impact on your lifestyle?",
            options=[
                "I'll adapt gradually when necessary",
                "I make moderate changes to reduce my impact",
                "I make significant daily changes to reduce emissions"
            ]
        ),
        IdeologyQuestion(
            id=3,
            text="Urban expansion vs green spaces—your preference?",
            options=[
                "More development means more opportunities",
                "Support growth while preserving some ecosystems",
                "Protect existing ecosystems and natural areas"
            ]
        ),
        IdeologyQuestion(
            id=4,
            text="Your stance on transportation infrastructure?",
            options=[
                "Build more highways and airports for connectivity",
                "Mix of new infrastructure with public transit investment",
                "Invest in public transit and reduce emissions"
            ]
        ),
        IdeologyQuestion(
            id=5,
            text="How do you balance convenience with environmental cost?",
            options=[
                "Convenience and comfort are priorities",
                "Balance convenience with reasonable environmental steps",
                "Environmental impact is non-negotiable"
            ]
        ),
    ]

    STATIC_INTERPRETATIONS = {
        "high_environmental": "You strongly prioritize environmental protection. You likely oppose airport expansion due to ecosystem impact and prefer sustainable alternatives.",
        "environmental": "You lean toward environmental considerations. You recognize growth benefits but want strong protections for natural areas and emissions reduction.",
        "balanced": "You balance both perspectives. You see merit in development opportunities and environmental protection, supporting growth with conditions.",
        "comfort": "You prioritize economic growth and convenience. You support airport expansion for jobs and connectivity, with reasonable environmental safeguards.",
        "high_comfort": "You strongly favor development and personal comfort. You see airport expansion as essential for growth and see environmental concerns as secondary.",
    }

    def __init__(self, ollama_base_url: str = "http://localhost:11434", timeout: int = 30):
        """Initialize service with optional Ollama integration"""
        self.ollama_url = ollama_base_url
        self.timeout = timeout

    def get_questions(self) -> list[IdeologyQuestion]:
        """Return all ideology questions"""
        return self.QUESTIONS

    def calculate_score(self, responses: list[int]) -> ScoringResult:
        """
        Calculate ideology scores from responses (0, 1, or 2 for each question)
        
        Scoring logic:
        - Option 0 (comfort/development): +25 comfort, +10 to others
        - Option 1 (neutral/balanced): +15 to all categories
        - Option 2 (environment): +25 environment, +10 to others
        
        Returns RadarScores with 4 independent 0-100 scales
        """
        if not responses or len(responses) != len(self.QUESTIONS):
            raise ValueError(f"Expected {len(self.QUESTIONS)} responses, got {len(responses)}")

        # Validate response values
        for resp in responses:
            if resp not in [0, 1, 2]:
                raise ValueError(f"Response values must be 0, 1, or 2, got {resp}")

        # Initialize category scores
        category_scores = {
            "environment": 0,
            "comfort": 0,
            "economic": 0,
            "social": 0
        }

        # Process each response
        for response in responses:
            if response == 0:  # Comfort/Development focused
                category_scores["comfort"] += 25
                category_scores["economic"] += 10
                category_scores["social"] += 10
                category_scores["environment"] += 5
            elif response == 1:  # Neutral/Balanced
                category_scores["environment"] += 15
                category_scores["comfort"] += 15
                category_scores["economic"] += 15
                category_scores["social"] += 15
            elif response == 2:  # Environment focused
                category_scores["environment"] += 25
                category_scores["economic"] += 10
                category_scores["social"] += 10
                category_scores["comfort"] += 5

        # Normalize to 0-100 scale (5 questions, so max is 125 per category)
        radar_scores = RadarScores(
            environment=min(100, int((category_scores["environment"] / 125) * 100)),
            comfort=min(100, int((category_scores["comfort"] / 125) * 100)),
            economic=min(100, int((category_scores["economic"] / 125) * 100)),
            social=min(100, int((category_scores["social"] / 125) * 100))
        )

        # Determine lean based on primary dimension (environment vs comfort)
        if radar_scores.environment > radar_scores.comfort + 10:
            lean = "environmental"
        elif radar_scores.comfort > radar_scores.environment + 10:
            lean = "comfort"
        else:
            lean = "balanced"

        return ScoringResult(radar_scores=radar_scores, lean=lean, responses=responses)

    def get_static_interpretation(self, radar_scores: RadarScores) -> str:
        """Get static interpretation based on RadarScores"""
        env = radar_scores.environment
        comfort = radar_scores.comfort
        
        if env > comfort + 10:
            if env >= 80:
                return self.STATIC_INTERPRETATIONS["high_environmental"]
            else:
                return self.STATIC_INTERPRETATIONS["environmental"]
        elif comfort > env + 10:
            if comfort >= 80:
                return self.STATIC_INTERPRETATIONS["high_comfort"]
            else:
                return self.STATIC_INTERPRETATIONS["comfort"]
        else:
            return self.STATIC_INTERPRETATIONS["balanced"]

    def get_ollama_interpretation(self, radar_scores: RadarScores, lean: str, responses: list[int]) -> str:
        """Get Ollama-generated interpretation (with fallback to static)"""
        try:
            primary_score = radar_scores.environment if lean == "environmental" else radar_scores.comfort
            prompt = f"""You are an environmental policy analyst discussing Barcelona airport expansion.

A person scored on an ideology questionnaire across 4 dimensions:
- Environment: {radar_scores.environment}/100
- Comfort: {radar_scores.comfort}/100
- Economic: {radar_scores.economic}/100
- Social: {radar_scores.social}/100

Their primary stance: {lean.title()}

Write a brief (2-3 sentences) interpretation of what these scores mean for their likely position on expanding Barcelona's airport. 
Reference the trade-off between economic growth/convenience and environmental impact. Be neutral and insightful."""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            interpretation = response.json().get("response", "").strip()

            if interpretation:
                return interpretation
        except Exception as e:
            print(f"Ollama inference failed: {e}, falling back to static interpretation")

        return self.get_static_interpretation(radar_scores)

    def interpret_score(self, responses: list[int], use_ollama: bool = False) -> IdeologyInterpretation:
        """
        Get interpretation of ideology score
        use_ollama: If True, attempt Ollama generation (fallback to static if fails)
        """
        score_data = self.calculate_score(responses)

        if use_ollama:
            interpretation = self.get_ollama_interpretation(score_data.radar_scores, score_data.lean, responses)
        else:
            interpretation = self.get_static_interpretation(score_data.radar_scores)

        return IdeologyInterpretation(
            radar_scores=score_data.radar_scores,
            lean=score_data.lean,
            interpretation=interpretation
        )


# Global service instance
_service: IdeologyAgentService | None = None


def get_ideology_service() -> IdeologyAgentService:
    """Get or create the ideology agent service"""
    global _service
    if _service is None:
        _service = IdeologyAgentService()
    return _service
