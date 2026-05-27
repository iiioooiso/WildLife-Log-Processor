// JS extracted from template: handles upload form UI and remote function calls
document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('file-input');
    const processBtn = document.getElementById('process-btn');
    const demoBtn = document.getElementById('demo-btn');
    let demoLoaded = false;

    function disableFunctionBoxes(state) {
        document.querySelectorAll('.function-box').forEach(el => {
            if (state) el.classList.add('disabled'); else el.classList.remove('disabled');
        });
    }

    // initial state: functions disabled, process button disabled
    disableFunctionBoxes(true);
    if (processBtn) processBtn.disabled = true;
    if (fileInput) {
        fileInput.addEventListener('change', function (e) {
            const fileName = e.target.files[0] ? e.target.files[0].name : 'No file chosen';
            const el = document.getElementById('file-name');
            if (el) el.textContent = fileName;
            // enable the Process File button (functions remain disabled until processed)
            if (processBtn) processBtn.disabled = false;
            showNotification('File selected. Click "Process File" to enable analysis options.');
        });
    }

    if (demoBtn) {
        demoBtn.addEventListener('click', function () {
            demoBtn.disabled = true;
            showNotification('Loading demo log...');
            fetch('/use_demo', { method: 'POST' })
                .then(r => { if (!r.ok) throw new Error('Failed to load demo'); return r.json(); })
                .then(() => {
                    demoLoaded = true;
                    const el = document.getElementById('file-name');
                    if (el) el.textContent = 'demo_log.txt';
                    if (processBtn) processBtn.disabled = false;
                    showNotification('Demo log loaded. Click "Process File" to enable analysis.');
                })
                .catch(err => {
                    showNotification('Error loading demo: ' + err.message, true);
                    demoBtn.disabled = false;
                });
        });
    }

    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const btn = document.getElementById('process-btn');
            const btnText = document.getElementById('btn-text');
            const btnSpinner = document.getElementById('btn-spinner');
            const fileInput = document.getElementById('file-input');
            if (!demoLoaded && (!fileInput || !fileInput.files[0])) { showNotification('Please select a file first!', true); return; }

            btn.disabled = true; btnText.style.display = 'none'; btnSpinner.style.display = 'inline';
            showNotification('Uploading and processing your log file...');
            const progressBar = document.getElementById('progress-bar');
            if (progressBar) { progressBar.style.width = '0%'; progressBar.style.transition = 'width 0.3s ease'; }

            if (demoLoaded) {
                // Demo already loaded on server; simulate processing progress without uploading
                let progress = 0;
                const progressInterval = setInterval(() => { progress += 15; if (progressBar) progressBar.style.width = `${progress}%`; if (progress >= 100) { clearInterval(progressInterval); showNotification('Processing complete! Analysis options enabled.'); btn.disabled = false; btnText.style.display = 'inline'; btnSpinner.style.display = 'none'; document.getElementById('file-name').textContent = 'demo_log.txt'; disableFunctionBoxes(false); } }, 250);
            } else {
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                fetch('/upload', { method: 'POST', body: formData })
                .then(response => { if (!response.ok) throw new Error('Upload failed'); return response; })
                .then(() => {
                    let progress = 0;
                    const progressInterval = setInterval(() => { progress += 10; if (progressBar) progressBar.style.width = `${progress}%`; if (progress >= 100) { clearInterval(progressInterval); showNotification('Processing complete! Analysis options enabled.'); btn.disabled = false; btnText.style.display = 'inline'; btnSpinner.style.display = 'none'; document.getElementById('file-name').textContent = fileInput.files[0].name; disableFunctionBoxes(false); } }, 300);
                })
                .catch(error => { showNotification(`Error: ${error.message}`, true); btn.disabled = false; btnText.style.display = 'inline'; btnSpinner.style.display = 'none'; if (progressBar) progressBar.style.width='0%'; });
            }
        });
    }
});

function showNotification(message, isError = false) {
    const notification = document.getElementById('notification');
    const messageEl = document.getElementById('notification-message');
    if (!notification || !messageEl) return;
    notification.style.background = isError ? '#ff6b6b' : '#4CAF50';
    messageEl.textContent = message;
    notification.classList.add('show');
    setTimeout(()=> notification.classList.remove('show'), 5000);
}

function runFunction(functionName) {
    const loadingElement = document.getElementById(`${functionName}_loading`);
    const outputElement = document.getElementById(`${functionName}_output`);
    outputElement.innerHTML = ''; outputElement.style.display = 'none'; if (loadingElement) loadingElement.style.display = 'block';
    // show spinner
    if (loadingElement) loadingElement.innerHTML = '<div class="spinner" aria-hidden="true"></div>';

    fetch(`/run_function?function=${functionName}`)
        .then(response => {
            if (!response.ok) { return response.json().then(err => { throw new Error(err.details || err.error || 'Request failed'); }); }
            return response.json();
        })
        .then(data => {
            if (loadingElement) { loadingElement.style.display = 'none'; loadingElement.innerHTML = ''; }
            if (data.error) {
                outputElement.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i>${data.error}${data.details?`<br><small>${data.details}</small>`:''}</div>`;
            } else {
                // prepare content
                let innerHTML = '';
                if (functionName === 'log_summary') innerHTML = data.result; else innerHTML = data.result.replace(/\n/g,'<br>');
                outputElement.innerHTML = `<div class="content-inner">${innerHTML}</div>`;
                // add download icon at top-right if available
                if (data.download_link) {
                    const dl = document.createElement('a');
                    dl.className = 'download-icon';
                    dl.href = data.download_link;
                    dl.setAttribute('download', '');
                    dl.setAttribute('onclick', 'event.stopPropagation()');
                    dl.innerHTML = '<i class="fas fa-arrow-down"></i>';
                    outputElement.prepend(dl);
                }
            }
            outputElement.style.display = 'block';
        })
        .catch(error => {
            if (loadingElement) { loadingElement.style.display = 'none'; loadingElement.innerHTML = ''; }
            outputElement.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i>${error.message}</div>`;
            outputElement.style.display = 'block';
            console.error('Error:', error);
        });
}
