import os
import re
import logging
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
from sklearn.preprocessing import minmax_scale
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
except Exception:
    AutoTokenizer = None
    AutoModel = None
    torch = None
from markdown import markdown
from bs4 import BeautifulSoup

OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'static/outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Event detection keywords
CRITICAL_KEYWORDS = {
    'poaching': ['tire tracks', 'gunshot', 'poach', 'trap', 'restricted area'],
    'injured_animal': ['injured', 'wounded', 'hurt', 'limping', 'bleeding'],
    'unusual_movement': ['unusual', 'strange', 'not normal', 'abnormal', 'migration']
}


class EventDetector:
    def __init__(self):
        self.keyword_patterns = {
            event: re.compile('|'.join(keywords), re.IGNORECASE)
            for event, keywords in CRITICAL_KEYWORDS.items()
        }

    def transform(self, X, y=None):
        alerts = []
        for text in X:
            detected_events = []
            for event, pattern in self.keyword_patterns.items():
                if pattern.search(text):
                    detected_events.append(event)
            alerts.append(detected_events if detected_events else None)
        return alerts


def generate_daily_report(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        processed_logs = [re.sub(r'\[\d{1,2}:\d{1,2}\]', '', log).lower() for log in logs]
        vectorizer = TfidfVectorizer(max_features=1000)
        X = vectorizer.fit_transform(processed_logs)

        report_str = "== DAILY REPORT ==\n\n"
        report_str += f"Total entries: {len(logs)}\n\n"
        report_str += "Top 10 keywords:\n"
        report_str += "\n".join(f"- {kw}" for kw in vectorizer.get_feature_names_out()[:10]) + "\n\n"
        report_str += "Sample processed entries:\n"
        report_str += "\n".join(f"- {log}" for log in processed_logs[:3])

        output_path = os.path.join(OUTPUT_DIR, 'daily_report.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_str)

        return report_str
    except Exception as e:
        logging.exception("generate_daily_report error")
        error_msg = f"Error generating daily report: {str(e)}"
        with open(os.path.join(OUTPUT_DIR, 'daily_report.txt'), 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg


def detect_events(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        detector = EventDetector()
        alerts = detector.transform(logs)

        alert_str = "=== CRITICAL EVENT ALERTS ===\n\n"
        alert_count = 0
        for log, alert in zip(logs, alerts):
            if alert:
                alert_count += 1
                alert_str += f"ALERT {alert_count}:\n"
                alert_str += f"Type: {', '.join(alert)}\n"
                alert_str += f"Log: {log}\n\n"

        if alert_count == 0:
            alert_str += "No critical events detected.\n"

        output_path = os.path.join(OUTPUT_DIR, 'alerts.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(alert_str)

        return alert_str
    except Exception as e:
        logging.exception("detect_events error")
        error_msg = f"Error detecting events: {str(e)}"
        with open(os.path.join(OUTPUT_DIR, 'alerts.txt'), 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg


def detect_patterns(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        processed_logs = [re.sub(r'\[\d{1,2}:\d{1,2}\]', '', log).lower() for log in logs]
        vectorizer = TfidfVectorizer(max_features=1000)
        X = vectorizer.fit_transform(processed_logs)

        lda = LatentDirichletAllocation(n_components=5, random_state=42)
        lda.fit(X)

        kmeans = KMeans(n_clusters=5, random_state=42)
        clusters = kmeans.fit_predict(X)
        cluster_logs = defaultdict(list)
        for log, cluster in zip(logs, clusters):
            cluster_logs[cluster].append(log)

        result_str = "=== PATTERN DETECTION ===\n\n"
        result_str += "Topic Modeling Results:\n"
        for idx, topic in enumerate(lda.components_):
            result_str += f"Topic {idx}: "
            result_str += ", ".join([vectorizer.get_feature_names_out()[int(i)] for i in topic.argsort()[-10:]])
            result_str += "\n"

        result_str += "\nLog Clusters:\n"
        for cluster, logs in cluster_logs.items():
            result_str += f"Cluster {cluster} ({len(logs)} logs)\n"
            result_str += "Sample logs:\n"
            for log in logs[:3]:
                result_str += f"- {log}"

        output_path = os.path.join(OUTPUT_DIR, 'patterns.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_str)

        return result_str
    except Exception as e:
        logging.exception('detect_patterns error')
        error_msg = f"Error detecting patterns: {str(e)}"
        with open(os.path.join(OUTPUT_DIR, 'patterns.txt'), 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg


def get_log_summary_from_ai(log_file, max_retries=3, retry_delay=5):
    # New extractive summarizer using TF-IDF + optional MiniLM embeddings
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        # Simple sentence splitting (robust fallback if nltk not available)
        try:
            import nltk
            try:
                nltk.data.find('tokenizers/punkt')
            except Exception:
                nltk.download('punkt')
            from nltk.tokenize import sent_tokenize
            sentences = [s.strip() for s in sent_tokenize(text) if s.strip()]
        except Exception:
            # fallback split by newline and punctuation
            sentences = [s.strip() for s in re.split(r'[\n\r]+|(?<=[.!?])\s+', text) if s.strip()]

        if not sentences:
            msg = "No content found in log file to summarize."
            out_path = os.path.join(OUTPUT_DIR, 'get_log_summary_from_ai.txt')
            with open(out_path, 'w', encoding='utf-8') as fh:
                fh.write(msg)
            return msg

        # TF-IDF scoring over sentences
        vectorizer = TfidfVectorizer(stop_words='english', max_features=2000)
        X = vectorizer.fit_transform(sentences)
        tfidf_scores = np.asarray(X.sum(axis=1)).ravel()

        # pick top sentences by TF-IDF score
        max_sentences = min(7, len(sentences))
        top_tfidf_idx = tfidf_scores.argsort()[-max_sentences:][::-1]

        # Try to load MiniLM embeddings and combine semantic relevance
        def load_embedding_model_once():
            if AutoTokenizer is None or AutoModel is None or torch is None:
                return None, None
            try:
                tok = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
                model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
                model.eval()
                return tok, model
            except Exception:
                logging.exception('Failed to load embedding model')
                return None, None

        def embed_sentences(sent_list, tokenizer, model):
            try:
                with torch.no_grad():
                    batch = tokenizer(sent_list, padding=True, truncation=True, return_tensors='pt')
                    outputs = model(**batch)
                    token_embeds = outputs.last_hidden_state
                    attention_mask = batch['attention_mask'].unsqueeze(-1)
                    summed = (token_embeds * attention_mask).sum(1)
                    counts = attention_mask.sum(1)
                    embeddings = summed / counts
                    return embeddings.cpu().numpy()
            except Exception:
                logging.exception('Embedding failure')
                return None

        tokenizer, model = load_embedding_model_once()
        final_indices = list(sorted(top_tfidf_idx))

        if tokenizer and model:
            # compute embeddings for all sentences (small models are fast)
            emb = embed_sentences(sentences, tokenizer, model)
            if emb is not None:
                centroid = emb.mean(axis=0)
                # cosine similarity
                sims = (emb @ centroid) / (np.linalg.norm(emb, axis=1) * np.linalg.norm(centroid) + 1e-12)
                # normalize and combine with TF-IDF score
                tfidf_norm = minmax_scale(tfidf_scores)
                sim_norm = minmax_scale(sims)
                combined = tfidf_norm + sim_norm
                combined_idx = combined.argsort()[-max_sentences:][::-1]
                # preserve original ordering of selected sentences for readability
                final_indices = sorted(combined_idx)

        # Build extractive summary preserving document order
        summary_sentences = [sentences[i] for i in final_indices]
        summary_text = "\n\n".join(summary_sentences)
        # Save as plain text and return a light HTML version
        output_path = os.path.join(OUTPUT_DIR, 'get_log_summary_from_ai.txt')
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(summary_text)

        # Return an HTML-safe formatted string
        html_out = markdown('\n\n'.join([f"- {s}" for s in summary_sentences]))
        return html_out

    except Exception as e:
        logging.exception("get_log_summary_from_ai error")
        error_msg = f"Error generating summary: {str(e)}"
        with open(os.path.join(OUTPUT_DIR, 'get_log_summary_from_ai.txt'), 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg
