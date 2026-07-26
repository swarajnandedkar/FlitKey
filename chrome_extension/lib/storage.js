/**
 * FlitKey Storage Manager using chrome.storage.local
 */

const DEFAULT_SNIPPETS = [
  {
    id: 'default-1',
    label: 'Current Date',
    trigger_type: 'keyword',
    keyword: '!date',
    hotkey: '',
    expansion_text: '{{date}}',
    enabled: true
  },
  {
    id: 'default-2',
    label: 'Current Time',
    trigger_type: 'keyword',
    keyword: '!time',
    hotkey: '',
    expansion_text: '{{time}}',
    enabled: true
  },
  {
    id: 'default-3',
    label: 'Meeting Notes Template',
    trigger_type: 'keyword',
    keyword: '!meeting',
    hotkey: '',
    expansion_text: '## Meeting Notes - {{datetime}}\n\nAttendees:\n- {{cursor}}\n\nAgenda:\n1. \n\nAction Items:\n- ',
    enabled: true
  },
  {
    id: 'default-4',
    label: 'Quick Email Signoff',
    trigger_type: 'keyword',
    keyword: '!ty',
    hotkey: '',
    expansion_text: 'Thank you and best regards,\n{{cursor}}',
    enabled: true
  },
  {
    id: 'default-5',
    label: 'Insert Clipboard',
    trigger_type: 'keyword',
    keyword: '!clip',
    hotkey: '',
    expansion_text: '{{clipboard}}',
    enabled: true
  }
];

const DEFAULT_SETTINGS = {
  paused: false,
  case_sensitive: false,
  show_toast: true,
  sound_notification: false
};

const FlitKeyStorage = {
  async getState() {
    return new Promise((resolve) => {
      chrome.storage.local.get(['snippets', 'settings'], (result) => {
        let snippets = result.snippets;
        let settings = result.settings;

        if (!snippets || !Array.isArray(snippets)) {
          snippets = DEFAULT_SNIPPETS;
          chrome.storage.local.set({ snippets });
        }
        if (!settings || typeof settings !== 'object') {
          settings = DEFAULT_SETTINGS;
          chrome.storage.local.set({ settings });
        }

        resolve({ snippets, settings: { ...DEFAULT_SETTINGS, ...settings } });
      });
    });
  },

  async saveSnippets(snippets) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ snippets }, () => {
        resolve(snippets);
      });
    });
  },

  async saveSettings(settings) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ settings }, () => {
        resolve(settings);
      });
    });
  },

  async saveState(snippets, settings) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ snippets, settings }, () => {
        resolve();
      });
    });
  },

  generateId() {
    return 'snip_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 7);
  }
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = FlitKeyStorage;
}
