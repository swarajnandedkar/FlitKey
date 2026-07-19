// Snippet Databases
const SNIPPET_PACKS = {
  all: [
    { trigger: ":shrug", name: "Shrug Emoji", replace: "¯\\_(ツ)_/¯", category: "General", desc: "Inserts shrug emoticon" },
    { trigger: ":date", name: "Current Date", replace: "", category: "Utility", desc: "Inserts today's date dynamically" },
    { trigger: ":time", name: "Current Time", replace: "", category: "Utility", desc: "Inserts the current time dynamically" },
    { trigger: ":lg", name: "Looks Good", replace: "Looks good to me! 👍", category: "Developer", desc: "Quick PR approval message" },
    { trigger: ":ty", name: "Thank You Note", replace: "Thank you so much for reaching out! Please let me know if you have any questions or need further assistance.", category: "Support", desc: "Polite support closing" },
    { trigger: ":inv", name: "Client Invoice Email", replace: "Dear client,\n\nPlease find the invoice for this month's services attached. Let me know if you need any adjustments or if you have any questions.\n\nBest regards,\n[Your Name]", category: "Freelancer", desc: "Standard invoicing email" },
    { trigger: ":wsp", name: "Warm Regards", replace: "Warm regards,\n\nSwaraj Nandedkar", category: "General", desc: "Professional signature email" },
    { trigger: ":review", name: "AI Code Review Prompt", replace: "Please perform a detailed code review of this code chunk. Focus on readability, potential edge-case errors, architectural bottlenecks, and compliance with modern JavaScript/CSS best practices.", category: "AI Prompts", desc: "Snippet for prompting AI systems" }
  ],
  dev: [
    { trigger: ":lg", name: "Looks Good", replace: "Looks good to me! 👍", category: "Developer", desc: "Quick PR approval message" },
    { trigger: ":issue", name: "GitHub Issue Template", replace: "### Describe the bug\n\n### Steps to reproduce\n1. Go to...\n2. Click on...\n3. Scroll to...\n\n### Expected behavior\n\n### Screenshots/Logs\n\n### Environment\n- OS: \n- Version: ", category: "Developer", desc: "Markdown bug template" },
    { trigger: ":docs", name: "JSDoc Comment block", replace: "/**\n * @function\n * @param {string} paramName - Description\n * @returns {Promise<void>} Description\n */", category: "Developer", desc: "Standard JSDoc code documentation block" },
    { trigger: ":lgtm", name: "LGTM detailed", replace: "Looks good to me! Ready for review. Tests passed on local environment.", category: "Developer", desc: "Detailed review confirmation" }
  ],
  support: [
    { trigger: ":ty", name: "Thank You Note", replace: "Thank you so much for reaching out! Please let me know if you have any questions or need further assistance.", category: "Support", desc: "Polite support closing" },
    { trigger: ":refund", name: "Refund Process Instruction", replace: "Dear Customer,\n\nWe have initiated your refund request. The funds should reflect in your account within 3-5 business days depending on your bank.\n\nLet us know if you need anything else.", category: "Support", desc: "Instructions for billing issues" },
    { trigger: ":steps", name: "Troubleshooting Steps", replace: "Could you please try the following troubleshooting steps:\n1. Clear your browser cache and cookies.\n2. Restart the TypeFlux desktop daemon.\n3. Verify your system permissions.\n\nLet us know if the issue persists.", category: "Support", desc: "Standard app error guide" }
  ],
  freelance: [
    { trigger: ":inv", name: "Client Invoice Email", replace: "Dear client,\n\nPlease find the invoice for this month's services attached. Let me know if you need any adjustments or if you have any questions.\n\nBest regards,\n[Your Name]", category: "Freelancer", desc: "Standard invoicing email" },
    { trigger: ":pitch", name: "Proposal Follow-up", replace: "Hi [Name],\n\nHope you are doing well! I'm following up on the proposal sent last week regarding the TypeFlux web design. I'm keen to hear your feedback and begin building the components.\n\nBest,", category: "Freelancer", desc: "Client pitch nudge template" },
    { trigger: ":update", name: "Weekly Status Update", replace: "Hi team,\n\nHere is a quick summary of progress this week:\n- Created initial design assets per branding specifications.\n- Integrated light/dark mode stylesheets.\n- Completed interactive demo component testing.\n\nNext steps: Launch beta builds and clear code warnings.", category: "Freelancer", desc: "Project milestone status report" }
  ],
  ai: [
    { trigger: ":review", name: "AI Code Review Prompt", replace: "Please perform a detailed code review of this code chunk. Focus on readability, potential edge-case errors, architectural bottlenecks, and compliance with modern JavaScript/CSS best practices.", category: "AI Prompts", desc: "Snippet for prompting AI systems" },
    { trigger: ":sum", name: "Summarize Text Prompt", replace: "Summarize the text below in three bullet points. Focus on key strategic findings, major action sequences, and metrics of success.", category: "AI Prompts", desc: "Short summarization helper template" },
    { trigger: ":translate", name: "Translate To Spanish", replace: "Translate the following block into professional Spanish, keeping technical variables and code placeholders intact:", category: "AI Prompts", desc: "Translation directive" }
  ]
};

