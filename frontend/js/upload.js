async function upload() {
    const fileInput = document.getElementById("file");
    const uploadBtn = document.getElementById("upload-btn") || document.querySelector("button[onclick='upload()']");
    const statusMsg = document.getElementById("status-msg"); // Optional: Add <p id="status-msg"></p> in HTML

    if (!fileInput || fileInput.files.length === 0) {
        alert("Please select a file to upload.");
        return;
    }

    const file = fileInput.files[0];
    const allowedExtensions = [".pdf", ".txt", ".md", ".xlsx", ".xls"];
    const fileExtension = "." + file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(fileExtension)) {
        alert("Invalid file type. Allowed: PDF, TXT, MD, Excel.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("access_token");
    if (!token) {
        alert("You must be logged in to upload files.");
        window.location.href = "login.html";
        return;
    }

    // UI Feedback: Disable button and show loading state
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerText = "Uploading...";
    }
    if (statusMsg) {
        statusMsg.innerText = "Uploading document...";
        statusMsg.style.color = "blue";
    }

    try {
        const res = await fetch("http://127.0.0.1:8000/upload/", {
            method: "POST",
            body: formData,
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await res.json();

        if (res.ok) {
            if (statusMsg) {
                statusMsg.innerText = "Success: " + (data.message || "File uploaded.");
                statusMsg.style.color = "green";
            }
            alert(data.message || "File uploaded successfully!");
            // Optionally, refresh the document list if the admin is viewing it
            if (typeof loadDocs === "function") {
                loadDocs();
            }
            fileInput.value = ""; // Clear the input
        } else {
            throw new Error(data.detail || "Unknown error");
        }
    } catch (error) {
        console.error("Upload error:", error);
        if (statusMsg) {
            statusMsg.innerText = "Error: " + error.message;
            statusMsg.style.color = "red";
        }
        alert("Upload failed: " + error.message);
    } finally {
        // Reset button state
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerText = "Upload";
        }
    }
}
