from __future__ import annotations

import ctypes
import sys
import threading
from ctypes import wintypes

from ..models import CapabilityReport, Snippet
from ..placeholders import render_placeholders
from .base import RuntimeBackend


ULONG_PTR = ctypes.c_size_t


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", ctypes.c_ssize_t),
        ("time", wintypes.DWORD),
        ("pt", POINT),
        ("lPrivate", wintypes.DWORD),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", wintypes.DWORD), ("data", INPUTUNION)]


class WindowsBackend(RuntimeBackend):
    """Native Windows keyboard hook and Unicode text injection backend."""

    WH_KEYBOARD_LL = 13
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    WM_SYSKEYDOWN = 0x0104
    WM_SYSKEYUP = 0x0105
    WM_QUIT = 0x0012
    PM_NOREMOVE = 0x0000

    LLKHF_INJECTED = 0x0010
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    TO_UNICODE_NO_STATE_CHANGE = 0x0004

    VK_BACK = 0x08
    VK_TAB = 0x09
    VK_RETURN = 0x0D
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_MENU = 0x12
    VK_ESCAPE = 0x1B
    VK_SPACE = 0x20
    VK_PRIOR = 0x21
    VK_NEXT = 0x22
    VK_END = 0x23
    VK_HOME = 0x24
    VK_LEFT = 0x25
    VK_UP = 0x26
    VK_RIGHT = 0x27
    VK_DOWN = 0x28
    VK_DELETE = 0x2E
    VK_LWIN = 0x5B
    VK_RWIN = 0x5C
    VK_F1 = 0x70
    VK_F24 = 0x87
    VK_LSHIFT = 0xA0
    VK_RSHIFT = 0xA1
    VK_LCONTROL = 0xA2
    VK_RCONTROL = 0xA3
    VK_LMENU = 0xA4
    VK_RMENU = 0xA5

    _SHIFT_VKS = frozenset({VK_SHIFT, VK_LSHIFT, VK_RSHIFT})
    _CTRL_VKS = frozenset({VK_CONTROL, VK_LCONTROL, VK_RCONTROL})
    _ALT_VKS = frozenset({VK_MENU, VK_LMENU, VK_RMENU})
    _WIN_VKS = frozenset({VK_LWIN, VK_RWIN})
    _MODIFIER_VKS = _SHIFT_VKS | _CTRL_VKS | _ALT_VKS | _WIN_VKS
    _BUFFER_RESET_VKS = frozenset(
        {
            VK_TAB,
            VK_RETURN,
            VK_ESCAPE,
            VK_PRIOR,
            VK_NEXT,
            VK_END,
            VK_HOME,
            VK_LEFT,
            VK_UP,
            VK_RIGHT,
            VK_DOWN,
            VK_DELETE,
        }
    )
    _SPECIAL_HOTKEY_NAMES = {
        VK_SPACE: "Space",
        VK_RETURN: "Enter",
        VK_TAB: "Tab",
        VK_ESCAPE: "Escape",
        VK_BACK: "Backspace",
        VK_DELETE: "Delete",
        VK_HOME: "Home",
        VK_END: "End",
        VK_PRIOR: "PageUp",
        VK_NEXT: "PageDown",
        VK_LEFT: "Left",
        VK_UP: "Up",
        VK_RIGHT: "Right",
        VK_DOWN: "Down",
    }

    def __init__(self) -> None:
        supported = sys.platform == "win32"
        report = CapabilityReport(
            session_type="windows",
            backend_name="windows-native",
            typed_expansion_supported=supported,
            global_hotkeys_supported=supported,
            tray_supported=True,
            autostart_supported=supported,
            status_message=(
                "Windows backend ready."
                if supported
                else "The Windows backend is only available on Windows."
            ),
        )
        super().__init__(report)

        self._snippets: list[Snippet] = []
        self._case_sensitive = False
        self._buffer = ""
        self._pressed_vks: set[int] = set()
        self._running = False
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._hook_handle: int | None = None
        self._hook_proc = None
        self._message_queue_ready = threading.Event()
        self._api_ready = False
        self._user32 = None
        self._kernel32 = None
        self._hook_proc_type = None

        if supported:
            try:
                self._configure_win32_api()
                self._api_ready = True
            except (AttributeError, OSError) as error:
                self._set_capability_failure(f"Windows input API unavailable: {error}")

    def _configure_win32_api(self) -> None:
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._hook_proc_type = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            ctypes.c_int,
            wintypes.WPARAM,
            ctypes.c_ssize_t,
        )

        self._user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            self._hook_proc_type,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        self._user32.SetWindowsHookExW.restype = ctypes.c_void_p
        self._user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
        self._user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        self._user32.CallNextHookEx.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            wintypes.WPARAM,
            ctypes.c_ssize_t,
        ]
        self._user32.CallNextHookEx.restype = ctypes.c_ssize_t
        self._user32.GetMessageW.argtypes = [
            ctypes.POINTER(MSG),
            ctypes.c_void_p,
            wintypes.UINT,
            wintypes.UINT,
        ]
        self._user32.GetMessageW.restype = ctypes.c_int
        self._user32.PeekMessageW.argtypes = [
            ctypes.POINTER(MSG),
            ctypes.c_void_p,
            wintypes.UINT,
            wintypes.UINT,
            wintypes.UINT,
        ]
        self._user32.PeekMessageW.restype = wintypes.BOOL
        self._user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
        self._user32.TranslateMessage.restype = wintypes.BOOL
        self._user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
        self._user32.DispatchMessageW.restype = ctypes.c_ssize_t
        self._user32.PostThreadMessageW.argtypes = [
            wintypes.DWORD,
            wintypes.UINT,
            wintypes.WPARAM,
            ctypes.c_ssize_t,
        ]
        self._user32.PostThreadMessageW.restype = wintypes.BOOL
        self._user32.GetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
        self._user32.GetKeyboardState.restype = wintypes.BOOL
        self._user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        self._user32.GetKeyboardLayout.restype = ctypes.c_void_p
        self._user32.ToUnicodeEx.argtypes = [
            wintypes.UINT,
            wintypes.UINT,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_wchar_p,
            ctypes.c_int,
            wintypes.UINT,
            ctypes.c_void_p,
        ]
        self._user32.ToUnicodeEx.restype = ctypes.c_int
        self._user32.SendInput.argtypes = [
            wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int,
        ]
        self._user32.SendInput.restype = wintypes.UINT

        self._kernel32.GetCurrentThreadId.argtypes = []
        self._kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        self._kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
        self._kernel32.GetModuleHandleW.restype = ctypes.c_void_p

    def start(self, snippets: list[Snippet], case_sensitive: bool) -> None:
        self._snippets = snippets
        self._case_sensitive = case_sensitive
        self._buffer = ""
        if not self._api_ready:
            self.status_changed.emit(self.capability_report.status_message)
            return
        if self._running:
            return

        self._running = True
        self._message_queue_ready.clear()
        self._thread = threading.Thread(
            target=self._run_message_loop,
            name="FlitKeyWindowsHook",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._message_queue_ready.wait(timeout=0.5)
        if self._thread_id and self._user32 is not None:
            self._user32.PostThreadMessageW(self._thread_id, self.WM_QUIT, 0, 0)
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._pressed_vks.clear()
        self._buffer = ""

    def can_inject_text(self) -> bool:
        return self._api_ready

    def inject_text(self, text: str, preserve_trailing_newline: bool = True) -> bool:
        if not self.can_inject_text():
            return False

        rendered = render_placeholders(text)
        if not preserve_trailing_newline:
            rendered = self._strip_single_trailing_newline(rendered)

        cursor_index = rendered.find("{{cursor}}")
        if cursor_index != -1:
            before_cursor = rendered[:cursor_index]
            after_cursor = rendered[cursor_index + len("{{cursor}}") :]
            typed_text = before_cursor + after_cursor
            move_left = len(after_cursor)
        else:
            typed_text = rendered
            move_left = 0

        if not self._send_text(typed_text):
            return False
        if move_left and not self._send_virtual_key(self.VK_LEFT, move_left):
            return False
        return True

    @staticmethod
    def _strip_single_trailing_newline(text: str) -> str:
        if text.endswith("\r\n"):
            return text[:-2]
        if text.endswith(("\n", "\r")):
            return text[:-1]
        return text

    def _run_message_loop(self) -> None:
        assert self._user32 is not None
        assert self._kernel32 is not None
        assert self._hook_proc_type is not None

        message = MSG()
        self._thread_id = int(self._kernel32.GetCurrentThreadId())
        self._user32.PeekMessageW(
            ctypes.byref(message),
            None,
            0,
            0,
            self.PM_NOREMOVE,
        )
        self._message_queue_ready.set()

        self._hook_proc = self._hook_proc_type(self._keyboard_proc)
        module_handle = self._kernel32.GetModuleHandleW(None)
        self._hook_handle = self._user32.SetWindowsHookExW(
            self.WH_KEYBOARD_LL,
            self._hook_proc,
            module_handle,
            0,
        )
        if not self._hook_handle:
            error_code = ctypes.get_last_error()
            self._running = False
            self._set_capability_failure(
                f"Could not start the Windows keyboard hook (error {error_code})."
            )
            self._thread_id = 0
            return

        self.status_changed.emit("Windows backend ready.")
        try:
            while self._running:
                result = self._user32.GetMessageW(
                    ctypes.byref(message),
                    None,
                    0,
                    0,
                )
                if result <= 0:
                    break
                self._user32.TranslateMessage(ctypes.byref(message))
                self._user32.DispatchMessageW(ctypes.byref(message))
        finally:
            if self._hook_handle:
                self._user32.UnhookWindowsHookEx(self._hook_handle)
            self._hook_handle = None
            self._hook_proc = None
            self._thread_id = 0
            self._running = False

    def _keyboard_proc(self, code: int, message: int, event_pointer: int) -> int:
        if code < 0:
            return self._call_next_hook(code, message, event_pointer)

        try:
            event = ctypes.cast(
                event_pointer,
                ctypes.POINTER(KBDLLHOOKSTRUCT),
            ).contents
            if event.flags & self.LLKHF_INJECTED:
                return self._call_next_hook(code, message, event_pointer)

            if message in {self.WM_KEYDOWN, self.WM_SYSKEYDOWN}:
                if self._handle_key_down(event):
                    return 1
            elif message in {self.WM_KEYUP, self.WM_SYSKEYUP}:
                self._pressed_vks.discard(int(event.vkCode))
        except Exception:
            # Native callbacks must never unwind through the Windows hook API.
            self._buffer = ""

        return self._call_next_hook(code, message, event_pointer)

    def _call_next_hook(self, code: int, message: int, event_pointer: int) -> int:
        if self._user32 is None:
            return 0
        return int(
            self._user32.CallNextHookEx(
                self._hook_handle,
                code,
                message,
                event_pointer,
            )
        )

    def _handle_key_down(self, event: KBDLLHOOKSTRUCT) -> bool:
        vk_code = int(event.vkCode)
        was_pressed = vk_code in self._pressed_vks
        self._pressed_vks.add(vk_code)

        if self._paused:
            return False
        if vk_code in self._MODIFIER_VKS:
            if vk_code not in self._SHIFT_VKS:
                self._buffer = ""
            return False

        if not was_pressed and not self._altgr_active() and self._trigger_hotkey(vk_code):
            self._buffer = ""
            return True

        if self._has_command_modifier():
            self._buffer = ""
            return False
        if vk_code == self.VK_BACK:
            self._buffer = self._buffer[:-1]
            return False
        if vk_code in self._BUFFER_RESET_VKS:
            self._buffer = ""
            return False

        typed_text = self._event_to_text(event)
        if not typed_text:
            self._buffer = ""
            return False

        self._buffer = (self._buffer + typed_text)[-100:]
        snippet = self._matching_keyword()
        if snippet is None:
            return False

        if self._expand_keyword(snippet, typed_text):
            self._buffer = ""
            self.snippet_triggered.emit(snippet.label)
            return True
        return False

    def _matching_keyword(self) -> Snippet | None:
        buffer_value = self._buffer if self._case_sensitive else self._buffer.lower()
        matches: list[tuple[int, Snippet]] = []
        for snippet in self._snippets:
            if not snippet.enabled or snippet.trigger_type != "keyword" or not snippet.keyword:
                continue
            keyword = snippet.keyword if self._case_sensitive else snippet.keyword.lower()
            if buffer_value.endswith(keyword):
                matches.append((len(keyword), snippet))
        if not matches:
            return None
        return max(matches, key=lambda item: item[0])[1]

    def _expand_keyword(self, snippet: Snippet, final_text: str) -> bool:
        prior_count = max(0, len(snippet.keyword) - len(final_text))
        visible_prefix = self._buffer[-len(snippet.keyword) : -len(final_text)]
        if prior_count and not self._send_virtual_key(self.VK_BACK, prior_count):
            return False
        if self.inject_text(snippet.expansion_text, preserve_trailing_newline=False):
            return True

        # Restore already-visible trigger text if the expansion could not be sent.
        if visible_prefix:
            self._send_text(visible_prefix)
        return False

    def _trigger_hotkey(self, vk_code: int) -> bool:
        key_name = self._hotkey_name_for_vk(vk_code)
        if not key_name:
            return False

        modifiers: list[str] = []
        if self._pressed_vks & self._CTRL_VKS:
            modifiers.append("Ctrl")
        if self._pressed_vks & self._ALT_VKS:
            modifiers.append("Alt")
        if self._pressed_vks & self._SHIFT_VKS:
            modifiers.append("Shift")
        if self._pressed_vks & self._WIN_VKS:
            modifiers.append("Win")
        pressed = "+".join(modifiers + [key_name])

        for snippet in self._snippets:
            if not snippet.enabled or snippet.trigger_type != "hotkey" or not snippet.hotkey:
                continue
            if self.normalize_hotkey(snippet.hotkey) != self.normalize_hotkey(pressed):
                continue
            if not self.inject_text(snippet.expansion_text):
                return False
            self.snippet_triggered.emit(snippet.label)
            return True
        return False

    @classmethod
    def normalize_hotkey(cls, value: str) -> str:
        parts = [part.strip() for part in value.split("+") if part.strip()]
        if not parts:
            return ""

        modifier_aliases = {
            "ctrl": "Ctrl",
            "control": "Ctrl",
            "alt": "Alt",
            "shift": "Shift",
            "win": "Win",
            "windows": "Win",
            "super": "Win",
        }
        key_aliases = {
            "return": "Enter",
            "enter": "Enter",
            "esc": "Escape",
            "escape": "Escape",
            "space": "Space",
            "backspace": "Backspace",
            "delete": "Delete",
            "pageup": "PageUp",
            "pagedown": "PageDown",
        }

        modifiers = {
            modifier_aliases[part.lower()]
            for part in parts[:-1]
            if part.lower() in modifier_aliases
        }
        raw_key = parts[-1]
        lowered_key = raw_key.lower()
        if len(raw_key) == 1:
            key = raw_key.upper()
        elif lowered_key in key_aliases:
            key = key_aliases[lowered_key]
        elif lowered_key.startswith("f") and lowered_key[1:].isdigit():
            key = lowered_key.upper()
        else:
            key = raw_key.title()

        ordered = [name for name in ("Ctrl", "Alt", "Shift", "Win") if name in modifiers]
        return "+".join(ordered + [key])

    def _hotkey_name_for_vk(self, vk_code: int) -> str | None:
        if ord("0") <= vk_code <= ord("9") or ord("A") <= vk_code <= ord("Z"):
            return chr(vk_code)
        if self.VK_F1 <= vk_code <= self.VK_F24:
            return f"F{vk_code - self.VK_F1 + 1}"
        return self._SPECIAL_HOTKEY_NAMES.get(vk_code)

    def _has_command_modifier(self) -> bool:
        if self._pressed_vks & self._WIN_VKS:
            return True
        if self._altgr_active():
            return False
        return bool(self._pressed_vks & (self._CTRL_VKS | self._ALT_VKS))

    def _altgr_active(self) -> bool:
        return self.VK_RMENU in self._pressed_vks and bool(self._pressed_vks & self._CTRL_VKS)

    def _event_to_text(self, event: KBDLLHOOKSTRUCT) -> str | None:
        assert self._user32 is not None
        keyboard_state = (ctypes.c_ubyte * 256)()
        if not self._user32.GetKeyboardState(keyboard_state):
            return None

        for vk_code in self._pressed_vks:
            if 0 <= vk_code < 256:
                keyboard_state[vk_code] |= 0x80
        keyboard_state[int(event.vkCode)] |= 0x80

        output = ctypes.create_unicode_buffer(8)
        layout = self._user32.GetKeyboardLayout(0)
        count = self._user32.ToUnicodeEx(
            int(event.vkCode),
            int(event.scanCode),
            keyboard_state,
            output,
            len(output),
            self.TO_UNICODE_NO_STATE_CHANGE,
            layout,
        )
        if count <= 0:
            return None
        return "".join(output[:count])

    def _send_text(self, text: str) -> bool:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        inputs: list[INPUT] = []
        for character in normalized:
            if character == "\n":
                inputs.extend(self._virtual_key_inputs(self.VK_RETURN))
                continue
            if character == "\t":
                inputs.extend(self._virtual_key_inputs(self.VK_TAB))
                continue
            encoded = character.encode("utf-16-le")
            for offset in range(0, len(encoded), 2):
                scan_code = int.from_bytes(encoded[offset : offset + 2], "little")
                inputs.append(self._keyboard_input(0, scan_code, self.KEYEVENTF_UNICODE))
                inputs.append(
                    self._keyboard_input(
                        0,
                        scan_code,
                        self.KEYEVENTF_UNICODE | self.KEYEVENTF_KEYUP,
                    )
                )
        return self._send_inputs(inputs)

    def _send_virtual_key(self, vk_code: int, count: int = 1) -> bool:
        inputs: list[INPUT] = []
        for _ in range(count):
            inputs.extend(self._virtual_key_inputs(vk_code))
        return self._send_inputs(inputs)

    def _virtual_key_inputs(self, vk_code: int) -> list[INPUT]:
        return [
            self._keyboard_input(vk_code, 0, 0),
            self._keyboard_input(vk_code, 0, self.KEYEVENTF_KEYUP),
        ]

    @staticmethod
    def _keyboard_input(vk_code: int, scan_code: int, flags: int) -> INPUT:
        item = INPUT()
        item.type = WindowsBackend.INPUT_KEYBOARD
        item.ki = KEYBDINPUT(
            wVk=vk_code,
            wScan=scan_code,
            dwFlags=flags,
            time=0,
            dwExtraInfo=0,
        )
        return item

    def _send_inputs(self, inputs: list[INPUT]) -> bool:
        if not inputs:
            return True
        if self._user32 is None:
            return False

        for start in range(0, len(inputs), 128):
            batch = inputs[start : start + 128]
            array_type = INPUT * len(batch)
            array = array_type(*batch)
            sent = self._user32.SendInput(
                len(batch),
                array,
                ctypes.sizeof(INPUT),
            )
            if sent != len(batch):
                return False
        return True

    def _set_capability_failure(self, message: str) -> None:
        self.capability_report.typed_expansion_supported = False
        self.capability_report.global_hotkeys_supported = False
        self.capability_report.status_message = message
        self.status_changed.emit(message)
