# System Automation Documentation

This document details all advanced native automations supported by **FRIDAY AI Assistant** across **macOS** and **Windows**.

---

## 1. Architecture Overview

Automation requests pass through the unified `SystemAutomation` interface, which routes intents to platform-specific adapters (`MacAutomation` for macOS and `WinAutomation` for Windows):

```
                   ┌───────────────────────────┐
                   │ SystemAutomation Router   │
                   └─────────────┬─────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌─────────────────────────────┐             ┌─────────────────────────────┐
│    MacAutomation Adapter    │             │    WinAutomation Adapter    │
│      (macOS / Darwin)       │             │      (Windows / win32)      │
└─────────────────────────────┘             └─────────────────────────────┘
```

---

## 2. Advanced Automation Commands & Platform Implementation

| Category | Intent Command | macOS Implementation | Windows Implementation |
| :--- | :--- | :--- | :--- |
| **App Launching** | `open <app>` | `open -a "<AppName>"` | `cmd.exe /c start <AppName>` |
| **App Closing** | `close <app>` | AppleScript `tell app to quit` / `pkill` | `taskkill /F /IM <AppName>.exe` |
| **Volume Control** | `set volume to X%` | `osascript -e 'set volume output volume X'` | PowerShell `WScript.Shell` SendKeys |
| **Mute / Unmute** | `mute sound` / `unmute sound` | `osascript -e 'set volume output muted true'` | PowerShell `SendKeys([char]173)` |
| **Brightness Control** | `set brightness to X%` | `brightness` utility / AppleScript | PowerShell WMI `WmiSetBrightness` |
| **Minimize All** | `minimize all` / `show desktop` | AppleScript Finder hide all windows | PowerShell `Shell.Application MinimizeAll()` |
| **Media Playback** | `play`, `pause`, `next`, `previous` | AppleScript Spotify & System Events | PowerShell `SendKeys` Media Keys |
| **Lock Screen** | `lock screen` | AppleScript Control+Cmd+Q keystroke | `rundll32.exe user32.dll,LockWorkStation` |
| **Sleep Laptop** | `sleep system` | `pmset sleepnow` | `rundll32.exe powrprof.dll,SetSuspendState` |
| **Clipboard Read** | `read clipboard` | `pbpaste` system utility | PowerShell `Get-Clipboard` |
| **Clipboard Write** | `copy <text>` | `pbcopy` system utility | PowerShell `Set-Clipboard -Value` |
| **File Search** | `find file <name>` | `mdfind -name <name>` (Spotlight) | PowerShell `Get-ChildItem -Filter` |
| **Open Web URL** | `open <url>` | Python `webbrowser.open(url)` | Python `webbrowser.open(url)` |
| **Screenshot** | `take a screenshot` | `screencapture -x <path>` | PowerShell .NET GDI+ `CopyFromScreen` |
| **Multi-Step Coding Mode**| `start coding mode` | Opens VS Code + Terminal + GitHub + Audio | Opens VS Code + Terminal + GitHub + Audio |