// Global State
let currentSnippets = [...SNIPPET_PACKS.all];
let selectedIndex = 0;
let currentPlatform = "windows";

// Stats Tracker (State kept in memory for browser trial, initialized to local strategy targets)
let sessionExpansions = 214;
let sessionCharsSaved = 18600;
let sessionTimeSaved = 1.5; // in hours

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initRaycastSimulator();
  initSandboxListener();
  initOSSelector();
  initPackLoaders();
  initFAQ();
});

/* ==========================================================================
   1. Light-Dark Mode Implementation
   ========================================================================== */
function initTheme() {
  const themeToggle = document.getElementById("theme-toggle");
  
  // Handled by header script, but let's sync button states
  const getTheme = () => document.documentElement.getAttribute("data-theme") || "light";
  
  themeToggle.addEventListener("click", () => {
    const current = getTheme();
    const target = current === "dark" ? "light" : "dark";
    
    document.documentElement.setAttribute("data-theme", target);
    localStorage.setItem("color-scheme", target);
  });

  // Watch for system color-scheme updates
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    if (!localStorage.getItem("color-scheme")) {
      const target = e.matches ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", target);
    }
  });
}

/* ==========================================================================
   2. Simulated Raycast Desktop App Manager
   ========================================================================== */
function initRaycastSimulator() {
  const searchInput = document.getElementById("raycast-input");
  
  // Render snippet list
  renderSnippetList();

  // Search logic
  searchInput.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    filterSnippets(query);
  });

  // Keyboard navigation inside simulator
  searchInput.addEventListener("keydown", (e) => {
    const items = document.querySelectorAll(".snippet-item");
    if (!items.length) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectedIndex = (selectedIndex + 1) % items.length;
      updateListSelection();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      selectedIndex = (selectedIndex - 1 + items.length) % items.length;
      updateListSelection();
    } else if (e.key === "Enter") {
      e.preventDefault();
      insertSelectedSnippet();
    }
  });

  // Focus search input when Ctrl + K is pressed
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      searchInput.focus();
      // Scroll smoothly to demo section
      document.getElementById("demo").scrollIntoView({ behavior: "smooth" });
    }
  });
}

function renderSnippetList() {
  const container = document.getElementById("snippet-list-items");
  container.innerHTML = "";
  
  if (currentSnippets.length === 0) {
    container.innerHTML = `<div class="snippet-item" style="cursor: default; pointer-events: none; color: var(--text-tertiary);">No matching snippets found.</div>`;
    updateDetailsPane(null);
    return;
  }

  currentSnippets.forEach((snippet, index) => {
    const item = document.createElement("div");
    item.className = `snippet-item ${index === selectedIndex ? 'selected' : ''}`;
    
    // Calculate dynamic values if needed
    const displayVal = getReplacementValue(snippet);
    
    item.innerHTML = `
      <div class="snippet-info">
        <span class="snippet-name">${snippet.name}</span>
        <span class="snippet-desc">${snippet.desc}</span>
      </div>
      <span class="snippet-trigger-badge">${snippet.trigger}</span>
    `;

    item.addEventListener("click", () => {
      selectedIndex = index;
      updateListSelection();
    });

    container.appendChild(item);
  });

  updateListSelection();
}

function updateListSelection() {
  const items = document.querySelectorAll(".snippet-item");
  items.forEach((item, index) => {
    if (index === selectedIndex) {
      item.classList.add("selected");
      // Scroll element into view inside parent scrollable
      item.scrollIntoView({ block: "nearest" });
    } else {
      item.classList.remove("selected");
    }
  });

  // Update Detail Pane
  if (currentSnippets[selectedIndex]) {
    updateDetailsPane(currentSnippets[selectedIndex]);
  }
}

