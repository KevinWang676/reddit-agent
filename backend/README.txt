
# Backend (FastAPI)

1) Paste your `dashboard_data.json` into: `backend/pipeline_output/`
2) Install & run:
   ```bash
   pip install -r requirements.txt
   uvicorn app:app --reload
   ```
API endpoints:
- GET /metadata
- GET /categories
- GET /insights
- GET /insights/{id}
- GET /posts
