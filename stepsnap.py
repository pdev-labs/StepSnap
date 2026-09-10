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
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
save_dir = os.path.join(downloads_path, timestamp)

if not os.path.exists(save_dir):
    os.makedirs(save_dir)
    if sudo_user:
        subprocess.run(['chown', '-R', sudo_user, save_dir])

console.print("\n" + "="*40)
console.print(f"[bold cyan]Screenshots will be saved to:[/bold cyan]\n{save_dir}")
console.print("="*40 + "\n")

screenshot_counter = 1
screenshot_lock = threading.Lock()
last_screenshot_time = 0.0
COOLDOWN_SECONDS = 1.0

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
        with screenshot_lock:
            current_time = time.time()
            if current_time - last_screenshot_time < COOLDOWN_SECONDS:
                return
            last_screenshot_time = current_time
            time.sleep(0.1)
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
        with screenshot_lock:
            current_time = time.time()
            if current_time - last_screenshot_time < COOLDOWN_SECONDS:
                return
            last_screenshot_time = current_time
            
            time.sleep(0.1)
            filename = os.path.join(save_dir, f"step_{screenshot_counter:03d}.png")
            try:
                with mss.mss() as sct:
                    sct.shot(output=filename)
                console.print(f"[green]✓ Captured:[/green] step_{screenshot_counter:03d}.png")
                screenshot_counter += 1
            except Exception as e:
                console.print(f"[red]✗ Error capturing screenshot: {e}[/red]")

    def on_click(x, y, button, pressed):
        if pressed:
            if triggers.get('mouse_left_click') and button == mouse.Button.left:
                take_screenshot()
            elif triggers.get('mouse_right_click') and button == mouse.Button.right:
                take_screenshot()

    def on_press(key):
        try:
            if triggers.get('enter_key') and key == keyboard.Key.enter:
                take_screenshot()
        except AttributeError:
            pass

    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_press)
    
    mouse_listener.start()
    keyboard_listener.start()

# Keep script running
with console.status("[bold green]Monitoring for actions... Press Ctrl+C to stop.", spinner="dots"):
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting tool. Your screenshots are safe in the Downloads folder![/bold yellow]")
