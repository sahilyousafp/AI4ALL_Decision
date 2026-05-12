# Ideology Assessment Agent Integration

This guide explains how to integrate the Ollama-powered ideology assessment agent into your STAC viewer.

## Overview

The ideology agent is a questionnaire that asks 5 questions about environmental vs personal comfort preferences, with 2 options per question. It determines where a person stands on issues like Barcelona airport expansion using:

- **Interactive UI**: Fixed bottom-center panel in the map
- **Compass Gauge**: Visual representation of the score (0-100)
- **Ollama Integration** (optional): Adaptive follow-ups and contextual interpretation

## Features

✅ **5 Core Questions** on ideology regarding:
- Land-use development priorities
- Climate change lifestyle impact
- Urban expansion vs green spaces
- Transportation infrastructure
- Convenience vs environmental cost

✅ **Adaptive Scoring**: Each response scores 0-100
- 0 = Personal Comfort / Economic Growth focused
- 100 = Environmental Wellbeing focused

✅ **Compass Gauge Visualization**: Interactive needle gauge showing where you stand

✅ **Ollama Integration** (optional):
- Adaptive follow-up questions based on responses
- Contextual interpretation of final score
- Dynamic option phrasing

## Quick Start

### 1. Without Ollama (Standalone Mode)

```python
from ideology_ui_generator import generate_ideology_ui_html
from stac_viewer_with_agent import create_stac_viewer_with_agent

# After your existing STAC cells:
output_path = create_stac_viewer_with_agent(
    items_by_year=items_by_year,
    year_left=1985,
    year_right=2022,
    output_html="stac_viewer_with_agent.html",
    enable_ollama=False  # No Ollama needed
)
```

### 2. With Ollama Integration (Recommended)

#### Prerequisites
1. Install Ollama: https://ollama.ai
2. Start Ollama: `ollama serve`
3. Pull a model: `ollama pull llama2` (or another model)

#### Usage
```python
from stac_viewer_with_agent import create_stac_viewer_with_agent

output_path = create_stac_viewer_with_agent(
    items_by_year=items_by_year,
    year_left=1985,
    year_right=2022,
    output_html="stac_viewer_with_agent.html",
    enable_ollama=True  # Requires Ollama running
)
```

## File Structure

```
ideology_agent.py                 # Ollama integration & scoring logic
ideology_ui_generator.py          # HTML/CSS/JS for the interactive UI
stac_viewer_with_agent.py         # Main integration with Folium map
IDEOLOGY_AGENT_SETUP.md          # This file
```

## How It Works

### User Flow

1. **Open Map**: User loads the HTML map with embedded agent
2. **Launch Quiz**: Click "🎯 Ideology Quiz" tab (appears at bottom-center)
3. **Answer Questions**: 5 questions with 2 options each
4. **Auto-progression**: Answer automatically advances to next question
5. **View Results**: Automatically shows compass gauge and interpretation
6. **Retake**: User can restart anytime with "Retake Quiz" button

### Scoring Logic

Each response (0 or 1) contributes 20 points to the final score:

```
Score = sum(responses) * 20
Total Range: 0-100
```

- **0-20**: Strongly comfort/development-focused
- **20-40**: Comfort-focused with some environmental consideration
- **40-60**: Balanced perspective
- **60-80**: Environmental-leaning
- **80-100**: Strongly environmental

### Compass Gauge

The compass gauge visualizes ideology as a needle pointing from:
- **Left (0°)**: Personal Comfort
- **Right (90°)**: Environmental Wellbeing
- **Top (45°)**: Balanced
- **Bottom (225°)**: Extreme positions

## Customization

### Change Questions

Edit `ideology_agent.py`:

```python
self.base_questions = [
    {
        "id": 1,
        "text": "Your custom question here?",
        "options": [
            "Option A (comfort/development)",
            "Option B (environmental)"
        ]
    },
    # ... more questions
]
```

### Change Colors

In `ideology_ui_generator.py`, modify the gradient:

```html
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Change Map Position

In `stac_viewer_with_agent.py`:

```python
output_path = create_stac_viewer_with_agent(
    ...
    map_center=(41.2974, 2.0833),  # Change lat/lon
    zoom_start=12                   # Change zoom
)
```

## Ollama Models

Popular models for this use case:

- `llama2` (default): Fast, good quality
- `mistral`: Faster inference
- `neural-chat`: Optimized for dialogue
- `orca-mini`: Compact

Example:
```bash
ollama pull mistral
```

Then update in `ideology_agent.py`:
```python
self.model = "mistral"
```

## Troubleshooting

### "Cannot connect to Ollama"

```
Error: Failed to connect to http://localhost:11434
```

**Solution:**
- Start Ollama: `ollama serve`
- Verify running: `curl http://localhost:11434/api/tags`
- Set `enable_ollama=False` to skip Ollama features

### Slow responses

- Use a faster model: `mistral` or `neural-chat`
- Reduce temperature in `ideology_agent.py` (lower = faster)
- Increase timeout: Change `timeout=30` to `timeout=60`

### Map doesn't load

- Check browser console (F12)
- Ensure TiTiler is accessible: https://titiler.xyz
- Verify STAC items are valid

## Integration with Your Notebook

Add this cell after your existing STAC visualization:

```python
# Import the enhanced STAC viewer
from stac_viewer_with_agent import create_stac_viewer_with_agent

# Create map with embedded ideology agent
output_path = create_stac_viewer_with_agent(
    items_by_year=items_by_year,  # From your previous cell
    year_left=1985,
    year_right=2022,
    output_html="stac_viewer_with_agent.html",
    enable_ollama=False  # Change to True if Ollama is running
)

# Display in notebook
from IPython.display import IFrame, display
display(IFrame(src=output_path.as_uri(), width="100%", height=700))
```

## Advanced: Ollama API Direct Usage

```python
from ideology_agent import IdeologyAgent

agent = IdeologyAgent(ollama_base_url="http://localhost:11434")

# Get adaptive follow-up
followup = agent.get_adaptive_followup(
    question_id=1,
    user_response="Economic growth is important"
)

# Calculate score
score_data = agent.calculate_score(responses=[0, 1, 1, 0, 1])
print(f"Score: {score_data['score']}/100")
print(f"Lean: {score_data['lean']}")

# Get interpretation
interpretation = agent.get_interpretation(score_data)
print(interpretation)
```

## Data Privacy

- **No data is sent to external servers** by default
- If Ollama is enabled, queries are sent to your local Ollama instance (http://localhost:11434)
- User responses are NOT saved or transmitted anywhere
- Quiz is completely client-side in the HTML

## Future Enhancements

- [ ] Export quiz results as JSON
- [ ] Multi-language support
- [ ] Advanced analytics (heat maps of responses)
- [ ] API integration for large-scale surveys
- [ ] Custom scoring rubrics

## Support

For issues or questions:
1. Check browser console (F12) for JavaScript errors
2. Verify Ollama is running: `ollama serve`
3. Review this documentation
4. Check the code comments in `ideology_agent.py` and `ideology_ui_generator.py`

---

**Version**: 1.0
**Last Updated**: 2026-05-12
**Author**: AI4ALL Participatory Motivation Team
