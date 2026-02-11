/**
 * Carenova Frontend JavaScript
 * Handles WebSocket communication, UI updates, and chat flow
 */

// ============= STATE MANAGEMENT =============
const state = {
    sessionId: generateSessionId(),
    stage: 'initial', // initial | followup | results
    initialSymptoms: '',
    followupQuestions: [],
    followupAnswers: [],
    analysisResult: null,
    ws: null,
    isConnected: false
};

// ============= DOM ELEMENTS =============
const elements = {
    chatMessages: document.getElementById('chatMessages'),
    symptomInput: document.getElementById('symptomInput'),
    submitSymptoms: document.getElementById('submitSymptoms'),
    initialStage: document.getElementById('initialStage'),
    followupStage: document.getElementById('followupStage'),
    resultsStage: document.getElementById('resultsStage'),
    questionsContainer: document.getElementById('questionsContainer'),
    submitFollowups: document.getElementById('submitFollowups'),
    analysisResults: document.getElementById('analysisResults'),
    resetBtn: document.getElementById('resetBtn'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    connectionStatus: document.getElementById('connectionStatus')
};

// ============= UTILITIES =============
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function log(message) {
    console.log('[Carenova] ' + message);
}

function showMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤍';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    elements.chatMessages.appendChild(messageDiv);

    // Auto-scroll to bottom
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function setStage(stage) {
    log(`Changing stage to: ${stage}`);
    
    // Hide all stages
    elements.initialStage.classList.remove('active');
    elements.followupStage.classList.remove('active');
    elements.resultsStage.classList.remove('active');

    // Show target stage
    if (stage === 'initial') {
        elements.initialStage.classList.add('active');
        setTimeout(() => elements.symptomInput.focus(), 100);
    } else if (stage === 'followup') {
        elements.followupStage.classList.add('active');
    } else if (stage === 'results') {
        elements.resultsStage.classList.add('active');
    }

    state.stage = stage;
}

function showSpinner(show = true) {
    if (show) {
        elements.loadingSpinner.classList.remove('hidden');
    } else {
        elements.loadingSpinner.classList.add('hidden');
    }
}

function setConnectionStatus(connected) {
    state.isConnected = connected;
    const status = elements.connectionStatus;
    
    if (connected) {
        status.textContent = '● Connected';
        status.classList.remove('disconnected');
        status.classList.add('connected');
    } else {
        status.textContent = '● Disconnected';
        status.classList.remove('connected');
        status.classList.add('disconnected');
    }
}

// ============= WEBSOCKET CONNECTION =============
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    log(`Connecting to ${wsUrl}`);

    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
        log('WebSocket connected');
        setConnectionStatus(true);
    };

    state.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    state.ws.onerror = (error) => {
        log(`WebSocket error: ${error}`);
        showMessage('bot', '❌ <strong>Connection Error</strong><br>Failed to connect to server. Please check if the server is running.');
        setConnectionStatus(false);
    };

    state.ws.onclose = () => {
        log('WebSocket disconnected');
        setConnectionStatus(false);
    };
}

function handleWebSocketMessage(message) {
    const { type, content, data } = message;

    if (type === 'thinking') {
        showMessage('bot', content);
        showSpinner(true);
    } else if (type === 'analysis') {
        showSpinner(false);
        state.analysisResult = data;
        displayAnalysisResults(data);
        setStage('results');
    } else if (type === 'error') {
        showSpinner(false);
        showMessage('bot', `❌ <strong>Error</strong><br>${message.message}`);
    }
}

function sendAnalysisRequest() {
    if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
        showMessage('bot', '❌ Server disconnected. Refreshing page...');
        setTimeout(() => location.reload(), 2000);
        return;
    }

    const request = {
        session_id: state.sessionId,
        initial_symptoms: state.initialSymptoms,
        followup_answers: state.followupAnswers
    };

    log('Sending analysis request...');
    state.ws.send(JSON.stringify(request));
}

