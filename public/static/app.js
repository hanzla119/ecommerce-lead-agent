// State management
let allLeads = [];
let pollingInterval = null;

// DOM Elements
const kpiTotal = document.getElementById("kpi-total");
const kpiEmails = document.getElementById("kpi-emails");
const kpiFounders = document.getElementById("kpi-founders");
const kpiPixels = document.getElementById("kpi-pixels");
const kpiOpportunity = document.getElementById("kpi-opportunity");
const leadsContainer = document.getElementById("leads-container");
const leadCountBadge = document.getElementById("lead-count-badge");

// Single Audit Elements
const singleUrlInput = document.getElementById("single-url-input");
const singleRegionSelect = document.getElementById("single-region-select");
const btnSingleAudit = document.getElementById("btn-single-audit");

// Batch Discovery Elements
const batchNicheInput = document.getElementById("batch-niche-input");
const batchRegionSelect = document.getElementById("batch-region-select");
const batchSourceSelect = document.getElementById("batch-source-select");
const batchCountSelect = document.getElementById("batch-count-select");
const btnLaunchAgent = document.getElementById("btn-launch-agent");

// Progress Box Elements
const progressBox = document.getElementById("progress-box");
const agentStepText = document.getElementById("agent-step-text");
const progressCount = document.getElementById("progress-count");
const progressFill = document.getElementById("progress-fill");
const terminalLogs = document.getElementById("terminal-logs");

// Toolbar & Filter Elements
const leadSearchInput = document.getElementById("lead-search-input");
const filterRegion = document.getElementById("filter-region");
const filterStatus = document.getElementById("filter-status");
const btnRefresh = document.getElementById("btn-refresh");
const btnExportExcel = document.getElementById("btn-export-excel");
const btnExportCsv = document.getElementById("btn-export-csv");

// Modals
const emailModal = document.getElementById("email-modal");
const modalToEmail = document.getElementById("modal-to-email");
const modalSubject = document.getElementById("modal-subject");
const modalBody = document.getElementById("modal-body");
const btnCloseEmailModal = document.getElementById("btn-close-email-modal");
const btnCancelSend = document.getElementById("btn-cancel-send");
const btnConfirmSend = document.getElementById("btn-confirm-send");
const emailAlert = document.getElementById("email-alert");
let currentSendingStoreUrl = "";

const smtpModal = document.getElementById("smtp-modal");
const btnEmailSettings = document.getElementById("btn-email-settings");
const btnCloseSmtpModal = document.getElementById("btn-close-smtp-modal");
const btnCancelSmtp = document.getElementById("btn-cancel-smtp");
const btnSaveSmtp = document.getElementById("btn-save-smtp");
const smtpSenderEmail = document.getElementById("smtp-sender-email");
const smtpAppPassword = document.getElementById("smtp-app-password");
const smtpAlert = document.getElementById("smtp-alert");

// Toast
const toast = document.getElementById("toast");
const toastIcon = document.getElementById("toast-icon");
const toastMessage = document.getElementById("toast-message");

function showToast(msg, iconClass = "fa-check-circle") {
  toastMessage.textContent = msg;
  toastIcon.className = `fa-solid ${iconClass}`;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 3500);
}

// 1. Initial Load
document.addEventListener("DOMContentLoaded", () => {
  fetchLeads();
  fetchStats();
  checkAgentStatus();
});

// 2. Fetch Leads & Stats API
async function fetchLeads() {
  try {
    const res = await fetch("/api/leads");
    const data = await res.json();
    allLeads = data.leads || [];
    renderLeads();
    fetchStats();
  } catch (err) {
    console.error("Error fetching leads:", err);
  }
}

async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    const stats = await res.json();
    kpiTotal.textContent = stats.total_leads || 0;
    kpiEmails.textContent = stats.emails_found || 0;
    kpiFounders.textContent = stats.linkedin_found || 0;
    kpiPixels.textContent = stats.missing_pixels || 0;
    kpiOpportunity.textContent = stats.high_opportunity || 0;
  } catch (err) {
    console.error("Error fetching stats:", err);
  }
}

