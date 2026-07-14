/**
 * EduGenie — Frontend Application
 * Auth-aware: requires a valid session token in localStorage.
 * Sends Authorization: Bearer <token> on every API request.
 * History is scoped to the logged-in user via server-side token lookup.
 */

const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api'
    : '/api';

// ── Auth ─────────────────────────────────────────────────────────────────────

function getToken() {
    return localStorage.getItem('edugenie_token');
}

function getUser() {
    try {
        return JSON.parse(localStorage.getItem('edugenie_user') || 'null');
    } catch {
        return null;
    }
}

function clearSession() {
    localStorage.removeItem('edugenie_token');
    localStorage.removeItem('edugenie_user');
}

/** Redirect to /login unless we already have a token. */
function requireAuth() {
    if (!getToken()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

/** Build the Authorization header object used for every API call. */
function authHeaders(extra = {}) {
    const token = getToken();
    return {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...extra,
    };
}

/** Verify the stored token is still valid against /api/auth/me.
 *  If not, clear session and redirect to login. */
async function verifySession() {
    try {
        const resp = await fetch(API_BASE + '/auth/me', {
            headers: authHeaders(),
        });
        if (resp.status === 401) {
            clearSession();
            window.location.href = '/login';
            return false;
        }
        return true;
    } catch {
        // Network error — let the user stay but don't crash
        return true;
    }
}

async function handleLogout() {
    try {
        await fetch(API_BASE + '/auth/logout', {
            method: 'POST',
            headers: authHeaders(),
        });
    } catch { /* ignore network errors on logout */ }
    clearSession();
    window.location.href = '/login';
}

// ── State ────────────────────────────────────────────────────────────────────

let currentTask = 'ask';
let isLoading = false;

// ── DOM References ───────────────────────────────────────────────────────────

const elements = {
    navItems:         () => document.querySelectorAll('.nav-item[data-task]'),
    contentTitle:     () => document.getElementById('content-title'),
    contentDesc:      () => document.getElementById('content-desc'),
    formContainer:    () => document.getElementById('form-container'),
    resultsPanel:     () => document.getElementById('results-panel'),
    resultsHeader:    () => document.getElementById('results-header'),
    resultsBody:      () => document.getElementById('results-body'),
    loadingIndicator: () => document.getElementById('loading-indicator'),
    userName:         () => document.getElementById('user-name'),
    userEmail:        () => document.getElementById('user-email'),
    userAvatar:       () => document.getElementById('user-avatar'),
};

// ── Task Configurations ──────────────────────────────────────────────────────

const TASKS = {
    ask: {
        title: 'Ask a Question',
        desc: 'Get a clear, complete educational answer to any question.',
        fields: [
            { name: 'question', label: 'Your Question', type: 'textarea',
              placeholder: 'e.g. How does photosynthesis work?' },
        ],
        endpoint: '/ask',
        method: 'POST',
        buildPayload: (form) => ({ question: form.question.value.trim() }),
        renderResult: (data) => data.answer,
    },
    explain: {
        title: 'Explain a Concept',
        desc: 'Get a structured breakdown — definition, relevance, examples, common pitfalls.',
        fields: [
            { name: 'topic', label: 'Topic', type: 'text',
              placeholder: 'e.g. Quantum Entanglement' },
        ],
        endpoint: '/explain',
        method: 'POST',
        buildPayload: (form) => ({ topic: form.topic.value.trim() }),
        renderResult: (data) => data.explanation,
    },
    quiz: {
        title: 'Generate a Quiz',
        desc: 'Create a multiple-choice quiz to test your knowledge.',
        fields: [
            { name: 'text', label: 'Topic', type: 'text',
              placeholder: 'e.g. World War II' },
            { name: 'num_questions', label: 'Questions', type: 'number',
              placeholder: '5', small: true, value: '5' },
        ],
        endpoint: '/quiz',
        method: 'POST',
        buildPayload: (form) => ({
            text: form.text.value.trim(),
            num_questions: parseInt(form.num_questions.value, 10) || 5,
        }),
        renderResult: (data) => renderQuiz(data.questions),
    },
    summarize: {
        title: 'Summarize Text',
        desc: 'Condense long material into key points for quick review.',
        fields: [
            { name: 'text', label: 'Text to Summarize', type: 'textarea',
              placeholder: 'Paste your study material, article, or notes here…' },
        ],
        endpoint: '/summarize',
        method: 'POST',
        buildPayload: (form) => ({ text: form.text.value.trim() }),
        renderResult: (data) => data.summary,
    },
    recommend: {
        title: 'Learning Path',
        desc: 'Get a beginner → intermediate → advanced roadmap for any topic.',
        fields: [
            { name: 'topic', label: 'What do you want to learn?', type: 'text',
              placeholder: 'e.g. Machine Learning' },
        ],
        endpoint: '/recommend',
        method: 'POST',
        buildPayload: (form) => ({ topic: form.topic.value.trim() }),
        renderResult: (data) => renderLearningPath(data.learning_path),
    },
    history: {
        title: 'My History',
        desc: 'Your recent interactions with EduGenie.',
        fields: [],
        endpoint: '/history',
        method: 'GET',
        buildPayload: () => null,
        renderResult: (data) => renderHistory(data.history),
    },
};

// ── Initialization ───────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;

    // Populate user info in sidebar
    const user = getUser();
    if (user) {
        const nameEl   = elements.userName();
        const emailEl  = elements.userEmail();
        const avatarEl = elements.userAvatar();
        if (nameEl)   nameEl.textContent  = user.username || 'User';
        if (emailEl)  emailEl.textContent = user.email    || '';
        if (avatarEl) avatarEl.textContent = (user.username || 'U')[0].toUpperCase();
    }

    bindNavigation();
    switchTask('ask');

    // Background session check — redirect to login if token expired
    verifySession();
});

