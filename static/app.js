let currentActiveTaskId = null;
let cachedSceneSources = [];
let cachedQueueCount = 0;
let activeMemoryFileTab = "person";
let activeTaskPersonData = null;
let activeTaskAskData = null;

function formatCodeWithLineNumbers(obj) {
  if (!obj) return "";
  const jsonStr = JSON.stringify(obj, null, 2);
  const lines = jsonStr.split("\n");
  return lines.map((line, idx) => {
    const num = (idx + 1).toString().padStart(2, " ");
    const safeLine = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return `<span class="line-num">${num}</span>  ${safeLine}`;
  }).join("\n");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function switchMemoryFileTab(tabName) {
  activeMemoryFileTab = tabName;
  const personBtn = document.getElementById("tab-btn-person");
  const askBtn = document.getElementById("tab-btn-ask");
  const codeEl = document.getElementById("memory-file-code-content");
  
  if (personBtn) personBtn.classList.toggle("active", tabName === "person");
  if (askBtn) askBtn.classList.toggle("active", tabName === "ask");
  
  if (codeEl) {
    const dataToDisplay = tabName === "person" ? activeTaskPersonData : activeTaskAskData;
    codeEl.innerHTML = formatCodeWithLineNumbers(dataToDisplay);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initApp();
  
  document.getElementById("btn-save-scene").addEventListener("click", handleSaveScene);
  document.getElementById("btn-run-scout").addEventListener("click", handleRunScout);
  document.getElementById("btn-clear-scene")?.addEventListener("click", handleClearScene);
  document.getElementById("btn-delete-test")?.addEventListener("click", handleDeleteTest);
  document.getElementById("btn-restore-memory")?.addEventListener("click", handleRestoreMemory);
  document.getElementById("btn-verify-person").addEventListener("click", handleVerifyPerson);
  document.getElementById("verify-person-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleVerifyPerson();
  });
});

async function initApp() {
  await loadScene();
  await refreshAll();
}

async function refreshAll() {
  await loadScoutJournal();
  await loadQueue();
  if (currentActiveTaskId) {
    await loadTaskDetails(currentActiveTaskId);
  }
  updateStatusLine();
}

function updateStatusLine() {
  const statusEl = document.getElementById("status-line");
  if (!statusEl) return;
  
  const scenePart = cachedSceneSources.length === 0 ? "Scene empty" : `Scene ${cachedSceneSources.length} source${cachedSceneSources.length === 1 ? '' : 's'}`;
  const queuePart = `Queue ${cachedQueueCount}`;
  const clerkPart = currentActiveTaskId ? `Clerk inspecting` : "Clerk idle";
  
  statusEl.textContent = `${scenePart} · ${queuePart} · ${clerkPart}`;
}

function showToast(msg) {
  const toast = document.getElementById("desk-toast");
  if (!toast) return;
  toast.textContent = msg;
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 2500);
}

async function loadScene() {
  try {
    const res = await fetch("/api/scene");
    const data = await res.json();
    cachedSceneSources = data.sources || [];
    
    let repoVal = "";
    let walletVal = "";
    
    cachedSceneSources.forEach(s => {
      if (s.startsWith("repo:")) {
        repoVal = s.replace(/^repo:/, "");
      } else if (s.startsWith("wallet:")) {
        walletVal = s.replace(/^wallet:/, "").replace(/@8453$/, "");
      }
    });
    
    const repoInput = document.getElementById("scene-repo");
    const walletInput = document.getElementById("scene-wallet");
    
    if (repoInput) repoInput.value = repoVal;
    if (walletInput) walletInput.value = walletVal;
    
    const isEmpty = cachedSceneSources.length === 0;
    if (repoInput) {
      if (isEmpty) repoInput.classList.add("pulse-empty");
      else repoInput.classList.remove("pulse-empty");
    }
    if (walletInput) {
      if (isEmpty) walletInput.classList.add("pulse-empty");
      else walletInput.classList.remove("pulse-empty");
    }
    
    updateStatusLine();
  } catch (err) {
    console.error("Failed to load scene:", err);
  }
}

