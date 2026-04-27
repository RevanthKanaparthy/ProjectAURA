document.addEventListener("DOMContentLoaded", () => {
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");

    if (chatInput) {
        chatInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener("click", sendMessage);
    }
});

async function sendMessage() {
    const inputField = document.getElementById("chat-input");
    const question = inputField.value.trim();

    if (!question) return;

    // 1. Add User Message
    appendMessage("user", question);
    inputField.value = "";

    // 2. Show Typing Indicator
    const loadingId = "loading-" + Date.now();
    appendMessage("bot", "", loadingId, true);

    const token = localStorage.getItem("access_token");
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    
    try {
        // 3. Send Request to Backend
        const res = await fetch(`${API_BASE}/chat/ask?question=${encodeURIComponent(question)}`, {
            method: "POST",
            headers: headers
        });

        const data = await parseApiResponse(res);

        // 4. Remove Loading and Add Bot Response
        removeMessage(loadingId);

        if (res.ok) {
            appendMessage("bot", data.answer || data.response || "No response received.");
        } else {
            const message = data.detail || data.message || "Could not fetch answer.";
            if (typeof showToast === "function") showToast(message, "error");
            appendMessage("bot", "Error: " + message);
        }

    } catch (error) {
        console.error("Chat error:", error);
        removeMessage(loadingId);
        if (typeof showToast === "function") showToast("Network error. Please check your connection.", "error");
        appendMessage("bot", "Network error. Please check your connection.");
    }
}

function appendMessage(sender, text, id = null, isTyping = false) {
    const chatBox = document.getElementById("chat-box");
    
    // Hide empty state if present
    const emptyState = document.getElementById("chat-empty-state");
    if (emptyState) emptyState.style.display = "none";

    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender === "user" ? "user-message" : "bot-message");
    if (id) msgDiv.id = id;
    
    if (isTyping) {
        msgDiv.innerHTML = `
            <div class="typing-indicator" style="background:transparent; box-shadow:none; padding:0;">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>`;
    } else {
        if (sender === "bot" && typeof marked !== "undefined") {
            msgDiv.innerHTML = marked.parse(text);
            // Apply syntax highlighting
            msgDiv.querySelectorAll('pre code').forEach((block) => {
                if (typeof hljs !== "undefined") hljs.highlightElement(block);
            });
        } else {
            msgDiv.innerText = text;
        }
    }
    
    chatBox.appendChild(msgDiv);
    
    // Auto-scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeMessage(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}