function bindNavigation() {
    elements.navItems().forEach((item) => {
        item.addEventListener('click', () => {
            if (!isLoading) switchTask(item.dataset.task);
        });
    });
}

// ── Task Switching ───────────────────────────────────────────────────────────

function switchTask(taskKey) {
    const task = TASKS[taskKey];
    if (!task) return;
    currentTask = taskKey;

    elements.navItems().forEach((item) => {
        item.classList.toggle('active', item.dataset.task === taskKey);
    });

    elements.contentTitle().textContent = task.title;
    elements.contentDesc().textContent  = task.desc;

    const formContainer = elements.formContainer();
    formContainer.innerHTML = '';

    if (task.fields.length > 0) {
        const form = document.createElement('form');
        form.id = 'task-form';
        form.addEventListener('submit', handleSubmit);

        const hasSmall = task.fields.some(f => f.small);
        let rowDiv = null;
        if (hasSmall) {
            rowDiv = document.createElement('div');
            rowDiv.className = 'input-row';
        }

        task.fields.forEach((field) => {
            const group = document.createElement('div');
            group.className = 'input-group' + (field.small ? ' small' : '');

            const label = document.createElement('label');
            label.className = 'input-label';
            label.textContent = field.label;
            label.setAttribute('for', field.name);

            let input;
            if (field.type === 'textarea') {
                input = document.createElement('textarea');
            } else {
                input = document.createElement('input');
                input.type = field.type;
            }
            input.className   = 'input-field';
            input.name        = field.name;
            input.id          = field.name;
            input.placeholder = field.placeholder || '';
            if (field.value !== undefined) input.value = field.value;
            if (field.type === 'number') { input.min = '1'; input.max = '20'; }
            input.required = true;

            group.appendChild(label);
            group.appendChild(input);
            (rowDiv || form).appendChild(group);
        });

        if (rowDiv) form.appendChild(rowDiv);

        const btn = document.createElement('button');
        btn.type = 'submit';
        btn.className = 'btn-submit';
        btn.id = 'submit-btn';
        btn.innerHTML = '<span>Generate</span>';
        form.appendChild(btn);
        formContainer.appendChild(form);
    }

    clearResults();
    if (taskKey === 'history') fetchHistory();
}

// ── Form Submission ──────────────────────────────────────────────────────────

async function handleSubmit(e) {
    e.preventDefault();
    if (isLoading) return;
    const task = TASKS[currentTask];
    await makeRequest(task.endpoint, task.buildPayload(e.target), task.method === 'GET');
}

async function fetchHistory() {
    await makeRequest('/history', null, true);
}

async function makeRequest(endpoint, payload, isGet = false) {
    const task = TASKS[currentTask];
    setLoading(true);
    clearResults();

    try {
        const url = API_BASE + endpoint;
        const options = isGet
            ? { method: 'GET', headers: authHeaders() }
            : {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify(payload),
              };

        const response = await fetch(url, options);

        // If 401, the session expired — send to login
        if (response.status === 401) {
            clearSession();
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error || errData.detail || `Server error (${response.status})`);
        }

        const data = await response.json();
        displayResult(task.renderResult(data));

    } catch (error) {
        displayError(error.message);
    } finally {
        setLoading(false);
    }
}

// ── Result Rendering ─────────────────────────────────────────────────────────

function displayResult(content) {
    const panel  = elements.resultsPanel();
    const body   = elements.resultsBody();
    const header = elements.resultsHeader();

    panel.style.display = 'block';
    header.textContent  = TASKS[currentTask].title + ' — Result';

    if (typeof content === 'string') {
        body.classList.add('text-content');
        body.textContent = content;
    } else {
        body.classList.remove('text-content');
        body.innerHTML = '';
        body.appendChild(content);
    }
}

function displayError(message) {
    const panel  = elements.resultsPanel();
    const body   = elements.resultsBody();
    const header = elements.resultsHeader();

    panel.style.display = 'block';
    header.textContent  = 'Error';
    body.classList.remove('text-content');
    body.innerHTML = `<div class="error-message">${escapeHtml(message)}</div>`;
}

function clearResults() {
    const panel = elements.resultsPanel();
    const body  = elements.resultsBody();
    panel.style.display = 'none';
    body.classList.remove('text-content');
    body.innerHTML = '';
}

