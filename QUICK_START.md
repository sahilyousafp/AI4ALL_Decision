# Quick Start Guide - Ideology Agent Integration

## 📋 What You Got

6 new files totaling ~50 KB:

1. **ideology_agent.py** - Ollama integration & AI logic
2. **ideology_ui_generator.py** - Interactive UI (HTML/CSS/JS)
3. **stac_viewer_with_agent.py** - Folium map integration
4. **ideology_agent_preview.html** - Standalone preview (test this first!)
5. **IDEOLOGY_AGENT_SETUP.md** - Full documentation
6. **IMPLEMENTATION_SUMMARY.md** - Detailed overview

## ⚡ 30-Second Setup

### Option A: No Ollama (Fastest)

Add this to your Jupyter notebook after the STAC cells:

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

### Option B: With Ollama (Advanced)

1. Install: `ollama pull llama2`
2. Start: `ollama serve`
3. Set: `enable_ollama=True` in the code above

## 🧪 Test First

1. **Open preview**: `ideology_agent_preview.html` in browser
2. **Click "🎯 Ideology Quiz"** (bottom-center)
3. **Answer 5 questions** → see compass gauge result

(This tests the UI without needing the notebook)

## 🎯 What It Does

**5 Questions on Environmental vs Personal Comfort:**
1. Land-use development priorities
2. Climate change lifestyle impact
3. Urban expansion vs green spaces
4. Transportation infrastructure
5. Convenience vs environmental cost

**Outputs:**
- **Score**: 0-100 (0=comfort, 100=environment)
- **Compass Gauge**: Visual needle pointing to stance
- **Interpretation**: What the score means

**Location**: Fixed bottom-center panel on map
**No Data Sent**: Fully client-side (unless Ollama enabled)

## 🔧 Customization

**Change questions?** Edit `ideology_agent.py` line 26+

**Change colors?** Edit `ideology_ui_generator.py` line 12 (the gradient)

**Change scoring?** Edit `ideology_agent.py` line 140

**Change map center?** Edit the `map_center=(41.2974, 2.0833)` parameter

## 📚 Documentation

- **IDEOLOGY_AGENT_SETUP.md** - Complete guide (setup, troubleshooting, API)
- **IMPLEMENTATION_SUMMARY.md** - Technical overview
- **NOTEBOOK_CELL_EXAMPLE.py** - Ready-to-copy code

## ✅ Features

✓ 5 questions with 2 options each
✓ Bottom-center fixed UI (90% width, max 600px)
✓ Compass/gauge visualization (Canvas-based)
✓ Auto-progressing questions (300ms delay)
✓ Minimizable panel
✓ Responsive on mobile
✓ Purple gradient design (customizable)
✓ Optional Ollama for AI features
✓ All original STAC features preserved

## 🚀 Next Steps

1. **Open** `ideology_agent_preview.html` → test the UI
2. **Copy** the code from "Option A" above → paste in notebook
3. **Run** → generates `stac_viewer_with_agent.html`
4. **Optional**: Install Ollama for adaptive features

## 🆘 Issues?

- **Map won't load?** Check browser console (F12), verify TiTiler reachable
- **Agent doesn't appear?** Clear browser cache, reload, set `enable_ollama=False`
- **Ollama connection fails?** Start with `ollama serve`, or set `enable_ollama=False`

---

**Questions?** See `IDEOLOGY_AGENT_SETUP.md` for detailed troubleshooting.

**Ready to go!** 🎉
