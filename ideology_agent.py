"""
Ideology Assessment Agent
Ollama-powered questionnaire for environmental vs personal comfort stance
"""

import json
import requests
from typing import Dict, List, Tuple


class IdeologyAgent:
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_base_url
        self.model = "llama2"  # or whatever model you prefer
        self.base_questions = [
            {
                "id": 1,
                "text": "When considering land-use development projects (like airport expansion), what matters most?",
                "options": [
                    "Economic growth and job creation",
                    "Environmental preservation and biodiversity"
                ]
            },
            {
                "id": 2,
                "text": "How do you view climate change impact on your lifestyle?",
                "options": [
                    "I'll adapt my habits gradually when necessary",
                    "I make significant daily changes to reduce my carbon footprint"
                ]
            },
            {
                "id": 3,
                "text": "Urban expansion vs green spaces—your preference?",
                "options": [
                    "More development = more opportunities and convenience",
                    "Protect existing ecosystems and natural areas"
                ]
            },
            {
                "id": 4,
                "text": "What's your stance on transportation infrastructure?",
                "options": [
                    "Build more highways and airports for faster travel",
                    "Invest in public transit and reduce mobility-related emissions"
                ]
            },
            {
                "id": 5,
                "text": "How do you balance personal convenience with environmental cost?",
                "options": [
                    "Convenience and comfort are priorities; trade-offs are worth it",
                    "Environmental impact is non-negotiable; I adjust for sustainability"
                ]
            }
        ]
    
    def get_adaptive_followup(self, question_id: int, user_response: str) -> str:
        """Get an adaptive follow-up question/comment from Ollama"""
        prompt = f"""You are an environmental scientist discussing ideology about land use and urban expansion.
        
The user answered question {question_id}: "{self.base_questions[question_id-1]['text']}"
Their answer: "{user_response}"

Provide a brief (1-2 sentence) insightful follow-up comment or question that probes deeper into their environmental vs comfort stance. Be conversational and non-judgmental."""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Ollama error: {e}")
            return ""
    
    def get_adaptive_options(self, question_id: int) -> Tuple[str, str]:
        """Get adaptive option phrasing based on Ollama"""
        base_opts = self.base_questions[question_id - 1]["options"]
        prompt = f"""You are a questionnaire designer focused on environmental ideology assessment.

Question: "{self.base_questions[question_id-1]['text']}"

Base options:
- Option A: {base_opts[0]}
- Option B: {base_opts[1]}

Refine these options to be more specific and compelling for a Barcelona airport expansion context. Keep them concise (under 15 words each).
Return ONLY two JSON lines, one per option, format: {{"option": "A", "text": "..."}} and {{"option": "B", "text": "..."}}"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.6
                },
                timeout=30
            )
            response.raise_for_status()
            text = response.json().get("response", "").strip()
            
            # Try to parse adaptive options
            lines = text.split('\n')
            options = [base_opts[0], base_opts[1]]
            for line in lines:
                try:
                    data = json.loads(line)
                    idx = 0 if data.get("option") == "A" else 1
                    options[idx] = data.get("text", options[idx])
                except:
                    pass
            return options[0], options[1]
        except Exception as e:
            print(f"Ollama error: {e}")
            return base_opts[0], base_opts[1]
    
    def calculate_score(self, responses: List[int]) -> Dict:
        """
        Calculate ideology score based on responses.
        responses: List of 0s (option A) and 1s (option B)
        Score: 0-100, where 0=comfort/development, 100=environmental
        """
        if not responses or len(responses) != 5:
            return {"score": 50, "lean": "balanced"}
        
        environment_score = sum(responses) * 20  # Each "B" (1) = environmental choice
        
        if environment_score >= 80:
            lean = "strongly environmental"
        elif environment_score >= 60:
            lean = "environmental"
        elif environment_score >= 40:
            lean = "balanced"
        elif environment_score >= 20:
            lean = "comfort-focused"
        else:
            lean = "strongly comfort-focused"
        
        return {
            "score": environment_score,
            "lean": lean,
            "label_left": "Personal Comfort",
            "label_right": "Environmental Wellbeing",
            "responses": responses
        }
    
    def get_interpretation(self, score_data: Dict) -> str:
        """Get Ollama-generated interpretation of the score"""
        score = score_data["score"]
        prompt = f"""You are an environmental policy analyst discussing the Barcelona airport expansion.

A person scored {score}/100 on an environmental vs personal comfort stance questionnaire (0=comfort, 100=environmental).
Their lean: {score_data['lean']}

Write a brief (2-3 sentences) interpretation of what this score means for their likely position on expanding Barcelona's airport. 
Reference the trade-off between economic growth/convenience and environmental impact."""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Ollama error: {e}")
            return f"Your score reflects a {score_data['lean']} stance on environmental policy."
    
    def export_questionnaire_json(self) -> str:
        """Export questions in JSON format for frontend"""
        return json.dumps({
            "questions": self.base_questions,
            "scoring": {
                "min": 0,
                "max": 100,
                "left_label": "Personal Comfort",
                "right_label": "Environmental Wellbeing"
            }
        }, indent=2)