async function handleSaveScene() {
  let rawRepo = (document.getElementById("scene-repo")?.value || "").trim();
  let rawWallet = (document.getElementById("scene-wallet")?.value || "").trim();
  
  const sources = [];
  
  if (rawRepo) {
    let cleanRepo = rawRepo
      .replace(/^https?:\/\/github\.com\//i, "")
      .replace(/^github\.com\//i, "")
      .replace(/^repo:/i, "")
      .replace(/\/issues\/([0-9]+)\/?$/i, "#$1")
      .replace(/\/$/, "")
      .trim();
    if (cleanRepo) {
      sources.push(`repo:${cleanRepo}`);
    }
  }
  
  if (rawWallet) {
    let cleanWallet = rawWallet
      .replace(/^wallet:/i, "")
      .replace(/@8453$/i, "")
      .trim();
    if (cleanWallet.startsWith("0x")) {
      sources.push(`wallet:${cleanWallet}@8453`);
    } else if (cleanWallet) {
      sources.push(`wallet:${cleanWallet}@8453`);
    }
  }
  
  try {
    const res = await fetch("/api/scene", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "OnRecord Desk", sources })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.detail || "Failed to save Scene.");
      return;
    }
    showToast("Scene saved.");
    await loadScene();
    await refreshAll();
  } catch (err) {
    alert("Error saving scene: " + err.message);
  }
}

async function handleClearScene() {
  const repoInput = document.getElementById("scene-repo");
  const walletInput = document.getElementById("scene-wallet");
  if (repoInput) repoInput.value = "";
  if (walletInput) walletInput.value = "";
  
  try {
    const res = await fetch("/api/scene", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "OnRecord Desk", sources: [] })
    });
    if (res.ok) {
      showToast("Scene cleared.");
      await loadScene();
      await refreshAll();
    }
  } catch (err) {
    alert("Error clearing scene: " + err.message);
  }
}

async function handleDeleteTest() {
  const confirmed = confirm("Execute The Delete Test?\n\nThis wipes tenant_scout memory from SQLite to verify:\n1. The Queue immediately drops to 0.\n2. All filed entities return NOT ON RECORD.\n3. Base pings are strictly refused.\n\n(You can repopulate anytime by clicking 'Run Scout').");
  if (!confirmed) return;
  
  const btn = document.getElementById("btn-delete-test");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "WIPING...";
  }
  
  try {
    const res = await fetch("/api/desk/delete_test", { method: "POST" });
    const data = await res.json();
    showToast(`Delete Test Passed: ${data.deleted_scout || 0} memory rows wiped. Queue is now 0.`);
    currentActiveTaskId = null;
    await refreshAll();
    
    const container = document.getElementById("active-task-container");
    if (container) {
      container.innerHTML = '<div class="col-empty">The Delete Test executed. Scout memory wiped. Queue is 0.<br/><br/>Click <strong>Restore Memory</strong> to recover snapshot, or <strong>Run Scout</strong> to rebuild from source.</div>';
    }
  } catch (err) {
    alert("Delete Test failed: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Delete Test";
    }
  }
}

async function handleRestoreMemory() {
  const btn = document.getElementById("btn-restore-memory");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "RESTORING...";
  }
  try {
    const res = await fetch("/api/desk/restore_memory", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || "Failed to restore memory.");
      return;
    }
    showToast(data.message || "Memory restored successfully.");
    await refreshAll();
  } catch (err) {
    alert("Restore failed: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Restore Memory";
    }
  }
}

async function handleRunScout() {
  const btn = document.getElementById("btn-run-scout");
  btn.disabled = true;
  btn.textContent = "FILING...";
  try {
    const res = await fetch("/api/scout/run", { method: "POST" });
    const data = await res.json();
    showToast(`Scout completed: ${data.count || 0} filings.`);
    await refreshAll();
  } catch (err) {
    alert("Scout sync failed: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Run Scout";
  }
}

async function loadScoutJournal() {
  const container = document.getElementById("scout-body");
  const countEl = document.getElementById("scout-count");
  try {
    const res = await fetch("/api/scout/journal");
    const data = await res.json();
    const events = data.events || [];
    
    if (countEl) countEl.textContent = events.length;

    if (events.length === 0) {
      container.innerHTML = '<div class="col-empty">No filings on record.<br/><br/><button type="button" class="btn-restore" style="padding:5px 12px;font-size:10px;cursor:pointer;" onclick="handleRestoreMemory()">Restore Memory</button></div>';
      return;
    }
    
    let html = "";
    events.slice().reverse().forEach(ev => {
      const extra = ev.extra || {};
      const personName = extra.person || "Contributor";
      const sourceDisplay = (extra.source || "scene").replace(/^repo:/, "").replace(/@8453$/, "");
      const timeStr = ev.ts ? new Date(ev.ts).toLocaleTimeString() : "";
      const title = extra.title || "";
      
      html += `
        <div class="desk-card">
          <div class="card-row">
            <span class="card-label">${escapeHtml(personName)}</span>
            <span class="card-ts">${timeStr}</span>
          </div>
          ${title ? `<div class="card-title-line" title="${escapeHtml(title)}">${escapeHtml(title)}</div>` : ''}
          <div class="card-subtext">Filed from ${escapeHtml(sourceDisplay)}</div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<div class="col-empty">Error reading Scout filings.</div>';
  }
}

async function loadQueue() {
  const container = document.getElementById("queue-body");
  const countEl = document.getElementById("queue-count");
  try {
    const res = await fetch("/api/queue");
    const data = await res.json();
    const queue = data.queue || [];
    
    cachedQueueCount = queue.length;
    if (countEl) countEl.textContent = cachedQueueCount;

    if (queue.length === 0) {
      container.innerHTML = '<div class="col-empty">Queue is empty.</div>';
      return;
    }
    
    let html = "";
    queue.forEach(item => {
      const isSelected = item.task_id === currentActiveTaskId;
      const sourceDisplay = (item.source || "").replace(/^repo:/, "").replace(/@8453$/, "");
      const title = item.title || "";
      
      html += `
        <div class="desk-card clickable ${isSelected ? 'selected' : ''}" onclick="selectTask('${item.task_id}')">
          <div class="card-row">
            <span class="card-label">${escapeHtml(item.person || 'Person')}</span>
            <span class="metal-tab tab-act">ON RECORD</span>
          </div>
          ${title ? `<div class="card-title-line" title="${escapeHtml(title)}">${escapeHtml(title)}</div>` : ''}
          <div class="card-subtext">${escapeHtml(sourceDisplay)}</div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<div class="col-empty">Error reading queue.</div>';
  }
}

function selectTask(taskId) {
  currentActiveTaskId = taskId;
  loadQueue();
  loadTaskDetails(taskId);
  updateStatusLine();
}

async function loadTaskDetails(taskId) {
  const container = document.getElementById("active-task-container");
  container.innerHTML = '<div class="col-empty">Reading task from memory...</div>';
  
  try {
    const res = await fetch(`/api/clerk/task/${taskId}`);
    const data = await res.json();
    
    if (data.status === "NOT_ON_RECORD") {
      container.innerHTML = `
        <div class="alert-stamp nor">
          <strong>NOT ON RECORD</strong><br/>
          This task is not filed on record.
        </div>
      `;
      return;
    }
    
    const person = data.person || {};
    const ask = data.ask || {};
    const bound = (person.bound || "").trim();
    const hasBound = Boolean(bound && bound.startsWith("0x"));
    const clerkStatus = data.clerk_status || "open";
    
    let tabClass = "tab-act";
    let tabText = "ON RECORD";
    if (clerkStatus === "skipped") {
      tabClass = "tab-skip";
      tabText = "SKIPPED";
    } else if (clerkStatus === "pinged") {
      tabClass = "tab-act";
      tabText = "PINGED";
    } else if (clerkStatus === "blocked") {
      tabClass = "tab-nor";
      tabText = "BLOCKED";
    }
    
    let blockedReason = "Execution blocked";
    const rawError = data.clerk_info?.extra?.error || "";
    if (rawError) {
      if (rawError.includes("BASE_PRIVATE_KEY") || rawError.includes("not provided") || rawError.includes("signing key")) {
        blockedReason = "Missing signing key in environment";
      } else if (rawError.includes("bound address") || rawError.includes("no bound")) {
        blockedReason = "Needs a wallet on this person";
      } else if (rawError.includes("confirmation required") || rawError.includes("Operator confirmation")) {
        blockedReason = "Operator confirmation required";
      } else if (rawError.includes("insufficient") || rawError.includes("gas") || rawError.includes("funds")) {
        blockedReason = "Insufficient Base ETH for gas";
      } else {
        blockedReason = rawError.length > 50 ? rawError.slice(0, 50) + "..." : rawError;
      }
    }
    
    const sourceDisplay = (ask.source || "").replace(/^repo:/, "").replace(/@8453$/, "");
    
    activeTaskPersonData = person;
    activeTaskAskData = ask;
    const initialFileCode = formatCodeWithLineNumbers(activeMemoryFileTab === "person" ? person : ask);

    container.innerHTML = `
      <div class="inspector-panel">
        <div class="inspector-head">
          <span class="inspector-id">${person.name || 'Person File'}</span>
          <span class="metal-tab ${tabClass}">${tabText}</span>
        </div>
        
        <!-- Person Details -->
        <div class="segment-box">
          <div class="segment-row">
            <span class="k">HANDLE</span>
            <span>${person.handle || 'N/A'}</span>
          </div>
          <div class="segment-row" style="align-items: flex-start;">
            <span class="k" style="margin-top: 5px;">WALLET</span>
            <div style="flex: 1; display: flex; flex-direction: column; gap: 6px; margin-left: 10px;">
              ${bound ? `
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 6px;">
                  <span class="card-ts" style="color: var(--brass-accent); font-weight: 600; word-break: break-all;">${bound}</span>
                  <button type="button" class="btn-change-wallet" onclick="toggleEditWallet(true)">Change</button>
                </div>
                <div id="edit-wallet-form" class="bind-wallet-row" style="display: none;">
                  <input type="text" id="bind-wallet-input" placeholder="0x... new Base address" value="${bound}" autocomplete="off" />
                  <button type="button" class="btn-bind-action" onclick="handleBindWallet('${escapeHtml(person.name)}', '${taskId}')">Save</button>
                  <button type="button" class="btn-cancel-action" onclick="toggleEditWallet(false)">✕</button>
                </div>
              ` : `
                <div class="bind-wallet-row">
                  <input type="text" id="bind-wallet-input" placeholder="0x... paste Base address to bind" autocomplete="off" />
                  <button type="button" class="btn-bind-action" onclick="handleBindWallet('${escapeHtml(person.name)}', '${taskId}')">Bind Wallet</button>
                </div>
              `}
            </div>
          </div>
        </div>
        
        <!-- Ask Details -->
        <div class="segment-box">
          <span class="segment-head">INCOMING ASK</span>
          <div class="ask-text-wrap">${ask.text || 'N/A'}</div>
          <div class="segment-row" style="margin-top: 4px;">
            <span class="k">SOURCE</span>
            <span>${sourceDisplay || 'N/A'}</span>
          </div>
        </div>
        
        <!-- Sibyl Memory Live File View (Builder Tip 02/04) -->
        <div class="memory-file-box">
          <div class="memory-file-head">
            <div class="memory-file-tabs">
              <button type="button" id="tab-btn-person" class="file-tab-btn ${activeMemoryFileTab === 'person' ? 'active' : ''}" onclick="switchMemoryFileTab('person')">
                person.json
              </button>
              <button type="button" id="tab-btn-ask" class="file-tab-btn ${activeMemoryFileTab === 'ask' ? 'active' : ''}" onclick="switchMemoryFileTab('ask')">
                ask.json
              </button>
            </div>
            <span class="memory-file-live"><span class="dot-pulse"></span> READING LIVE FROM SIBYL MEMORY</span>
          </div>
          <pre class="memory-file-code"><code id="memory-file-code-content">${initialFileCode}</code></pre>
          <div class="memory-file-foot">
            This record came from this file in storage, not chat history.
          </div>
        </div>
        
        <!-- Actions -->
        <div class="action-row">
          <button type="button" class="btn-primary" onclick="openTaskAction('${taskId}')" ${clerkStatus !== 'open' ? 'disabled' : ''}>
            Open Task
          </button>
          <button type="button" class="btn-secondary" onclick="skipTaskAction('${taskId}')" ${clerkStatus !== 'open' ? 'disabled' : ''}>
            Skip
          </button>
        </div>
        
        <!-- Base Ping Section -->
        <div class="base-deck">
          <div class="base-head">
            <span>ONCHAIN PING (BASE MAINNET)</span>
            <span>${hasBound ? 'WALLET BOUND' : 'NO WALLET'}</span>
          </div>
          ${!hasBound ? '<div style="font-size: 11px; font-family: var(--font-mono); color: var(--brass-accent);">Needs a wallet on this person — paste and bind above to unlock onchain ping.</div>' : ''}
          ${clerkStatus === 'open' ? `
            <label class="confirm-label">
              <input type="checkbox" id="confirm-ping-checkbox" ${!hasBound ? 'disabled' : ''} />
              Confirm onchain ping
            </label>
            <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 8px;">
              <button type="button" class="btn-wallet-ping" id="btn-wallet-ping" ${!hasBound ? 'disabled' : ''} onclick="pingWithBrowserWallet('${taskId}', '${bound}')">
                Sign with Browser Wallet (MetaMask / Coinbase)
              </button>
              <button type="button" class="btn-secondary" id="btn-execute-ping" ${!hasBound ? 'disabled' : ''} onclick="pingTaskAction('${taskId}')">
                Use Desk Signer (Headless)
              </button>
            </div>
          ` : ''}
          ${clerkStatus === 'blocked' ? `
            <div class="alert-stamp nor" style="margin-top: 4px;">
              Couldn't send: ${blockedReason}
            </div>
          ` : ''}
          ${clerkStatus === 'pinged' ? `
            <div class="alert-stamp act" style="margin-top: 4px;">
              Confirmed onchain: ${data.clerk_info?.extra?.tx_hash ? `<a href="https://basescan.org/tx/${data.clerk_info.extra.tx_hash}" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: underline;">${data.clerk_info.extra.tx_hash.slice(0, 12)}...${data.clerk_info.extra.tx_hash.slice(-8)}</a>` : 'Broadcast successful'}
            </div>
          ` : ''}
          <div id="ping-result" class="ping-result-box"></div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="col-empty">Error loading task details.</div>`;
  }
}

async function handleVerifyPerson() {
  const input = document.getElementById("verify-person-input");
  const name = input.value.trim();
  const resContainer = document.getElementById("verifier-result");
  if (!name) return;
  
  resContainer.innerHTML = '<div style="font-size: 10px; font-family: var(--font-mono); color: var(--text-dim); padding: 4px 8px;">Checking record...</div>';
  try {
    const res = await fetch(`/api/clerk/check?name=${encodeURIComponent(name)}`);
    const data = await res.json();
    
    if (data.status === "ON_RECORD") {
      const p = data.person || {};
      resContainer.innerHTML = `
        <div class="alert-stamp act" style="margin-bottom: 6px;">
          <strong>ON RECORD</strong><br/>
          ${p.name} ${p.handle ? `(${p.handle})` : ''}
        </div>
      `;
    } else {
      resContainer.innerHTML = `
        <div class="alert-stamp nor" style="margin-bottom: 6px;">
          <strong>NOT ON RECORD</strong><br/>
          '${name}' is not filed on record.
        </div>
      `;
    }
  } catch (err) {
    resContainer.innerHTML = `<div class="alert-stamp nor">Error: Could not verify.</div>`;
  }
}

async function openTaskAction(taskId) {
  try {
    const res = await fetch("/api/clerk/open", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId })
    });
    const data = await res.json();
    showToast("Task opened.");
    await refreshAll();
  } catch (err) {
    alert("Failed to open task.");
  }
}

