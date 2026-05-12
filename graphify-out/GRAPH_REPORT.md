# Graph Report - .  (2026-05-12)

## Corpus Check
- Corpus is ~1,363 words - fits in a single context window. You may not need a graph.

## Summary
- 25 nodes · 30 edges · 5 communities detected
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Legend and Color System|Legend and Color System]]
- [[_COMMUNITY_Notebook and Data Stack|Notebook and Data Stack]]
- [[_COMMUNITY_Layer Comparison Controls|Layer Comparison Controls]]
- [[_COMMUNITY_Advanced Map Controls|Advanced Map Controls]]
- [[_COMMUNITY_Viewer Overview|Viewer Overview]]

## God Nodes (most connected - your core abstractions)
1. `Stac_viewer.ipynb` - 7 edges
2. `TiTiler` - 4 edges
3. `1985 TiTiler layer` - 4 edges
4. `2022 TiTiler layer` - 4 edges
5. `Interactive STAC viewer` - 3 edges
6. `Styled Layer Descriptor (SLD)` - 3 edges
7. `Custom colormaps` - 3 edges
8. `Advanced controls` - 3 edges
9. `Rich UI` - 3 edges
10. `Opacity slider` - 3 edges

## Surprising Connections (you probably didn't know these)
- `GLC_FCS30D legend` --references--> `GLC_FCS30D land cover data`  [INFERRED]
  lc_glc.fcs30d.html → GEMINI.md
- `GLC_FCS30D legend` --references--> `Styled Layer Descriptor (SLD)`  [INFERRED]
  lc_glc.fcs30d.html → GEMINI.md
- `Historical comparison` --references--> `Side-by-side control`  [EXTRACTED]
  GEMINI.md → lc_glc.fcs30d.html
- `Advanced controls` --references--> `Opacity slider`  [EXTRACTED]
  GEMINI.md → lc_glc.fcs30d.html
- `1985 TiTiler layer` --references--> `TiTiler`  [EXTRACTED]
  lc_glc.fcs30d.html → GEMINI.md

## Hyperedges (group relationships)
- **Side-by-side land cover comparison** — gemini_historical_comparison, html_side_by_side_control, html_1985_tile_layer, html_2022_tile_layer [INFERRED 0.91]

## Communities

### Community 0 - "Legend and Color System"
Cohesion: 0.29
Nodes (7): Custom colormaps, Rich UI, Styled Layer Descriptor (SLD), Use TiTiler colormap parameter for categorical colors, 1985 label, 2022 label, GLC_FCS30D legend

### Community 1 - "Notebook and Data Stack"
Cohesion: 0.33
Nodes (6): Folium / Leaflet, OpenLandMap COGs, Python / Jupyter, STAC API, Stac_viewer.ipynb, OpenStreetMap base layer

### Community 2 - "Layer Comparison Controls"
Cohesion: 0.7
Nodes (5): TiTiler, 1985 TiTiler layer, 2022 TiTiler layer, Opacity slider, Side-by-side control

### Community 3 - "Advanced Map Controls"
Cohesion: 0.5
Nodes (4): Advanced controls, Target Folium-generated layer IDs in custom JS, High zoom support, Set folium.TileLayer max_zoom to 24

### Community 4 - "Viewer Overview"
Cohesion: 0.67
Nodes (3): GLC_FCS30D land cover data, Historical comparison, Interactive STAC viewer

## Knowledge Gaps
- **9 isolated node(s):** `OpenLandMap COGs`, `Python / Jupyter`, `STAC API`, `Use TiTiler colormap parameter for categorical colors`, `Target Folium-generated layer IDs in custom JS` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Stac_viewer.ipynb` connect `Notebook and Data Stack` to `Legend and Color System`, `Layer Comparison Controls`, `Viewer Overview`?**
  _High betweenness centrality (0.503) - this node is a cross-community bridge._
- **Why does `TiTiler` connect `Layer Comparison Controls` to `Legend and Color System`, `Notebook and Data Stack`?**
  _High betweenness centrality (0.411) - this node is a cross-community bridge._
- **Why does `Opacity slider` connect `Layer Comparison Controls` to `Advanced Map Controls`?**
  _High betweenness centrality (0.290) - this node is a cross-community bridge._
- **What connects `OpenLandMap COGs`, `Python / Jupyter`, `STAC API` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._