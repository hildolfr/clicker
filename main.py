import sys
from PyQt5 import QtWidgets, QtGui
import os
import json
import time
import threading
import pyautogui
import keyboard
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import heapq
import atexit

SETTINGS_FILE = 'settings.json'
KEYSTROKES_FILE = 'keystrokes.txt'
LOCKFILE = 'clicker.lock'

settings = {}
keystrokes = []
toggle_key = '~'
pause_time = 0.5
running_flag = {'active': False}
thread = {'obj': None}
observer = None
hotkey_ref = {'key': None}
lock = threading.Lock()

# --- Singleton check ---
def check_singleton():
    if os.path.exists(LOCKFILE):
        QtWidgets.QMessageBox.critical(None, 'Already running', 'Another instance of Clicker is already running.')
        sys.exit(1)
    with open(LOCKFILE, 'w') as f:
        f.write(str(os.getpid()))
    def cleanup():
        try:
            os.remove(LOCKFILE)
        except Exception:
            pass
    atexit.register(cleanup)

# Load settings and keystrokes

def load_settings():
    global settings, toggle_key, pause_time
    with lock:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        toggle_key = settings.get('toggle_key', '~')
        pause_time = settings.get('pause_time', 0.5)

def load_keystrokes():
    global keystrokes
    with lock:
        keystrokes = []
        with open(KEYSTROKES_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    key, delay = parts
                    try:
                        delay = float(delay)
                        keystrokes.append((key, delay))
                    except ValueError:
                        continue

def parse_keystroke(key_str):
    parts = key_str.split('-')
    mods = []
    key = parts[-1]
    for p in parts[:-1]:
        if p == 'S':
            mods.append('shift')
        elif p == 'C':
            mods.append('ctrl')
        elif p == 'A':
            mods.append('alt')
    return mods, key

# --- Serialized Automation Worker ---

def automation_worker():
    schedule = []
    with lock:
        now = time.time()
        for idx, (key_str, delay) in enumerate(keystrokes):
            heapq.heappush(schedule, (now + pause_time, idx, key_str, delay))
    while True:
        with lock:
            active = running_flag['active']
        if not active or not schedule:
            break
        next_fire, idx, key_str, delay = heapq.heappop(schedule)
        wait_time = max(0, next_fire - time.time())
        if wait_time > 0:
            time.sleep(wait_time)
        with lock:
            if not running_flag['active']:
                break
        mods, key = parse_keystroke(key_str)
        try:
            if mods:
                pyautogui.hotkey(*mods, key)
            else:
                pyautogui.press(key)
        except Exception as e:
            # Log or ignore key errors
            pass
        with lock:
            schedule.append((time.time() + delay, idx, key_str, delay))
            heapq.heapify(schedule)

# --- End Worker ---

def start_automation():
    with lock:
        if running_flag['active']:
            return
        running_flag['active'] = True
    thread['obj'] = threading.Thread(target=automation_worker, daemon=True)
    thread['obj'].start()

def stop_automation():
    with lock:
        running_flag['active'] = False
    # Worker will exit on next check

def rebind_hotkey():
    # Remove previous hotkey if set
    if hotkey_ref['key'] is not None:
        try:
            keyboard.remove_hotkey(hotkey_ref['key'])
        except Exception:
            pass
    hotkey_ref['key'] = keyboard.add_hotkey(toggle_key, toggle)

def toggle():
    with lock:
        active = running_flag['active']
    if active:
        stop_automation()
    else:
        start_automation()

def reload_all():
    stop_automation()
    load_settings()
    load_keystrokes()
    rebind_hotkey()

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(SETTINGS_FILE) or event.src_path.endswith(KEYSTROKES_FILE):
            reload_all()

def main():
    global observer
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    check_singleton()

    # Create the icon
    if os.path.exists('icon.ico'):
        icon = QtGui.QIcon('icon.ico')
    else:
        icon = QtGui.QIcon()
        icon.addPixmap(app.style().standardPixmap(QtWidgets.QStyle.SP_ComputerIcon))

    # Create the tray
    tray = QtWidgets.QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    # Create the menu
    menu = QtWidgets.QMenu()
    open_keystrokes_action = menu.addAction('Open keystrokes.txt')
    open_settings_action = menu.addAction('Open settings.json')
    reload_action = menu.addAction('Reload settings/keystrokes')
    quit_action = menu.addAction('Quit')

    def open_file(path):
        abs_path = os.path.abspath(path)
        try:
            os.startfile(abs_path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, 'Error', f'Could not open {abs_path}: {e}')

    open_keystrokes_action.triggered.connect(lambda: open_file(KEYSTROKES_FILE))
    open_settings_action.triggered.connect(lambda: open_file(SETTINGS_FILE))
    reload_action.triggered.connect(reload_all)
    quit_action.triggered.connect(lambda: (stop_automation(), app.quit()))

    tray.setContextMenu(menu)

    # Initial load
    load_settings()
    load_keystrokes()
    rebind_hotkey()

    # Watchdog setup
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, '.', recursive=False)
    observer.start()

    try:
        sys.exit(app.exec_())
    finally:
        observer.stop()
        observer.join()
        stop_automation()
        keyboard.unhook_all_hotkeys()
        if os.path.exists(LOCKFILE):
            try:
                os.remove(LOCKFILE)
            except Exception:
                pass

if __name__ == '__main__':
    main() 