async function skipTaskAction(taskId) {
  try {
    const res = await fetch("/api/clerk/skip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId })
    });
    const data = await res.json();
    showToast("Task skipped.");
    await refreshAll();
  } catch (err) {
    alert("Failed to skip task.");
  }
}

async function pingTaskAction(taskId) {
  const checkbox = document.getElementById("confirm-ping-checkbox");
  const confirmed = checkbox ? checkbox.checked : false;
  const resultDiv = document.getElementById("ping-result");
  
  if (!confirmed) {
    alert("Please check the confirmation box.");
    return;
  }
  
  resultDiv.innerHTML = '<span style="color: var(--brass-accent);">Broadcasting onchain via desk signer...</span>';
  
  try {
    const res = await fetch("/api/clerk/ping", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId, confirm: confirmed })
    });
    const data = await res.json();
    
    if (data.status === "pinged") {
      const tx = data.tx_hash || "";
      const txDisplay = tx ? `<a href="https://basescan.org/tx/${tx}" target="_blank" rel="noopener noreferrer" style="color: var(--brass-accent); text-decoration: underline;">${tx.slice(0, 10)}...${tx.slice(-6)}</a>` : "Confirmed";
      resultDiv.innerHTML = `<span style="color: var(--brass-accent); font-weight: 700;">CONFIRMED: ${txDisplay}</span>`;
      showToast("Ping confirmed onchain.");
    } else {
      let shortReason = data.reason || "No signer key configured";
      if (data.reason && data.reason.includes("bound")) shortReason = "Needs a wallet on this person";
      else if (data.reason && data.reason.includes("confirm")) shortReason = "Operator confirmation required";
      else if (data.reason && (data.reason.includes("browser wallet") || data.reason.includes("BASE_PRIVATE_KEY"))) {
        shortReason = "Desk has no private key. Use 'Sign with Browser Wallet' above.";
      }
      resultDiv.innerHTML = `<span style="color: var(--signal-red);">Couldn't send: ${shortReason}</span>`;
    }
    await refreshAll();
  } catch (err) {
    resultDiv.innerHTML = `<span style="color: var(--signal-red);">Couldn't send: Network error</span>`;
  }
}

