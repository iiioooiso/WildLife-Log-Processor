import os
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from backend.services import (
    generate_daily_report,
    detect_events,
    analyze_sentiment,
    detect_patterns,
    translate_logs,
    clean_and_detect_anomalies,
    get_log_summary_from_ai
)

OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'static/outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI()

# Mount static directory (serves frontend assets)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routes defined in backend.routes.main_routes
from backend.routes.main_routes import router as main_router

app.include_router(main_router)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.main:app', host='0.0.0.0', port=int(os.getenv('PORT', 7860)), reload=False)
