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
    const chatBox = document.getElementById("chat-box");
    const question = inputField.value.trim();

    if (!question) return;

    // 1. Add User Message
    appendMessage("user", question);
    inputField.value = "";

    // 2. Show Loading Indicator
    const loadingId = "loading-" + Date.now();
    appendMessage("bot", "Thinking...", loadingId);

    const token = localStorage.getItem("access_token");
    
    const headers = {
        "Content-Type": "application/json"
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    
    try {
        // 3. Send Request to Backend
        // Note: Using query parameter for question as per backend logs
        const res = await fetch(`http://127.0.0.1:8000/chat/ask?question=${encodeURIComponent(question)}`, {
            method: "POST",
            headers: headers
        });

        const data = await res.json();

        // 4. Remove Loading and Add Bot Response
        removeMessage(loadingId);

        if (res.ok) {
            appendMessage("bot", data.answer || data.response || "No response received.");
        } else {
            appendMessage("bot", "Error: " + (data.detail || "Could not fetch answer."));
        }

    } catch (error) {
        console.error("Chat error:", error);
        removeMessage(loadingId);
        appendMessage("bot", "Network error. Please check your connection.");
    }
}

function appendMessage(sender, text, id = null) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    
    msgDiv.classList.add("message", sender === "user" ? "user-message" : "bot-message");
    if (id) msgDiv.id = id;
    
    // Simple formatting for line breaks
    msgDiv.innerText = text;
    
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