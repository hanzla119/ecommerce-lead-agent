let allLeads = [];
let pollingInterval = null;

// On page load
document.addEventListener("DOMContentLoaded", () => {
  fetchLeads();
  fetchStats();
  checkAgentStatus();
  loadEmailSettings();
});

// Show Toast notification
function showToast(message, icon = "fa-check") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<i class="fa-solid ${icon}" style="color: var(--cyan);"></i> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// Copy to Clipboard
function copyText(text, label) {
  navigator.clipboard.writeText(text).then(() => {
    showToast(`${label} copied to clipboard!`, "fa-copy");
  }).catch(err => {
    showToast("Failed to copy", "fa-triangle-exclamation");
  });
}

// Email Settings Modal
function openEmailSettingsModal() {
  const modal = document.getElementById("email-modal");
  if (modal) modal.style.display = "flex";
}

function closeEmailSettingsModal() {
  const modal = document.getElementById("email-modal");
  if (modal) modal.style.display = "none";
}

async function loadEmailSettings() {
  try {
    const res = await fetch("/api/get-smtp-settings");
    const data = await res.json();
    const emailInput = document.getElementById("modal-sender-email");
    if (emailInput && data.sender_email) {
      emailInput.value = data.sender_email;
    }
  } catch (err) {
    console.error("Error loading SMTP settings:", err);
  }
}

async function saveEmailSettings() {
  const email = document.getElementById("modal-sender-email").value.trim();
  const pwd = document.getElementById("modal-app-password").value.trim();

  if (!email || !email.includes("@")) {
    showToast("Please enter a valid Gmail address", "fa-triangle-exclamation");
    return;
  }
  if (!pwd) {
    showToast("Please enter your 16-character Google App Password", "fa-triangle-exclamation");
    return;
  }

  try {
    const res = await fetch("/api/save-smtp-settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sender_email: email, app_password: pwd })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast("Gmail credentials saved securely!", "fa-shield-halved");
      closeEmailSettingsModal();
    } else {
      showToast(data.message || "Failed to save", "fa-triangle-exclamation");
    }
  } catch (err) {
    showToast("Error saving email settings", "fa-triangle-exclamation");
  }
}

