# FlitKey on Windows

FlitKey has a native Windows backend for typed keyword expansion, global hotkeys, Unicode text insertion, tray controls, and per-user autostart.

The supported installer target is 64-bit Windows 10/11. The installer is self-contained and installs to the current user's `%LOCALAPPDATA%\Programs\FlitKey`, so administrator access is not required.

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
dist\windows\FlitKey-Setup-0.3.0-x64.exe
```

The build uses PyInstaller for the application directory and Inno Setup for the installable `.exe`. The generated application includes the Qt runtime and does not require Python on the target machine.

## Build through GitHub Actions

Open the repository's **Actions** tab, select **Build Windows installer**, choose **Run workflow**, and download the `FlitKey-Windows-x64` artifact from the completed run. The workflow runs on a native Windows runner, which is required because PyInstaller does not cross-compile Windows executables from Linux.

## Windows behavior

The backend uses `SetWindowsHookEx(WH_KEYBOARD_LL)` to observe keyboard input and `SendInput` to remove triggers and insert Unicode text. The `Launch at login` setting uses the per-user `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` registry key.

Windows prevents a non-elevated process from injecting input into an elevated application. If the target application is running as administrator, start FlitKey as administrator as well.

Configuration is stored in `%APPDATA%\flitkey\config.json`.

## Windows Security & SmartScreen Notice

When installing FlitKey on Windows, Windows Defender SmartScreen may display a warning:
> **"Windows protected your PC — Microsoft Defender SmartScreen prevented an unrecognized app from starting."** (Publisher: *Unknown Publisher*)

### Why this happens
FlitKey is an open-source application and community-built executables are not digitally signed with a commercial Code Signing Certificate. Windows Defender SmartScreen automatically flags unsigned downloaded `.exe` files as untrusted until they build reputation or are digitally signed.

### How to install safely
1. **Graphical Installer Bypass**:
   * Click **"More info"** on the SmartScreen dialog.
   * Click **"Run anyway"** to launch the installer.
2. **PowerShell Unblock Command**:
   If Windows blocks the file from running, open PowerShell in your downloads folder and unblock the installer:
   ```powershell
   Unblock-File -Path .\FlitKey-Setup-*-x64.exe
   ```

### Code Signing for Maintainers & Custom Builds
If you have a Code Signing Certificate (PFX file) or Azure Trusted Signing, you can automatically sign the generated executable and installer:

1. **Local Build**: Set the environment variables before running `python build_windows.py`:
   ```powershell
   $env:CODESIGN_CERT_PATH = "C:\path\to\certificate.pfx"
   $env:CODESIGN_CERT_PASSWORD = "YourPassword"
   python build_windows.py
   ```
2. **GitHub Actions**: Add the repository secret `CODESIGN_CERT_BASE64` and `CODESIGN_CERT_PASSWORD`. The workflow will automatically sign `FlitKey.exe` and `FlitKey-Setup-*.exe`.
3. **SmartScreen Reputation (Free)**: Submit clean release binaries to [Microsoft Defender Security Intelligence](https://www.microsoft.com/en-us/wdsi/filesubmit) under **Software Developer -> Incorrectly detected as malware/untrusted** to accelerate reputation whitelist approval.