function updateDetailsPane(snippet) {
  const pane = document.getElementById("snippet-detail");
  if (!snippet) {
    pane.innerHTML = `
      <div style="text-align: center; color: var(--text-tertiary); margin-top: 40px;">
        <p>No snippet selected.</p>
      </div>
    `;
    return;
  }

  const cleanReplace = getReplacementValue(snippet);

  pane.innerHTML = `
    <div class="detail-header">
      <div class="detail-cat">${snippet.category}</div>
      <h4 class="detail-title">${snippet.name}</h4>
    </div>
    
    <div class="detail-section">
      <h5>Shortcut Trigger</h5>
      <kbd>${snippet.trigger}</kbd>
    </div>

    <div class="detail-section">
      <h5>Snippet Output Preview</h5>
      <div class="detail-preview-box">${escapeHtml(cleanReplace)}</div>
    </div>

    <div class="detail-meta">
      <div class="detail-meta-row">
        <span class="label">Character Length:</span>
        <span class="val">${cleanReplace.length} chars</span>
      </div>
      <div class="detail-meta-row">
        <span class="label">Input saved ratio:</span>
        <span class="val">${(cleanReplace.length / Math.max(1, snippet.trigger.length)).toFixed(1)}x shorter</span>
      </div>
      <div class="detail-meta-row">
        <span class="label">Local Status:</span>
        <span class="val" style="color: var(--success)">✓ System Active</span>
      </div>
    </div>

    <button class="btn btn-primary btn-small btn-detail-insert" id="btn-insert-now">
      Insert Snippet
    </button>
  `;

  // Attach listener to insert button
  document.getElementById("btn-insert-now").addEventListener("click", () => {
    insertSelectedSnippet();
  });
}

function filterSnippets(query) {
  if (!query) {
    currentSnippets = [...SNIPPET_PACKS.all];
  } else {
    currentSnippets = SNIPPET_PACKS.all.filter(s => 
      s.name.toLowerCase().includes(query) ||
      s.trigger.toLowerCase().includes(query) ||
      s.category.toLowerCase().includes(query) ||
      s.desc.toLowerCase().includes(query)
    );
  }
  selectedIndex = 0;
  renderSnippetList();
}

function getReplacementValue(snippet) {
  if (snippet.trigger === ":date") {
    const today = new Date();
    return today.toISOString().split('T')[0]; // YYYY-MM-DD
  }
  if (snippet.trigger === ":time") {
    const today = new Date();
    return today.toTimeString().split(' ')[0].substring(0, 5); // HH:MM
  }
  return snippet.replace;
}

function insertSelectedSnippet() {
  const snippet = currentSnippets[selectedIndex];
  if (!snippet) return;

  const val = getReplacementValue(snippet);
  const textarea = document.getElementById("demo-textarea");
  
  // Insert at cursor
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const currentText = textarea.value;
  
  textarea.value = currentText.substring(0, start) + val + currentText.substring(end);
  textarea.focus();
  textarea.selectionStart = textarea.selectionEnd = start + val.length;
  
  // Update char count
  updateCharCount(textarea.value.length);
  
  // Show toast feedback
  showToast(snippet.trigger, val);
}

/* ==========================================================================
   3. Text Editor Sandbox & Expansion Simulation
   ========================================================================== */
function initSandboxListener() {
  const textarea = document.getElementById("demo-textarea");
  const clearBtn = document.getElementById("clear-sandbox");

  textarea.addEventListener("input", (e) => {
    const text = e.target.value;
    updateCharCount(text.length);
    
    // Check for trigger match (we match when word is finished / space is typed or custom input detection)
    // For browser demo, we check if the user typed a known trigger keyword
    // We scan the words of the text
    SNIPPET_PACKS.all.forEach(snippet => {
      const trigger = snippet.trigger;
      // We look if text ends with the trigger keyword
      if (text.endsWith(trigger)) {
        const replaceVal = getReplacementValue(snippet);
        
        // Perform local text expansion
        const startPos = text.length - trigger.length;
        const expandedText = text.substring(0, startPos) + replaceVal;
        
        textarea.value = expandedText;
        updateCharCount(expandedText.length);
        
        // Show success toast
        showToast(trigger, replaceVal);
        
        // Record simulated productivity stats!
        recordSavedTime(trigger.length, replaceVal.length);
      }
    });
  });

  clearBtn.addEventListener("click", () => {
    textarea.value = "";
    textarea.focus();
    updateCharCount(0);
  });
}

function updateCharCount(length) {
  document.getElementById("editor-char-count").innerText = `${length} chars`;
}

function showToast(trigger, replacement) {
  const toast = document.getElementById("demo-toast");
  const msg = document.getElementById("toast-message");
  
  const shortRepl = replacement.length > 25 ? replacement.substring(0, 22) + "..." : replacement;
  msg.innerHTML = `Expanded <strong>${trigger}</strong> ➔ <code>${escapeHtml(shortRepl)}</code>`;
  
  toast.classList.remove("hidden");
  
  // Hide after 3 seconds
  if (window.toastTimeout) clearTimeout(window.toastTimeout);
  window.toastTimeout = setTimeout(() => {
    toast.classList.add("hidden");
  }, 3000);
}

