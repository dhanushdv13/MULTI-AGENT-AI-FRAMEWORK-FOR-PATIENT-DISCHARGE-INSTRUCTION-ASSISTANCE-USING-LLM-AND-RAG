// ============================================================
// Healthcare Assistant - Frontend (Complete)
// ============================================================

const API_BASE = 'http://localhost:8000';
let _currentViewerDocId = null; // track doc being viewed

// ── Auth helpers ───────────────────────────────────────────────
function getToken() { return localStorage.getItem('token') || ''; }
function getUser() {
    try { return JSON.parse(localStorage.getItem('user') || 'null'); }
    catch { return null; }
}
function saveAuth(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
}
function clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

// ── API call with auth (auto re-login on 401) ─────────────────
async function apiCall(url, options = {}) {
    const token = getToken();
    const headers = options.headers || {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const response = await fetch(`${API_BASE}${url}`, { ...options, headers });
    if (response.status === 401) {
        clearAuth();
        showAuthScreen();
        throw new Error('Session expired. Please login again.');
    }
    return response;
}

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('signup-form').addEventListener('submit', handleSignup);
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    document.getElementById('discharge-file').addEventListener('change', (e) => {
        const name = e.target.files[0]?.name;
        if (name) document.getElementById('discharge-status').textContent = `Selected: ${name}`;
    });
    document.getElementById('bill-file').addEventListener('change', (e) => {
        const name = e.target.files[0]?.name;
        if (name) document.getElementById('bill-status').textContent = `Selected: ${name}`;
    });

    if (getToken() && getUser()) {
        showAppScreen();
    }
});

// ============================================================
// AUTH
// ============================================================
function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    if (tab === 'login') {
        document.querySelectorAll('.tab')[0].classList.add('active');
        document.getElementById('login-form').classList.add('active');
    } else {
        document.querySelectorAll('.tab')[1].classList.add('active');
        document.getElementById('signup-form').classList.add('active');
    }
    document.getElementById('auth-message').textContent = '';
    document.getElementById('auth-message').className = 'message';
}

