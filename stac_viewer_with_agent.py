"""
Enhanced STAC Viewer with Ideology Agent Integration
Run this after the main STAC viewer to generate HTML with embedded agent
"""

import json
from pathlib import Path
from urllib.parse import quote_plus, urljoin
from xml.etree import ElementTree as ET
import re
import time

import requests
import folium
from folium.plugins import SideBySideLayers
from IPython.display import IFrame, display

# Import the ideology agent and UI generator
from ideology_ui_generator import generate_ideology_ui_html
from ideology_agent import IdeologyAgent


def create_stac_viewer_with_agent(
    items_by_year: dict,
    year_left: int = 1985,
    year_right: int = 2022,
    output_html: str = "stac_viewer_with_agent.html",
    map_center: tuple = (41.2974, 2.0833),
    zoom_start: int = 12,
    enable_ollama: bool = False
):
    """
    Create STAC viewer map with embedded ideology agent
    
    Args:
        items_by_year: Dictionary of STAC items by year
        year_left: Left side comparison year
        year_right: Right side comparison year
        output_html: Output HTML filename
        map_center: Map center coordinates (lat, lon)
        zoom_start: Initial zoom level
        enable_ollama: Whether to enable Ollama for adaptive features
    """
    
    # Initialize ideology agent (optional Ollama integration)
    agent = IdeologyAgent() if enable_ollama else None
    
    def get_tile_url(year):
        """Fetch tile URL and legend from STAC item"""
        if year not in items_by_year:
            return None, None
        item = items_by_year[year]
        preferred = "lc_glc.fcs30d_c_30m_s"
        asset_href = item["assets"].get(preferred, {}).get("href")
        if not asset_href:
            asset_href = next(iter(item["assets"].values()))["href"]
        
        style_href = item["assets"].get("sld", {}).get("href")
        colormap_dict = {}
        legend_entries = []
        
        if style_href:
            try:
                style_xml = requests.get(style_href, timeout=60).text
                style_root = ET.fromstring(style_xml)
                namespace = {"sld": "http://www.opengis.net/sld"}
                for entry in style_root.findall(".//sld:ColorMapEntry", namespace):
                    quantity = entry.attrib.get("quantity")
                    label = entry.attrib.get("label") or quantity
                    color = entry.attrib.get("color")
                    if color:
                        if quantity:
                            colormap_dict[quantity] = color
                        if label:
                            legend_entries.append((label, color))
            except Exception as e:
                print(f"Warning: Could not fetch SLD: {e}")
        
        base_url = "https://titiler.xyz/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png?url=" + quote_plus(asset_href)
        if colormap_dict:
            base_url += f"&colormap={quote_plus(json.dumps(colormap_dict))}"
        
        return base_url, legend_entries
    
    # Get tile URLs
    url_left, legend_left = get_tile_url(year_left)
    url_right, legend_right = get_tile_url(year_right)
    
    if not url_left or not url_right:
        raise ValueError(f"Missing data for {year_left} or {year_right}")
    
    # Create Folium map
    m = folium.Map(
        location=map_center,
        zoom_start=zoom_start,
        tiles="OpenStreetMap",
        control_scale=True
    )
    
    # Add tile layers
    layer_left = folium.TileLayer(
        tiles=url_left,
        name=f"GLC_FCS30D {year_left}",
        attr="OpenLandMap",
        overlay=True,
        max_zoom=24,
    ).add_to(m)
    
    layer_right = folium.TileLayer(
        tiles=url_right,
        name=f"GLC_FCS30D {year_right}",
        attr="OpenLandMap",
        overlay=True,
        max_zoom=24,
    ).add_to(m)
    
    # Add side-by-side comparison
    SideBySideLayers(layer_left, layer_right).add_to(m)
    
    # Build legend HTML
    from html import escape
    legend_items = "\n".join(
        f"<div style='display:flex; align-items:center; gap:8px; margin:4px 0;'>"
        f"<span style='width:14px; height:14px; background:{color}; border:1px solid #666; display:inline-block;'></span>"
        f"<span style='font-size:12px; line-height:1.2;'>{escape(label)}</span></div>"
        for label, color in legend_left
    )
    
    left_id = layer_left.get_name()
    right_id = layer_right.get_name()
    
    # Top labels
    top_labels_html = f'''
    <div style="position: fixed; top: 20px; left: 60px; z-index: 9999; background: rgba(255,255,255,0.9); padding: 8px 16px; border: 2px solid #333; border-radius: 6px; font-weight: 800; font-family: sans-serif; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">{year_left}</div>
    <div style="position: fixed; top: 20px; right: 20px; z-index: 9999; background: rgba(255,255,255,0.9); padding: 8px 16px; border: 2px solid #333; border-radius: 6px; font-weight: 800; font-family: sans-serif; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">{year_right}</div>
    '''
    
    # Legend
    legend_html = f'''
    <div style="position: fixed; bottom: 120px; left: 20px; z-index: 9998; background: rgba(255,255,255,0.95); padding: 12px 14px; border: 1px solid #999; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.15); font-family: sans-serif; max-width: 320px;">
        <div style="font-weight: 700; margin-bottom: 8px;">GLC_FCS30D Legend ({year_left} vs {year_right})</div>
        
        <div style="margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee;">
            <div style="font-size: 11px; font-weight: bold; margin-bottom: 5px; color: #333;">Render Opacity: <span id="opacity-val">1.0</span></div>
            <input id="opacity-slider" type="range" min="0" max="1" step="0.05" value="1" style="width: 100%; cursor: pointer;">
        </div>

        <div style="max-height: 250px; overflow-y: auto; padding-right: 4px;">
            {legend_items}
        </div>
    </div>
    '''
    
    # Opacity control script
    opacity_script = f'''
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            var slider = document.getElementById("opacity-slider");
            var label = document.getElementById("opacity-val");
            var renderLayers = ["{left_id}", "{right_id}"];
            
            function updateOpacity(val) {{
                label.innerText = parseFloat(val).toFixed(2);
                renderLayers.forEach(function(id) {{
                    if (window[id] && typeof window[id].setOpacity === "function") {{
                        window[id].setOpacity(val);
                    }}
                }});
            }}
            
            if (slider) {{
                slider.addEventListener("input", function() {{
                    updateOpacity(this.value);
                }});
            }}
        }});
    </script>
    '''
    
    # Add all HTML to map
    m.get_root().html.add_child(folium.Element(
        top_labels_html + legend_html + opacity_script
    ))
    
    # Add ideology agent UI
    ideology_ui = generate_ideology_ui_html()
    m.get_root().html.add_child(folium.Element(ideology_ui))
    
    # Save map
    map_path = Path(output_html).resolve()
    m.save(str(map_path))
    
    print(f"✅ Map saved to: {map_path}")
    print(f"   Features:")
    print(f"   - Side-by-side comparison: {year_left} vs {year_right}")
    print(f"   - Opacity control")
    print(f"   - Ideology assessment agent (bottom-center)")
    print(f"   - Compass gauge visualization for results")
    
    if enable_ollama:
        print(f"   - Ollama integration: ENABLED (ensure Ollama is running on http://localhost:11434)")
    
    return map_path


# Example usage (uncomment when running in notebook)
"""
# After running the previous STAC cells:
output_path = create_stac_viewer_with_agent(
    items_by_year=items_by_year,
    year_left=1985,
    year_right=2022,
    output_html="stac_viewer_with_agent.html",
    map_center=(41.2974, 2.0833),  # Barcelona
    enable_ollama=False  # Set to True if Ollama is running
)

# Display in notebook
display(IFrame(src=output_path.as_uri(), width="100%", height=700))
"""
