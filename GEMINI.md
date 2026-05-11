# AI4ALL Participatory Motivation: STAC Viewer

This project provides an interactive SpatioTemporal Asset Catalog (STAC) viewer for Global Land Cover data (GLC_FCS30D), allowing for detailed spatial analysis and historical comparison of land cover changes.

## Project Overview

The core of the project is a Jupyter Notebook (`Stac_viewer.ipynb`) that fetches, styles, and visualizes Cloud Optimized GeoTIFFs (COGs) from OpenLandMap. It uses **TiTiler** as a dynamic tile server to apply custom colormaps in real-time.

### Main Technologies
- **Python / Jupyter**: For analysis and visualization logic.
- **Folium / Leaflet**: For the interactive web map interface.
- **TiTiler**: For on-the-fly rendering of COG assets with custom colormaps.
- **STAC API**: To discover and retrieve yearly land cover data.
- **Styled Layer Descriptor (SLD)**: For extracting legend categories and HEX colors.

### Key Features
- **Historical Comparison**: A side-by-side comparison slider between 1985 and 2022 land cover data.
- **Custom Colormaps**: Dynamic colormap generation from remote SLD files, ensuring the map aligns with the scientific legend.
- **Advanced Controls**: Interactive opacity slider for data layers and high-zoom support (up to level 24).
- **Rich UI**: Floating year labels, high-contrast dark base maps (or standard OSM), and scrollable legends.

## Building and Running

### Prerequisites
Ensure you have a Python environment (a `.venv` is present in the project) with the following dependencies installed:

```bash
pip install folium requests ipython pystac-client pystac
```

### Usage
1. Open the `Stac_viewer.ipynb` notebook.
2. Execute the cells in order.
3. The first cell fetches the collection metadata.
4. The second cell generates the interactive map and saves it to `stac_viewer_map.html`.
5. The map will be displayed inline via an IFrame.

## Development Conventions

- **TiTiler Integration**: Always use the `colormap` parameter in TiTiler URLs to ensure categorical land cover data is rendered with the correct colors.
- **Folium Layer IDs**: When adding custom JavaScript controls (like the opacity slider), target layers by their Folium-generated `get_name()` to ensure they are found in the Leaflet global scope.
- **Zoom Levels**: Standard base maps often cap at zoom 18-20. To support high-resolution analysis, `folium.TileLayer` is configured with `max_zoom=24`.
