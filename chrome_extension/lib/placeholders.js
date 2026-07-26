/**
 * FlitKey Placeholders Engine
 * Render dynamic tokens: {{date}}, {{time}}, {{datetime}}, {{clipboard}}, {{cursor}}
 */

const FlitKeyPlaceholders = {
  formatDate(date = new Date()) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  },

  formatTime(date = new Date()) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
  },

  formatDateTime(date = new Date()) {
    return `${this.formatDate(date)} ${this.formatTime(date)}`;
  },

  async getClipboardText() {
    try {
      if (navigator.clipboard && navigator.clipboard.readText) {
        return (await navigator.clipboard.readText()) || '';
      }
    } catch (e) {
      console.warn('FlitKey: Clipboard read access not available or denied:', e);
    }
    return '';
  },

  /**
   * Renders placeholders in expansionText.
   * Returns object { renderedText, cursorIndex }
   * cursorIndex is relative to the start of renderedText, or -1 if {{cursor}} is not present.
   */
  async render(expansionText) {
    if (!expansionText) return { renderedText: '', cursorIndex: -1 };

    let text = expansionText;
    const now = new Date();

    text = text.replaceAll('{{date}}', this.formatDate(now));
    text = text.replaceAll('{{time}}', this.formatTime(now));
    text = text.replaceAll('{{datetime}}', this.formatDateTime(now));

    if (text.includes('{{clipboard}}')) {
      const clip = await this.getClipboardText();
      text = text.replaceAll('{{clipboard}}', clip);
    }

    let cursorIndex = -1;
    if (text.includes('{{cursor}}')) {
      cursorIndex = text.indexOf('{{cursor}}');
      text = text.replaceAll('{{cursor}}', '');
    }

    return { renderedText: text, cursorIndex };
  }
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = FlitKeyPlaceholders;
}
