# Contributing to codex-only-float

Thank you for your interest in contributing to codex-only-float.

This project should stay lightweight, local-first, and privacy-focused. It is meant to be a small Windows helper for Codex users, not a general quota dashboard, provider framework, or background service.

## How to Contribute

You can help by:

1. Reporting bugs.
2. Improving documentation.
3. Suggesting Windows usability improvements.
4. Testing the app in different Windows environments.
5. Improving error handling and release packaging.

## Reporting Issues

When opening an issue, please include:

1. Your Windows version.
2. Your Python version.
3. How you ran the project.
4. What you expected to happen.
5. What actually happened.
6. Screenshots or logs if they are safe to share.

Do not include private credentials, tokens, cookies, `auth.json`, `.env` files, personal account IDs, or local logs containing credentials.

## Pull Requests

Before opening a pull request:

1. Keep changes focused and small.
2. Explain what problem the PR solves.
3. Add or update documentation when behavior changes.
4. Avoid adding credential storage, telemetry, or unsafe data collection.
5. Make sure the app remains lightweight, local-first, and privacy-focused.

Recommended checks before submitting:

```powershell
python -m py_compile codex_quota_float.py
python codex_quota_float.py --test
```

For documentation-only pull requests, make sure Markdown links point to files that exist in the repository.

## Privacy Rules

Never commit or paste:

- Codex tokens
- ChatGPT cookies
- `auth.json`
- `.env` files
- Personal account data
- Local logs containing credentials
- Generated `config.json`
- Desktop shortcuts such as `.lnk` files

The app should keep credentials in memory only. It should not save, upload, print, or log credentials.

## Project Direction

Good contributions usually fit one of these areas:

- Improving the Windows floating window experience.
- Making usage parsing more reliable.
- Improving error messages when the Codex usage endpoint fails.
- Adding clear documentation, screenshots, troubleshooting notes, or FAQ entries.
- Preparing a packaged Windows executable release without changing the local-first design.

Please avoid changes that add unnecessary background services, unrelated providers, telemetry, account data collection, or complex configuration that is not needed for this tool.

## Maintainer Notes

This repository currently provides a source preview release. Do not describe it as having a packaged `.exe` release until an actual executable artifact is published.
