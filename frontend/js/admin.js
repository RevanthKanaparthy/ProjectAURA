async function loadDocs() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        alert("You must be logged in to view documents.");
        return;
    }

    const res = await fetch("http://127.0.0.1:8000/admin/docs", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });
    const data = await res.json();

    if (res.ok) {
        const list = document.getElementById("doc-list");
        list.innerHTML = "";

        data.forEach(doc => {
            const li = document.createElement("li");
            li.className = "doc-list-item";
            li.innerHTML = `<span>${doc.filename}</span>
              <button onclick="deleteDoc(${doc.id})">Delete</button>`;
            list.appendChild(li);
        });
    } else {
        alert(`Error loading documents: ${data.detail || "Unknown error"}`);
    }
}

async function deleteDoc(id) {
    const token = localStorage.getItem("access_token");
    if (!token) {
        alert("You must be logged in to delete documents.");
        return;
    }
    
    if (!confirm("Are you sure you want to delete this document?")) {
        return;
    }

    const res = await fetch(`http://127.0.0.1:8000/admin/docs/${id}`, {
        method: "DELETE",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (res.ok) {
        const data = await res.json();
        alert(data.message || "Document deleted");
        loadDocs();
    } else {
        const data = await res.json();
        alert(`Error deleting document: ${data.detail || "Unknown error"}`);
    }
}