function setLoading(loading) {
    isLoading = loading;
    const indicator = elements.loadingIndicator();
    const btn = document.getElementById('submit-btn');
    if (indicator) indicator.classList.toggle('active', loading);
    if (btn) {
        btn.disabled = loading;
        const span = btn.querySelector('span');
        if (span) span.textContent = loading ? 'Thinking…' : 'Generate';
    }
}

// ── Quiz Renderer ────────────────────────────────────────────────────────────

function renderQuiz(questions) {
    const container = document.createElement('div');

    if (!Array.isArray(questions) || questions.length === 0) {
        container.textContent = 'No quiz questions were generated. Try again.';
        return container;
    }

    questions.forEach((q, i) => {
        const qDiv = document.createElement('div');
        qDiv.className = 'quiz-question';

        const num = document.createElement('div');
        num.className = 'quiz-question-number';
        num.textContent = `Question ${i + 1} of ${questions.length}`;

        const text = document.createElement('div');
        text.className = 'quiz-question-text';
        text.textContent = q.question;

        qDiv.appendChild(num);
        qDiv.appendChild(text);

        if (Array.isArray(q.options)) {
            q.options.forEach((opt) => {
                const optDiv = document.createElement('div');
                optDiv.className = 'quiz-option';
                optDiv.textContent = opt;
                optDiv.addEventListener('click', () => {
                    const siblings = qDiv.querySelectorAll('.quiz-option');
                    siblings.forEach((s) => {
                        const letter = s.textContent.charAt(0);
                        if (letter === q.correct_answer) s.classList.add('correct');
                        else if (s === optDiv)           s.classList.add('incorrect');
                        s.style.pointerEvents = 'none';
                    });
                    if (!qDiv.querySelector('.quiz-answer-reveal')) {
                        const reveal = document.createElement('div');
                        reveal.className = 'quiz-answer-reveal';
                        reveal.textContent = `Correct answer: ${q.correct_answer}`;
                        qDiv.appendChild(reveal);
                    }
                });
                qDiv.appendChild(optDiv);
            });
        }
        container.appendChild(qDiv);
    });
    return container;
}

// ── Learning Path Renderer ───────────────────────────────────────────────────

function renderLearningPath(path) {
    const container = document.createElement('div');
    container.className = 'learning-path';

    if (!path || typeof path !== 'object') {
        container.textContent = String(path);
        return container;
    }

    // Fallback: model returned raw text instead of JSON
    if (path.raw_response) {
        const pre = document.createElement('pre');
        pre.className = 'raw-response';
        pre.textContent = path.raw_response;
        container.appendChild(pre);
        return container;
    }

    ['beginner', 'intermediate', 'advanced'].forEach((level) => {
        const data = path[level];
        if (!data) return;

        const div = document.createElement('div');
        div.className = `path-level ${level}`;

        const title = document.createElement('div');
        title.className = 'path-level-title';
        title.textContent = level.charAt(0).toUpperCase() + level.slice(1);
        div.appendChild(title);

        if (data.description) {
            const desc = document.createElement('div');
            desc.className = 'path-level-desc';
            desc.textContent = data.description;
            div.appendChild(desc);
        }

        [['Resources', data.resources], ['Projects', data.projects]].forEach(([label, items]) => {
            if (!Array.isArray(items) || !items.length) return;
            const sTitle = document.createElement('div');
            sTitle.className = 'path-section-title';
            sTitle.textContent = label;
            div.appendChild(sTitle);
            const ul = document.createElement('ul');
            ul.className = 'path-list';
            items.forEach((item) => {
                const li = document.createElement('li');
                li.textContent = item;
                ul.appendChild(li);
            });
            div.appendChild(ul);
        });

        if (data.duration) {
            const dur = document.createElement('div');
            dur.className = 'path-duration';
            dur.textContent = `Estimated time: ${data.duration}`;
            div.appendChild(dur);
        }

        container.appendChild(div);
    });

    return container;
}

// ── History Renderer ─────────────────────────────────────────────────────────

function renderHistory(records) {
    const container = document.createElement('div');

    if (!Array.isArray(records) || records.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'empty-state';
        empty.innerHTML = '<h3>No history yet</h3><p>Your interactions will appear here.</p>';
        container.appendChild(empty);
        return container;
    }

    const typeLabels = {
        ask: '💬 Ask', explain: '📖 Explain',
        quiz: '📝 Quiz', summarize: '✂️ Summarize', recommend: '🗺️ Path',
    };

    records.forEach((record) => {
        const item = document.createElement('div');
        item.className = 'history-item';

        const meta = document.createElement('div');
        meta.className = 'history-meta';

        const typeTag = document.createElement('span');
        typeTag.className = 'history-type';
        typeTag.textContent = typeLabels[record.interaction_type] || record.interaction_type;

        const dateTag = document.createElement('span');
        dateTag.className = 'history-date';
        dateTag.textContent = new Date(record.created_at).toLocaleString();

        meta.appendChild(typeTag);
        meta.appendChild(dateTag);

        const question = document.createElement('div');
        question.className = 'history-question';
        question.textContent = record.question;

        item.appendChild(meta);
        item.appendChild(question);
        container.appendChild(item);
    });

    return container;
}

// ── Utilities ────────────────────────────────────────────────────────────────

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