// 3. Render Leads
function renderLeads() {
  const query = leadSearchInput.value.toLowerCase().trim();
  const regFilter = filterRegion.value;
  const statusFilter = filterStatus.value;

  const filtered = allLeads.filter(l => {
    const brand = (l["Brand Name"] || l.url || "").toLowerCase();
    const email = (l["Contact Email"] || "").toLowerCase();
    const founder = (l["Founder / Decision Maker"] || "").toLowerCase();
    const region = l["Region"] || "";
    const status = l["Outreach Status"] || "New Lead";

    const matchQuery = !query || brand.includes(query) || email.includes(query) || founder.includes(query);
    const matchRegion = regFilter === "ALL" || region === regFilter;
    const matchStatus = statusFilter === "ALL" || status === statusFilter;

    return matchQuery && matchRegion && matchStatus;
  });

  leadCountBadge.textContent = filtered.length;

  if (filtered.length === 0) {
    leadsContainer.innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-layer-group empty-icon"></i>
        <h3>No Leads Found</h3>
        <p>No leads match your current search or filter criteria. Try resetting filters or running a discovery.</p>
      </div>
    `;
    return;
  }

  leadsContainer.innerHTML = filtered.map((lead, idx) => buildLeadCardHTML(lead, idx)).join("");
}

function buildLeadCardHTML(l, idx) {
  const brand = l["Brand Name"] || l["Store URL"] || "E-Com Brand";
  const url = l["Store URL"] || l.url || "#";
  const region = l["Region"] || "UK";
  const email = l["Contact Email"] || "";
  const deliverability = l["Email Deliverability"] || "Unverified";
  const founder = l["Founder / Decision Maker"] || "";
  const founderTitle = l["Founder Title"] || "";
  const founderLinkedIn = l["Founder LinkedIn Profile"] || "";
  const igHandle = l["Instagram Handle"] || "";
  const igUrl = l["Instagram URL"] || "";
  const fbUrl = l["Facebook URL"] || "";
  const status = l["Outreach Status"] || "New Lead";

  const metaPixel = l["Meta Pixel Active"] || "MISSING ❌";
  const ttPixel = l["TikTok Pixel Active"] || "MISSING ❌";
  const ga = l["Google Analytics"] || "MISSING ❌";
  const reviews = l["Reviews App"] || "None";
  const speed = l["Response Speed (ms)"] || 0;

  const subj1 = l["Email Subject 1 (Scale Proof)"] || `Idea for ${brand} (scaled UK brand to £696k+)`;
  const body1 = l["Email Body 1 (Scale Proof)"] || "";
  const subj2 = l["Email Subject 2 (Tracking Leak)"] || `Quick observation on ${brand}'s conversion & tracking`;
  const body2 = l["Email Body 2 (Tracking Leak)"] || "";
  const subj3 = l["Email Subject 3 (CRO 4.89%)"] || `Quick CRO fix for ${brand} (hit £88k/mo with this)`;
  const body3 = l["Email Body 3 (CRO 4.89%)"] || "";
  const subj4 = l["Email Subject 4 (Short Hook)"] || `2-min video for ${brand}?`;
  const body4 = l["Email Body 4 (Short Hook)"] || "";
  const liNote = l["LinkedIn Connection Note"] || "";
  const igDm = l["Instagram Direct Message"] || "";

  const isMetaActive = metaPixel.includes("ACTIVE");
  const isTtActive = ttPixel.includes("ACTIVE");

  return `
    <div class="lead-card" id="lead-card-${idx}">
      <div class="lead-header">
        <div class="lead-main-info">
          <div class="brand-avatar">${brand.charAt(0).toUpperCase()}</div>
          <div class="lead-title-box">
            <h3>${brand}</h3>
            <div class="lead-meta-row">
              <a href="${url}" target="_blank" class="lead-url-link"><i class="fa-solid fa-arrow-up-right-from-square"></i> ${url.replace('https://','').replace('http://','')}</a>
              <span class="badge badge-purple">${region}</span>
              ${speed > 0 ? `<span class="badge ${speed < 1200 ? 'badge-green':'badge-red'}"><i class="fa-solid fa-gauge-high"></i> ${speed}ms</span>` : ''}
            </div>
          </div>
        </div>

        <div class="lead-badges">
          <span class="badge ${isMetaActive ? 'badge-green' : 'badge-red'}">Meta Pixel: ${isMetaActive ? 'Active' : 'Missing'}</span>
          <span class="badge ${isTtActive ? 'badge-green' : 'badge-red'}">TikTok Pixel: ${isTtActive ? 'Active' : 'Missing'}</span>
          ${reviews !== 'None' ? `<span class="badge badge-blue">Reviews: ${reviews}</span>` : ''}
        </div>
      </div>

      <!-- CONTACTS & AUDIT DETAILS -->
      <div class="lead-details-grid">
        <div class="detail-col">
          <h4>Verified Contact Data</h4>
          <div class="contact-row">
            <i class="fa-solid fa-envelope"></i>
            ${email ? `<strong>${email}</strong> <span class="badge ${deliverability.includes('Deliverable') ? 'badge-green':'badge-red'}">${deliverability}</span>` : '<span class="text-muted">No Email Found</span>'}
          </div>
          <div class="contact-row">
            <i class="fa-solid fa-user-tie"></i>
            ${founder ? `<span>${founder} (${founderTitle || 'Founder'})</span>` : '<span class="text-muted">Decision Maker Not Found</span>'}
            ${founderLinkedIn ? `<a href="${founderLinkedIn}" target="_blank"><i class="fa-brands fa-linkedin"></i></a>` : ''}
          </div>
          <div class="contact-row">
            <i class="fa-brands fa-instagram"></i>
            ${igHandle ? `<a href="${igUrl || 'https://instagram.com/' + igHandle.replace('@','')}" target="_blank">${igHandle}</a>` : '<span class="text-muted">No IG handle</span>'}
            ${fbUrl ? `<a href="${fbUrl}" target="_blank" style="margin-left: 10px;"><i class="fa-brands fa-facebook"></i></a>` : ''}
          </div>
        </div>

        <div class="detail-col">
          <h4>Store Audit Gaps</h4>
          <div class="audit-pills">
            ${!isMetaActive ? `<span class="badge badge-red">Missing Meta Pixel / CAPI</span>` : ''}
            ${!isTtActive ? `<span class="badge badge-red">Missing TikTok Retargeting</span>` : ''}
            ${reviews === 'None' ? `<span class="badge badge-red">No Reviews App Found</span>` : ''}
            ${isMetaActive && isTtActive && reviews !== 'None' ? `<span class="badge badge-green">Core Tracking Active</span>` : ''}
          </div>
        </div>
      </div>

      <!-- PITCH TABS -->
      <div class="pitch-container">
        <div class="pitch-tabs">
          <button class="pitch-tab active" onclick="switchPitchTab(${idx}, 'scale')">🏆 £696k Scale Proof</button>
          <button class="pitch-tab" onclick="switchPitchTab(${idx}, 'tracking')">⚡ Tracking Leak</button>
          <button class="pitch-tab" onclick="switchPitchTab(${idx}, 'cro')">🎯 4.89% CVR Hook</button>
          <button class="pitch-tab" onclick="switchPitchTab(${idx}, 'short')">⏱️ 4-Line Hook</button>
          <button class="pitch-tab" onclick="switchPitchTab(${idx}, 'linkedin')">🔗 LinkedIn Note</button>
          <button class="pitch-tab" onclick="switchPitchTab(${idx}, 'instagram')">📷 Instagram DM</button>
        </div>

        <div class="pitch-content-box" id="pitch-box-${idx}">
          <div class="pitch-subject" id="pitch-subj-${idx}">Subject: ${escapeHTML(subj1)}</div>
          <div class="pitch-text" id="pitch-text-${idx}">${escapeHTML(body1)}</div>
        </div>
      </div>

      <!-- FOOTER ACTIONS -->
      <div class="lead-footer-actions">
        <div class="status-select-box">
          <label style="font-size:12px; color:var(--text-muted); margin-right:6px;">Status:</label>
          <select class="filter-select" onchange="updateLeadStatus('${url}', this.value)">
            <option value="New Lead" ${status === 'New Lead' ? 'selected':''}>New Lead</option>
            <option value="Contacted" ${status === 'Contacted' ? 'selected':''}>Contacted</option>
            <option value="Replied" ${status === 'Replied' ? 'selected':''}>Replied</option>
            <option value="Meeting Booked" ${status === 'Meeting Booked' ? 'selected':''}>Meeting Booked</option>
          </select>
        </div>

        <div class="footer-btn-group">
          <button class="btn btn-secondary" onclick="copyCurrentPitch(${idx})">
            <i class="fa-solid fa-copy"></i> Copy Pitch
          </button>
          ${email ? `
            <button class="btn btn-primary" onclick="openEmailModal('${email}', ${idx}, '${url}')">
              <i class="fa-solid fa-paper-plane"></i> Send Email
            </button>
          ` : ''}
        </div>
      </div>
    </div>
  `;
}

function escapeHTML(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// 4. Tab Switching
window.switchPitchTab = function(idx, tab) {
  const card = document.getElementById(`lead-card-${idx}`);
  const tabs = card.querySelectorAll(".pitch-tab");
  tabs.forEach(t => t.classList.remove("active"));
  event.target.classList.add("active");

  const l = allLeads[idx];
  const subjEl = document.getElementById(`pitch-subj-${idx}`);
  const textEl = document.getElementById(`pitch-text-${idx}`);

  if (tab === "scale") {
    subjEl.style.display = "block";
    subjEl.textContent = `Subject: ${l["Email Subject 1 (Scale Proof)"] || ""}`;
    textEl.textContent = l["Email Body 1 (Scale Proof)"] || "";
  } else if (tab === "tracking") {
    subjEl.style.display = "block";
    subjEl.textContent = `Subject: ${l["Email Subject 2 (Tracking Leak)"] || ""}`;
    textEl.textContent = l["Email Body 2 (Tracking Leak)"] || "";
  } else if (tab === "cro") {
    subjEl.style.display = "block";
    subjEl.textContent = `Subject: ${l["Email Subject 3 (CRO 4.89%)"] || ""}`;
    textEl.textContent = l["Email Body 3 (CRO 4.89%)"] || "";
  } else if (tab === "short") {
    subjEl.style.display = "block";
    subjEl.textContent = `Subject: ${l["Email Subject 4 (Short Hook)"] || ""}`;
    textEl.textContent = l["Email Body 4 (Short Hook)"] || "";
  } else if (tab === "linkedin") {
    subjEl.style.display = "none";
    textEl.textContent = l["LinkedIn Connection Note"] || "";
  } else if (tab === "instagram") {
    subjEl.style.display = "none";
    textEl.textContent = l["Instagram Direct Message"] || "";
  }
};

window.copyCurrentPitch = function(idx) {
  const subjEl = document.getElementById(`pitch-subj-${idx}`);
  const textEl = document.getElementById(`pitch-text-${idx}`);
  let text = textEl.textContent;
  if (subjEl.style.display !== "none") {
    text = `${subjEl.textContent}\n\n${text}`;
  }
  navigator.clipboard.writeText(text);
  showToast("Pitch copied to clipboard!", "fa-copy");
};

// 5. Update Lead Status API
window.updateLeadStatus = async function(url, newStatus) {
  try {
    const res = await fetch("/api/update-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ store_url: url, new_status: newStatus })
    });
    if (res.ok) {
      showToast(`Status updated to "${newStatus}"`);
    }
  } catch (err) {
    console.error("Status update error:", err);
  }
};

// 6. Instant Single Store Audit
btnSingleAudit.addEventListener("click", async () => {
  const url = singleUrlInput.value.trim();
  const region = singleRegionSelect.value;
  if (!url) {
    showToast("Please enter a valid store URL", "fa-triangle-exclamation");
    return;
  }

  btnSingleAudit.disabled = true;
  btnSingleAudit.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Auditing...`;

  try {
    const res = await fetch("/api/audit-single", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, region })
    });
    const data = await res.json();
    if (res.ok) {
      showToast("Store audit & pitch generated!", "fa-circle-check");
      singleUrlInput.value = "";
      await fetchLeads();
    } else {
      showToast(data.detail || "Failed to audit store", "fa-circle-xmark");
    }
  } catch (err) {
    showToast("Error connecting to server", "fa-circle-xmark");
  } finally {
    btnSingleAudit.disabled = false;
    btnSingleAudit.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Audit Store`;
  }
});

