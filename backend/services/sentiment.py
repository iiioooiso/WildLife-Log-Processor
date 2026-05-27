import os
import re
import logging
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from transformers import pipeline

OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'static/outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load heavy models once globally
try:
    sentiment_analyzer = pipeline(
        "sentiment-analysis",
        model="distilbert/distilbert-base-uncased-finetuned-sst-2-english"
    )
except Exception:
    sentiment_analyzer = None

try:
    emotion_analyzer = pipeline(
        "text-classification",
        model="bhadresh-savani/bert-base-uncased-emotion"
    )
except Exception:
    emotion_analyzer = None


def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\[\d{1,2}:\d{1,2}\]', '', text)
    tokens = word_tokenize(text)
    tokens = [w for w in tokens if w not in string.punctuation]
    stop_words = set(stopwords.words('english'))
    tokens = [w for w in tokens if w not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(w) for w in tokens]
    return ' '.join(tokens)


def analyze_sentiment(log_file):
    try:
        if sentiment_analyzer is None or emotion_analyzer is None:
            raise RuntimeError('Required transformers pipelines not loaded')

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        results = []
        for log in logs:
            clean_log = re.sub(r'\[\d{1,2}:\d{1,2}\]', '', log).strip()
            if len(clean_log.split()) > 3:
                try:
                    sentiment_result = sentiment_analyzer(clean_log)
                    emotion_result = emotion_analyzer(clean_log)

                    sentiment_list = list(sentiment_result) if sentiment_result is not None else []
                    emotion_list = list(emotion_result) if emotion_result is not None else []

                    if sentiment_list and emotion_list:
                        sentiment = sentiment_list[0]
                        emotion_raw = emotion_list[0]
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
                        results.append({'log': log, 'error': 'No result returned'})
                except Exception as e:
                    results.append({'log': log, 'error': str(e)})

        result_str = "=== SENTIMENT ANALYSIS ===\n\n"
        for result in results:
            result_str += f"Log: {result['log']}"
            if 'error' in result:
                result_str += f"Error: {result['error']}\n\n"
            else:
                s = result['sentiment']
                e = result['emotion']
                score_s = f" ({s['score']:.2f})" if isinstance(s.get('score'), float) else ''
                score_e = f" ({e['score']:.2f})" if isinstance(e.get('score'), float) else ''
                result_str += f"Sentiment: {s['label']}{score_s}\n"
                result_str += f"Emotion: {e['label']}{score_e}\n\n"

        output_path = os.path.join(OUTPUT_DIR, 'sentiment_analysis.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_str)

        return result_str
    except Exception as e:
        logging.exception('analyze_sentiment error')
        error_msg = f"Error analyzing sentiment: {str(e)}"
        with open(os.path.join(OUTPUT_DIR, 'sentiment_analysis.txt'), 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg
