# COPY THIS CELL INTO YOUR JUPYTER NOTEBOOK AFTER THE STAC VIEWER CELLS

# Cell: Create STAC Viewer with Embedded Ideology Agent

from stac_viewer_with_agent import create_stac_viewer_with_agent
from IPython.display import IFrame, display

# Create the map with embedded ideology agent
# Set enable_ollama=True if you have Ollama running locally
output_path = create_stac_viewer_with_agent(
    items_by_year=items_by_year,      # Use the items_by_year from previous cell
    year_left=1985,
    year_right=2022,
    output_html="stac_viewer_with_agent.html",
    map_center=(41.2974, 2.0833),     # Barcelona coordinates
    zoom_start=12,
    enable_ollama=False                # Set to True if Ollama is running on http://localhost:11434
)

# Display the map in the notebook
display(IFrame(src=output_path.as_uri(), width="100%", height=700))
