/**
 * FlitKey Popup Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  let snippets = [];
  let settings = {};
  let editingId = null;

  const searchInput = document.getElementById('search-input');
  const snippetList = document.getElementById('snippet-list');
  const btnPause = document.getElementById('btn-pause');
  const btnAdd = document.getElementById('btn-add');
  const btnOptions = document.getElementById('btn-options');

  const modalOverlay = document.getElementById('modal-overlay');
  const modalTitle = document.getElementById('modal-title');
  const inputLabel = document.getElementById('input-label');
  const inputTriggerType = document.getElementById('input-trigger-type');
  const inputKeyword = document.getElementById('input-keyword');
  const inputHotkey = document.getElementById('input-hotkey');
  const inputExpansion = document.getElementById('input-expansion');
  const groupKeyword = document.getElementById('group-keyword');
  const groupHotkey = document.getElementById('group-hotkey');
  const btnSaveModal = document.getElementById('btn-save-modal');
  const btnCancelModal = document.getElementById('btn-cancel-modal');

  async function refreshData() {
    const state = await FlitKeyStorage.getState();
    snippets = state.snippets || [];
    settings = state.settings || {};
    updatePauseUI();
    renderSnippets();
  }

  function updatePauseUI() {
    if (settings.paused) {
      btnPause.textContent = 'Resume';
      btnPause.style.background = '#e2e8f0';
      btnPause.style.color = '#475569';
    } else {
      btnPause.textContent = 'Pause';
      btnPause.style.background = '';
      btnPause.style.color = '';
    }
  }

  function renderSnippets() {
    const query = (searchInput.value || '').toLowerCase().trim();
    snippetList.innerHTML = '';

    const filtered = snippets.filter(s => {
      if (!query) return true;
      return (
        s.label.toLowerCase().includes(query) ||
        (s.keyword && s.keyword.toLowerCase().includes(query)) ||
        (s.expansion_text && s.expansion_text.toLowerCase().includes(query))
      );
    });

    if (filtered.length === 0) {
      snippetList.innerHTML = `
        <div class="empty-state">
          ${query ? 'No matching snippets found.' : 'No snippets configured yet. Click "+ Add" to create one.'}
        </div>
      `;
      return;
    }

    filtered.forEach(s => {
      const card = document.createElement('div');
      card.className = 'snippet-card';

      const triggerText = s.trigger_type === 'keyword' ? (s.keyword || 'No keyword') : (s.hotkey || 'No hotkey');

      card.innerHTML = `
        <div class="snippet-header">
          <span class="snippet-label">${escapeHtml(s.label)}</span>
          <span class="snippet-trigger">${escapeHtml(triggerText)}</span>
        </div>
        <div class="snippet-preview">${escapeHtml(s.expansion_text)}</div>
        <div class="snippet-actions">
          <label class="toggle-switch">
            <input type="checkbox" class="chk-enable" ${s.enabled ? 'checked' : ''}>
            <span>Enabled</span>
          </label>
          <div>
            <button class="btn btn-sm btn-insert" title="Insert into active input">Insert</button>
            <button class="btn btn-sm btn-edit" title="Edit Snippet">✏️</button>
            <button class="btn btn-sm btn-delete" title="Delete Snippet">🗑️</button>
          </div>
        </div>
      `;

      // Quick Insert click handler
      card.querySelector('.btn-insert').addEventListener('click', (e) => {
        e.stopPropagation();
        chrome.runtime.sendMessage({
          action: 'INSERT_INTO_ACTIVE_TAB',
          snippetText: s.expansion_text
        }, () => {
          window.close();
        });
      });

      // Enable Toggle handler
      card.querySelector('.chk-enable').addEventListener('change', async (e) => {
        s.enabled = e.target.checked;
        await saveSnippetsState();
      });

      // Edit handler
      card.querySelector('.btn-edit').addEventListener('click', (e) => {
        e.stopPropagation();
        openModal(s);
      });

      // Delete handler
      card.querySelector('.btn-delete').addEventListener('click', async (e) => {
        e.stopPropagation();
        if (confirm(`Are you sure you want to delete "${s.label}"?`)) {
          snippets = snippets.filter(item => item.id !== s.id);
          await saveSnippetsState();
          renderSnippets();
        }
      });

      snippetList.appendChild(card);
    });
  }

  async function saveSnippetsState() {
    await FlitKeyStorage.saveSnippets(snippets);
    chrome.runtime.sendMessage({ action: 'SAVE_SNIPPETS', snippets });
  }

  // Search filter typing listener
  searchInput.addEventListener('input', () => {
    renderSnippets();
  });

  // Pause toggle button listener
  btnPause.addEventListener('click', async () => {
    settings.paused = !settings.paused;
    await FlitKeyStorage.saveSettings(settings);
    chrome.runtime.sendMessage({ action: 'SAVE_SETTINGS', settings });
    updatePauseUI();
  });

  // Open Full Manager Options Page
  btnOptions.addEventListener('click', () => {
    if (chrome.runtime.openOptionsPage) {
      chrome.runtime.openOptionsPage();
    } else {
      window.open(chrome.runtime.getURL('options.html'));
    }
  });

  // Modal Dialog Handlers
  btnAdd.addEventListener('click', () => {
    openModal(null);
  });

  function openModal(snippet = null) {
    editingId = snippet ? snippet.id : null;
    modalTitle.textContent = snippet ? 'Edit Snippet' : 'Add New Snippet';
    inputLabel.value = snippet ? snippet.label : '';
    inputTriggerType.value = snippet ? snippet.trigger_type : 'keyword';
    inputKeyword.value = snippet ? snippet.keyword : '';
    inputHotkey.value = snippet ? snippet.hotkey : '';
    inputExpansion.value = snippet ? snippet.expansion_text : '';

    updateModalFields();
    modalOverlay.classList.add('active');
  }

  function closeModal() {
    modalOverlay.classList.remove('active');
    editingId = null;
  }

  inputTriggerType.addEventListener('change', updateModalFields);

  function updateModalFields() {
    if (inputTriggerType.value === 'keyword') {
      groupKeyword.style.display = 'flex';
      groupHotkey.style.display = 'none';
    } else {
      groupKeyword.style.display = 'none';
      groupHotkey.style.display = 'flex';
    }
  }

  btnCancelModal.addEventListener('click', closeModal);

  btnSaveModal.addEventListener('click', async () => {
    const label = inputLabel.value.trim();
    const trigger_type = inputTriggerType.value;
    const keyword = inputKeyword.value.trim();
    const hotkey = inputHotkey.value.trim();
    const expansion_text = inputExpansion.value;

    if (!label) {
      alert('Snippet Label is required.');
      return;
    }
    if (!expansion_text) {
      alert('Expansion Text is required.');
      return;
    }
    if (trigger_type === 'keyword' && !keyword) {
      alert('Keyword trigger is required for keyword snippets.');
      return;
    }

    if (editingId) {
      const idx = snippets.findIndex(s => s.id === editingId);
      if (idx !== -1) {
        snippets[idx] = {
          ...snippets[idx],
          label,
          trigger_type,
          keyword,
          hotkey,
          expansion_text
        };
      }
    } else {
      snippets.push({
        id: FlitKeyStorage.generateId(),
        label,
        trigger_type,
        keyword,
        hotkey,
        expansion_text,
        enabled: true
      });
    }

    await saveSnippetsState();
    closeModal();
    renderSnippets();
  });

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  await refreshData();
});
