"""
Entrypoint. Runs the FastAPI app in `backend.main` using Uvicorn.
Use this as the single entry point for local runs and Hugging Face Spaces.
"""
import os
import uvicorn


if __name__ == '__main__':
    port = int(os.getenv('PORT', 7860))
    uvicorn.run('backend.main:app', host='0.0.0.0', port=port)
