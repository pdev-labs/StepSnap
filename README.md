# StepSnap 📸

> A lightweight, intelligent screenshot tool that automatically documents your workflow steps — perfect for GitHub tutorials, Pull Requests, and issue reports.

StepSnap runs silently in the background and takes a screenshot every time you click your mouse or press `Enter`. It is fully **cross-platform**, supporting **Windows**, **macOS**, and **Linux** (both X11 and Wayland).

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌍 **Cross-Platform** | Works on Windows, macOS, and Linux (X11 & Wayland) |
| 📝 **Auto-Generate Markdown** | Automatically builds a `steps.md` file as you work — copy and paste it straight into GitHub! |
| 🏷️ **Custom Session Names** | Name your screenshot folder per session, or let it default to the current date and time |
| ⏸️ **Pause / Resume** | Press `F9` anytime to pause and resume capturing |
| 🐧 **Wayland Native** | Uses `evdev` on Linux to bypass Wayland's security restrictions |
| 🛡️ **Click Throttling** | 1-second cooldown prevents duplicate screenshots from double-clicks |
| 🧙 **Setup Wizard** | Interactive terminal wizard to configure your trigger preferences |

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/pdev-labs/StepSnap.git
cd StepSnap
```

### 2. Set up a Virtual Environment *(Recommended)*
```bash
python -m venv .venv
```

### 3. Activate & Install Dependencies

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

> **Linux users** may need the `evdev` system library: `sudo apt install python3-evdev` (Debian/Ubuntu) or `sudo pacman -S python-evdev` (Arch).

---

## 🚀 Usage

### Windows & macOS
No special permissions needed! Just run:
```bash
python stepsnap.py
```

### Linux (Wayland & X11)
Because StepSnap reads raw kernel inputs to support Wayland, it must be run with `sudo`. Use the `-E` flag to preserve your display session variables:
```bash
sudo -E .venv/bin/python stepsnap.py
```

> Also make sure you have a screenshot utility installed: `gnome-screenshot`, `grim`, `spectacle`, or `scrot`.

---

## 🎮 Controls

| Key | Action |
|---|---|
| `F9` | Pause / Resume capturing |
| `Ctrl+C` | Exit StepSnap |

---

## ⚙️ How It Works

1. **Start the tool** — you'll be greeted by an interactive wizard.
2. **Name your session** — type a name for the screenshot folder (e.g., `my-github-tutorial`), or press Enter to use the current date and time.
3. **Configure triggers** — choose whether to capture on left click, right click, and/or the Enter key.
4. **Do your work** — StepSnap watches silently in the background.
5. **Find your results** — a timestamped folder is created in your `~/Downloads/` directory containing all your screenshots AND a ready-to-use `steps.md` file.

### Output Example
```
~/Downloads/my-github-tutorial/
├── step_001.png
├── step_002.png
├── step_003.png
└── steps.md        ← Copy & paste this directly into GitHub!
```

### `steps.md` Example
```markdown
### Step 1
![Step 1](step_001.png)

### Step 2
![Step 2](step_002.png)
```

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](LICENSE) file for details.
