document.addEventListener('DOMContentLoaded', () => {
    console.log("SANAD SCRIPT LOADED");

    // ==============================
    // 1. Theme Persistence (Dark / Light Mode)
    // ==============================
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const savedTheme = localStorage.getItem('sanad_theme');

    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            const isLight = document.body.classList.contains('light-theme');
            localStorage.setItem('sanad_theme', isLight ? 'light' : 'dark');
        });
    }

    // ==============================
    // 2. Category Buttons Selection
    // ==============================
    const categoryButtons = document.querySelectorAll('.hero-buttons .btn, .category-pill');
    categoryButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.classList.contains('category-pill')) {
                btn.classList.toggle('selected');
            } else {
                categoryButtons.forEach((button) => {
                    button.style.borderColor = "var(--border-color)";
                });
                btn.style.borderColor = "var(--accent-purple)";
            }
        });
    });

    // ==============================
    // 3. Wizard Steps Navigation 
    // ==============================
    let currentStep = 1;
    const steps = document.querySelectorAll('.wizard-step-content');
    const stepIndicators = document.querySelectorAll('.step-item');

    function updateWizard() {
        steps.forEach((step, index) => {
            step.style.display = (index + 1 === currentStep) ? 'block' : 'none';
        });

        stepIndicators.forEach((indicator, index) => {
            if (index + 1 === currentStep) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }

    const nextButtons = document.querySelectorAll('.next-btn');
    nextButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (currentStep < steps.length) {
                currentStep++;
                updateWizard();
            }
        });
    });

    const prevButtons = document.querySelectorAll('.prev-btn');
    prevButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (currentStep > 1) {
                currentStep--;
                updateWizard();
            }
        });
    });

    // ==============================
    // 4. Create Project Form Submit State
    // ==============================
    const createProjectForm = document.getElementById("createProjectForm");
    if (createProjectForm) {
        createProjectForm.addEventListener("submit", () => {
            const submitButton = createProjectForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerText = "Creating...";
            }
        });
    }

    // ==============================
    // 5. AI Chatbot UI Event Listeners
    // ==============================
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');

    if (sendBtn && chatInput) {
        sendBtn.addEventListener('click', sendAiMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendAiMessage();
            }
        });
    }
});

// ==============================
// Global Helper Functions
// ==============================

// إغلاق الـ Modal عند الضغط خارجها
window.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
        e.target.classList.remove("active");
    }
});

function handleAuthSubmit(e) {
    e.preventDefault();
    if (typeof closeModal === 'function') {
        closeModal("authModal");
    }
}

// Function to toggle chat window visibility
function toggleChatWindow() {
    const chatWindow = document.getElementById('ai-chat-window');
    if (chatWindow) {
        chatWindow.classList.toggle('chat-window-hidden');
    }
}

// Send AI Message Function
function sendAiMessage() {
    const inputField = document.getElementById('chat-input');
    if (!inputField) return;
    
    const message = inputField.value.trim();
    if (!message) return;

    const chatLogs = document.getElementById('chat-logs');
    if (!chatLogs) return;
    
    // 1. Display user message
    chatLogs.innerHTML += `<div class="user-message" style="background-color: var(--accent-purple, #007bff); color: white; padding: 8px 12px; border-radius: 8px; max-width: 80%; align-self: flex-end; margin: 5px 0;">${message}</div>`;
    inputField.value = '';
    chatLogs.scrollTop = chatLogs.scrollHeight;

    // 2. Loading state
    const loadingId = 'loading-' + Date.now();
    chatLogs.innerHTML += `<div id="${loadingId}" class="ai-message" style="background-color: var(--bg-card-solid, #e2e8f0); color: var(--text-primary, #333); padding: 8px 12px; border-radius: 8px; max-width: 80%; align-self: flex-start; margin: 5px 0;">Thinking...</div>`;
    chatLogs.scrollTop = chatLogs.scrollHeight;

    // 3. Send to Django Endpoint (/api/chatbot/)
    fetch('/api/chatbot/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') || ''
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) {
            loadingElem.innerHTML = data.reply || 'No response received.';
        }
        chatLogs.scrollTop = chatLogs.scrollHeight;
    })
    .catch(error => {
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) {
            loadingElem.remove();
        }
        chatLogs.innerHTML += `<div class="ai-message" style="color: #e74c3c; padding: 8px 12px; margin: 5px 0;">Connection error: ${error.message}</div>`;
        chatLogs.scrollTop = chatLogs.scrollHeight;
    });
}

// Django's CSRF protection retrieval function
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}