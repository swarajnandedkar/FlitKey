/**
 * FlitKey Snippet Importer Engine
 * Supports JSON, Espanso (YAML/JSON), AutoHotkey (.ahk), and CSV/TSV
 */

const FlitKeyImporter = {
  parseFile(content, fileName) {
    const lowerName = fileName.toLowerCase();

    if (lowerName.endsWith('.json')) {
      return this.parseJSON(content);
    } else if (lowerName.endsWith('.yaml') || lowerName.endsWith('.yml')) {
      return this.parseEspanso(content);
    } else if (lowerName.endsWith('.ahk')) {
      return this.parseAutoHotkey(content);
    } else if (lowerName.endsWith('.csv') || lowerName.endsWith('.tsv') || lowerName.endsWith('.txt')) {
      return this.parseCSV(content, lowerName.endsWith('.tsv') ? '\t' : ',');
    }

    // Default fallback try JSON then CSV
    try {
      return this.parseJSON(content);
    } catch (e) {
      return this.parseCSV(content, ',');
    }
  },

  parseJSON(content) {
    const data = JSON.parse(content);
    const rawList = Array.isArray(data) ? data : (data.snippets || []);
    const result = [];

    for (const item of rawList) {
      if (!item || typeof item !== 'object') continue;
      const label = item.label || item.name || item.trigger || 'Imported Snippet';
      const trigger_type = item.trigger_type || 'keyword';
      const keyword = item.keyword || item.trigger || '';
      const hotkey = item.hotkey || '';
      const expansion_text = item.expansion_text || item.replace || item.text || '';

      if (keyword || hotkey || expansion_text) {
        result.push({
          id: 'snip_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 6),
          label: label.trim(),
          trigger_type,
          keyword: keyword.trim(),
          hotkey: hotkey.trim(),
          expansion_text: expansion_text,
          enabled: item.enabled !== false
        });
      }
    }
    return result;
  },

  parseEspanso(content) {
    // Simple line-by-line parser for Espanso matches
    const result = [];
    const lines = content.split('\n');
    let currentTrigger = '';
    let currentReplace = '';
    let currentLabel = '';

    for (let line of lines) {
      line = line.trim();
      if (line.startsWith('trigger:')) {
        if (currentTrigger && currentReplace) {
          result.push(this._createSnippet(currentLabel || currentTrigger, currentTrigger, currentReplace));
          currentTrigger = '';
          currentReplace = '';
          currentLabel = '';
        }
        currentTrigger = line.replace('trigger:', '').trim().replace(/^["']|["']$/g, '');
      } else if (line.startsWith('replace:')) {
        currentReplace = line.replace('replace:', '').trim().replace(/^["']|["']$/g, '');
      } else if (line.startsWith('label:')) {
        currentLabel = line.replace('label:', '').trim().replace(/^["']|["']$/g, '');
      }
    }

    if (currentTrigger && currentReplace) {
      result.push(this._createSnippet(currentLabel || currentTrigger, currentTrigger, currentReplace));
    }

    return result;
  },

  parseAutoHotkey(content) {
    // AHK hotstring parser e.g. ::!date::2026-07-21 or :*:!date::Expansion
    const result = [];
    const lines = content.split('\n');
    const ahkRegex = /^::([^:]+)::(.+)$/;
    const ahkRegexOptions = /^:([^:]*):([^:]+)::(.+)$/;

    for (let line of lines) {
      line = line.trim();
      if (line.startsWith(';') || !line) continue;

      let match = line.match(ahkRegexOptions) || line.match(ahkRegex);
      if (match) {
        const keyword = (match[2] || match[1]).trim();
        const replacement = (match[3] || match[2]).trim();
        if (keyword && replacement) {
          result.push(this._createSnippet(keyword, keyword, replacement));
        }
      }
    }

    return result;
  },

  parseCSV(content, delimiter = ',') {
    const result = [];
    const lines = content.split('\n');

    for (let line of lines) {
      line = line.trim();
      if (!line) continue;

      const parts = line.split(delimiter);
      if (parts.length >= 2) {
        const keyword = parts[0].trim().replace(/^["']|["']$/g, '');
        const replacement = parts.slice(1).join(delimiter).trim().replace(/^["']|["']$/g, '');

        if (keyword && replacement) {
          result.push(this._createSnippet(keyword, keyword, replacement));
        }
      }
    }

    return result;
  },

  _createSnippet(label, keyword, text) {
    return {
      id: 'snip_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 6),
      label: label.trim(),
      trigger_type: 'keyword',
      keyword: keyword.trim(),
      hotkey: '',
      expansion_text: text,
      enabled: true
    };
  }
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = FlitKeyImporter;
}