function recordSavedTime(triggerLen, replaceLen) {
  const diff = replaceLen - triggerLen;
  if (diff <= 0) return;

  sessionExpansions += 1;
  sessionCharsSaved += diff;
  
  // Calculate average typing speed 40WPM (~200 characters per minute)
  // Time saved = chars / (200 chars / min) = chars / 200 minutes
  const additionalMin = diff / 200;
  const additionalHrs = additionalMin / 60;
  sessionTimeSaved += additionalHrs;

  // Update DOM elements on the productivity card
  const numberBoxes = document.querySelectorAll(".stat-number-box .number");
  if (numberBoxes.length >= 3) {
    numberBoxes[0].innerText = sessionExpansions;
    
    // Formatting big numbers
    if (sessionCharsSaved >= 1000) {
      numberBoxes[1].innerText = `${(sessionCharsSaved / 1000).toFixed(1)}k`;
    } else {
      numberBoxes[1].innerText = sessionCharsSaved;
    }

    numberBoxes[2].innerText = `${sessionTimeSaved.toFixed(1)}h`;
  }
}

/* ==========================================================================
   4. OS Switcher Sim
   ========================================================================== */
function initOSSelector() {
  const toggles = document.querySelectorAll(".os-toggle");
  
  toggles.forEach(toggle => {
    toggle.addEventListener("click", (e) => {
      toggles.forEach(t => t.classList.remove("active"));
      e.target.classList.add("active");
      
      currentPlatform = e.target.getAttribute("data-platform");
      
      // Update UI characteristics for Raycast mock window
      const appWindow = document.getElementById("app-window");
      const engineText = document.querySelector(".status-txt");
      
      if (currentPlatform === "linux") {
        engineText.innerText = "X11 Daemon Active";
        appWindow.style.borderLeftColor = "rgba(79, 70, 229, 0.4)";
      } else {
        engineText.innerText = "Engine Active";
        appWindow.style.borderLeftColor = "";
      }
    });
  });
}

/* ==========================================================================
   5. Pack Loaders (Integration with interactive editor)
   ========================================================================== */
function initPackLoaders() {
  const packBtns = document.querySelectorAll(".view-pack-btn");
  const searchInput = document.getElementById("raycast-input");

  packBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      const packId = e.target.getAttribute("data-pack");
      const packItems = SNIPPET_PACKS[packId];
      
      if (packItems) {
        // Load snippets into active grid
        currentSnippets = [...packItems];
        selectedIndex = 0;
        renderSnippetList();
        
        // Focus search input or simulator
        searchInput.focus();
        document.getElementById("demo").scrollIntoView({ behavior: "smooth" });
        
        // Show trigger indicator toast
        const packNames = {
          dev: "Developer & GitHub",
          support: "Customer Support",
          freelance: "Freelancer Client",
          ai: "AI Prompt Engineering"
        };
        
        showGeneralToast(`Loaded <strong>${packNames[packId]} Pack</strong> into preview! Try typing triggers on the left.`);
      }
    });
  });
}

function showGeneralToast(htmlContent) {
  const toast = document.getElementById("demo-toast");
  const msg = document.getElementById("toast-message");
  
  msg.innerHTML = htmlContent;
  toast.classList.remove("hidden");
  
  if (window.toastTimeout) clearTimeout(window.toastTimeout);
  window.toastTimeout = setTimeout(() => {
    toast.classList.add("hidden");
  }, 4000);
}

/* ==========================================================================
   6. FAQ Accordion Interaction
   ========================================================================== */
function initFAQ() {
  const faqItems = document.querySelectorAll(".faq-item");

  faqItems.forEach(item => {
    const trigger = item.querySelector(".faq-trigger");
    const content = item.querySelector(".faq-content");
    const icon = item.querySelector(".faq-icon");

    trigger.addEventListener("click", () => {
      const isOpen = item.classList.contains("active");

      // Close all items
      faqItems.forEach(i => {
        i.classList.remove("active");
        i.querySelector(".faq-trigger").setAttribute("aria-expanded", "false");
        i.querySelector(".faq-content").setAttribute("hidden", "true");
      });

      // Open clicked item if it was closed
      if (!isOpen) {
        item.classList.add("active");
        trigger.setAttribute("aria-expanded", "true");
        content.removeAttribute("hidden");
      }
    });
  });
}

/* ==========================================================================
   Helpers
   ========================================================================== */
function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