// ============= FOLLOW-UP QUESTIONS =============
async function loadFollowupQuestions(symptoms) {
    try {
        showSpinner(true);
        showMessage('bot', '📝 Generating follow-up questions...');

        const response = await fetch('/followup-questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symptoms })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        showSpinner(false);

        state.followupQuestions = data.questions;
        renderFollowupQuestions(data.questions);

        setStage('followup');

    } catch (error) {
        log(`Error loading followup questions: ${error}`);
        showSpinner(false);
        showMessage('bot', '❌ Failed to generate questions. Using defaults...');

        // Fallback questions
        state.followupQuestions = [
            "How long have you had these symptoms?",
            "Are the symptoms getting worse?",
            "Do you have fever, rash, or other symptoms?"
        ];
        renderFollowupQuestions(state.followupQuestions);
        setStage('followup');
    }
}

function renderFollowupQuestions(questions) {
    elements.questionsContainer.innerHTML = '';
    state.followupAnswers = [];

    questions.forEach((question, index) => {
        const questionItem = document.createElement('div');
        questionItem.className = 'question-item';

        const label = document.createElement('label');
        label.htmlFor = `answer_${index}`;
        label.textContent = question;

        const textarea = document.createElement('textarea');
        textarea.id = `answer_${index}`;
        textarea.placeholder = 'Your answer...';
        textarea.rows = 2;

        textarea.addEventListener('input', (e) => {
            state.followupAnswers[index] = e.target.value;
        });

        questionItem.appendChild(label);
        questionItem.appendChild(textarea);
        elements.questionsContainer.appendChild(questionItem);
    });

    // Show submit button
    elements.submitFollowups.style.display = 'block';
}

// ============= RESULTS DISPLAY =============
function displayAnalysisResults(result) {
    elements.analysisResults.innerHTML = '';

    // Severity badge
    const severityClass = result.severity.toLowerCase();
    const severityBadge = document.createElement('div');
    severityBadge.className = `severity-badge ${severityClass}`;
    severityBadge.innerHTML = `
        <strong>${result.severity}</strong> Severity
        <span style="margin-left: 1rem;">Confidence: ${result.confidence}</span>
    `;
    elements.analysisResults.appendChild(severityBadge);

    // Possible Conditions
    const conditionsSection = document.createElement('div');
    conditionsSection.className = 'result-section';
    conditionsSection.innerHTML = `
        <h3>🔍 Possible Conditions</h3>
        <ul>
            ${result.possible_conditions.map(c => `<li>${c}</li>`).join('')}
        </ul>
    `;
    elements.analysisResults.appendChild(conditionsSection);

    // Home Care Tips
    const tipsSection = document.createElement('div');
    tipsSection.className = 'result-section';
    tipsSection.innerHTML = `
        <h3>🏠 What May Help</h3>
        <ul>
            ${result.home_care_tips.map(tip => `<li>${tip}</li>`).join('')}
        </ul>
    `;
    elements.analysisResults.appendChild(tipsSection);

    // When to See Doctor
    const warningsSection = document.createElement('div');
    warningsSection.className = 'result-section';
    warningsSection.innerHTML = `
        <h3>🚨 See a Doctor If</h3>
        <ul>
            ${result.when_to_see_doctor.map(w => `<li>${w}</li>`).join('')}
        </ul>
    `;
    elements.analysisResults.appendChild(warningsSection);

    // Disclaimer
    const disclaimerDiv = document.createElement('div');
    disclaimerDiv.className = 'disclaimer';
    disclaimerDiv.innerHTML = `⚠️ ${result.disclaimer}`;
    elements.analysisResults.appendChild(disclaimerDiv);
}

// ============= EVENT LISTENERS =============
elements.submitSymptoms.addEventListener('click', () => {
    const symptoms = elements.symptomInput.value.trim();

    if (!symptoms || symptoms.length < 5) {
        alert('Please describe your symptoms in at least 5 characters.');
        return;
    }

    state.initialSymptoms = symptoms;
    showMessage('user', symptoms);
    showMessage('bot', 'Thank you for sharing 🤍<br><br><em>Let me generate some follow-up questions...</em>');

    loadFollowupQuestions(symptoms);
});

elements.submitFollowups.addEventListener('click', () => {
    const allAnswered = state.followupAnswers.every(a => a && a.trim());

    if (!allAnswered) {
        alert('Please answer all questions before proceeding.');
        return;
    }

    // Show user answers
    state.followupQuestions.forEach((q, i) => {
        showMessage('user', state.followupAnswers[i]);
    });

    // Send to WebSocket
    sendAnalysisRequest();
});

elements.resetBtn.addEventListener('click', () => {
    log('Resetting chat...');
    state.initialSymptoms = '';
    state.followupQuestions = [];
    state.followupAnswers = [];
    state.analysisResult = null;
    state.sessionId = generateSessionId();

    elements.chatMessages.innerHTML = `
        <div class="message bot-message">
            <div class="avatar">🤍</div>
            <div class="message-content">
                <p><strong>Hi, I'm Carenova</strong> 🤍</p>
                <p>Tell me how you're feeling, and I'll guide you step by step.</p>
            </div>
        </div>
    `;

    elements.symptomInput.value = '';
    elements.questionsContainer.innerHTML = '';
    elements.submitFollowups.style.display = 'none';
    elements.analysisResults.innerHTML = '';

    setStage('initial');
});

// ============= INITIALIZATION =============
document.addEventListener('DOMContentLoaded', () => {
    log('Initializing Carenova Frontend');
    connectWebSocket();
    setStage('initial');

    // Optional: Set up enter key for input
    elements.symptomInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            elements.submitSymptoms.click();
        }
    });
});

// ============= UNLOAD CLEANUP =============
window.addEventListener('beforeunload', () => {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.close();
    }
});
