/**
 * FlitKey Content Script
 * Listens to typing on web pages, expands typed keywords into snippets,
 * and handles direct text insertion into active inputs/editable elements.
 * Supports unlimited word count expansion (multi-line & multi-paragraph).
 */

(function () {
  if (window.__flitkey_content_script_injected) return;
  window.__flitkey_content_script_injected = true;

  let keyBuffer = '';
  let activeElement = null;
  let cachedSnippets = [];
  let cachedSettings = { paused: false, case_sensitive: false, show_toast: true };

  // Load state from background service worker
  function updateState() {
    chrome.runtime.sendMessage({ action: 'GET_STATE' }, (response) => {
      if (response && response.snippets) {
        cachedSnippets = response.snippets;
        cachedSettings = response.settings || cachedSettings;
      }
    });
  }

  updateState();

  // Listen for storage changes
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'local') {
      if (changes.snippets) cachedSnippets = changes.snippets.newValue || [];
      if (changes.settings) cachedSettings = changes.settings.newValue || cachedSettings;
    }
  });

  // Track focused element
  document.addEventListener('focusin', (e) => {
    if (isEditable(e.target)) {
      activeElement = e.target;
      keyBuffer = '';
    }
  });

  function isEditable(el) {
    if (!el) return false;
    const tagName = el.tagName ? el.tagName.toLowerCase() : '';
    return (
      tagName === 'input' ||
      tagName === 'textarea' ||
      el.isContentEditable ||
      el.getAttribute?.('contenteditable') === 'true'
    );
  }

  // Monitor keydown events
  document.addEventListener('keydown', (e) => {
    if (cachedSettings.paused) return;
    const el = e.target;
    if (!isEditable(el)) return;

    activeElement = el;

    if (e.key === 'Backspace') {
      keyBuffer = keyBuffer.slice(0, -1);
      return;
    }

    if (e.key === 'Escape' || e.key === 'Tab') {
      keyBuffer = '';
      return;
    }

    if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
      keyBuffer += e.key;
      // Cap buffer length to prevent keybuffer memory growth
      if (keyBuffer.length > 100) {
        keyBuffer = keyBuffer.slice(-100);
      }
      checkAndExpand(el);
    }
  });

  async function checkAndExpand(el) {
    if (!keyBuffer || cachedSettings.paused) return;

    const enabledKeywords = cachedSnippets.filter(s => s.enabled && s.trigger_type === 'keyword' && s.keyword);

    for (const snippet of enabledKeywords) {
      const kw = snippet.keyword;
      let matched = false;

      if (cachedSettings.case_sensitive) {
        matched = keyBuffer.endsWith(kw);
      } else {
        matched = keyBuffer.toLowerCase().endsWith(kw.toLowerCase());
      }

      if (matched) {
        keyBuffer = '';
        await expandSnippetInElement(el, kw, snippet.expansion_text, snippet.label);
        break;
      }
    }
  }

  async function expandSnippetInElement(el, keyword, expansionText, label) {
    const { renderedText, cursorIndex } = await FlitKeyPlaceholders.render(expansionText);

    const tagName = el.tagName ? el.tagName.toLowerCase() : '';

    if (tagName === 'input' || tagName === 'textarea') {
      const start = el.selectionStart || 0;
      const end = el.selectionEnd || 0;
      const val = el.value || '';

      // Calculate where keyword starts
      const kwLen = keyword ? keyword.length : 0;
      const replaceStart = Math.max(0, start - kwLen);

      const before = val.substring(0, replaceStart);
      const after = val.substring(end);

      // Bypass maxlength restriction if present
      const origMaxLength = el.getAttribute('maxlength');
      if (origMaxLength && (before.length + renderedText.length + after.length) > parseInt(origMaxLength, 10)) {
        el.removeAttribute('maxlength');
      }

      el.value = before + renderedText + after;

      if (origMaxLength) {
        el.setAttribute('maxlength', origMaxLength);
      }

      // Position cursor
      let newCursorPos = replaceStart + renderedText.length;
      if (cursorIndex !== -1) {
        newCursorPos = replaceStart + cursorIndex;
      }

      try {
        el.setSelectionRange(newCursorPos, newCursorPos);
      } catch (e) {
        // Ignore for input types that don't support selection range (e.g. email, number)
      }

      // Trigger standard input/change events for framework compatibility (React/Vue/Angular)
      el.dispatchEvent(new Event('beforeinput', { bubbles: true, cancelable: true }));
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    } else if (el.isContentEditable || el.getAttribute?.('contenteditable') === 'true') {
      // Robust ContentEditable insertion for large multi-line & multi-paragraph text
      const sel = window.getSelection();
      if (sel && sel.rangeCount > 0) {
        const range = sel.getRangeAt(0);

        // Delete the typed keyword
        if (keyword && keyword.length > 0) {
          for (let i = 0; i < keyword.length; i++) {
            document.execCommand('delete', false, null);
          }
        }

        let inserted = false;
        try {
          const currentRange = window.getSelection().getRangeAt(0);
          currentRange.deleteContents();

          const fragment = document.createDocumentFragment();
          const lines = renderedText.split('\n');
          let cursorTargetNode = null;
          let cursorTargetOffset = 0;
          let charCounter = 0;

          lines.forEach((line, idx) => {
            if (idx > 0) {
              fragment.appendChild(document.createElement('br'));
              charCounter += 1;
            }
            if (line.length > 0) {
              const textNode = document.createTextNode(line);
              fragment.appendChild(textNode);

              if (cursorIndex !== -1 && !cursorTargetNode) {
                if (charCounter + line.length >= cursorIndex) {
                  cursorTargetNode = textNode;
                  cursorTargetOffset = cursorIndex - charCounter;
                }
              }
              charCounter += line.length;
            }
          });

          const lastNode = fragment.lastChild;
          currentRange.insertNode(fragment);

          if (cursorTargetNode) {
            currentRange.setStart(cursorTargetNode, cursorTargetOffset);
            currentRange.setEnd(cursorTargetNode, cursorTargetOffset);
          } else if (lastNode) {
            currentRange.setStartAfter(lastNode);
            currentRange.setEndAfter(lastNode);
          }

          sel.removeAllRanges();
          sel.addRange(currentRange);
          inserted = true;
        } catch (err) {
          console.warn('FlitKey DOM Range insertion fallback:', err);
        }

        if (!inserted) {
          document.execCommand('insertText', false, renderedText);
        }

        el.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }

    if (cachedSettings.show_toast) {
      showToast(`Expanded: ${label || keyword}`);
    }
  }

  // Listen for direct insertion messages from popup/background
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'INSERT_SNIPPET') {
      const targetEl = activeElement || document.activeElement;
      if (isEditable(targetEl)) {
        (async () => {
          await expandSnippetInElement(targetEl, '', message.snippetText, 'FlitKey Quick Insert');
          sendResponse({ success: true });
        })();
        return true;
      } else {
        // Fallback: Copy to clipboard if no editable element is focused
        (async () => {
          const { renderedText } = await FlitKeyPlaceholders.render(message.snippetText);
          try {
            await navigator.clipboard.writeText(renderedText);
            showToast('Snippet copied to clipboard!');
            sendResponse({ success: true, copied: true });
          } catch (err) {
            showToast('Failed to copy snippet to clipboard');
            sendResponse({ success: false, error: err.message });
          }
        })();
        return true;
      }
    }
  });

  // UI Toast Notification
  function showToast(text) {
    let toast = document.getElementById('flitkey-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'flitkey-toast';
      toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #102a43;
        color: #ffffff;
        padding: 10px 16px;
        border-radius: 8px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
        font-weight: 500;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        z-index: 2147483647;
        transition: opacity 0.3s ease, transform 0.3s ease;
        opacity: 0;
        transform: translateY(10px);
        pointer-events: none;
      `;
      document.body.appendChild(toast);
    }

    toast.textContent = text;
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';

    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
    }, 2500);
  }
})();