// Send Direct Email via Gmail SMTP
async function sendDirectEmail(btn, storeUrl, toEmail, subject, body) {
  if (!toEmail) {
    showToast("No email address found for this store", "fa-triangle-exclamation");
    return;
  }

  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Sending...`;

  try {
    const res = await fetch("/api/send-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        store_url: storeUrl,
        to_email: toEmail,
        subject: subject,
        body: body
      })
    });

    const data = await res.json();
    if (res.ok && data.status === "success") {
      showToast(`Email sent to ${toEmail}! Marked as Contacted.`, "fa-paper-plane");
      btn.className = "btn btn-outline-emerald btn-sm";
      btn.innerHTML = `<i class="fa-solid fa-check"></i> Sent!`;
      fetchLeads();
      fetchStats();
    } else {
      const errorMsg = data.detail || data.error || "Failed to send email";
      showToast(errorMsg, "fa-triangle-exclamation");
      btn.disabled = false;
      btn.innerHTML = originalHtml;
      
      if (errorMsg.includes("Password") || errorMsg.includes("Credentials") || errorMsg.includes("Authentication")) {
        openEmailSettingsModal();
      }
    }
  } catch (err) {
    showToast("Error sending email: Check network or settings", "fa-triangle-exclamation");
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// Fetch all leads from backend
async function fetchLeads() {
  try {
    const res = await fetch("/api/leads");
    const data = await res.json();
    allLeads = data.leads || [];
    renderLeads(allLeads);
    fetchStats();
  } catch (err) {
    console.error("Error fetching leads:", err);
  }
}

// Fetch stats
async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    const stats = await res.json();
    document.getElementById("stat-total").innerText = stats.total_leads || 0;
    document.getElementById("stat-emails").innerText = stats.emails_found || 0;
    document.getElementById("stat-linkedin").innerText = stats.linkedin_found || 0;
    document.getElementById("stat-missing").innerText = stats.missing_pixels || 0;
    document.getElementById("leads-count-header").innerText = allLeads.length;
  } catch (err) {
    console.error("Error fetching stats:", err);
  }
}

// Clean brand name helper
function cleanBrand(rawName, url) {
  if (rawName && !rawName.startsWith("http") && !rawName.startsWith("www.") && rawName.length < 30) {
    return rawName.replace(/\.(com|co\.uk|co|store|shop|io|org|net|us|eu)$/i, '').trim();
  }
  try {
    const u = new URL(url.startsWith("http") ? url : "https://" + url);
    const host = u.hostname.replace("www.", "");
    const base = host.split(".")[0];
    return base.charAt(0).toUpperCase() + base.slice(1);
  } catch {
    return rawName || "E-Commerce Brand";
  }
}

// Filter leads by search query and dropdowns
function filterLeads() {
  const query = document.getElementById("search-filter").value.toLowerCase();
  const region = document.getElementById("region-filter").value.toUpperCase();
  const status = document.getElementById("status-filter").value;

  const filtered = allLeads.filter(lead => {
    const brand = String(lead["Brand Name"] || "").toLowerCase();
    const email = String(lead["Contact Email"] || "").toLowerCase();
    const founder = String(lead["Founder / Owner"] || "").toLowerCase();
    const leadRegion = String(lead["Target Region"] || "").toUpperCase();
    const leadStatus = String(lead["Outreach Status"] || "Ready to Send");

    const matchesQuery = !query || brand.includes(query) || email.includes(query) || founder.includes(query);
    const matchesRegion = region === "ALL" || leadRegion.includes(region);
    const matchesStatus = status === "ALL" || leadStatus === status;

    return matchesQuery && matchesRegion && matchesStatus;
  });

  renderLeads(filtered);
}

// Render lead cards
function renderLeads(leads) {
  const grid = document.getElementById("leads-grid");
  grid.innerHTML = "";

  if (leads.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 48px; color: var(--text-muted);">
        <i class="fa-solid fa-folder-open" style="font-size: 32px; margin-bottom: 12px; opacity: 0.5;"></i>
        <p>No leads found. Use the Agent form above to discover new stores!</p>
      </div>
    `;
    return;
  }

  leads.forEach((lead, idx) => {
    const url = lead["Store URL"] || "#";
    const brand = cleanBrand(lead["Brand Name"], url);
    const region = lead["Target Region"] || "UK";
    const email = lead["Contact Email"] || "";
    const founder = lead["Founder / Owner"] || "";
    const founderTitle = lead["Founder Title"] || "Founder";
    const founderLinkedin = lead["Founder LinkedIn Profile"] || "";
    const instagram = lead["Instagram Profile"] || "";
    const platform = lead["Store Platform"] || "Shopify";
    const metaPixel = lead["Meta Pixel Active"] || "NO (Missing)";
    const tiktokPixel = lead["TikTok Pixel Active"] || "NO (Missing)";
    const speed = lead["Response Speed (TTFB)"] || "N/A";
    const status = lead["Outreach Status"] || "Ready to Send";

    // Pitches & Templates
    const emailSubject1 = lead["Email Subject (Template 1)"] || lead["Email Subject"] || `Idea for ${brand} (scaled similar store to £696k)`;
    const emailBody1 = lead["Email Pitch Body (Template 1)"] || lead["Email Pitch Body"] || "";
    const emailSubject2 = lead["Email Subject (Template 2)"] || `Quick observation on ${brand}'s checkout & tracking`;
    const emailBody2 = lead["Email Pitch Body (Template 2)"] || "";
    const linkedinNote = lead["LinkedIn Connection Note"] || "";
    const igPitch = lead["Instagram DM Pitch"] || "";

    const card = document.createElement("div");
    card.className = "lead-card";
    card.innerHTML = `
      <!-- Top -->
      <div class="lead-top">
        <div class="lead-title-area">
          <div class="lead-brand">
            ${brand}
          </div>
          <a href="${url}" target="_blank" rel="noreferrer" class="lead-url">
            <i class="fa-solid fa-arrow-up-right-from-square"></i> ${url.replace('https://', '').replace('http://', '')}
          </a>
        </div>
        <div class="badges">
          <span class="badge badge-region">${region}</span>
          <span class="badge badge-platform">${platform}</span>
        </div>
      </div>

      <!-- Tracking & Audit Tags -->
      <div class="badges">
        <span class="badge ${metaPixel.includes('Missing') ? 'badge-missing' : 'badge-active'}">
          <i class="fa-brands fa-meta"></i> Meta: ${metaPixel.includes('Missing') ? 'Missing' : 'Active'}
        </span>
        <span class="badge ${tiktokPixel.includes('Missing') ? 'badge-missing' : 'badge-active'}">
          <i class="fa-brands fa-tiktok"></i> TikTok: ${tiktokPixel.includes('Missing') ? 'Missing' : 'Active'}
        </span>
        <span class="badge" style="background: rgba(255,255,255,0.05); color: #cbd5e1;">
          <i class="fa-solid fa-gauge-high"></i> ${speed}
        </span>
      </div>

      <!-- Decision Maker & Outreach Channels -->
      <div class="contacts-box">
        <div class="contact-row">
          <div class="contact-founder">
            <i class="fa-solid fa-user-tie" style="color: var(--cyan);"></i>
            <span>${founder || 'Decision Maker'}</span>
            <span style="font-size: 11px; color: var(--text-dim);">(${founderTitle})</span>
          </div>
          <div class="contact-actions">
            <!-- Email Direct -->
            <button class="channel-btn ${!email ? 'disabled' : ''}" title="${email || 'No email'}" onclick="openEmailSettingsModal()">
              <i class="fa-solid fa-envelope"></i>
            </button>
            <!-- LinkedIn -->
            <a href="${founderLinkedin || '#'}" target="_blank" rel="noreferrer" class="channel-btn ${!founderLinkedin ? 'disabled' : ''}" title="LinkedIn Profile">
              <i class="fa-brands fa-linkedin"></i>
            </a>
            <!-- Instagram -->
            <a href="${instagram || '#'}" target="_blank" rel="noreferrer" class="channel-btn ${!instagram ? 'disabled' : ''}" title="Instagram Profile">
              <i class="fa-brands fa-instagram"></i>
            </a>
          </div>
        </div>
        ${email ? `
          <div style="font-size: 11px; color: var(--cyan); word-break: break-all; margin-top: 4px; display: flex; align-items: center; justify-content: space-between;">
            <span><i class="fa-regular fa-envelope"></i> ${email}</span>
            <span style="font-size: 10px; padding: 2px 6px; border-radius: 4px; background: ${lead['Email Deliverability'] && lead['Email Deliverability'].includes('Verified') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)'}; color: ${lead['Email Deliverability'] && lead['Email Deliverability'].includes('Verified') ? 'var(--emerald)' : 'var(--amber)'};">
              <i class="fa-solid fa-shield-halved"></i> ${lead['Email Deliverability'] || 'MX Checked'}
            </span>
          </div>` : ''}
        ${lead['Instagram Handle'] ? `
          <div style="font-size: 11px; color: var(--pink); word-break: break-all; margin-top: 2px;">
            <i class="fa-brands fa-instagram"></i> ${lead['Instagram Handle']}
          </div>` : ''}
      </div>

      <!-- Pitches Switcher -->
      <div class="pitch-container">
        <div class="pitch-tabs">
          <button class="pitch-tab active" onclick="switchPitchTab(this, 'email1-${idx}')">
            ✉️ Pitch 1 (£696k)
          </button>
          <button class="pitch-tab" onclick="switchPitchTab(this, 'email2-${idx}')">
            ✉️ Pitch 2 (ROAS)
          </button>
          <button class="pitch-tab" onclick="switchPitchTab(this, 'li-${idx}')">
            <i class="fa-brands fa-linkedin"></i> LinkedIn
          </button>
          <button class="pitch-tab" onclick="switchPitchTab(this, 'ig-${idx}')">
            <i class="fa-brands fa-instagram"></i> IG DM
          </button>
        </div>

        <!-- Tab 1: Email Template 1 -->
        <div id="email1-${idx}" class="pitch-tab-panel">
          <div style="font-size: 11px; color: var(--amber); margin-bottom: 4px; font-weight: 600;">
            Subject: ${emailSubject1}
          </div>
          <div class="pitch-content-box">${emailBody1 || 'Generating customized pitch...'}</div>
          
          <div style="display: flex; gap: 8px; margin-top: 8px;">
            <button class="btn btn-primary btn-sm" style="flex: 1.2;" onclick="sendDirectEmail(this, '${url}', '${email}', \`${emailSubject1.replace(/`/g, '\\`')}\`, \`${emailBody1.replace(/`/g, '\\`')}\`)">
              <i class="fa-solid fa-paper-plane"></i> Send Direct Email
            </button>
            <button class="btn btn-secondary btn-sm" style="flex: 1;" onclick="copyText(\`Subject: ${emailSubject1.replace(/`/g, '\\`')}\\n\\n${emailBody1.replace(/`/g, '\\`')}\`, 'Email Pitch 1')">
              <i class="fa-regular fa-copy"></i> Copy
            </button>
          </div>
        </div>

        <!-- Tab 2: Email Template 2 -->
        <div id="email2-${idx}" class="pitch-tab-panel" style="display: none;">
          <div style="font-size: 11px; color: var(--amber); margin-bottom: 4px; font-weight: 600;">
            Subject: ${emailSubject2}
          </div>
          <div class="pitch-content-box">${emailBody2 || emailBody1 || 'Generating customized pitch...'}</div>
          
          <div style="display: flex; gap: 8px; margin-top: 8px;">
            <button class="btn btn-primary btn-sm" style="flex: 1.2;" onclick="sendDirectEmail(this, '${url}', '${email}', \`${emailSubject2.replace(/`/g, '\\`')}\`, \`${(emailBody2 || emailBody1).replace(/`/g, '\\`')}\`)">
              <i class="fa-solid fa-paper-plane"></i> Send Direct Email
            </button>
            <button class="btn btn-secondary btn-sm" style="flex: 1;" onclick="copyText(\`Subject: ${emailSubject2.replace(/`/g, '\\`')}\\n\\n${(emailBody2 || emailBody1).replace(/`/g, '\\`')}\`, 'Email Pitch 2')">
              <i class="fa-regular fa-copy"></i> Copy
            </button>
          </div>
        </div>

        <!-- Tab 3: LinkedIn -->
        <div id="li-${idx}" class="pitch-tab-panel" style="display: none;">
          <div class="pitch-content-box">${linkedinNote || 'Generating custom LinkedIn connection note...'}</div>
          <button class="btn btn-secondary btn-sm" style="margin-top: 6px; width: 100%;" onclick="copyText(\`${linkedinNote.replace(/`/g, '\\`')}\`, 'LinkedIn Note')">
            <i class="fa-brands fa-linkedin"></i> Copy LinkedIn Note
          </button>
        </div>

        <!-- Tab 4: Instagram -->
        <div id="ig-${idx}" class="pitch-tab-panel" style="display: none;">
          <div class="pitch-content-box">${igPitch || 'Generating custom Instagram DM...'}</div>
          <button class="btn btn-secondary btn-sm" style="margin-top: 6px; width: 100%;" onclick="copyText(\`${igPitch.replace(/`/g, '\\`')}\`, 'Instagram DM')">
            <i class="fa-brands fa-instagram"></i> Copy Instagram DM
          </button>
        </div>
      </div>

      <!-- Footer & Status -->
      <div class="card-footer">
        <span style="font-size: 11px; color: var(--text-dim);">${lead["Date Added"] || "Recent"}</span>
        <select class="status-select" onchange="updateLeadStatus('${url}', this.value)">
          <option value="Ready to Send" ${status === 'Ready to Send' ? 'selected' : ''}>Ready to Send</option>
          <option value="Contacted" ${status === 'Contacted' ? 'selected' : ''}>Contacted</option>
          <option value="Meeting Booked" ${status === 'Meeting Booked' ? 'selected' : ''}>Meeting Booked</option>
          <option value="Closed Deal" ${status === 'Closed Deal' ? 'selected' : ''}>Closed Deal</option>
        </select>
      </div>
    `;
    grid.appendChild(card);
  });
}

// Switch tabs inside lead card
function switchPitchTab(btn, panelId) {
  const container = btn.closest(".pitch-container");
  container.querySelectorAll(".pitch-tab").forEach(t => t.classList.remove("active"));
  btn.classList.add("active");

  container.querySelectorAll(".pitch-tab-panel").forEach(p => p.style.display = "none");
  const panel = document.getElementById(panelId);
  if (panel) panel.style.display = "block";
}

// Update lead status in backend
async function updateLeadStatus(storeUrl, newStatus) {
  try {
    const res = await fetch("/api/update-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ store_url: storeUrl, new_status: newStatus })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(`Status updated to "${newStatus}"`, "fa-check-circle");
    }
  } catch (err) {
    showToast("Failed to update status", "fa-triangle-exclamation");
  }
}

// Handle AI Lead Discovery Search Form
async function handleSearch(e) {
  e.preventDefault();
  const niche = document.getElementById("input-niche").value.trim();
  const source = document.getElementById("input-source") ? document.getElementById("input-source").value : "web";
  const region = document.getElementById("input-region").value;
  const count = parseInt(document.getElementById("input-count").value) || 10;

  const btn = document.getElementById("btn-run-agent");
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Launching...`;

  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ niche, region, count, source })
    });
    const data = await res.json();
    
    if (!res.ok) {
      showToast(data.detail || data.message || "Failed to start agent", "fa-triangle-exclamation");
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-play"></i> Launch Agent`;
      return;
    }
    
    if (data.status === "Completed" && data.leads) {
      allLeads = data.leads;
      renderLeads(allLeads);
      updateStats(allLeads);
      showToast(data.message || `Discovered ${allLeads.length} leads!`, "fa-check");
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-play"></i> Launch Agent`;
    } else {
      showToast(data.message || "Agent searching in background...", "fa-robot");
      startPollingAgent();
    }
  } catch (err) {
    showToast("Failed to communicate with agent", "fa-triangle-exclamation");
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-play"></i> Launch Agent`;
  }
}

