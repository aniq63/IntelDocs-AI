(() => {
  if (!Session.isCompanyAuthed()) {
    window.location.href = "index.html";
    return;
  }

  const companyName = Session.companyName();
  document.getElementById("companyNameLabel").textContent = companyName;
  document.getElementById("companyInitial").textContent = (companyName[0] || "C").toUpperCase();
  document.getElementById("statCompanyName").textContent = companyName;

  // ---------------- View switching ----------------
  const views = document.querySelectorAll(".view");
  const links = document.querySelectorAll("[data-view]");
  function goToView(name) {
    views.forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
    document.querySelectorAll(".sidebar-link").forEach((l) => l.classList.toggle("active", l.dataset.view === name));
    if (name === "teams") loadTeams();
    if (name === "documents") loadCompanyDocs();
    if (name === "chat") loadSessions();
  }
  links.forEach((l) => l.addEventListener("click", () => goToView(l.dataset.view)));

  // ---------------- Logout ----------------
  document.getElementById("logoutBtn").addEventListener("click", async () => {
    try { await Api.companyLogout(); } catch (e) { /* proceed regardless */ }
    Session.clearCompany();
    window.location.href = "index.html";
  });

  // ---------------- Overview ----------------
  async function loadOverview() {
    try {
      const overview = await Api.companyOverview();
      document.getElementById("statTeams").textContent = Api.pick(overview, ["total_teams", "teams_count", "team_count"], "—");
      document.getElementById("statDocs").textContent = Api.pick(overview, ["total_documents", "documents_count", "document_count"], "—");
    } catch (err) {
      toast(err.message, "error");
    }
    try {
      const teams = await Api.companyTeams();
      renderTeamsTable(teams, document.getElementById("overviewTeamsTable"), true);
    } catch (err) {
      document.getElementById("overviewTeamsTable").innerHTML = emptyState("Couldn't load teams", err.message);
    }
  }

  // ---------------- Teams ----------------
  async function loadTeams() {
    const el = document.getElementById("teamsTable");
    try {
      const teams = await Api.teamList();
      renderTeamsTable(teams, el, false);
    } catch (err) {
      el.innerHTML = emptyState("Couldn't load teams", err.message);
    }
  }

  function renderTeamsTable(teams, container, compact) {
    if (!teams || teams.length === 0) {
      container.innerHTML = emptyState("No teams yet", "Create your first team to get started.");
      return;
    }
    const rows = teams.map((t) => {
      const name = Api.pick(t, ["name"], "unnamed");
      const desc = Api.pick(t, ["description"], "—");
      const docCount = Api.pick(t, ["document_count", "documents_count", "total_documents"], null);
      return `
        <tr>
          <td><strong>${escapeHtml(name)}</strong></td>
          <td class="muted">${escapeHtml(desc || "—")}</td>
          ${docCount !== null ? `<td>${escapeHtml(docCount)}</td>` : ""}
          ${!compact ? `
          <td>
            <div class="row-actions">
              <button class="btn btn-ghost btn-sm" data-team-login="${escapeHtml(name)}">Log in</button>
              <button class="btn btn-ghost btn-sm" data-team-edit="${escapeHtml(name)}" data-team-desc="${escapeHtml(desc || "")}">Edit</button>
              <button class="btn btn-danger btn-sm" data-team-delete="${escapeHtml(name)}">Delete</button>
            </div>
          </td>` : ""}
        </tr>`;
    }).join("");

    container.innerHTML = `
      <table class="data-table">
        <thead><tr>
          <th>Team</th><th>Description</th>${teams.some(t=>Api.pick(t,["document_count","documents_count","total_documents"],null)!==null) ? "<th>Docs</th>" : ""}${!compact ? "<th></th>" : ""}
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>`;

    if (!compact) {
      container.querySelectorAll("[data-team-login]").forEach((btn) =>
        btn.addEventListener("click", () => openTeamLogin(btn.dataset.teamLogin)));
      container.querySelectorAll("[data-team-edit]").forEach((btn) =>
        btn.addEventListener("click", () => openTeamModal("edit", btn.dataset.teamEdit, btn.dataset.teamDesc)));
      container.querySelectorAll("[data-team-delete]").forEach((btn) =>
        btn.addEventListener("click", () => deleteTeam(btn.dataset.teamDelete)));
    }
  }

  async function deleteTeam(name) {
    if (!confirm(`Delete team "${name}"? This can't be undone.`)) return;
    try {
      await Api.teamDelete(name);
      toast(`Team "${name}" deleted`);
      loadTeams();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  // ---- Create / Edit team modal ----
  const teamModalOverlay = document.getElementById("teamModalOverlay");
  const teamForm = document.getElementById("teamForm");
  let teamModalMode = "create";

  document.getElementById("openCreateTeam").addEventListener("click", () => openTeamModal("create"));
  document.getElementById("teamModalClose").addEventListener("click", () => teamModalOverlay.classList.remove("active"));
  teamModalOverlay.addEventListener("click", (e) => { if (e.target === teamModalOverlay) teamModalOverlay.classList.remove("active"); });

  function openTeamModal(mode, name = "", description = "") {
    teamModalMode = mode;
    document.getElementById("teamModalTitle").textContent = mode === "create" ? "Create a team" : `Edit "${name}"`;
    document.getElementById("teamFormSubmit").textContent = mode === "create" ? "Create team" : "Save changes";
    document.getElementById("teamOriginalName").value = name;
    document.getElementById("teamName").value = name;
    document.getElementById("teamDescription").value = description;
    document.getElementById("teamPassword").value = "";
    document.getElementById("teamPassword").placeholder = mode === "create" ? "Team password" : "Leave blank to keep unchanged";
    document.getElementById("teamModalMsg").className = "form-msg";
    teamModalOverlay.classList.add("active");
  }

  teamForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("teamModalMsg");
    const btn = document.getElementById("teamFormSubmit");
    const originalName = document.getElementById("teamOriginalName").value;
    const name = document.getElementById("teamName").value.trim();
    const description = document.getElementById("teamDescription").value.trim();
    const password = document.getElementById("teamPassword").value;

    btn.disabled = true;
    const originalLabel = btn.textContent;
    btn.innerHTML = `<span class="spinner"></span> Saving…`;
    try {
      if (teamModalMode === "create") {
        await Api.teamCreate({ name, description, password });
        toast(`Team "${name}" created`);
      } else {
        const payload = { name, description };
        if (password) payload.password = password;
        await Api.teamUpdate(originalName, payload);
        toast(`Team "${name}" updated`);
      }
      teamModalOverlay.classList.remove("active");
      loadTeams();
    } catch (err) {
      msg.textContent = err.message;
      msg.className = "form-msg error";
    } finally {
      btn.disabled = false;
      btn.textContent = originalLabel;
    }
  });

  // ---- Team login modal ----
  const teamLoginOverlay = document.getElementById("teamLoginOverlay");
  let teamLoginTarget = null;

  function openTeamLogin(name) {
    teamLoginTarget = name;
    document.getElementById("teamLoginName").textContent = name;
    document.getElementById("teamLoginPassword").value = "";
    document.getElementById("teamLoginMsg").className = "form-msg";
    teamLoginOverlay.classList.add("active");
  }
  document.getElementById("teamLoginClose").addEventListener("click", () => teamLoginOverlay.classList.remove("active"));
  teamLoginOverlay.addEventListener("click", (e) => { if (e.target === teamLoginOverlay) teamLoginOverlay.classList.remove("active"); });

  document.getElementById("teamLoginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("teamLoginMsg");
    const btn = document.getElementById("teamLoginSubmit");
    const password = document.getElementById("teamLoginPassword").value;

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Entering…`;
    try {
      const res = await Api.teamLogin({
        team_name: teamLoginTarget,
        company_name: Session.companyName(),
        password,
      });
      Session.setTeam(res.access_token, teamLoginTarget);
      window.location.href = "team-dashboard.html";
    } catch (err) {
      msg.textContent = err.message;
      msg.className = "form-msg error";
    } finally {
      btn.disabled = false;
      btn.textContent = "Enter team workspace";
    }
  });

  // ---------------- Documents ----------------
  async function loadCompanyDocs() {
    const el = document.getElementById("companyDocsTable");
    try {
      const docs = await Api.companyDocsList();
      renderDocsTable(docs, el, Api.companyDocDelete);
    } catch (err) {
      el.innerHTML = emptyState("Couldn't load documents", err.message);
    }
  }
  document.getElementById("refreshCompanyDocs").addEventListener("click", loadCompanyDocs);

  function renderDocsTable(docs, container, deleteFn) {
    if (!docs || docs.length === 0) {
      container.innerHTML = emptyState("No documents yet", "Upload your first document above.");
      return;
    }
    const rows = docs.map((d) => {
      const name = Api.pick(d, ["name", "source", "filename", "title"], "document");
      const uploaded = Api.pick(d, ["created_at", "uploaded_at", "timestamp"], null);
      const visibility = Api.pick(d, ["visibility"], null);
      return `
        <tr>
          <td><strong>${escapeHtml(name)}</strong></td>
          <td class="muted">${uploaded ? formatDate(uploaded) : "—"}</td>
          ${visibility ? `<td><span class="badge ${visibility === 'team' ? 'badge-slate' : ''}">${escapeHtml(visibility)}</span></td>` : ""}
          <td><button class="btn btn-danger btn-sm" data-doc-delete="${escapeHtml(name)}">Delete</button></td>
        </tr>`;
    }).join("");
    container.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Name</th><th>Uploaded</th>${docs.some(d=>Api.pick(d,["visibility"],null)) ? "<th>Scope</th>" : ""}<th></th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    container.querySelectorAll("[data-doc-delete]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!confirm(`Delete "${btn.dataset.docDelete}"?`)) return;
        try {
          await deleteFn(btn.dataset.docDelete);
          toast("Document deleted");
          loadCompanyDocs();
        } catch (err) {
          toast(err.message, "error");
        }
      }));
  }

  const fileInput = document.getElementById("companyFileInput");
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
      await Api.companyDocsUpload(file);
      toast(`"${file.name}" uploaded`);
      document.getElementById("uploadFileName").textContent = "PDF, DOCX, TXT — one at a time";
      loadCompanyDocs();
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
      const sessions = await Api.companyChatSessions();
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
      const messages = await Api.companyChatMessages(sessionId);
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
      const res = await Api.companyChatAsk(question, currentSessionId);
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
