# CleanBox

Lightweight Windows desktop background app for storage monitoring and one-click directory cleanup.

## Features

- 🗑️ **One-click cleanup** - Empty Downloads folder and Recycle Bin instantly
- 💾 **Storage monitoring** - Get notified when disk space is low (< 10GB)
- 🚀 **Auto-start** - Runs silently at Windows startup
- ⚙️ **Customizable** - Add/remove directories to cleanup list

## Installation

```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the app
python src/main.py
```

The app will:
1. Appear in the system tray
2. Auto-detect Downloads folder and Recycle Bin on first run
3. Monitor disk space every 60 seconds

### Tray Menu

- **Left-click**: Open Settings
- **Right-click**: Context menu
  - Cleanup Now
  - Settings
  - Exit

## Configuration

Config stored at: `%APPDATA%\CleanBox\config.json`

## Requirements

- Windows 10/11
- Python 3.11+
