import os
import re
import logging
import numpy as np

OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'static/outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clean_and_detect_anomalies(log_file):
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.readlines()

        features = []
        for log in logs:
            length = len(log)
            word_count = len(log.split())
            has_time = 1 if re.search(r'\[\d{1,2}:\d{1,2}\]', log) else 0
            features.append([length, word_count, has_time])

        X = np.array(features)
        from sklearn.ensemble import IsolationForest
        clf = IsolationForest(contamination=0.05)
        anomalies = clf.fit_predict(X)
        unique_logs = list(set(logs))
        duplicate_count = len(logs) - len(unique_logs)

        result_str = "=== LOG CLEANUP & ANOMALY DETECTION ===\n\n"
        result_str += f"Total logs: {len(logs)}\n"
        result_str += f"Unique logs: {len(unique_logs)}\n"
        result_str += f"Duplicate logs: {duplicate_count}\n"
        result_str += f"Anomalies detected: {int(np.sum(anomalies == -1))}\n\n"

        if np.sum(anomalies == -1) > 0:
            result_str += "Anomalous logs:\n"
            for idx, is_anomaly in enumerate(anomalies):
                if is_anomaly == -1:
                    result_str += f"- {logs[idx]}"

        output_path = os.path.join(OUTPUT_DIR, 'cleanup_report.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_str)

        return result_str
    except Exception as e:
        logging.exception('clean_and_detect_anomalies error')
        error_msg = f"Error cleaning logs: {str(e)}"
        with open(os.path.join(OUTPUT_DIR, 'cleanup_report.txt'), 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg
