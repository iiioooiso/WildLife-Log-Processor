import os
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
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

router = APIRouter()

OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'static/outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

templates = Jinja2Templates(directory="backend/templates")
# Disable Jinja2 template caching to avoid hashing issues with request/context objects
try:
    templates.env.cache_size = 0
except Exception:
    # Fallback: clear cache dict if attribute not available
    try:
        templates.env.cache.clear()
    except Exception:
        pass


@router.get('/', response_class=HTMLResponse)
def index(request: Request):
    # Serve the main HTML with static paths injected to avoid Jinja2 templating issues
    tpl_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'index.html')
    tpl_path = os.path.normpath(tpl_path)
    try:
        with open(tpl_path, 'r', encoding='utf-8') as f:
            html = f.read()
        # Replace template calls to request.url_for with direct static paths
        html = html.replace("{{ request.url_for('static', path='css/style.css') }}", "/static/css/style.css")
        html = html.replace("{{ request.url_for('static', path='js/app.js') }}", "/static/js/app.js")
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading index: {e}")


@router.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail='No selected file')
    input_path = os.path.join(OUTPUT_DIR, 'log.txt')
    # clear previous outputs except log.txt
    for f in os.listdir(OUTPUT_DIR):
        if f != 'log.txt':
            try:
                os.remove(os.path.join(OUTPUT_DIR, f))
            except Exception:
                pass

    with open(input_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    return {"status": "ok"}


@router.post('/use_demo')
def use_demo():
    """Load the demo Log.txt from the repo root into the outputs folder as log.txt"""
    repo_log = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'Log.txt'))
    if not os.path.exists(repo_log):
        raise HTTPException(status_code=404, detail='Demo Log.txt not found in repository')

    input_path = os.path.join(OUTPUT_DIR, 'log.txt')
    # clear previous outputs except log.txt
    for f in os.listdir(OUTPUT_DIR):
        if f != 'log.txt':
            try:
                os.remove(os.path.join(OUTPUT_DIR, f))
            except Exception:
                pass

    try:
        with open(repo_log, 'rb') as src, open(input_path, 'wb') as dst:
            dst.write(src.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok", "message": "Demo log loaded"}


@router.get('/download_demo')
def download_demo():
    """Serve the repository demo Log.txt for direct download."""
    repo_log = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'Log.txt'))
    if not os.path.exists(repo_log):
        raise HTTPException(status_code=404, detail='Demo Log.txt not found')
    # Force a plain text attachment response so browsers download instead of rendering JSON/text
    return FileResponse(repo_log, media_type='text/plain', filename='demo_log.txt')


@router.get('/run_function')
def run_function(function: str):
    log_file = os.path.join(OUTPUT_DIR, 'log.txt')
    if not os.path.exists(log_file):
        raise HTTPException(status_code=400, detail='Please upload a log file first')

    try:
        start_time = time.time()
        if function == 'daily_report':
            result = generate_daily_report(log_file)
            output_file = 'daily_report.txt'
        elif function == 'event_detection':
            result = detect_events(log_file)
            output_file = 'alerts.txt'
        elif function == 'sentiment_analysis':
            result = analyze_sentiment(log_file)
            output_file = 'sentiment_analysis.txt'
        elif function == 'pattern_detection':
            result = detect_patterns(log_file)
            output_file = 'patterns.txt'
        elif function == 'translation':
            result = translate_logs(log_file)
            output_file = 'translated_hi.txt'
        elif function == 'log_summary':
            result = get_log_summary_from_ai(log_file)
            output_file = 'get_log_summary_from_ai.txt'
        elif function == 'anomaly_detection':
            result = clean_and_detect_anomalies(log_file)
            output_file = 'cleanup_report.txt'
        else:
            raise HTTPException(status_code=400, detail='Invalid function specified')

        output_path = os.path.join(OUTPUT_DIR, output_file)
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                output_content = f.read()
        else:
            output_content = result

        processing_time = time.time() - start_time
        return {
            'result': output_content,
            'download_link': f"/download/{output_file}",
            'processing_time': f"{processing_time:.2f} seconds"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/download/{filename}')
def download_file(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='File not found')
    return FileResponse(path, filename=filename)
