from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, jsonify
import os
from pipeline import (
    generate_daily_report,
    detect_events,
    analyze_sentiment,
    detect_patterns,
    translate_logs,
    clean_and_detect_anomalies,
    get_log_summary_from_ai
)
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'static/outputs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # We no longer show download links on the main page
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    # Clear previous outputs
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if f != 'log.txt':  # Keep the uploaded file
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
            except:
                pass
    
    # Save uploaded file
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], 'log.txt')
    file.save(input_path)
    
    return redirect(url_for('index'))

@app.route('/run_function')
def run_function():
    function_name = request.args.get('function')
    log_file = os.path.join(app.config['UPLOAD_FOLDER'], 'log.txt')
    
    if not os.path.exists(log_file):
        return jsonify({'error': 'Please upload a log file first'}), 400
    
    try:
        start_time = time.time()
        
        if function_name == 'daily_report':
            result = generate_daily_report(log_file)
            output_file = 'daily_report.txt'
        elif function_name == 'event_detection':
            result = detect_events(log_file)
            output_file = 'alerts.txt'
        elif function_name == 'sentiment_analysis':
            result = analyze_sentiment(log_file)
            output_file = 'sentiment_analysis.txt'
        elif function_name == 'pattern_detection':
            result = detect_patterns(log_file)
            output_file = 'patterns.txt'
        elif function_name == 'translation':
            result = translate_logs(log_file)
            output_file = 'translated_hi.txt'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_file)           
            if not os.path.exists(output_path):
                raise RuntimeError("Translation output file was not created")               
            with open(output_path, 'r', encoding='utf-8') as f:
                output_content = f.read()
        elif function_name == 'log_summary':
            result = get_log_summary_from_ai(log_file)  
            output_file = 'get_log_summary_from_ai.txt'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_file)
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    output_content = f.read()
            else:
                output_content = result  
 
        elif function_name == 'anomaly_detection':
            result = clean_and_detect_anomalies(log_file)
            output_file = 'cleanup_report.txt'
        else:
            return jsonify({'error': 'Invalid function specified'}), 400
        
        
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_file)
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                output_content = f.read()
        else:
            output_content = f"Report generated but file not found: {output_file}"
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'result': output_content,
            'download_link': f"/download/{output_file}",
            'processing_time': f"{processing_time:.2f} seconds"
        })
    except Exception as e:
        app.logger.error(f"Error in {function_name}: {str(e)}")
        return jsonify({
            'error': f"Error processing {function_name}",
            'details': str(e)
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
