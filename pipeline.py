
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import re
from sklearn.base import BaseEstimator, TransformerMixin
from transformers import pipeline, MarianMTModel, MarianTokenizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
from collections import defaultdict
from sklearn.ensemble import IsolationForest
import numpy as np

os.makedirs('static/outputs', exist_ok=True)

# NLTK Text Processing
def preprocess_text(text):
    text = text.lower()
    # Remove timestamps like [14:20]
    text = re.sub(r'\[\d{1,2}:\d{1,2}\]', '', text)

    tokens = word_tokenize(text)

    tokens = [word for word in tokens if word not in string.punctuation]

    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]

    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return ' '.join(tokens)

import time
from markdown import markdown
from bs4 import BeautifulSoup
from openai import OpenAI

import os
import time
from markdown import markdown
from bs4 import BeautifulSoup
from openai import OpenAI
os.makedirs('static/outputs', exist_ok=True)


from markdown import markdown
from bs4 import BeautifulSoup

#LLM (Transformer-based) : Uses markdown formatting, requires API key
def get_log_summary_from_ai(log_file, max_retries=3, retry_delay=5):
    """Summarize markdown logs using an AI model via API and return HTML-rendered content."""
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        api_key = "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"

        markdown_text = "\n\n".join(logs)
        html_text = markdown(markdown_text)
        soup = BeautifulSoup(html_text, features="html.parser")
        structured_text = soup.get_text()

        prompt = (
            "You are a helpful assistant specialized in log analysis and summarization.\n"
            "Given the following system/application logs, summarize the key events, issues, errors, and insights. "
            "Structure the summary clearly with:\n"
            "- Main headings (##)\n"
            "- Subheadings (###)\n"
            "- Bullet points\n"
            "- Bold important items (**text**)\n"
            "- Italics for less critical notes (*text*)\n"
            "Format the response in proper markdown that will be rendered to HTML.\n\n"
            f"LOGS TO SUMMARIZE:\n{structured_text}"
        )

        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        attempt = 0
        while attempt < max_retries:
            try:
                response = client.chat.completions.create(
                    model="deepseek/deepseek-chat:free",
                    messages=[{"role": "user", "content": prompt}]
                )

                if response.choices:
                    markdown_summary = response.choices[0].message.content
                    safe_markdown_summary = markdown_summary if markdown_summary is not None else ""
                    html_summary = markdown(safe_markdown_summary)
                    output_path = 'static/outputs/get_log_summary_from_ai.txt'
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(safe_markdown_summary)
                    return html_summary  

                return markdown("❌ **Error**: No response from the AI API.")

            except Exception as e:
                time.sleep(retry_delay)
                attempt += 1

        error_msg = markdown("❌ **Failed** to fetch summary after multiple attempts.")
        with open('static/outputs/get_log_summary_from_ai.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg

    except Exception as e:
        error_msg = markdown(f"❌ **Error processing logs**: {str(e)}")
        with open('static/outputs/get_log_summary_from_ai.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg

# TF-IDF Vectorizer : Feature Extraction , Uses scikit-learn's TfidfVectorizer
# Extracts important keywords
def generate_daily_report(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        processed_logs = [preprocess_text(log) for log in logs]
        vectorizer = TfidfVectorizer(max_features=1000)
        X = vectorizer.fit_transform(processed_logs)

        report_str = "== DAILY REPORT ==\n\n"
        report_str += f"Total entries: {len(logs)}\n\n"
        report_str += "Top 10 keywords:\n"
        report_str += "\n".join(f"- {kw}" for kw in vectorizer.get_feature_names_out()[:10]) + "\n\n"
        report_str += "Sample processed entries:\n"
        report_str += "\n".join(f"- {log}" for log in processed_logs[:3])

        output_path = 'static/outputs/daily_report.txt'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_str)

        return report_str
    except Exception as e:
        error_msg = f"Error generating daily report: {str(e)}"
        with open('static/outputs/daily_report.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg


#Regex-based Classifier :(Rule-based NLP) Detects critical events using keyword patterns
CRITICAL_KEYWORDS = {
    'poaching': ['tire tracks', 'gunshot', 'poach', 'trap', 'restricted area'],
    'injured_animal': ['injured', 'wounded', 'hurt', 'limping', 'bleeding'],
    'unusual_movement': ['unusual', 'strange', 'not normal', 'abnormal', 'migration']
}
class EventDetector(BaseEstimator, TransformerMixin):
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

def detect_events(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        detector = EventDetector()
        alerts = detector.transform(logs)

        # Format alerts as string
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

        output_path = 'static/outputs/alerts.txt'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(alert_str)

        return alert_str
    except Exception as e:
        error_msg = f"Error detecting events: {str(e)}"
        with open('static/outputs/alerts.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg

#HuggingFace Pipeline :(Transformer Model),Sentiment analysis (positive/negative)
#BERT-base-uncased(bhadresh-savani) : Emotion classification
import re
from transformers import pipeline

def analyze_sentiment(log_file):
    try:
        sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english"
)
        emotion_analyzer = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")
        # Get label-to-emotion mapping
        label_map = emotion_analyzer.model.config.id2label

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        results = []
        for log in logs:
            clean_log = re.sub(r'\[\d{1,2}:\d{1,2}\]', '', log).strip()
            if len(clean_log.split()) > 3:
                try:
                    sentiment_result = sentiment_analyzer(clean_log)
                    emotion_result = emotion_analyzer(clean_log)
                    
                    # Convert to list if generator, and check for None
                    sentiment_list = list(sentiment_result) if sentiment_result is not None else []
                    emotion_list = list(emotion_result) if emotion_result is not None else []
                    
                    if sentiment_list and emotion_list:
                        sentiment = sentiment_list[0]
                        emotion_raw = emotion_list[0]
                        # Translate label
                        # Ensure emotion_raw is a dict before accessing 'label'
                        if isinstance(emotion_raw, dict) and 'label' in emotion_raw:
                            emotion_label = emotion_raw.get('label')
                            emotion_score = emotion_raw.get('score')
                        else:
                            emotion_label = str(emotion_raw)
                            emotion_score = None

                        results.append({
                            'log': log,
                            'sentiment': sentiment,
                            'emotion': {
                                'label': emotion_label,
                                'score': emotion_score
                            }
                        })
                    else:
                        results.append({
                            'log': log,
                            'error': 'No result returned from sentiment or emotion analyzer'
                        })
                except Exception as e:
                    results.append({
                        'log': log,
                        'error': str(e)
                    })

        # Format results as string
        result_str = "=== SENTIMENT ANALYSIS ===\n\n"
        for result in results:
            result_str += f"Log: {result['log']}"
            if 'error' in result:
                result_str += f"Error: {result['error']}\n\n"
            else:
                result_str += f"Sentiment: {result['sentiment']['label']} ({result['sentiment']['score']:.2f})\n"
                result_str += f"Emotion: {result['emotion']['label']} ({result['emotion']['score']:.2f})\n\n"

        # Save to file
        output_path = 'static/outputs/sentiment_analysis.txt'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_str)

        return result_str

    except Exception as e:
        error_msg = f"Error analyzing sentiment: {str(e)}"
        with open('static/outputs/sentiment_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg



#TF-IDF + LDA :(Topic Modeling) Uses scikit-learn's LatentDirichletAllocation
#K-Means Clutering 
def detect_patterns(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        processed_logs = [preprocess_text(log) for log in logs]
        vectorizer = TfidfVectorizer(max_features=1000)
        X = vectorizer.fit_transform(processed_logs)

        # Topic Modeling
        lda = LatentDirichletAllocation(n_components=5, random_state=42)
        lda.fit(X)

        # Clustering
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

        output_path = 'static/outputs/patterns.txt'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_str)

        return result_str
    except Exception as e:
        error_msg = f"Error detecting patterns: {str(e)}"
        with open('static/outputs/patterns.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg


#MarianMT (opus-mt-en-hi) :Seq2Seq Transformer ,Helsinki-NLP model, batche processing
from transformers import MarianMTModel, MarianTokenizer
import logging
class LogTranslator:
    def __init__(self):
        self.model_loaded = False
        self.tokenizer = None
        self.model = None
        
    def load_model(self):
        try:
            if not self.model_loaded:
                logging.info("Loading Hindi translation model...")
                model_name = "Helsinki-NLP/opus-mt-en-hi"
                self.tokenizer = MarianTokenizer.from_pretrained(model_name)
                self.model = MarianMTModel.from_pretrained(model_name)
                self.model_loaded = True
                logging.info("Model loaded successfully")
        except Exception as e:
            logging.error(f"Model loading failed: {str(e)}")
            raise RuntimeError(f"Could not load translation model: {str(e)}")

    def translate_batch(self, texts):
        try:
            if not self.model_loaded or self.tokenizer is None or self.model is None:
                self.load_model()
            # Ensure tokenizer and model are loaded before calling them
            if self.tokenizer is None:
                raise RuntimeError("Tokenizer is not loaded.")
            if self.model is None:
                raise RuntimeError("Model is not loaded.")
            inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
            outputs = self.model.generate(**inputs)
            return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        except Exception as e:
            logging.error(f"Translation failed: {str(e)}")
            raise RuntimeError(f"Translation error: {str(e)}")
        
def translate_logs(log_file):
    try:
        translator = LogTranslator()
        translator.load_model()  
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = [line.strip() for line in f.readlines() if line.strip()]

        result_str = "=== ENGLISH TO HINDI TRANSLATION ===\n\n"
        translated_logs = []
        
        # Process in small batches
        batch_size = 5
        for i in range(0, min(20, len(logs)), batch_size):
            batch = logs[i:i+batch_size]
            try:
                translated = translator.translate_batch(batch)
                translated_logs.extend(translated)
                
                for orig, trans in zip(batch, translated):
                    result_str += f"Original: {orig}\n"
                    result_str += f"Translated: {trans}\n\n"
            except Exception as e:
                translated_logs.extend([f"Error: {str(e)}"] * len(batch))
                result_str += f"Error processing batch: {str(e)}\n\n"

        output_path = 'static/outputs/translated_hi.txt'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(translated_logs))

        return result_str
        
    except Exception as e:
        error_msg = f"Translation failed: {str(e)}"
        logging.error(error_msg)
        with open('static/outputs/translated_hi.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg


#Isolation Forest :Anomaly Detection ,Identifies unusual log entries
def clean_and_detect_anomalies(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        # Feature extraction
        features = []
        for log in logs:
            length = len(log)
            word_count = len(log.split())
            has_time = 1 if re.search(r'\[\d{1,2}:\d{1,2}\]', log) else 0
            features.append([length, word_count, has_time])

        X = np.array(features)
        clf = IsolationForest(contamination=0.05)
        anomalies = clf.fit_predict(X)
        unique_logs = list(set(logs))
        duplicate_count = len(logs) - len(unique_logs)

        # Format results
        result_str = "=== LOG CLEANUP & ANOMALY DETECTION ===\n\n"
        result_str += f"Total logs: {len(logs)}\n"
        result_str += f"Unique logs: {len(unique_logs)}\n"
        result_str += f"Duplicate logs: {duplicate_count}\n"
        result_str += f"Anomalies detected: {np.sum(anomalies == -1)}\n\n"
        
        if np.sum(anomalies == -1) > 0:
            result_str += "Anomalous logs:\n"
            for idx, is_anomaly in enumerate(anomalies):
                if is_anomaly == -1:
                    result_str += f"- {logs[idx]}"

        # Save to file
        output_path = 'static/outputs/cleanup_report.txt'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_str)

        return result_str
    except Exception as e:
        error_msg = f"Error cleaning logs: {str(e)}"
        with open('static/outputs/cleanup_report.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg


def full_pipeline(log_file='log.txt'):
    results = {}
    results['daily_report'] = generate_daily_report(log_file)
    results['event_detection'] = detect_events(log_file)
    results['sentiment_analysis'] = analyze_sentiment(log_file)
    results['pattern_detection'] = detect_patterns(log_file)
    results['translation'] = translate_logs(log_file)  # Removed 'sw' parameter
    results['anomaly_detection'] = clean_and_detect_anomalies(log_file)
    results['log_summary'] = get_log_summary_from_ai(log_file)
    return results
