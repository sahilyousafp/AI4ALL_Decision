# ✅ Ideology Assessment Agent - Implementation Complete

## Summary

I've created a comprehensive Ollama-powered ideology questionnaire agent integrated into your STAC viewer. The agent asks **5 questions with 2 options each** to determine a person's stance on environmental wellbeing vs personal comfort (metaphorically: their position on Barcelona airport expansion).

## What's Been Created

### 1. **Core Python Modules**

#### `ideology_agent.py` (7.9 KB)
- Ollama integration for adaptive features
- 5 core ideology questions
- Scoring logic (0-100 scale)
- Adaptive follow-up generation
- Interpretation generation

**Key Methods:**
- `get_adaptive_followup()` - Get AI-generated follow-up questions
- `get_adaptive_options()` - Dynamically refine question options
- `calculate_score()` - Convert responses to 0-100 score
- `get_interpretation()` - Generate contextual meaning

#### `ideology_ui_generator.py` (14.8 KB)
- Complete HTML/CSS/JS for interactive UI
- Fixed bottom-center panel design
- Compass gauge visualization (Canvas-based)
- Tab navigation (Quiz / Results)
- Responsive styling with gradients and animations

**Features:**
- Auto-progressing questions
- Real-time progress bar
- Interactive compass gauge
- Smooth transitions and hover effects

#### `stac_viewer_with_agent.py` (8.5 KB)
- Integration with your existing Folium map
- Combines STAC viewer + ideology agent
- Preserves all original features (side-by-side comparison, legend, opacity slider)
- Optional Ollama integration

### 2. **Documentation**

#### `IDEOLOGY_AGENT_SETUP.md` (7.4 KB)
Complete setup guide covering:
- Feature overview
- Quick start (with and without Ollama)
- How it works (user flow & scoring)
- Customization options
- Troubleshooting
- Privacy considerations

#### `NOTEBOOK_CELL_EXAMPLE.py`
Copy-paste ready code cell for your Jupyter notebook

### 3. **Preview & Testing**

#### `ideology_agent_preview.html` (16.6 KB)
Standalone HTML file to preview the UI without integration. 
**How to use:**
1. Open in browser: `file:///path/to/ideology_agent_preview.html`
2. Click "🎯 Ideology Quiz" (bottom-center)
3. Answer 5 questions
4. View compass gauge result

---

## Key Features

### ✅ Five Ideology Questions

1. **Land-use development priorities**
   - Option A: Economic growth & jobs
   - Option B: Environmental preservation

2. **Climate change lifestyle impact**
   - Option A: Adapt gradually
   - Option B: Make significant daily changes

3. **Urban expansion vs green spaces**
   - Option A: More development = opportunities
   - Option B: Protect ecosystems

4. **Transportation infrastructure**
   - Option A: Build more highways/airports
   - Option B: Invest in public transit

5. **Convenience vs environmental cost**
   - Option A: Convenience is priority
   - Option B: Environmental impact non-negotiable

### ✅ Scoring System

- **Score Range**: 0-100
- **Calculation**: Each "Option B" response = +20 points
- **Left extreme (0-20)**: Strongly comfort/development-focused
- **Balanced (40-60)**: Mixed perspective
- **Right extreme (80-100)**: Strongly environmental

### ✅ Compass Gauge Visualization

- **Canvas-based** rendering
- **Dynamic needle** pointing to score
- **4-way orientation**:
  - Top: COMFORT
  - Bottom: ENVIRONMENT
  - Left: COMFORT
  - Right: ENVIRONMENT
- **Real-time score display**

### ✅ UI Design

- **Bottom-center fixed panel** (90% width, max 600px)
- **Purple gradient** background (customizable)
- **Tab navigation** (Quiz / Results)
- **Auto-progression** after each answer
- **Smooth animations** and transitions
- **Minimizable** to button when closed
- **Responsive** on mobile devices

### ✅ Optional Ollama Integration

When enabled:
- **Adaptive follow-ups** based on responses
- **Contextual interpretation** of final score
- **Dynamic option phrasing** for questions
- **Requires**: Ollama running locally (`http://localhost:11434`)

---

## How to Use

### Quick Start (No Ollama)

Add this cell to your Jupyter notebook **after your existing STAC cells**:

```python
from stac_viewer_with_agent import create_stac_viewer_with_agent
from IPython.display import IFrame, display

output_path = create_stac_viewer_with_agent(
    items_by_year=items_by_year,
    year_left=1985,
    year_right=2022,
    output_html="stac_viewer_with_agent.html",
    enable_ollama=False
)

display(IFrame(src=output_path.as_uri(), width="100%", height=700))
```

### With Ollama (Advanced)

1. **Install Ollama**: https://ollama.ai
2. **Start Ollama**: `ollama serve`
3. **Pull model**: `ollama pull llama2`
4. **Enable in notebook**:

