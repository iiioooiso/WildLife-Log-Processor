import os
import logging
from transformers import MarianMTModel, MarianTokenizer

OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'static/outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

TRANSLATOR = {
    'model': None,
    'tokenizer': None,
}


def _ensure_translation_loaded():
    if TRANSLATOR['model'] is None or TRANSLATOR['tokenizer'] is None:
        model_name = "Helsinki-NLP/opus-mt-en-hi"
        TRANSLATOR['tokenizer'] = MarianTokenizer.from_pretrained(model_name)
        TRANSLATOR['model'] = MarianMTModel.from_pretrained(model_name)


def translate_logs(log_file):
    try:
        _ensure_translation_loaded()
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = [line.strip() for line in f.readlines() if line.strip()]

        result_str = "=== ENGLISH TO HINDI TRANSLATION ===\n\n"
        translated_logs = []
        batch_size = 5
        for i in range(0, min(200, len(logs)), batch_size):
            batch = logs[i:i+batch_size]
            inputs = TRANSLATOR['tokenizer'](batch, return_tensors='pt', padding=True, truncation=True)
            outputs = TRANSLATOR['model'].generate(**inputs)
            translated = TRANSLATOR['tokenizer'].batch_decode(outputs, skip_special_tokens=True)
            translated_logs.extend(translated)
            for orig, trans in zip(batch, translated):
                result_str += f"Original: {orig}\nTranslated: {trans}\n\n"

        output_path = os.path.join(OUTPUT_DIR, 'translated_hi.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(translated_logs))

        return result_str
    except Exception as e:
        logging.exception('translate_logs error')
        error_msg = f"Translation failed: {str(e)}"
        with open(os.path.join(OUTPUT_DIR, 'translated_hi.txt'), 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg
