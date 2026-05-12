STAC Viewer — Local Dev & Build

Backend (FastAPI)

1. Create virtual env and install:

   python -m venv .venv
   .venv\Scripts\activate
   pip install -r backend\requirements.txt

2. Run backend:

   python backend\server.py

The backend serves /datasets and will serve production frontend files from frontend/public when present.

Frontend (Dev with Vite)

1. Install deps and run dev server:

   cd frontend
   npm install
   npm run dev

2. Vite dev server proxies /datasets to the backend (see frontend/vite.config.ts). Ensure backend is running on http://localhost:8000.

Build & Serve Production

1. Build frontend and copy build artifacts to frontend/public (so backend can serve static files):

   python scripts\build_frontend.py

2. Run backend and open http://localhost:8000

Notes

- The app uses Leaflet and the leaflet-side-by-side plugin (loaded via CDN). A small compatibility shim is injected in the frontend index.html to support Leaflet 1.9+.
- Colors and colormaps come from the tile URLs and are preserved exactly.
