async function upload() {
    const fileInput = document.getElementById("file");
    const uploadBtn = document.getElementById("upload-btn") || document.querySelector("button[onclick='upload()']");
    const statusMsg = document.getElementById("status-msg"); 

    if (!fileInput || fileInput.files.length === 0) {
        if (typeof showToast === "function") showToast("Please select a file to upload.", "error");
        return;
    }

    const file = fileInput.files[0];
    const allowedExtensions = [".pdf", ".txt", ".md", ".xlsx", ".xls"];
    const fileExtension = "." + file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(fileExtension)) {
        if (typeof showToast === "function") showToast("Invalid file type. Allowed: PDF, TXT, MD, Excel.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("access_token");
    if (!token) {
        if (typeof showToast === "function") showToast("You must be logged in to upload files.", "error");
        window.location.href = "login.html";
        return;
    }

    // UI Feedback: Disable button and show loading state
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = `
            <span>Uploading...</span>
            <div class="typing-indicator" style="background:transparent; box-shadow:none; padding:0; margin-left: 5px;">
                <div class="typing-dot" style="background: white"></div>
                <div class="typing-dot" style="background: white"></div>
                <div class="typing-dot" style="background: white"></div>
            </div>`;
    }
    if (statusMsg) {
        statusMsg.innerText = "Processing document in the backend...";
        statusMsg.style.color = "var(--text-muted)";
    }

    try {
        const res = await fetch(`${API_BASE}/upload/`, {
            method: "POST",
            body: formData,
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await parseApiResponse(res);

        if (res.ok) {
            if (statusMsg) {
                statusMsg.innerText = "";
            }
            if (typeof showToast === "function") showToast(data.message || "File uploaded successfully!", "success");
            
            // Optionally, refresh the document list if the admin is viewing it
            if (typeof loadDocs === "function") {
                loadDocs();
            }
            fileInput.value = ""; // Clear the input
            document.getElementById('file-name-display').textContent = 'Select a file to upload';
        } else {
            throw new Error(data.detail || "Unknown error");
        }
    } catch (error) {
        console.error("Upload error:", error);
        if (statusMsg) {
            statusMsg.innerText = "";
        }
        if (typeof showToast === "function") showToast("Upload failed: " + error.message, "error");
    } finally {
        // Reset button state
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerText = "Upload Document";
        }
    }
}
