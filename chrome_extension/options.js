/**
 * FlitKey Options Page Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  let snippets = [];
  let settings = {};
  let editingId = null;

  const tableBody = document.getElementById('table-body');
  const searchInput = document.getElementById('search-main');

  const btnAddMain = document.getElementById('btn-add-main');
  const btnExport = document.getElementById('btn-export');
  const btnImportTrigger = document.getElementById('btn-import-trigger');
  const fileImport = document.getElementById('file-import');

  const chkCaseSensitive = document.getElementById('chk-case-sensitive');
  const chkShowToast = document.getElementById('chk-show-toast');
  const chkPaused = document.getElementById('chk-paused');

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

  async function loadData() {
    const state = await FlitKeyStorage.getState();
    snippets = state.snippets || [];
    settings = state.settings || {};

    chkCaseSensitive.checked = !!settings.case_sensitive;
    chkShowToast.checked = settings.show_toast !== false;
    chkPaused.checked = !!settings.paused;

    renderTable();
  }

  function renderTable() {
    const query = (searchInput.value || '').toLowerCase().trim();
    tableBody.innerHTML = '';

    const filtered = snippets.filter(s => {
      if (!query) return true;
      return (
        s.label.toLowerCase().includes(query) ||
        (s.keyword && s.keyword.toLowerCase().includes(query)) ||
        (s.expansion_text && s.expansion_text.toLowerCase().includes(query))
      );
    });

    if (filtered.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 30px;">
            No snippets found.
          </td>
        </tr>
      `;
      return;
    }

    filtered.forEach(s => {
      const tr = document.createElement('tr');
      const triggerDisplay = s.trigger_type === 'keyword' ? (s.keyword || 'None') : (s.hotkey || 'None');

      tr.innerHTML = `
        <td><strong>${escapeHtml(s.label)}</strong></td>
        <td><span class="snippet-trigger">${escapeHtml(triggerDisplay)}</span></td>
        <td style="max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(s.expansion_text)}</td>
        <td>
          <label class="toggle-switch">
            <input type="checkbox" class="chk-enable" ${s.enabled ? 'checked' : ''}>
            <span>${s.enabled ? 'Enabled' : 'Disabled'}</span>
          </label>
        </td>
        <td>
          <button class="btn btn-sm btn-edit">Edit</button>
          <button class="btn btn-sm btn-delete" style="color: #ef4444;">Delete</button>
        </td>
      `;

      tr.querySelector('.chk-enable').addEventListener('change', async (e) => {
        s.enabled = e.target.checked;
        await saveSnippets();
        renderTable();
      });

      tr.querySelector('.btn-edit').addEventListener('click', () => {
        openModal(s);
      });

      tr.querySelector('.btn-delete').addEventListener('click', async () => {
        if (confirm(`Delete snippet "${s.label}"?`)) {
          snippets = snippets.filter(item => item.id !== s.id);
          await saveSnippets();
          renderTable();
        }
      });

      tableBody.appendChild(tr);
    });
  }

  async function saveSnippets() {
    await FlitKeyStorage.saveSnippets(snippets);
    chrome.runtime.sendMessage({ action: 'SAVE_SNIPPETS', snippets });
  }

  async function saveSettings() {
    await FlitKeyStorage.saveSettings(settings);
    chrome.runtime.sendMessage({ action: 'SAVE_SETTINGS', settings });
  }

  // Preferences Change Listeners
  chkCaseSensitive.addEventListener('change', () => {
    settings.case_sensitive = chkCaseSensitive.checked;
    saveSettings();
  });

  chkShowToast.addEventListener('change', () => {
    settings.show_toast = chkShowToast.checked;
    saveSettings();
  });

  chkPaused.addEventListener('change', () => {
    settings.paused = chkPaused.checked;
    saveSettings();
  });

  searchInput.addEventListener('input', renderTable);

  // Export JSON
  btnExport.addEventListener('click', () => {
    const payload = {
      version: '0.4.0',
      exported_at: new Date().toISOString(),
      snippets,
      settings
    };
    const jsonStr = JSON.stringify(payload, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `flitkey_snippets_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // Import Snippets
  btnImportTrigger.addEventListener('click', () => {
    fileImport.click();
  });

  fileImport.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (evt) => {
      try {
        const content = evt.target.result;
        const imported = FlitKeyImporter.parseFile(content, file.name);

        if (!imported || imported.length === 0) {
          alert('No valid snippets found in selected file.');
          return;
        }

        snippets.push(...imported);
        await saveSnippets();
        renderTable();
        alert(`Successfully imported ${imported.length} snippet(s)!`);
      } catch (err) {
        alert(`Failed to import file: ${err.message}`);
      } finally {
        fileImport.value = '';
      }
    };
    reader.readAsText(file);
  });

  // Modal Dialog Logic
  btnAddMain.addEventListener('click', () => openModal(null));

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

    await saveSnippets();
    closeModal();
    renderTable();
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

  await loadData();
});
