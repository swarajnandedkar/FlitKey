# TypeFlux on Windows

TypeFlux has a native Windows backend for typed keyword expansion, global hotkeys, Unicode text insertion, tray controls, and per-user autostart.

The supported installer target is 64-bit Windows 10/11. The installer is self-contained and installs to the current user's `%LOCALAPPDATA%\Programs\TypeFlux`, so administrator access is not required.

## Build the installer locally

Run these commands from a Windows PowerShell prompt:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-windows.txt
python build_windows.py
```

Install Inno Setup 6 before the build. The resulting file is:

```text
dist\windows\TypeFlux-Setup-0.3.0-x64.exe
```

The build uses PyInstaller for the application directory and Inno Setup for the installable `.exe`. The generated application includes the Qt runtime and does not require Python on the target machine.

## Build through GitHub Actions

Open the repository's **Actions** tab, select **Build Windows installer**, choose **Run workflow**, and download the `TypeFlux-Windows-x64` artifact from the completed run. The workflow runs on a native Windows runner, which is required because PyInstaller does not cross-compile Windows executables from Linux.

## Windows behavior

The backend uses `SetWindowsHookEx(WH_KEYBOARD_LL)` to observe keyboard input and `SendInput` to remove triggers and insert Unicode text. The `Launch at login` setting uses the per-user `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` registry key.

Windows prevents a non-elevated process from injecting input into an elevated application. If the target application is running as administrator, start TypeFlux as administrator as well.

Configuration is stored in `%APPDATA%\typeflux\config.json`.
