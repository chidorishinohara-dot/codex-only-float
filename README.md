# codex-only-float

A small Windows floating window for checking Codex usage.

It is intentionally minimal: one compact always-on-top Tkinter window, Codex-only data, no provider system, no browser cookie extraction, and no background service.

## Features

- Shows Codex session and weekly usage.
- Refreshes automatically every 60 seconds.
- Reads existing Codex login data from the normal local Codex auth file.
- Uses the ChatGPT/Codex usage endpoint.
- Keeps credentials in memory only; it does not save tokens, cookies, or account IDs.
- Can launch Codex first, then automatically open the floating window.
- Closes itself when the Codex desktop app is closed.

## Requirements

- Windows
- Python 3.10 or newer
- Codex desktop app already installed and logged in

No third-party Python packages are required.

## Usage

Run only the floating window:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Launch Codex and then open the floating window:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_codex_with_float.ps1
```

The app creates/updates `config.json` locally for window position, theme, and refresh interval. This file is ignored by git and should not be committed.

## Safety Notes

This project reads the local Codex auth file only to call the usage endpoint. It does not modify that file, and it does not print, log, copy, or persist credentials.

The usage endpoint is an internal ChatGPT/Codex endpoint. It may change or stop working without notice.

## Attribution

Inspired by [Win-CodexBar](https://github.com/Finesssee/Win-CodexBar) and the original CodexBar. This repository is an independent Python/Tkinter implementation and does not copy their source code.

## License

MIT