// Handle Single Store Audit
async function handleSingleAudit(e) {
  e.preventDefault();
  const url = document.getElementById("single-url").value.trim();
  const btn = document.getElementById("btn-single-audit");

  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;

  try {
    const res = await fetch("/api/audit-single", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url, region: "UK" })
    });
    const data = await res.json();
    showToast(`Audited ${data.lead.contacts.brand_name || url}!`, "fa-bolt");
    document.getElementById("single-url").value = "";
    fetchLeads();
  } catch (err) {
    showToast("Error auditing store", "fa-triangle-exclamation");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-bolt"></i> Audit`;
  }
}

// Check agent status
async function checkAgentStatus() {
  try {
    const res = await fetch("/api/status");
    const status = await res.json();
    if (status.is_running) {
      startPollingAgent();
    }
  } catch (err) {
    console.error(err);
  }
}

// Poll agent status during background run
function startPollingAgent() {
  const box = document.getElementById("progress-box");
  box.classList.add("active");
  const stepText = document.getElementById("progress-step");
  const countText = document.getElementById("progress-count");
  const fill = document.getElementById("progress-fill");
  const logs = document.getElementById("terminal-logs");
  const btn = document.getElementById("btn-run-agent");

  if (pollingInterval) clearInterval(pollingInterval);

  pollingInterval = setInterval(async () => {
    try {
      const res = await fetch("/api/status");
      const status = await res.json();

      stepText.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${status.current_step}`;
      countText.innerText = `${status.progress}/${status.total}`;

      const pct = status.total > 0 ? (status.progress / status.total) * 100 : 0;
      fill.style.width = `${pct}%`;

      logs.innerHTML = status.logs.map(l => `<div>> ${l}</div>`).join("");
      logs.scrollTop = logs.scrollHeight;

      if (!status.is_running) {
        clearInterval(pollingInterval);
        box.classList.remove("active");
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-play"></i> Launch Agent`;
        showToast("Lead discovery completed!", "fa-circle-check");
        fetchLeads();
      }
    } catch (err) {
      console.error(err);
    }
  }, 1500);
}
