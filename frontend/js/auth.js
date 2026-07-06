(() => {
  // If a company session already exists, skip the landing page.
  if (Session.isCompanyAuthed()) {
    window.location.href = "company-dashboard.html";
    return;
  }

  const overlay = document.getElementById("authOverlay");
  const tabLogin = document.getElementById("tabLogin");
  const tabSignup = document.getElementById("tabSignup");
  const loginPane = document.getElementById("loginPane");
  const signupPane = document.getElementById("signupPane");

  function showModal(mode) {
    overlay.classList.add("active");
    setMode(mode);
  }
  function hideModal() {
    overlay.classList.remove("active");
  }
  function setMode(mode) {
    const isLogin = mode === "login";
    tabLogin.classList.toggle("active", isLogin);
    tabSignup.classList.toggle("active", !isLogin);
    loginPane.style.display = isLogin ? "block" : "none";
    signupPane.style.display = isLogin ? "none" : "block";
  }

  ["openLogin", "heroLogin", "ctaLogin", "footerLogin"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", (e) => { e.preventDefault(); showModal("login"); });
  });
  ["openSignup", "heroSignup", "ctaSignup", "footerSignup"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", (e) => { e.preventDefault(); showModal("signup"); });
  });

  document.getElementById("authClose").addEventListener("click", hideModal);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) hideModal(); });
  tabLogin.addEventListener("click", () => setMode("login"));
  tabSignup.addEventListener("click", () => setMode("signup"));
  document.getElementById("toSignup").addEventListener("click", () => setMode("signup"));
  document.getElementById("toLogin").addEventListener("click", () => setMode("login"));

  function showFormMsg(el, message, type) {
    el.textContent = message;
    el.className = `form-msg ${type}`;
  }

  // ---------------- Login ----------------
  document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("loginSubmit");
    const msg = document.getElementById("loginMsg");
    msg.className = "form-msg";

    const name = document.getElementById("loginName").value.trim();
    const password = document.getElementById("loginPassword").value;

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Logging in…`;
    try {
      const res = await Api.companyLogin({ name, password });
      Session.setCompany(res.access_token, name);
      toast("Welcome back!");
      window.location.href = "company-dashboard.html";
    } catch (err) {
      showFormMsg(msg, err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Log in";
    }
  });

  // ---------------- Signup ----------------
  document.getElementById("signupForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("signupSubmit");
    const msg = document.getElementById("signupMsg");
    msg.className = "form-msg";

    const name = document.getElementById("signupName").value.trim();
    const email = document.getElementById("signupEmail").value.trim();
    const password = document.getElementById("signupPassword").value;

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Creating…`;
    try {
      await Api.companyRegister({ name, email, password });
      showFormMsg(msg, "Account created — logging you in…", "success");
      const res = await Api.companyLogin({ name, password });
      Session.setCompany(res.access_token, name);
      toast("Workspace created!");
      window.location.href = "company-dashboard.html";
    } catch (err) {
      showFormMsg(msg, err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Create account";
    }
  });

  // Mobile nav toggle (simple: reveal links as a stacked menu)
  const navToggle = document.getElementById("navToggle");
  if (navToggle) {
    navToggle.addEventListener("click", () => {
      const links = document.querySelector(".nav-links");
      const open = links.style.display === "flex";
      links.style.display = open ? "none" : "flex";
      links.style.cssText += open ? "" : "position:absolute; top:72px; left:0; right:0; background:#222831; flex-direction:column; padding:20px 32px; gap:18px;";
    });
  }
})();
