<p align="center">
  English
</p>

<h1 align="center">🪟 Codex Usage Float</h1>

<p align="center">
  A lightweight Windows floating window for monitoring Codex session usage and weekly usage.
</p>

<p align="center">
  <img alt="License" src="https://img.shields.io/badge/LICENSE-MIT-3b82f6?style=for-the-badge">
  <img alt="Version" src="https://img.shields.io/badge/VERSION-v0.1.0-10b981?style=for-the-badge">
  <img alt="Platform" src="https://img.shields.io/badge/PLATFORM-WINDOWS-8b5cf6?style=for-the-badge">
  <img alt="Release" src="https://img.shields.io/badge/RELEASE-SOURCE_PREVIEW-f59e0b?style=for-the-badge">
</p>

<p align="center">
  <img alt="codex-only-float preview" src="assets/preview.png" width="720">
</p>

<p align="center">
  <strong>This project is designed for Codex users who want a lightweight way to monitor usage without repeatedly checking manually.</strong>
</p>

---

## What It Solves

Codex usage can be easy to miss when users need to check it manually. This project keeps session and weekly usage visible in a compact always-on-top Windows floating window while Codex is running.

It is intentionally minimal: one Tkinter window, Codex-only data, no provider system, no browser cookie extraction, and no background service.

## Features

- Shows Codex session usage and weekly usage.
- Refreshes automatically every 60 seconds.
- Reads existing Codex login data from `CODEX_HOME\auth.json` or `%USERPROFILE%\.codex\auth.json`.
- Uses the ChatGPT/Codex usage endpoint: `https://chatgpt.com/backend-api/wham/usage`.
- Keeps credentials in memory only; it does not save tokens, cookies, or account IDs.
- Can launch Codex first, then automatically open the floating window.
- Closes itself when the Codex desktop app is closed.

## Quick Start

### Requirements

- Windows
- Python 3.10 or newer
- Codex desktop app already installed and logged in

No third-party Python packages are required.

### Run Only the Floating Window

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

### Launch Codex With the Floating Window

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_codex_with_float.ps1
```

The launcher starts Codex first, waits until `Codex.exe` is detected, and then opens the floating usage window.

The app creates or updates `config.json` locally for window position, theme, and refresh interval. This file is ignored by git and should not be committed.

## Privacy and Safety

This project is designed to be lightweight, local-first, and privacy-focused.

- It reads the local Codex auth file only to call the usage endpoint.
- It does not modify `auth.json`.
- It does not print, log, copy, upload, or persist credentials.
- It does not upload usage data, account data, cookies, or local configuration.
- It does not install a background service.

The usage endpoint is an internal ChatGPT/Codex endpoint. It may change or stop working without notice.

## Roadmap

- [ ] Add packaged Windows executable release.
- [ ] Improve error handling when the Codex usage endpoint fails.
- [ ] Add startup on Windows login option.
- [ ] Add configuration file support for refresh interval and window position.
- [ ] Improve README with screenshots, troubleshooting, and FAQ.

## Attribution

Inspired by [Win-CodexBar](https://github.com/Finesssee/Win-CodexBar) and the original CodexBar. This repository is an independent Python/Tkinter implementation and does not copy their source code.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](./CONTRIBUTING.md) before opening an issue or pull request.

The project direction should stay lightweight, local-first, and privacy-focused.

## License

MIT
