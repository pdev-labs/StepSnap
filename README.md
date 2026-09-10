# StepSnap

StepSnap is a lightweight, background screenshot tool designed to help you quickly document your steps for GitHub repositories, tutorials, and Pull Requests.

It silently runs in the background and automatically takes a screenshot whenever you click your mouse or press the `Enter` key. It's built to work seamlessly on both **X11** and strict **Wayland** display servers.

## Features
- **Zero-Friction Documentation**: No need to manually trigger screenshots. Just go about your workflow.
- **Wayland Native Support**: Uses `evdev` to detect global inputs directly from the Linux kernel, bypassing Wayland's security blocks on global hotkeys.
- **Interactive Setup Wizard**: Beautiful, interactive terminal UI to configure exactly which actions trigger a screenshot.
- **Click Throttling**: Built-in 1-second cooldown prevents spamming screenshots when you double-click or drag items.
- **Auto-detects Utilities**: Automatically finds and uses `gnome-screenshot`, `grim`, `spectacle`, or `scrot`.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pdev-labs/StepSnap.git
   cd StepSnap
   ```

2. **Set up a Virtual Environment (Recommended)**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   > **Note:** Depending on your setup, you might need to install Python headers or `evdev` system libraries (e.g., `sudo apt install python3-evdev`).

## Usage

Because StepSnap relies on `evdev` to read raw input events from the kernel, **you must run it with `sudo` privileges**.

If you are using a virtual environment, use the `-E` flag to preserve your Wayland display variables, and point `sudo` to the virtual environment's python executable:

```bash
sudo -E .venv/bin/python stepsnap.py
```

### The Wizard

The first time you run it, a wizard will ask you what actions should trigger a screenshot (Left Click, Right Click, Enter Key). Your preferences are saved automatically!

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.