```python
output_path = create_stac_viewer_with_agent(
    items_by_year=items_by_year,
    year_left=1985,
    year_right=2022,
    output_html="stac_viewer_with_agent.html",
    enable_ollama=True  # <- Change to True
)
```

### Preview the UI

Open `ideology_agent_preview.html` in your browser to test the interface:
```bash
# Windows
start ideology_agent_preview.html

# Mac
open ideology_agent_preview.html

# Linux
xdg-open ideology_agent_preview.html
```

---

## File Locations

```
AI4ALL_Participatory motivation/
├── ideology_agent.py                      (NEW)
├── ideology_ui_generator.py              (NEW)
├── stac_viewer_with_agent.py             (NEW)
├── IDEOLOGY_AGENT_SETUP.md               (NEW) - Full documentation
├── NOTEBOOK_CELL_EXAMPLE.py              (NEW) - Copy-paste for notebook
├── ideology_agent_preview.html           (NEW) - Standalone preview
├── lc_glc.fcs30d.ipynb                   (EXISTING)
├── lc_glc.fcs30d.html                    (EXISTING)
└── ... other files
```

---

## Customization

### Change Questions

Edit `ideology_agent.py`, the `self.base_questions` list:

```python
self.base_questions = [
    {
        "id": 1,
        "text": "Your custom question?",
        "options": [
            "Comfort/development-focused option",
            "Environmental-focused option"
        ]
    },
    # ... 5 total questions
]
```

### Change Colors

In `ideology_ui_generator.py`:

```html
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
<!-- Change hex codes #667eea and #764ba2 -->
```

### Change Scoring

In `ideology_agent.py`, modify `calculate_score()`:

```python
environment_score = sum(responses) * 20  # Change 20 to scale differently
```

### Change Map Location

In `stac_viewer_with_agent.py`:

```python
map_center=(41.2974, 2.0833),  # latitude, longitude
zoom_start=12,                  # initial zoom level
```

---

## What's Preserved

✅ **All original features maintained:**
- Side-by-side layer comparison (1985 vs 2022)
- Year labels (top-left and top-right)
- Legend with land cover categories
- Opacity slider for data layers
- High-zoom support (up to level 24)
- TiTiler integration with custom colormaps
- SLD-based color extraction

✅ **No breaking changes** to existing workflow

---

## Data Privacy

- ✅ **Client-side quiz** - responses stored only in browser memory
- ✅ **No data transmission** by default
- ✅ **If Ollama enabled** - queries go to your local machine (`http://localhost:11434`)
- ✅ **No external API calls** (TiTiler tiles are cached)
- ✅ **No analytics or tracking**

---

## Next Steps

1. **Test the preview**: Open `ideology_agent_preview.html` in browser
2. **Copy notebook cell**: Add code from `NOTEBOOK_CELL_EXAMPLE.py` to your notebook
3. **Run your notebook**: Execute with `enable_ollama=False` first
4. **Optional: Install Ollama**: For adaptive follow-ups and interpretations
5. **Customize as needed**: See IDEOLOGY_AGENT_SETUP.md

---

## Troubleshooting

**Q: Map doesn't load**
- Check browser console (F12) for errors
- Verify TiTiler is reachable: https://titiler.xyz
- Ensure STAC items are valid

**Q: Agent UI doesn't appear**
- Clear browser cache and reload
- Check that `enable_ollama=False` if Ollama isn't installed
- Verify `ideology_ui_generator.py` is imported correctly

**Q: Ollama connection fails**
- Start Ollama: `ollama serve`
- Verify running: `curl http://localhost:11434/api/tags`
- Or set `enable_ollama=False` to skip Ollama

**Q: Slow responses with Ollama**
- Use faster model: `ollama pull mistral`
- Reduce temperature in `ideology_agent.py`
- Increase timeout value

---

## Version Info

- **Version**: 1.0
- **Created**: 2026-05-12
- **Python**: 3.8+
- **Dependencies**: folium, requests, pystac-client, pystac
- **Optional**: Ollama (for adaptive features)

---

## Files Summary

| File | Size | Purpose |
|------|------|---------|
| `ideology_agent.py` | 7.9 KB | Core Ollama integration & scoring |
| `ideology_ui_generator.py` | 14.8 KB | Interactive HTML/CSS/JS interface |
| `stac_viewer_with_agent.py` | 8.5 KB | Folium map integration |
| `IDEOLOGY_AGENT_SETUP.md` | 7.4 KB | Comprehensive setup guide |
| `NOTEBOOK_CELL_EXAMPLE.py` | <1 KB | Copy-paste notebook cell |
| `ideology_agent_preview.html` | 16.6 KB | Standalone preview |

**Total new files**: 6
**Total new code**: ~50 KB

---

**Ready to integrate!** 🚀

Start with the preview HTML, then add the notebook cell. Full documentation in `IDEOLOGY_AGENT_SETUP.md`.
