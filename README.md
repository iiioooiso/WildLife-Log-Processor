# 🐾 Wildlife Log Processor

[![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-modern-brightgreen?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-orange?logo=uvicorn)](https://www.uvicorn.org/) [![Transformers](https://img.shields.io/badge/transformers-🤗-blueviolet?logo=huggingface)](https://huggingface.co/docs/transformers)

[![PyTorch](https://img.shields.io/badge/PyTorch-ML-red?logo=PyTorch)](https://pytorch.org/) [![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-yellowgreen?logo=scikit-learn)](https://scikit-learn.org/) [![NLTK](https://img.shields.io/badge/NLTK-NLP-lightgrey?logo=nltk)](https://www.nltk.org/) [![MiniLM](https://img.shields.io/badge/MiniLM-embeddings-lightgrey)](https://www.sbert.net/) [![TF-IDF](https://img.shields.io/badge/TF--IDF-extractive-informational)](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) [![Docker](https://img.shields.io/badge/Docker-container-blue?logo=docker)](https://www.docker.com/)

[![HuggingFace Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-orange?logo=huggingface)](https://huggingface.co/spaces)

A modern, production-minded web application for uploading and processing wildlife log files. It helps you analyze, summarize, and report wildlife activity from raw text logs with minimal setup — optimized for local runs or deployment to Hugging Face Spaces (Docker).

---

## Why this project

- Built for readable, real-world wildlife logs: extractive summaries, event detection, anomaly detection, translations, sentiment and pattern analysis.
- Models and heavy pipelines are loaded once (module-level) to avoid repeated downloads and to  keep request latency low.
- Local-first and privacy-friendly: you can run everything locally; no hardcoded API keys. Optional integrations (OpenRouter/OpenAI) are available for advanced summaries when you provide secrets.

---

## Features

<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px;">
  <figure style="flex:1 1 48%;margin:0;">
    <img src="https://github.com/user-attachments/assets/5ac3009b-3138-4cc3-9eca-605936f63eb4" alt="screenshot-1" style="width:100%;border-radius:8px;box-shadow:0 6px 20px rgba(0,0,0,0.08);"/>
  </figure>
  <figure style="flex:1 1 48%;margin:0;">
    <img src="https://github.com/user-attachments/assets/371dc7c4-0efc-4402-bb6e-a17f2b45028c" alt="screenshot-2" style="width:100%;border-radius:8px;box-shadow:0 6px 20px rgba(0,0,0,0.08);"/>
  </figure>
</div>

| Feature | Description | Technique |
|---|---|---|
| Upload & Process | Upload plain-text wildlife logs or use the built-in demo to start processing instantly. | — |
| Extractive Summaries | TF‑IDF driven extractive summaries; optionally re-ranked with MiniLM semantic embeddings for improved relevance. | ![TF-IDF](https://img.shields.io/badge/TF--IDF-informational) ![MiniLM](https://img.shields.io/badge/MiniLM-lightgrey)
| Event Detection | Keyword and heuristic detectors for events such as poaching, injury, or unusual movement patterns. | Keywords + rules
| Pattern Detection | LDA topic modeling and clustering surface recurring activities and patrol patterns. | LDA / Clustering
| Sentiment Analysis | Hugging Face pipelines extract sentiment/emotion signals from notes and field observations. | ![Transformers](https://img.shields.io/badge/transformers-🤗-blueviolet)
| Anomaly Detection | IsolationForest and lightweight heuristics flag outliers, corrupted entries, and suspicious patterns. | IsolationForest
| Translation & Reports | Translate logs (Hindi demo) and download full, shareable report files. | Marian (HF)
| Demo Mode | One-click demo using `Log.txt` with an immediate download option for quick evaluation. | —

---

## Quickstart — Run locally (Windows PowerShell)

1. Create a virtual environment and activate it:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. (Recommended) set local Hugging Face cache dirs so model files are stored under `.cache`:

```powershell
$env:HF_HOME = ".cache"
$env:TRANSFORMERS_CACHE = ".cache\transformers"
$env:TORCH_HOME = ".cache\torch"
```

3. Install dependencies and run the app:

```powershell
venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 7860
```

4. Open your browser at `http://127.0.0.1:7860`.

---

## Deployment (Hugging Face Spaces / Docker)

- This repo contains a `Dockerfile` configured to expose port `7860` for Spaces. Add your repository to a Docker Space and set any required environment secrets (e.g. `OPENROUTER_API_KEY`) in the Space settings.

---

## UI Highlights

- One-page interface: upload or use demo, process, then run analysis tiles (Daily Report, Log Summary, Event Detection, Sentiment, Pattern Detection, Translation, Anomaly Detection).
- Professional modern look with badges showing which technique is used for each tile (TF‑IDF, MiniLM, LDA, IsolationForest, etc.).
- Demo log button with built-in download for quick evaluation.

---

## Project layout

- `app.py` — optional entrypoint wrapper.
- `backend/main.py` — FastAPI app, static mounts and router inclusion.
- `backend/routes/main_routes.py` — API routes: upload, demo, run_function, download.
- `backend/services/` — modular services: `summarizer.py`, `sentiment.py`, `translation.py`, `anomaly.py`, `agentic.py`, etc.
- `backend/templates/` + `static/` — frontend template and assets (`css`, `js`, `bg.png`).
- `Log.txt` — curated demo log used by the demo flow.

---

## Notes & Tips

- If you want faster model downloads in CI or Spaces, set an authenticated `HF_TOKEN` or use smaller models during testing.
- To remove heavy downloads after development: delete the `venv` directory and the `.cache` directory (contains transformers/torch models).
- NLTK tokenizers will be auto-downloaded if missing; optionally preinstall them in your environment:

```powershell
venv\Scripts\python.exe -c "import nltk; nltk.download('punkt')"
```

---

## Contributing

Contributions welcome — open an issue or PR. Keep changes focused, add tests where practical, and follow the repository style (modular services, single-responsibility functions).

---

## License & Credits

This project is provided as-is for demonstration and utility. Add your preferred license as needed before publishing.

---

Enjoy — and thank you for building conservation tools that make it easier to turn raw field notes into actionable intelligence. 🐾

