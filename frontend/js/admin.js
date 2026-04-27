async function loadDocs() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        if(typeof showToast === "function") showToast("You must be logged in to view documents.", "error");
        return;
    }

    const res = await fetch(`${API_BASE}/admin/docs`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await parseApiResponse(res);

    if (res.ok) {
        const list = document.getElementById("doc-list");
        const emptyState = document.getElementById("doc-empty-state");
        
        // Clear all LI elements but preserve the empty state if it's there
        Array.from(list.children).forEach(child => {
            if (child.tagName.toLowerCase() === 'li') child.remove();
        });

        if (data.length === 0) {
            if (emptyState) emptyState.style.display = "flex";
        } else {
            if (emptyState) emptyState.style.display = "none";
            
            data.forEach(doc => {
                const li = document.createElement("li");
                li.innerHTML = `<span>${doc.filename}</span>
                  <button onclick="deleteDoc(${doc.id})">Delete</button>`;
                list.appendChild(li);
            });
        }
    } else {
        if(typeof showToast === "function") showToast(`Error loading documents: ${data.detail || "Unknown error"}`, "error");
    }
}

async function deleteDoc(id) {
    const token = localStorage.getItem("access_token");
    if (!token) {
        if(typeof showToast === "function") showToast("You must be logged in to delete documents.", "error");
        return;
    }
    
    if (!confirm("Are you sure you want to delete this document?")) {
        return;
    }

    const res = await fetch(`${API_BASE}/admin/docs/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (res.ok) {
        const data = await parseApiResponse(res);
        if(typeof showToast === "function") showToast(data.message || "Document deleted", "success");
        loadDocs();
    } else {
        const data = await parseApiResponse(res);
        if(typeof showToast === "function") showToast(`Error deleting document: ${data.detail || "Unknown error"}`, "error");
    }
}
