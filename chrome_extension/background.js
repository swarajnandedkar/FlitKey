/**
 * FlitKey Background Service Worker
 * Handles extension lifecycle, storage sync, context menus, and messaging
 */

importScripts('lib/placeholders.js', 'lib/storage.js');

// Helper to rebuild context menus from active snippets
async function refreshContextMenus() {
  try {
    await chrome.contextMenus.removeAll();

    const { snippets, settings } = await FlitKeyStorage.getState();
    if (settings.paused) {
      chrome.action.setBadgeText({ text: 'OFF' });
      chrome.action.setBadgeBackgroundColor({ color: '#888888' });
      return;
    } else {
      chrome.action.setBadgeText({ text: '' });
    }

    const enabledSnippets = snippets.filter(s => s.enabled);
    if (enabledSnippets.length === 0) return;

    chrome.contextMenus.create({
      id: 'flitkey-root',
      title: 'FlitKey Snippets',
      contexts: ['editable']
    });

    enabledSnippets.slice(0, 20).forEach(snippet => {
      chrome.contextMenus.create({
        id: `snip_${snippet.id}`,
        parentId: 'flitkey-root',
        title: `${snippet.label} (${snippet.trigger_type === 'keyword' ? snippet.keyword : snippet.hotkey || 'No trigger'})`,
        contexts: ['editable']
      });
    });
  } catch (err) {
    console.error('FlitKey: Failed to refresh context menus:', err);
  }
}

// On Extension Installation or Startup
chrome.runtime.onInstalled.addListener(async () => {
  await FlitKeyStorage.getState(); // Initializes default snippets & settings
  await refreshContextMenus();
});

chrome.runtime.onStartup.addListener(async () => {
  await refreshContextMenus();
});

// Listen for storage changes to update context menus & badge automatically
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local' && (changes.snippets || changes.settings)) {
    refreshContextMenus();
  }
});

// Handle Context Menu click
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!tab || !tab.id || !info.menuItemId.startsWith('snip_')) return;

  const snippetId = info.menuItemId.replace('snip_', '');
  const { snippets } = await FlitKeyStorage.getState();
  const snippet = snippets.find(s => s.id === snippetId);

  if (snippet) {
    chrome.tabs.sendMessage(tab.id, {
      action: 'INSERT_SNIPPET',
      snippetText: snippet.expansion_text
    });
  }
});

// Handle Messages from Popup, Options, or Content Scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      if (message.action === 'GET_STATE') {
        const state = await FlitKeyStorage.getState();
        sendResponse(state);
      } else if (message.action === 'SAVE_SNIPPETS') {
        await FlitKeyStorage.saveSnippets(message.snippets);
        await refreshContextMenus();
        sendResponse({ success: true });
      } else if (message.action === 'SAVE_SETTINGS') {
        await FlitKeyStorage.saveSettings(message.settings);
        await refreshContextMenus();
        sendResponse({ success: true });
      } else if (message.action === 'TOGGLE_PAUSE') {
        const { snippets, settings } = await FlitKeyStorage.getState();
        settings.paused = !settings.paused;
        await FlitKeyStorage.saveSettings(settings);
        await refreshContextMenus();
        sendResponse({ success: true, paused: settings.paused });
      } else if (message.action === 'INSERT_INTO_ACTIVE_TAB') {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.id) {
          chrome.tabs.sendMessage(tab.id, {
            action: 'INSERT_SNIPPET',
            snippetText: message.snippetText
          });
          sendResponse({ success: true });
        } else {
          sendResponse({ success: false, error: 'No active tab found' });
        }
      }
    } catch (err) {
      console.error('FlitKey Background Error:', err);
      sendResponse({ success: false, error: err.message });
    }
  })();
  return true; // Keep channel open for async response
});
