# FlitKey — Code Analysis: Issues to Improve

Date: 2026-08-22

## Critical / correctness issues

1. **X11 backend misses/races on keyword expansion** (`runtime/x11_backend.py:_expand_keyword`).
   No true key suppression on X11 (xinput is passive); only a 0.6s `suppress_until`
   window during which ALL typing is silently dropped from the buffer — typing right
   after an expansion loses input tracking. Timing races with xdotool can interleave chars.

2. **X11 keymap loaded once at startup, never refreshed.** Layout switches or remaps
   break text reconstruction (`_keycode_to_text`) and hotkey matching until restart.

3. **X11 buffer desyncs from reality.** Arrow keys, mouse clicks mid-word, autocomplete,
   IME input change on-screen text without updating `_buffer` → false/missed expansions.
   Windows backend resets on nav keys; X11 only handles backspace/newline/tab.

4. **Windows `_event_to_text` does heavy work inside the low-level hook**
   (`GetKeyboardState`, `ToUnicodeEx`, `GetForegroundWindow`, layout lookup per keystroke).
   Slow hook procs cause Windows to silently remove the hook or make the desktop laggy.

5. **Dead-key / AltGr handling.** `_altgr_active()` requires RMENU+Ctrl simultaneously in
   `_pressed_vks`, but many layouts deliver AltGr as just VK_RMENU without Ctrl in the
   LL hook — non-US keyboard users get wrong characters or blocked hotkeys.

## Design / architecture issues

6. **Backend reload drops the running listener** — `RuntimeBackend.reload()` does
   stop/start; on X11 this kills/respawns `xinput test-xi2` on every snippet edit,
   losing keystrokes in the gap.

7. **Thread-safety.** `_suppress_until`, `_buffer`, `_pressed_keycodes` mutated from
   backend worker thread and main thread (stop/reload) with no locks.

8. **Duplicate-hotkey detection compares raw lowercase strings** (`app.py:_duplicate_hotkey`):
   `"ctrl+a"` vs `"Ctrl+A"` vs `"control+a"` treated as different, even though both
   backends have normalizers. Should normalize before comparing.

9. **Wayland fallback gives no actionable guidance** in the UI flow (e.g. "run under
   XWayland") beyond a status label.

10. **`import_state()` replaces all data with no backup/undo**, no dedup;
    `export_state`/`import_state`/`delete_state` have no GUI entry points
    (compliance features not wired up).

11. **Repo hygiene**: `dist/pkgroot/` holds a stale full copy of the source in git;
    backup dirs (`FlitKey HP.backup-*`, `.broken-*`, `.pre-livesync-*`) in project root;
    `__pycache__` present.

12. **Tests not runnable locally** — pytest not installed (PEP 668); needs a venv.

## Minor

13. `placeholders.py` imports PyQt6 at module level, making backend logic untestable
    without Qt.
14. X11 `inject_text` uses `--clearmodifiers`, releasing held modifiers (breaks if the
    user holds Shift).
15. Tray notification on every expansion — noisy; no setting to disable.
16. No single-instance lock in `main.py` — two copies double-expand every keystroke.

## Fix order

1. #8 (trivial) → 2. #3/#2 (X11 correctness) → 3. #7 (locks) → 4. #12 (venv + tests)
