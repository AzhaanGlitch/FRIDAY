# System Automation Documentation

This document explains how FRIDAY handles cross-platform automation on **macOS** and **Windows**.

---

## 1. Architecture Overview

Automation calls pass through a unified interface:

```
                  ┌────────────────────────┐
                  │ SystemAutomation Router│
                  └───────────┬────────────┘
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│  MacAutomation Adapter  │       │  WinAutomation Adapter  │
│      (macOS / Darwin)   │       │       (Windows / win32) │
└─────────────────────────┘       └─────────────────────────┘
```

---

## 2. macOS Automation (`backend/automation/mac_automation.py`)

### 1. Application Launching (`open_application`)
- **Technology**: Native macOS binary `open -a "<AppName>"`
- **How it works**: Spawns macOS system process dispatcher. Automatically resolves paths for macOS applications (e.g. `Spotify`, `Calculator`, `Visual Studio Code`, `Safari`, `Terminal`).

### 2. Volume Control (`set_volume`)
- **Technology**: AppleScript via `osascript -e`
- **Script**: `set volume output volume <0-100>`
- **How it works**: Directly instructs the macOS CoreAudio engine to update speaker output volume dynamically without requiring admin privileges.

### 3. Screen Capture (`take_screenshot`)
- **Technology**: macOS system utility `screencapture -x <path>`
- **How it works**: Quietly captures primary display screenshot to file (used by Vision module).

---

## 3. Windows Automation (`backend/automation/win_automation.py`)

### 1. Application Launching (`open_application`)
- **Technology**: Windows CMD Shell `start <AppName>`
- **How it works**: Uses Windows Shell launcher to locate and open installed desktop apps or executables registered in the Windows Path or Registry.

### 2. Volume Control (`set_volume`)
- **Technology**: Windows PowerShell `WScript.Shell` / `SendKeys`
- **How it works**: Sends native virtual keycodes (`VK_VOLUME_UP` / `VK_VOLUME_DOWN`) to adjust Windows Master Volume.

### 3. Screen Capture (`take_screenshot`)
- **Technology**: Windows PowerShell `Graphics.CopyFromScreen` via `.NET` (`System.Drawing`)
- **How it works**: Uses native .NET GDI+ API to grab screen bounds and write PNG screenshots.

---

## 4. Supported Automation Commands Summary

| Intent Command | macOS Implementation | Windows Implementation |
| :--- | :--- | :--- |
| `open <app>` | `open -a <app>` | `cmd.exe /c start <app>` |
| `set volume to <X>` | `osascript set volume output volume X` | PowerShell `WScript.Shell SendKeys` |
| `take screenshot` | `screencapture -x <path>` | PowerShell `.NET CopyFromScreen` |
| `system info` | `platform`, `sys.platform` | `platform`, `sys.platform` |