async function handleSignup(e) {
    e.preventDefault();
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    showAuthMessage('Creating account...', 'success');
    try {
        const res = await fetch(`${API_BASE}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, full_name: name }),
        });
        const data = await res.json();
        if (res.ok) {
            showAuthMessage('Account created! Please login.', 'success');
            setTimeout(() => switchTab('login'), 1000);
        } else {
            showAuthMessage(data.detail || 'Signup failed', 'error');
        }
    } catch {
        showAuthMessage('Cannot reach server. Is the backend running?', 'error');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    showAuthMessage('Logging in...', 'success');
    try {
        const body = new URLSearchParams();
        body.append('username', email);
        body.append('password', password);
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: body,
        });
        const data = await res.json();
        if (res.ok && data.access_token) {
            saveAuth(data.access_token, { email, name: email.split('@')[0] });
            showAuthMessage('Success!', 'success');
            showAppScreen();
        } else {
            showAuthMessage(data.detail || 'Login failed', 'error');
        }
    } catch {
        showAuthMessage('Cannot reach server. Is the backend running?', 'error');
    }
}

function logout() {
    clearAuth();
    showAuthScreen();
    document.getElementById('chat-messages').innerHTML = `
        <div class="welcome-message">
            <h2>Welcome!</h2>
            <p>Upload documents and ask me anything!</p>
        </div>`;
}

function showAuthMessage(msg, type) {
    const el = document.getElementById('auth-message');
    el.textContent = msg;
    el.className = `message ${type}`;
}

function showAuthScreen() {
    document.getElementById('auth-screen').classList.add('active');
    document.getElementById('app-screen').classList.remove('active');
}

function showAppScreen() {
    document.getElementById('auth-screen').classList.remove('active');
    document.getElementById('app-screen').classList.add('active');
    const user = getUser();
    document.getElementById('user-name').textContent = user?.name || user?.email || 'User';
    loadDocuments();
}

// ============================================================
// NAVIGATION
// ============================================================
function showView(viewName) {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    // Find the clicked button
    const btns = document.querySelectorAll('.nav-btn');
    const viewMap = { chat: 0, documents: 1, upload: 2 };
    if (viewMap[viewName] !== undefined) btns[viewMap[viewName]].classList.add('active');
    document.getElementById(`${viewName}-view`).classList.add('active');
    if (viewName === 'documents') loadDocuments();
}

// ============================================================
// CHAT
// ============================================================
function askQuestion(question) {
    showView('chat');
    document.getElementById('chat-input').value = question;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const container = document.getElementById('chat-messages');
    const welcome = container.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    addBubble(message, 'user');
    input.value = '';

    const loader = document.createElement('div');
    loader.className = 'message-loading';
    loader.textContent = 'Thinking...';
    container.appendChild(loader);
    container.scrollTop = container.scrollHeight;

    try {
        const res = await apiCall('/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });
        loader.remove();
        if (res.ok) {
            const data = await res.json();
            addBubble(data.response || 'No response', 'assistant');
        } else {
            const err = await res.json().catch(() => ({}));
            addBubble(`Error: ${err.detail || 'Something went wrong'}`, 'assistant');
        }
    } catch (err) {
        loader.remove();
        addBubble(err.message || 'Connection error', 'assistant');
    }
}

function addBubble(text, sender) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message-bubble message-${sender}`;
    let html = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\[(\d+)\]/g, '<strong>[$1]</strong>')
        .replace(/\n/g, '<br>');
    div.innerHTML = html;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ============================================================
// DOCUMENTS (list with View / Delete buttons)
// ============================================================
async function loadDocuments() {
    try {
        const res = await apiCall('/documents/');
        if (!res.ok) return;
        const data = await res.json();
        const docs = data.documents || data || [];
        renderDocuments(docs);
    } catch {
        // silently fail
    }
}

function renderDocuments(docs) {
    const container = document.getElementById('documents-list');
    if (!docs.length) {
        container.innerHTML = '<p class="empty-state">No documents yet. Upload some to get started!</p>';
        return;
    }
    container.innerHTML = docs.map(doc => {
        const statusClass = doc.processed === 1 ? 'processed' : doc.processed === -1 ? 'failed' : 'processing';
        const statusText = doc.processed === 1 ? 'Processed' : doc.processed === -1 ? 'Failed' : 'Processing...';
        const isReady = doc.processed === 1;
        return `
        <div class="doc-card" data-id="${doc.id}">
            <h3>${doc.original_filename || doc.filename}</h3>
            <p>Type: <span class="doc-badge ${doc.doc_type}">${(doc.doc_type || '').toUpperCase()}</span></p>
            <p>Uploaded: ${new Date(doc.uploaded_at).toLocaleDateString()}</p>
            ${doc.year ? `<p>Year: ${doc.year}</p>` : ''}
            <span class="doc-badge ${statusClass}">${statusText}</span>
            <div class="doc-actions">
                <button class="btn-sm btn-view" onclick="viewDocContent(${doc.id}, '${(doc.original_filename || doc.filename).replace(/'/g, "\\'")}')"
                    ${isReady ? '' : 'disabled title="Wait for processing to finish"'}>
                    View Content
                </button>
                <button class="btn-sm btn-download" onclick="downloadDocWord(${doc.id})"
                    ${isReady ? '' : 'disabled'}>
                    Download Word
                </button>
                <button class="btn-sm btn-delete" onclick="deleteDocument(${doc.id}, '${(doc.original_filename || doc.filename).replace(/'/g, "\\'")}')">
                    Delete
                </button>
            </div>
        </div>`;
    }).join('');
}

// ── View document extracted content ───────────────────────────
async function viewDocContent(docId, filename) {
    _currentViewerDocId = docId;
    const overlay = document.getElementById('doc-viewer-overlay');
    const title = document.getElementById('doc-viewer-title');
    const content = document.getElementById('doc-viewer-content');

    title.textContent = filename || 'Document Content';
    content.innerHTML = '<p style="color:#888">Loading extracted text...</p>';
    overlay.style.display = 'flex';

    try {
        const res = await apiCall(`/documents/${docId}`);
        if (!res.ok) {
            content.innerHTML = '<p style="color:red">Failed to load document content.</p>';
            return;
        }
        const data = await res.json();
        if (data.extracted_text) {
            // Render extracted text with basic formatting
            const escaped = data.extracted_text
                .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                .replace(/\n/g, '<br>');
            content.innerHTML = `
                <div class="doc-meta">
                    <p><strong>Type:</strong> ${(data.doc_type || '').toUpperCase()}</p>
                    ${data.year ? `<p><strong>Year:</strong> ${data.year}</p>` : ''}
                    <p><strong>Uploaded:</strong> ${new Date(data.uploaded_at).toLocaleDateString()}</p>
                </div>
                <hr>
                <div class="doc-text">${escaped}</div>
            `;
        } else {
            content.innerHTML = '<p style="color:#888">No extracted text available yet. The document may still be processing.</p>';
        }
    } catch (err) {
        content.innerHTML = `<p style="color:red">Error: ${err.message}</p>`;
    }
}

function closeDocViewer(event) {
    document.getElementById('doc-viewer-overlay').style.display = 'none';
    _currentViewerDocId = null;
}

// ── Download as Word ──────────────────────────────────────────
async function downloadDocWord(docId) {
    const id = docId || _currentViewerDocId;
    if (!id) return;
    try {
        const res = await apiCall(`/documents/${id}/word`);
        if (!res.ok) {
            alert('Failed to generate Word document. Is the document processed?');
            return;
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `document_${id}.docx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert('Error downloading: ' + err.message);
    }
}

// ── Delete document ───────────────────────────────────────────
async function deleteDocument(docId, filename) {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    try {
        const res = await apiCall(`/documents/${docId}`, { method: 'DELETE' });
        if (res.ok || res.status === 204) {
            loadDocuments(); // refresh list
        } else {
            alert('Failed to delete document.');
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// ============================================================
// UPLOAD (with progress tracking — concurrent uploads supported)
// ============================================================
async function uploadDocument(type) {
    const fileInput = document.getElementById(`${type}-file`);
    const statusDiv = document.getElementById(`${type}-status`);
    const uploadBtn = document.getElementById(`${type}-upload-btn`);
    const progressContainer = document.getElementById(`${type}-progress-container`);
    const progressBar = document.getElementById(`${type}-progress-bar`);
    const progressText = document.getElementById(`${type}-progress-text`);
    const file = fileInput.files[0];

    if (!file) {
        statusDiv.textContent = 'Please select a file first';
        statusDiv.className = 'upload-status error';
        return;
    }

    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';
    statusDiv.textContent = 'Uploading file to server...';
    statusDiv.className = 'upload-status';
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressBar.className = 'progress-fill';
    progressText.textContent = 'Uploading...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await apiCall(`/documents/upload/${type}`, {
            method: 'POST',
            body: formData,
        });
        if (res.ok) {
            const data = await res.json();
            statusDiv.textContent = 'Uploaded! Processing...';
            statusDiv.className = 'upload-status success';
            fileInput.value = '';
            pollProgress(data.id, type, progressBar, progressText, statusDiv, uploadBtn);
        } else {
            const err = await res.json().catch(() => ({}));
            statusDiv.textContent = `Error: ${err.detail || 'Upload failed'}`;
            statusDiv.className = 'upload-status error';
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload';
            progressContainer.style.display = 'none';
        }
    } catch (err) {
        statusDiv.textContent = err.message || 'Upload failed. Check server.';
        statusDiv.className = 'upload-status error';
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload';
        progressContainer.style.display = 'none';
    }
}

async function pollProgress(docId, type, progressBar, progressText, statusDiv, uploadBtn) {
    let attempts = 0;
    const maxAttempts = 200;

    const poll = async () => {
        attempts++;
        if (attempts > maxAttempts) {
            statusDiv.textContent = 'Taking very long. Check Documents tab later.';
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload';
            return;
        }
        try {
            const res = await apiCall(`/documents/progress/${docId}`);
            if (!res.ok) { setTimeout(poll, 2000); return; }
            const data = await res.json();
            const pct = data.progress || 0;
            const msg = data.message || '';
            progressBar.style.width = `${pct}%`;
            progressText.textContent = `${pct}% — ${msg}`;

            if (data.status === 'done') {
                progressBar.style.width = '100%';
                progressBar.classList.add('done');
                progressText.textContent = '100% — Done!';
                statusDiv.textContent = 'Processing complete!';
                statusDiv.className = 'upload-status success';
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload';
                loadDocuments();
                return;
            }
            if (data.status === 'error') {
                progressBar.classList.add('error');
                progressText.textContent = `Failed: ${msg}`;
                statusDiv.textContent = 'Processing failed. Try re-uploading.';
                statusDiv.className = 'upload-status error';
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload';
                return;
            }
            setTimeout(poll, 1500);
        } catch {
            setTimeout(poll, 3000);
        }
    };
    setTimeout(poll, 1000);
}
