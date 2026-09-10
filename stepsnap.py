import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.live import Live
from rich.text import Text

console = Console()
CONFIG_FILE = 'config.json'

def run_wizard():
    console.clear()
    console.print(Panel.fit("[bold blue]Automatic Screenshot Tool Setup[/bold blue]", border_style="blue"))
    console.print("Welcome! Let's configure your screenshot session.\n")

    triggers = {
        "mouse_left_click": Confirm.ask("Take screenshot on [bold green]Left Mouse Click[/bold green]?", default=True),
        "mouse_right_click": Confirm.ask("Take screenshot on [bold green]Right Mouse Click[/bold green]?", default=False),
        "enter_key": Confirm.ask("Take screenshot on [bold green]Enter Key[/bold green] press?", default=True)
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump({
            "triggers": triggers,
            "screenshot_command": "auto"
        }, f, indent=4)
        
    return triggers

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return run_wizard()
        
    console.print("[yellow]Previous configuration found.[/yellow]")
    if Confirm.ask("Do you want to reconfigure your triggers?", default=False):
        return run_wizard()
    
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        return config.get("triggers", {})

triggers = load_config()

console.print("")
console.print("")
while True:
    session_name = console.input("[bold cyan]Enter a folder name for this session[/bold cyan] (leave blank for date/time): ").strip()
    if not session_name:
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        break
    
    # Determine the downloads path to check for existing folder
    _check_home = os.path.expanduser("~")
    _check_dir = os.path.join(_check_home, 'Downloads', session_name)
    
    if os.path.exists(_check_dir):
        console.print(f"[bold yellow]⚠ Warning:[/bold yellow] A folder named '[bold]{session_name}[/bold]' already exists in your Downloads.")
        choice = console.input("  [dim]Type a [bold]new name[/bold] or press [bold]Enter[/bold] to overwrite: [/dim]").strip()
        if not choice:
            # User confirmed overwrite
            console.print(f"[dim]Using existing folder '{session_name}'.[/dim]")
            break
        else:
            session_name = choice
    else:
        break

# Setup paths based on platform and sudo
if sys.platform == 'linux':
    if os.geteuid() != 0:
        console.print(Panel.fit("[bold red]Error: On Linux, this tool must be run with sudo![/bold red]\nTry running: [bold]sudo -E python stepsnap.py[/bold]", border_style="red"))
        sys.exit(1)
        
    sudo_user = os.getenv('SUDO_USER')
    if sudo_user:
        home_dir = os.path.expanduser(f"~{sudo_user}")
    else:
        home_dir = os.path.expanduser("~")
else:
    # Windows/Mac
    home_dir = os.path.expanduser("~")
    sudo_user = None

downloads_path = os.path.join(home_dir, 'Downloads')
save_dir = os.path.join(downloads_path, session_name)

if not os.path.exists(save_dir):
    os.makedirs(save_dir)
    if sudo_user:
        subprocess.run(['chown', '-R', sudo_user, save_dir])

console.print("\n" + "="*40)
console.print(f"[bold cyan]Screenshots will be saved to:[/bold cyan]\n{save_dir}")
console.print("="*40)
console.print("\n[dim]Press [bold white]F9[/bold white] to Pause/Resume   |   [bold white]Ctrl+C[/bold white] to Stop[/dim]\n")

screenshot_counter = 1
screenshot_lock = threading.Lock()
last_screenshot_time = 0.0
COOLDOWN_SECONDS = 1.0
is_paused = False

def append_to_markdown(counter, filename):
    md_file = os.path.join(save_dir, "steps.md")
    with open(md_file, "a", encoding="utf-8") as f:
        f.write(f"### Step {counter}\n![Step {counter}]({os.path.basename(filename)})\n\n")
    if sys.platform == 'linux' and sudo_user:
        try:
            subprocess.run(['chown', sudo_user, md_file], check=False)
        except Exception:
            pass

def toggle_pause():
    global is_paused
    is_paused = not is_paused
    state = "PAUSED" if is_paused else "ACTIVE"
    color = "red" if is_paused else "green"

# -------------------------------------------------------------
# Linux (evdev) implementation
# -------------------------------------------------------------
if sys.platform == 'linux':
    import evdev
    from evdev import ecodes
    
    cmd_pref = "auto"
    def determine_screenshot_cmd(filename):
        if cmd_pref != "auto":
            return cmd_pref.replace("{file}", filename).split()

        if subprocess.run(['which', 'gnome-screenshot'], capture_output=True).returncode == 0:
            return ['gnome-screenshot', '-f', filename]
        if subprocess.run(['which', 'grim'], capture_output=True).returncode == 0:
            return ['grim', filename]
        if subprocess.run(['which', 'spectacle'], capture_output=True).returncode == 0:
            return ['spectacle', '-b', '-n', '-o', filename]
        if subprocess.run(['which', 'scrot'], capture_output=True).returncode == 0:
            return ['scrot', filename]

        console.print("[bold red]WARNING:[/bold red] Could not find a suitable screenshot tool.")
        return None

    def take_screenshot():
        global screenshot_counter, last_screenshot_time
        if is_paused:
            return
            
        with screenshot_lock:
            current_time = time.time()
            if current_time - last_screenshot_time < COOLDOWN_SECONDS:
                return
            last_screenshot_time = current_time
            filename = os.path.join(save_dir, f"step_{screenshot_counter:03d}.png")
            
            cmd = determine_screenshot_cmd(filename)
            if not cmd:
                return
                
            try:
                if sudo_user:
                    uid = subprocess.check_output(['id', '-u', sudo_user]).decode().strip()
                    env = os.environ.copy()
                    xdg_runtime = f'/run/user/{uid}'
                    env['XDG_RUNTIME_DIR'] = xdg_runtime
                    
                    if 'WAYLAND_DISPLAY' not in env:
                        import glob
                        sockets = glob.glob(f'{xdg_runtime}/wayland-[0-9]')
                        if sockets:
                            env['WAYLAND_DISPLAY'] = os.path.basename(sockets[0])
                        else:
                            env['WAYLAND_DISPLAY'] = 'wayland-0'
                            
                    if 'DISPLAY' not in env:
                        env['DISPLAY'] = ':0'
                        
                    if 'grim' in cmd and 'SWAYSOCK' not in env:
                        swaysocks = glob.glob(f'{xdg_runtime}/sway-ipc.*.sock')
                        if swaysocks:
                            env['SWAYSOCK'] = swaysocks[0]
                            
                    if 'grim' in cmd and 'HYPRLAND_INSTANCE_SIGNATURE' not in env:
                        hypr = glob.glob(f'/tmp/hypr/*')
                        if hypr:
                            env['HYPRLAND_INSTANCE_SIGNATURE'] = os.path.basename(hypr[0])
                            
                    res = subprocess.run(['sudo', '-u', sudo_user, '-E'] + cmd, env=env, capture_output=True, text=True)
                else:
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    
                if res.returncode == 0:
                    console.print(f"[green]✓ Captured:[/green] step_{screenshot_counter:03d}.png")
                    append_to_markdown(screenshot_counter, filename)
                    screenshot_counter += 1
                else:
                    console.print(f"[red]✗ Error capturing screenshot. Command: {' '.join(cmd)}[/red]")
                    console.print(f"[red]Details: {res.stderr.strip()}[/red]")
                    
            except Exception as e:
                console.print(f"[red]✗ Error capturing screenshot: {e}[/red]")

    def monitor_device(device):
        try:
            for event in device.read_loop():
                if event.type == ecodes.EV_KEY and event.value == 1:
                    if event.code == ecodes.KEY_F9:
                        toggle_pause()
                        continue
                        
                    if is_paused:
                        continue
                        
                    if triggers.get('mouse_left_click') and event.code == ecodes.BTN_LEFT:
                        take_screenshot()
                    elif triggers.get('mouse_right_click') and event.code == ecodes.BTN_RIGHT:
                        take_screenshot()
                    elif triggers.get('enter_key') and event.code == ecodes.KEY_ENTER:
                        take_screenshot()
        except Exception:
            pass

    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    input_devices = [d for d in devices if ecodes.EV_KEY in d.capabilities()]

    if not input_devices:
        console.print("[bold red]No input devices found. Did you run with sudo?[/bold red]")
        sys.exit(1)

    threads = []
    for device in input_devices:
        t = threading.Thread(target=monitor_device, args=(device,), daemon=True)
        t.start()
        threads.append(t)

# -------------------------------------------------------------
# Windows / macOS (pynput + mss) implementation
# -------------------------------------------------------------
else:
    from pynput import mouse, keyboard
    import mss

    def take_screenshot():
        global screenshot_counter, last_screenshot_time
        if is_paused:
            return
            
        with screenshot_lock:
            current_time = time.time()
            if current_time - last_screenshot_time < COOLDOWN_SECONDS:
                return
            last_screenshot_time = current_time
            
            filename = os.path.join(save_dir, f"step_{screenshot_counter:03d}.png")
            try:
                with mss.mss() as sct:
                    sct.shot(output=filename)
                console.print(f"[green]✓ Captured:[/green] step_{screenshot_counter:03d}.png")
                append_to_markdown(screenshot_counter, filename)
                screenshot_counter += 1
            except Exception as e:
                console.print(f"[red]✗ Error capturing screenshot: {e}[/red]")

    def on_click(x, y, button, pressed):
        if is_paused:
            return
        if pressed:
            if triggers.get('mouse_left_click') and button == mouse.Button.left:
                take_screenshot()
            elif triggers.get('mouse_right_click') and button == mouse.Button.right:
                take_screenshot()

    def on_press(key):
        try:
            if key == keyboard.Key.f9:
                toggle_pause()
                return
                
            if is_paused:
                return
                
            if triggers.get('enter_key') and key == keyboard.Key.enter:
                take_screenshot()
        except AttributeError:
            pass

    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_press)
    
    mouse_listener.start()
    keyboard_listener.start()

# Keep script running with a live status panel
def make_status_panel():
    state = "PAUSED ⏸" if is_paused else "ACTIVE ▶"
    color = "bold red" if is_paused else "bold green"
    count_info = f"[dim]Screenshots captured:[/dim] [bold white]{screenshot_counter - 1}[/bold white]"
    controls = "[dim]\[F9] Pause/Resume   \[Ctrl+C] Stop[/dim]"
    panel_content = Text.from_markup(
        f"Status: [{color}]{state}[/{color}]   {count_info}\n{controls}"
    )
    return Panel(panel_content, title="[bold blue]StepSnap[/bold blue]", border_style="blue")

try:
    with Live(make_status_panel(), refresh_per_second=4, console=console) as live:
        while True:
            live.update(make_status_panel())
            time.sleep(0.25)
except KeyboardInterrupt:
    console.print("\n[bold yellow]Exiting tool. Your screenshots are safe in the Downloads folder![/bold yellow]")
