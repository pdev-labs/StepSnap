# StepSnap

StepSnap is a lightweight, background screenshot tool designed to help you quickly document your steps for GitHub repositories, tutorials, and Pull Requests.

It silently runs in the background and automatically takes a screenshot whenever you click your mouse or press the `Enter` key. It is fully **cross-platform**, supporting Windows, macOS, and Linux (both X11 and Wayland).

## Features
- **Cross-Platform**: Works everywhere.
- **Zero-Friction Documentation**: No need to manually trigger screenshots. Just go about your workflow.
- **Auto-Generate Markdown**: Automatically embeds every screenshot you take into a `steps.md` file that you can copy straight into GitHub!
- **Wayland Native Support**: Uses `evdev` to detect global inputs directly from the Linux kernel, bypassing Wayland's security blocks on global hotkeys.
- **Custom Sessions**: Name your own screenshot folders, or let it default to the current date and time.
- **Pause/Resume**: Press `F9` at any time to temporarily pause the automatic screenshots if you need to do something else.
- **Click Throttling**: Built-in 1-second cooldown prevents spamming screenshots when you double-click or drag items.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pdev-labs/StepSnap.git
   cd StepSnap
   ```

2. **Set up a Virtual Environment (Recommended)**:
   ```bash
   python -m venv .venv
   ```

3. **Activate the Environment & Install Dependencies**:
   
   **On Windows (PowerShell):**
   ```powershell
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   **On Linux / macOS:**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

**On Windows and macOS:**
Just run the script directly. No special permissions are required!
```bash
python stepsnap.py
```

**On Linux:**
Because StepSnap relies on `evdev` to read raw input events from the kernel to support strict Wayland environments, **you must run it with `sudo` privileges**. Use the `-E` flag to preserve your Wayland display variables, and point `sudo` to the virtual environment's python executable:
```bash
sudo -E .venv/bin/python stepsnap.py
```

### The Wizard

The first time you run it, a wizard will ask you what actions should trigger a screenshot (Left Click, Right Click, Enter Key). Your preferences are saved automatically!

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.
