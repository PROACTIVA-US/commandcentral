# Chrome for Testing Setup for Claude Code

> **Type:** Operations Skill
> **Priority:** P1
> **Keywords:** chrome, browser, puppeteer, claude-in-chrome, automation

---

## Overview

Chrome for Testing is a separate Chrome installation used by Puppeteer. To use the Claude in Chrome MCP tools, the Claude extension must be loaded into Chrome for Testing with specific configuration.

---

## Prerequisites

- Claude extension installed in regular Chrome (extension ID: `fcoeoabgfenejglbffodgkkbkcdhcgfn`)
- Chrome for Testing installed via Puppeteer (`~/.cache/puppeteer/chrome/`)
- Claude Code with `--claude-in-chrome-mcp` flag

---

## Setup Steps

### 1. Create Persistent Profile Directory

```bash
mkdir -p ~/.chrome-for-testing-profile
```

### 2. Copy Native Messaging Host Config

```bash
# Copy from regular Chrome to Chrome for Testing profile
cp ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/com.anthropic.claude_code_browser_extension.json \
   ~/.chrome-for-testing-profile/NativeMessagingHosts/
```

### 3. Create Launch Script

Create `~/.claude/launch-chrome-for-testing.sh`:

```bash
#!/bin/bash
# Launch Chrome for Testing with Claude extension and persistent profile
# Includes remote debugging for auto-authorization with Claude Code

CHROME_PATH="$HOME/.cache/puppeteer/chrome/mac_arm-141.0.7390.54/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
EXTENSION_PATH="$HOME/Library/Application Support/Google/Chrome/Default/Extensions/fcoeoabgfenejglbffodgkkbkcdhcgfn/1.0.41_0"
PROFILE_PATH="$HOME/.chrome-for-testing-profile"

"$CHROME_PATH" \
  --user-data-dir="$PROFILE_PATH" \
  --load-extension="$EXTENSION_PATH" \
  --disable-extensions-except="$EXTENSION_PATH" \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check \
  "$@"
```

Make executable:
```bash
chmod +x ~/.claude/launch-chrome-for-testing.sh
```

---

## Key Flags

| Flag | Purpose |
|------|---------|
| `--user-data-dir` | Persistent profile for login/session state |
| `--load-extension` | Load Claude extension from regular Chrome |
| `--disable-extensions-except` | Only allow Claude extension |
| `--remote-debugging-port=9222` | **Critical**: Enables auto-authorization |
| `--no-first-run` | Skip first-run wizard |

---

## Usage

### Launch Chrome for Testing
```bash
~/.claude/launch-chrome-for-testing.sh &
```

### Connect via Claude Code
The `mcp__claude-in-chrome__*` tools will auto-connect when Chrome for Testing is running with this configuration.

### First-Time Setup
1. Launch Chrome for Testing
2. Log into Google (if needed for your workflow)
3. The profile persists logins across restarts

---

## Troubleshooting

### "Browser extension is not connected"
- Ensure Chrome for Testing is running (not regular Chrome)
- Check that `--remote-debugging-port=9222` is included
- Verify native messaging host is copied to profile

### Extension version mismatch
If Claude extension updates in regular Chrome, update `EXTENSION_PATH` in the script:
```bash
ls ~/Library/Application\ Support/Google/Chrome/Default/Extensions/fcoeoabgfenejglbffodgkkbkcdhcgfn/
```

### Profile locked error
Only one Chrome instance can use a profile at a time. Kill existing instances:
```bash
pkill -9 -f "Chrome for Testing"
```

---

## Why Remote Debugging?

The `--remote-debugging-port=9222` flag is critical because:
1. It enables the Chrome DevTools Protocol (CDP)
2. The Claude extension can auto-authorize via this channel
3. Without it, manual "Authorize" click is required each launch

---

## File Locations

| Item | Path |
|------|------|
| Chrome for Testing | `~/.cache/puppeteer/chrome/mac_arm-*/chrome-mac-arm64/` |
| Claude extension | `~/Library/Application Support/Google/Chrome/Default/Extensions/fcoeoabgfenejglbffodgkkbkcdhcgfn/` |
| Persistent profile | `~/.chrome-for-testing-profile/` |
| Native messaging host | `~/.chrome-for-testing-profile/NativeMessagingHosts/` |
| Launch script | `~/.claude/launch-chrome-for-testing.sh` |
