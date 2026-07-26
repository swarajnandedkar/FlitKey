# FlitKey — Multi-Channel Distribution Guide & Checklists

This document summarizes the release artifacts and step-by-step submission checklists for publishing FlitKey across Chrome Web Store, Linux repositories (Debian, AUR, Flathub), Windows, and software directories.

---

## 1. Chrome Web Store (Browser Extension Channel)

- **Packaged Zip File**: `dist/flitkey-chrome-extension.zip`
- **Metadata Reference**: [`chrome_extension/CHROMEWEBSTORE.md`](file:///home/swaraj/Desktop/Projects/Linux%20aText%20Tool/chrome_extension/CHROMEWEBSTORE.md)

### Submission Steps:
1. Log in to the [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole).
2. Click **Add new item** and upload `dist/flitkey-chrome-extension.zip`.
3. Fill out the Store Listing metadata using `chrome_extension/CHROMEWEBSTORE.md`:
   - Name: `FlitKey - Text Expander & Snippet Manager`
   - Summary & Detailed Description
   - Category: `Productivity`
4. Provide the permission justifications from Section 2 of `CHROMEWEBSTORE.md` for `storage`, `activeTab`, `scripting`, `contextMenus`, `clipboardRead`, and `<all_urls>`.
5. Enter Privacy Policy URL: `https://flitkey.xyz/privacy.html`.
6. Submit for review.

---

## 2. Linux Packages (Debian / AUR / Flathub)

### A. Debian / Ubuntu `.deb` Package
- **Build Command**: `python3 build_deb.py`
- **Output Artifact**: `dist/flitkey_0.4.0_all.deb`
- **Install Command**: `sudo dpkg -i dist/flitkey_0.4.0_all.deb`

### B. Arch Linux User Repository (AUR)
- **Manifest File**: [`installer/PKGBUILD`](file:///home/swaraj/Desktop/Projects/Linux%20aText%20Tool/installer/PKGBUILD)
- **Submission Steps**:
  1. Clone your AUR package repo: `git clone ssh://aur@aur.archlinux.org/flitkey-bin.git`
  2. Copy `installer/PKGBUILD` into the repository.
  3. Generate `.SRCINFO`: `makepkg --printsrcinfo > .SRCINFO`
  4. Commit and push: `git add PKGBUILD .SRCINFO && git commit -m "Release v0.4.0" && git push`

### C. Flathub (Flatpak)
- **Manifest File**: [`installer/xyz.flitkey.FlitKey.json`](file:///home/swaraj/Desktop/Projects/Linux%20aText%20Tool/installer/xyz.flitkey.FlitKey.json)
- **Submission Steps**:
  1. Fork the [flathub/flathub](https://github.com/flathub/flathub) repository on GitHub.
  2. Create a pull request adding `xyz.flitkey.FlitKey.json` to submit FlitKey to Flathub.

---

## 3. Windows Release & SmartScreen Whitelisting

- **Build Script**: [`build_windows.py`](file:///home/swaraj/Desktop/Projects/Linux%20aText%20Tool/build_windows.py)
- **Output Executable**: `dist/windows/FlitKey-Setup-0.4.0-x64.exe`
- **Signing Hook**: Pass environment variables `$env:CODESIGN_CERT_PATH` and `$env:CODESIGN_CERT_PASSWORD` during local build or set GitHub secrets `CODESIGN_CERT_BASE64` and `CODESIGN_CERT_PASSWORD` for CI builds.
- **SmartScreen Reputation Approval**: Submit clean binaries to [Microsoft Defender Security Intelligence](https://www.microsoft.com/en-us/wdsi/filesubmit) under *Software Developer -> Incorrectly detected as malware/untrusted* to accelerate reputation whitelisting.

---

## 4. Third-Party Software Directory Seedings (AlternativeTo.net)

- **Page URL**: [AlternativeTo.net / Add Application](https://alternativeto.net/software/add/)
- **Name**: FlitKey
- **Tagline**: Fast, 100% offline text expander for Linux & Windows (Espanso & AHK Alternative)
- **License**: Open Source (MIT) / Open-Core ($29 Pro)
- **Alternatives To**: Espanso, AutoHotkey, TextExpander, aText, PhraseExpress
- **Website**: https://flitkey.xyz
