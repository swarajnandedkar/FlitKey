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

  // Clear keybuffer when pointer/mouse clicks anywhere to prevent stale trigger sequences
  document.addEventListener('pointerdown', () => {
    keyBuffer = '';
  });

  function isEditable(el) {
    if (!el) return false;
    const tagName = el.tagName ? el.tagName.toLowerCase() : '';
    return (
      tagName === 'input' ||
      tagName === 'textarea' ||
      el.isContentEditable ||
      el.getAttribute?.('contenteditable') === 'true' ||
      Boolean(el.closest?.('[contenteditable="true"]'))
    );
  }

  let isExpanding = false;
  let suppressTriggerKey = null;
  let suppressTimeout = null;

  function setTriggerKeySuppression(key) {
    suppressTriggerKey = key;
    clearTimeout(suppressTimeout);
    suppressTimeout = setTimeout(() => {
      suppressTriggerKey = null;
    }, 150);
  }

  // Intercept beforeinput in capture phase so neither the browser nor rich-text editors insert the trigger character
  window.addEventListener('beforeinput', (e) => {
    if (suppressTriggerKey !== null && e.data === suppressTriggerKey) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      suppressTriggerKey = null;
      clearTimeout(suppressTimeout);
    }
  }, true);

  // Intercept legacy keypress in capture phase
  window.addEventListener('keypress', (e) => {
    if (suppressTriggerKey !== null && e.key === suppressTriggerKey) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
    }
  }, true);

  // Intercept keyup in capture phase
  window.addEventListener('keyup', (e) => {
    if (suppressTriggerKey !== null && e.key === suppressTriggerKey) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      suppressTriggerKey = null;
      clearTimeout(suppressTimeout);
    }
  }, true);

  // Find enabled snippet matching the end of the key buffer
  function findMatchingSnippet(buffer) {
    if (!buffer || cachedSettings.paused) return null;
    const enabledKeywords = cachedSnippets
      .filter(s => s.enabled && s.trigger_type === 'keyword' && s.keyword)
      .sort((a, b) => b.keyword.length - a.keyword.length); // Longest match first

    for (const snippet of enabledKeywords) {
      const kw = snippet.keyword;
      let matched = false;

      if (cachedSettings.case_sensitive) {
        matched = buffer.endsWith(kw);
      } else {
        matched = buffer.toLowerCase().endsWith(kw.toLowerCase());
      }

      if (matched) {
        return snippet;
      }
    }
    return null;
  }

  // Monitor keydown events in capture phase to intercept keystrokes before any web app editor processes them
  window.addEventListener('keydown', (e) => {
    if (cachedSettings.paused || isExpanding) return;
    const el = e.target;
    if (!isEditable(el)) return;

    activeElement = el;

    if (e.key === 'Backspace') {
      keyBuffer = keyBuffer.slice(0, -1);
      return;
    }

    if (
      e.key === 'Escape' ||
      e.key === 'Tab' ||
      e.key === 'Enter' ||
      e.key === 'ArrowLeft' ||
      e.key === 'ArrowRight' ||
      e.key === 'ArrowUp' ||
      e.key === 'ArrowDown' ||
      e.key === 'Home' ||
      e.key === 'End'
    ) {
      keyBuffer = '';
      return;
    }

    if (e.isComposing) return;

    if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
      const nextBuffer = (keyBuffer + e.key).slice(-100);
      const matchedSnippet = findMatchingSnippet(nextBuffer);

      if (matchedSnippet) {
        // Prevent the trigger key from being natively inserted into the element
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        setTriggerKeySuppression(e.key);

        keyBuffer = '';
        expandSnippetInElement(el, matchedSnippet.keyword, matchedSnippet.expansion_text, matchedSnippet.label, true);
        return;
      }

      keyBuffer = nextBuffer;
    }
  }, true);

  async function expandSnippetInElement(el, keyword, expansionText, label, isKeydownTrigger = false) {
    if (isExpanding) return;
    isExpanding = true;

    try {
      let renderedText = '';
      let cursorIndex = -1;

      if (FlitKeyPlaceholders.renderSync && !expansionText?.includes('{{clipboard}}')) {
        ({ renderedText, cursorIndex } = FlitKeyPlaceholders.renderSync(expansionText));
      } else {
        ({ renderedText, cursorIndex } = await FlitKeyPlaceholders.render(expansionText));
      }

      const tagName = el.tagName ? el.tagName.toLowerCase() : '';

      if (tagName === 'input' || tagName === 'textarea') {
        const start = el.selectionStart || 0;
        const end = el.selectionEnd || 0;
        const val = el.value || '';

        // Dynamically detect how much of the keyword actually exists in the element before cursor
        const textBefore = val.substring(0, start);
        let matchLen = 0;
        if (keyword && textBefore.endsWith(keyword)) {
          matchLen = keyword.length;
        } else if (keyword && textBefore.endsWith(keyword.slice(0, -1))) {
          matchLen = keyword.length - 1;
        } else if (keyword && !cachedSettings.case_sensitive) {
          if (textBefore.toLowerCase().endsWith(keyword.toLowerCase())) {
            matchLen = keyword.length;
          } else if (textBefore.toLowerCase().endsWith(keyword.slice(0, -1).toLowerCase())) {
            matchLen = keyword.length - 1;
          }
        } else {
          matchLen = isKeydownTrigger ? Math.max(0, (keyword ? keyword.length : 0) - 1) : (keyword ? keyword.length : 0);
        }

        const replaceStart = Math.max(0, start - matchLen);
        const before = val.substring(0, replaceStart);
        const after = val.substring(end);

        // Bypass maxlength restriction if present
        const origMaxLength = el.getAttribute('maxlength');
        if (origMaxLength && (before.length + renderedText.length + after.length) > parseInt(origMaxLength, 10)) {
          el.removeAttribute('maxlength');
        }

        // Try inserting with document.execCommand first (preserves native undo stack)
        let inserted = false;
        try {
          el.focus();
          el.setSelectionRange(replaceStart, end);
          inserted = document.execCommand('insertText', false, renderedText);
        } catch (e) {
          inserted = false;
        }

        if (!inserted) {
          // Fallback: direct assignment with support for framework prototype setters
          const proto = Object.getPrototypeOf(el);
          const protoDesc = Object.getOwnPropertyDescriptor(proto, 'value');
          if (protoDesc && protoDesc.set) {
            protoDesc.set.call(el, before + renderedText + after);
          } else {
            el.value = before + renderedText + after;
          }

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
        } else if (cursorIndex !== -1) {
          const customPos = replaceStart + cursorIndex;
          try {
            el.setSelectionRange(customPos, customPos);
          } catch (e) {}
        }

        if (origMaxLength) {
          el.setAttribute('maxlength', origMaxLength);
        }
      } else if (el.isContentEditable || el.getAttribute?.('contenteditable') === 'true' || el.closest?.('[contenteditable="true"]')) {
        // Robust ContentEditable insertion
        const sel = window.getSelection();
        if (sel && sel.rangeCount > 0) {
          const range = sel.getRangeAt(0);

          // Dynamically detect keyword characters present in the text node
          let matchLen = isKeydownTrigger ? Math.max(0, (keyword ? keyword.length : 0) - 1) : (keyword ? keyword.length : 0);
          if (range.startContainer && range.startContainer.nodeType === Node.TEXT_NODE) {
            const textBefore = range.startContainer.nodeValue.slice(0, range.startOffset);
            if (keyword && textBefore.endsWith(keyword)) {
              matchLen = keyword.length;
            } else if (keyword && textBefore.endsWith(keyword.slice(0, -1))) {
              matchLen = keyword.length - 1;
            } else if (keyword && !cachedSettings.case_sensitive) {
              if (textBefore.toLowerCase().endsWith(keyword.toLowerCase())) {
                matchLen = keyword.length;
              } else if (textBefore.toLowerCase().endsWith(keyword.slice(0, -1).toLowerCase())) {
                matchLen = keyword.length - 1;
              }
            }
          }

          // Delete the typed keyword sequence
          for (let i = 0; i < matchLen; i++) {
            document.execCommand('delete', false, null);
          }

          let inserted = false;
          try {
            // Primary method: native execCommand insertion preserves paragraph structure and doesn't split lines
            inserted = document.execCommand('insertText', false, renderedText);
            if (inserted && cursorIndex !== -1) {
              const moveBack = renderedText.length - cursorIndex;
              for (let i = 0; i < moveBack; i++) {
                sel.modify('move', 'backward', 'character');
              }
            }
          } catch (e) {
            inserted = false;
          }

          if (!inserted) {
            // Safe DOM Range fallback with clean text node boundary positioning
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
                // Place cursor INSIDE the text node at the end, not after it, so it does not start a new paragraph
                if (lastNode.nodeType === Node.TEXT_NODE) {
                  currentRange.setStart(lastNode, lastNode.nodeValue.length);
                  currentRange.setEnd(lastNode, lastNode.nodeValue.length);
                } else {
                  currentRange.setStartAfter(lastNode);
                  currentRange.setEndAfter(lastNode);
                }
              }

              sel.removeAllRanges();
              sel.addRange(currentRange);
              inserted = true;
            } catch (err) {
              console.warn('FlitKey DOM Range insertion fallback:', err);
            }
          }

          el.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }

      if (cachedSettings.show_toast) {
        showToast(`Expanded: ${label || keyword}`);
      }
    } finally {
      isExpanding = false;
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