// 7. Launch Batch Discovery Agent
btnLaunchAgent.addEventListener("click", async () => {
  const niche = batchNicheInput.value.trim();
  const region = batchRegionSelect.value;
  const source = batchSourceSelect.value;
  const count = parseInt(batchCountSelect.value, 10);

  if (!niche) {
    showToast("Please specify a target niche", "fa-triangle-exclamation");
    return;
  }

  btnLaunchAgent.disabled = true;
  btnLaunchAgent.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Launching...`;

  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ niche, region, count, source })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message || "Discovery agent started!", "fa-robot");
      if (data.leads && data.leads.length > 0) {
        allLeads = data.leads;
        renderLeads();
        fetchStats();
      }
      if (data.status === "Started") {
        progressBox.classList.remove("hidden");
        startPollingStatus();
      } else {
        btnLaunchAgent.disabled = false;
        btnLaunchAgent.innerHTML = `<i class="fa-solid fa-play"></i> Launch Agent`;
        await fetchLeads();
      }
    } else {
      showToast(data.detail || "Agent is busy", "fa-circle-xmark");
      btnLaunchAgent.disabled = false;
      btnLaunchAgent.innerHTML = `<i class="fa-solid fa-play"></i> Launch Agent`;
    }
  } catch (err) {
    showToast("Error starting agent", "fa-circle-xmark");
    btnLaunchAgent.disabled = false;
    btnLaunchAgent.innerHTML = `<i class="fa-solid fa-play"></i> Launch Agent`;
  }
});

// 8. Polling Status
function startPollingStatus() {
  if (pollingInterval) clearInterval(pollingInterval);
  pollingInterval = setInterval(checkAgentStatus, 1500);
}

async function checkAgentStatus() {
  try {
    const res = await fetch("/api/status");
    const status = await res.json();
    if (!status) return;

    if (status.is_running) {
      progressBox.classList.remove("hidden");
      agentStepText.textContent = status.current_step || "Processing...";
      progressCount.textContent = `${status.progress || 0}/${status.total || 0}`;
      const pct = status.total > 0 ? Math.min(100, Math.round((status.progress / status.total) * 100)) : 10;
      progressFill.style.width = `${pct}%`;

      if (status.logs && status.logs.length > 0) {
        terminalLogs.innerHTML = status.logs.map(log => `<div>&gt; ${escapeHTML(log)}</div>`).join("");
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
      }
    } else {
      if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        btnLaunchAgent.disabled = false;
        btnLaunchAgent.innerHTML = `<i class="fa-solid fa-play"></i> Launch Agent`;
        showToast("Lead discovery completed!", "fa-circle-check");
        fetchLeads();
      }
    }
  } catch (err) {
    console.error("Status check error:", err);
  }
}

// 9. Email Modal
window.openEmailModal = function(toEmail, idx, storeUrl) {
  currentSendingStoreUrl = storeUrl;
  modalToEmail.value = toEmail;
  const subjEl = document.getElementById(`pitch-subj-${idx}`);
  const textEl = document.getElementById(`pitch-text-${idx}`);
  modalSubject.value = subjEl.textContent.replace("Subject: ", "");
  modalBody.value = textEl.textContent;
  emailAlert.classList.add("hidden");
  emailModal.classList.remove("hidden");
};

btnCloseEmailModal.addEventListener("click", () => emailModal.classList.add("hidden"));
btnCancelSend.addEventListener("click", () => emailModal.classList.add("hidden"));

btnConfirmSend.addEventListener("click", async () => {
  const to = modalToEmail.value;
  const subject = modalSubject.value.trim();
  const body = modalBody.value.trim();

  if (!subject || !body) {
    emailAlert.className = "alert-box error";
    emailAlert.textContent = "Subject and body cannot be empty.";
    emailAlert.classList.remove("hidden");
    return;
  }

  btnConfirmSend.disabled = true;
  btnConfirmSend.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Sending...`;

  try {
    const res = await fetch("/api/send-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ to_email: to, subject, body, store_url: currentSendingStoreUrl })
    });
    const data = await res.json();
    if (res.ok) {
      emailModal.classList.add("hidden");
      showToast(`Email delivered to ${to}!`, "fa-paper-plane");
      fetchLeads();
    } else {
      emailAlert.className = "alert-box error";
      emailAlert.textContent = data.detail || "Failed to send email.";
      emailAlert.classList.remove("hidden");
    }
  } catch (err) {
    emailAlert.className = "alert-box error";
    emailAlert.textContent = "Connection error.";
    emailAlert.classList.remove("hidden");
  } finally {
    btnConfirmSend.disabled = false;
    btnConfirmSend.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Send Email`;
  }
});

// 10. SMTP Settings Modal
btnEmailSettings.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/get-smtp-settings");
    const data = await res.json();
    if (data.sender_email) smtpSenderEmail.value = data.sender_email;
  } catch (e) {}
  smtpAlert.classList.add("hidden");
  smtpModal.classList.remove("hidden");
});

btnCloseSmtpModal.addEventListener("click", () => smtpModal.classList.add("hidden"));
btnCancelSmtp.addEventListener("click", () => smtpModal.classList.add("hidden"));

btnSaveSmtp.addEventListener("click", async () => {
  const email = smtpSenderEmail.value.trim();
  const pwd = smtpAppPassword.value.trim();
  if (!email || !pwd) {
    smtpAlert.className = "alert-box error";
    smtpAlert.textContent = "Please provide both sender email and app password.";
    smtpAlert.classList.remove("hidden");
    return;
  }

  try {
    const res = await fetch("/api/save-smtp-settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sender_email: email, app_password: pwd })
    });
    if (res.ok) {
      smtpModal.classList.add("hidden");
      showToast("Email credentials saved!", "fa-check-circle");
    }
  } catch (err) {
    smtpAlert.className = "alert-box error";
    smtpAlert.textContent = "Error saving settings.";
    smtpAlert.classList.remove("hidden");
  }
});

// 11. Search & Filter Listeners
leadSearchInput.addEventListener("input", renderLeads);
filterRegion.addEventListener("change", renderLeads);
filterStatus.addEventListener("change", renderLeads);
btnRefresh.addEventListener("click", fetchLeads);

// 12. Export Excel & CSV
btnExportExcel.addEventListener("click", () => window.open("/api/download/excel", "_blank"));
btnExportCsv.addEventListener("click", () => window.open("/api/download/csv", "_blank"));
