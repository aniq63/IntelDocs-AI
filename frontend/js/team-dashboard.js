(() => {
  if (!Session.isCompanyAuthed()) {
    window.location.href = "index.html";
    return;
  }
  if (!Session.isTeamAuthed()) {
    window.location.href = "company-dashboard.html";
    return;
  }

  const teamName = Session.teamName();
  document.getElementById("teamNameLabel").textContent = teamName;
  document.getElementById("teamInitial").textContent = (teamName[0] || "T").toUpperCase();
  document.getElementById("statTeamName").textContent = teamName;
  document.getElementById("companyOfTeamLabel").textContent = `under ${Session.companyName()}`;

  // ---------------- View switching ----------------
  const views = document.querySelectorAll(".view");
  const links = document.querySelectorAll("[data-view]");
  function goToView(name) {
    views.forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
    document.querySelectorAll(".sidebar-link").forEach((l) => l.classList.toggle("active", l.dataset.view === name));
    if (name === "documents") loadDocs();
    if (name === "chat") loadSessions();
  }
  links.forEach((l) => l.addEventListener("click", () => goToView(l.dataset.view)));

  // ---------------- Logout (team only) ----------------
  document.getElementById("logoutBtn").addEventListener("click", async () => {
    try { await Api.teamLogout(); } catch (e) { /* proceed regardless */ }
    Session.clearTeam();
    window.location.href = "company-dashboard.html";
  });

  // ---------------- Overview ----------------
  async function loadOverview() {
    try {
      const overview = await Api.teamOverview();
      document.getElementById("statDocs").textContent = Api.pick(overview, ["total_documents", "documents_count", "document_count"], "—");
    } catch (err) {
      toast(err.message, "error");
    }
    try {
      const docs = await Api.teamDocsAll();
      renderDocsTable((docs || []).slice(0, 5), document.getElementById("overviewDocsTable"));
    } catch (err) {
      document.getElementById("overviewDocsTable").innerHTML = emptyState("Couldn't load documents", err.message);
    }
  }

  // ---------------- Documents ----------------
  async function loadDocs() {
    const el = document.getElementById("teamDocsTable");
    try {
      const docs = await Api.teamDocsList();
      renderDocsTable(docs, el, true);
    } catch (err) {
      el.innerHTML = emptyState("Couldn't load documents", err.message);
    }
  }
  document.getElementById("refreshTeamDocs").addEventListener("click", loadDocs);

  function renderDocsTable(docs, container, withActions) {
    if (!docs || docs.length === 0) {
      container.innerHTML = emptyState("No documents yet", "Upload your first document.");
      return;
    }
    const rows = docs.map((d) => {
      const name = Api.pick(d, ["name", "source", "filename", "title"], "document");
      const uploaded = Api.pick(d, ["created_at", "uploaded_at", "timestamp"], null);
      return `
        <tr>
          <td><strong>${escapeHtml(name)}</strong></td>
          <td class="muted">${uploaded ? formatDate(uploaded) : "—"}</td>
          ${withActions ? `<td><button class="btn btn-danger btn-sm" data-doc-delete="${escapeHtml(name)}">Delete</button></td>` : ""}
        </tr>`;
    }).join("");
    container.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Name</th><th>Uploaded</th>${withActions ? "<th></th>" : ""}</tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    if (withActions) {
      container.querySelectorAll("[data-doc-delete]").forEach((btn) =>
        btn.addEventListener("click", async () => {
          if (!confirm(`Delete "${btn.dataset.docDelete}"?`)) return;
          try {
            await Api.teamDocDelete(btn.dataset.docDelete);
            toast("Document deleted");
            loadDocs();
          } catch (err) {
            toast(err.message, "error");
          }
        }));
    }
  }

  const fileInput = document.getElementById("teamFileInput");
  const uploadDrop = document.getElementById("uploadDrop");
  fileInput.addEventListener("change", () => handleUpload(fileInput.files[0]));
  ["dragover", "dragleave", "drop"].forEach((evt) => {
    uploadDrop.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadDrop.classList.toggle("dragover", evt === "dragover");
      if (evt === "drop" && e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]);
    });
  });

  async function handleUpload(file) {
    if (!file) return;
    document.getElementById("uploadFileName").textContent = `Uploading ${file.name}…`;
    try {
      await Api.teamDocsUpload(file);
      toast(`"${file.name}" uploaded`);
      document.getElementById("uploadFileName").textContent = "PDF, DOCX, TXT — one at a time";
      loadDocs();
    } catch (err) {
      toast(err.message, "error");
      document.getElementById("uploadFileName").textContent = "PDF, DOCX, TXT — one at a time";
    }
  }

  // ---------------- Chat ----------------
  let currentSessionId = null;

  async function loadSessions() {
    const el = document.getElementById("sessionsList");
    try {
      const sessions = await Api.teamChatSessions();
      if (!sessions || sessions.length === 0) {
        el.innerHTML = `<div class="empty-state"><p>No sessions yet</p></div>`;
        return;
      }
      el.innerHTML = sessions.map((s) => {
        const id = Api.pick(s, ["id", "session_id"]);
        const title = Api.pick(s, ["title", "name"], `Session ${id}`);
        return `<button class="chat-session-item" data-session="${id}">${escapeHtml(title)}</button>`;
      }).join("");
      el.querySelectorAll("[data-session]").forEach((btn) =>
        btn.addEventListener("click", () => openSession(btn.dataset.session)));
    } catch (err) {
      el.innerHTML = emptyState("Couldn't load sessions", err.message);
    }
  }

  async function openSession(sessionId) {
    currentSessionId = sessionId;
    document.querySelectorAll(".chat-session-item").forEach((b) => b.classList.toggle("active", b.dataset.session === String(sessionId)));
    const box = document.getElementById("chatMessages");
    box.innerHTML = `<div class="empty-state"><p>Loading…</p></div>`;
    try {
      const messages = await Api.teamChatMessages(sessionId);
      renderMessages(messages);
    } catch (err) {
      toast(err.message, "error");
    }
  }

  function renderMessages(messages) {
    const box = document.getElementById("chatMessages");
    if (!messages || messages.length === 0) {
      box.innerHTML = `<div class="empty-state"><p>No messages yet</p></div>`;
      return;
    }
    box.innerHTML = messages.map((m) => {
      const role = Api.pick(m, ["role"], null);
      if (role) {
        const isUser = role === "user";
        return `<div class="chat-bubble ${isUser ? "user" : "ai"}">${escapeHtml(Api.pick(m, ["content", "text", "message"], ""))}</div>`;
      }
      const q = Api.pick(m, ["question"], null);
      const a = Api.pick(m, ["answer"], null);
      let out = "";
      if (q) out += `<div class="chat-bubble user">${escapeHtml(q)}</div>`;
      if (a) out += `<div class="chat-bubble ai">${escapeHtml(a)}</div>`;
      return out;
    }).join("");
    box.scrollTop = box.scrollHeight;
  }

  document.getElementById("newChatBtn").addEventListener("click", () => {
    currentSessionId = null;
    document.querySelectorAll(".chat-session-item").forEach((b) => b.classList.remove("active"));
    document.getElementById("chatMessages").innerHTML = `<div class="empty-state"><p>Start a new conversation</p></div>`;
  });

  async function sendMessage() {
    const input = document.getElementById("chatInput");
    const question = input.value.trim();
    if (!question) return;
    input.value = "";

    const box = document.getElementById("chatMessages");
    if (box.querySelector(".empty-state")) box.innerHTML = "";
    box.innerHTML += `<div class="chat-bubble user">${escapeHtml(question)}</div>`;
    box.innerHTML += `<div class="chat-bubble ai" id="pendingBubble"><span class="spinner"></span></div>`;
    box.scrollTop = box.scrollHeight;

    try {
      const res = await Api.teamChatAsk(question, currentSessionId);
      currentSessionId = Api.pick(res, ["session_id"], currentSessionId);
      const answer = Api.pick(res, ["answer", "response", "message"], "(no answer returned)");
      const pending = document.getElementById("pendingBubble");
      if (pending) pending.textContent = answer;
      loadSessions();
    } catch (err) {
      const pending = document.getElementById("pendingBubble");
      if (pending) { pending.textContent = err.message; pending.style.color = "#c8392f"; }
    }
    box.scrollTop = box.scrollHeight;
  }

  document.getElementById("chatSendBtn").addEventListener("click", sendMessage);
  document.getElementById("chatInput").addEventListener("keydown", (e) => { if (e.key === "Enter") sendMessage(); });

  // ---------------- Helpers ----------------
  function emptyState(title, sub) {
    return `<div class="empty-state"><p>${escapeHtml(title)}</p><span>${escapeHtml(sub || "")}</span></div>`;
  }

  loadOverview();
})();