async function pingWithBrowserWallet(taskId, boundAddress) {
  const checkbox = document.getElementById("confirm-ping-checkbox");
  const confirmed = checkbox ? checkbox.checked : false;
  const resultDiv = document.getElementById("ping-result");
  
  if (!confirmed) {
    alert("Please check the confirmation box.");
    return;
  }

  if (typeof window.ethereum === "undefined") {
    resultDiv.innerHTML = '<span style="color: var(--signal-red);">No browser wallet detected. Install MetaMask or Coinbase Wallet.</span>';
    return;
  }

  resultDiv.innerHTML = '<span style="color: var(--brass-accent);">Connecting wallet...</span>';
  
  try {
    // 1. Request account connection
    const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
    if (!accounts || accounts.length === 0) {
      resultDiv.innerHTML = '<span style="color: var(--signal-red);">No wallet account selected.</span>';
      return;
    }
    const userAccount = accounts[0];

    // 2. Ensure Base Mainnet (Chain ID 8453 = 0x2105)
    resultDiv.innerHTML = '<span style="color: var(--brass-accent);">Switching network to Base Mainnet...</span>';
    try {
      await window.ethereum.request({
        method: "wallet_switchEthereumChain",
        params: [{ chainId: "0x2105" }]
      });
    } catch (switchErr) {
      if (switchErr.code === 4902) {
        await window.ethereum.request({
          method: "wallet_addEthereumChain",
          params: [{
            chainId: "0x2105",
            chainName: "Base",
            nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
            rpcUrls: ["https://mainnet.base.org"],
            blockExplorerUrls: ["https://basescan.org"]
          }]
        });
      } else {
        throw switchErr;
      }
    }

    // 3. Send 0-ETH ping transaction to bound address with calldata
    resultDiv.innerHTML = '<span style="color: var(--brass-accent);">Awaiting signature in wallet...</span>';
    
    const messageStr = `OnRecord task=${taskId}`;
    let hexData = "0x";
    for (let i = 0; i < messageStr.length; i++) {
      hexData += messageStr.charCodeAt(i).toString(16).padStart(2, "0");
    }

    const txHash = await window.ethereum.request({
      method: "eth_sendTransaction",
      params: [{
        from: userAccount,
        to: boundAddress,
        value: "0x0",
        data: hexData
      }]
    });

    resultDiv.innerHTML = `<span style="color: var(--brass-accent); font-weight: 700;">Broadcasted: <a href="https://basescan.org/tx/${txHash}" target="_blank" rel="noopener noreferrer" style="color: var(--brass-accent); text-decoration: underline;">${txHash.slice(0, 10)}...${txHash.slice(-6)}</a>. Recording to Sibyl Memory...</span>`;

    // 4. Submit txHash to Clerk
    const res = await fetch("/api/clerk/ping", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId, confirm: true, tx_hash: txHash })
    });
    const data = await res.json();

    if (data.status === "pinged") {
      resultDiv.innerHTML = `<span style="color: var(--brass-accent); font-weight: 700;">CONFIRMED ONCHAIN: <a href="https://basescan.org/tx/${txHash}" target="_blank" rel="noopener noreferrer" style="color: var(--brass-accent); text-decoration: underline;">${txHash}</a></span>`;
      showToast("Ping confirmed onchain.");
    } else {
      resultDiv.innerHTML = `<span style="color: var(--signal-red);">Error logging to Clerk: ${data.reason || "Unknown"}</span>`;
    }

    await refreshAll();
  } catch (err) {
    console.error("Wallet ping error:", err);
    const msg = err.message || "User cancelled or transaction failed";
    resultDiv.innerHTML = `<span style="color: var(--signal-red);">Signing failed: ${msg.slice(0, 60)}</span>`;
  }
}

function toggleEditWallet(show) {
  const form = document.getElementById("edit-wallet-form");
  if (form) {
    form.style.display = show ? "flex" : "none";
    if (show) {
      const input = document.getElementById("bind-wallet-input");
      if (input) input.focus();
    }
  }
}

async function handleBindWallet(personName, taskId) {
  const input = document.getElementById("bind-wallet-input");
  const rawAddress = (input ? input.value : "").trim();
  
  if (!rawAddress) {
    alert("Please enter a Base wallet address (e.g. 0x...).");
    return;
  }
  
  if (!/^0x[a-fA-F0-9]{40}$/.test(rawAddress)) {
    alert("Invalid address format. Address must start with 0x followed by 40 hex characters.");
    return;
  }

  try {
    const res = await fetch("/api/clerk/bind_wallet", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ person_name: personName, address: rawAddress })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.detail || "Failed to bind wallet.");
      return;
    }
    showToast(`Wallet bound to ${personName}.`);
    await loadTaskDetails(taskId);
    await loadQueue();
  } catch (err) {
    alert("Error binding wallet: " + err.message);
  }
}

