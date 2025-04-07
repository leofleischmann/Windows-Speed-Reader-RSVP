# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os
import sys
import traceback

# --- Dependency Imports ---
try: from pynput import keyboard; HAS_PYNPUT = True
except ImportError: HAS_PYNPUT = False; print("FATAL ERROR: 'pynput' not found."); # sys.exit("pynput required.")
try: import pyperclip; HAS_PYPERCLIP = True
except ImportError: HAS_PYPERCLIP = False; print("Warning: 'pyperclip' not found.")
try: import pystray; from PIL import Image; HAS_PYSTRAY = True
except ImportError: HAS_PYSTRAY = False; # Pillow check in utils

# --- Local Module Imports ---
try:
    from config import ConfigManager, DEFAULT_SETTINGS
    # Import HAS_PILLOW check from utils
    from utils import create_default_icon, DEFAULT_ICON_NAME, HAS_PILLOW, preprocess_text
    from system_utils import resource_path # Import resource_path
    # Import startup functions if on Windows
    if sys.platform == 'win32':
         from system_utils import add_to_startup, remove_from_startup, is_in_startup
    else: # Provide dummy functions otherwise
         def add_to_startup(p): return False
         def remove_from_startup(): return False
         def is_in_startup(): return False

    from settings_window import SettingsWindow
    from reading_window import ReadingWindow
except ImportError as e:
     print(f"FATAL ERROR: Could not import local modules: {e}")
     root_err = tk.Tk(); root_err.withdraw(); messagebox.showerror("Import Fehler", f"Modulimport fehlgeschlagen: {e}"); root_err.destroy(); sys.exit(f"Import Error: {e}")


# --- Main Application Class ---
class SpeedReaderApp:
    def __init__(self, root):
        self.root = root
        self.config = ConfigManager()
        self.hide_main_window_flag = HAS_PYSTRAY and self.config.get("hide_main_window")
        self.hotkey_listener = None; self.listener_thread = None
        self.reading_window_instance = None; self.settings_window_instance = None
        self.tray_icon = None; self.tray_thread = None

        if self.hide_main_window_flag:
            print("Hiding main window."); self.root.withdraw(); self.status_label = None; self.menu_bar = None
        else:
            print("Main window visible."); self.root.title("Speed Reader Steuerung"); self.root.geometry("350x150"); self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
            self.menu_bar = tk.Menu(root); root.config(menu=self.menu_bar)
            file_menu = tk.Menu(self.menu_bar, tearoff=0); self.menu_bar.add_cascade(label="Datei", menu=file_menu)
            file_menu.add_command(label="Datei lesen...", command=self.read_from_file)
            cb_state = "normal" if HAS_PYPERCLIP else "disabled"; file_menu.add_command(label="Aus Zwischenablage lesen", command=self.read_from_clipboard, state=cb_state)
            file_menu.add_separator(); file_menu.add_command(label="Beenden", command=self.quit_app)
            settings_menu = tk.Menu(self.menu_bar, tearoff=0); self.menu_bar.add_cascade(label="Optionen", menu=settings_menu)
            settings_menu.add_command(label="Einstellungen...", command=self.open_settings)
            self.status_label = ttk.Label(root, text="Initialisiere...", padding=10, anchor="center"); self.status_label.pack(pady=20, fill="x", expand=True)

        if HAS_PYNPUT: self.start_hotkey_listener()
        else: self.update_status_label("Hotkey Fehler: pynput fehlt!")

        if HAS_PYSTRAY and HAS_PILLOW: # Pillow needed for icon
            self.setup_tray_icon()
            if self.tray_icon: self.tray_thread = threading.Thread(target=self.run_tray_icon, daemon=True); self.tray_thread.start()
            else: print("Tray icon setup failed."); self.update_status_label("Tray Fehler: Icon Setup")
        else:
             msg = ""
             if not HAS_PYSTRAY: msg += "pystray fehlt. "
             if not HAS_PILLOW: msg += "Pillow fehlt."
             print(f"Tray icon disabled: {msg}")
             self.update_status_label(f"Tray deaktiviert: {msg}")

        self.update_status_label()

    def update_status_label(self, message=None):
        if not hasattr(self, 'status_label') or not self.status_label: return
        try:
            if not self.status_label.winfo_exists(): return
            if message: display_text = message
            else:
                hotkey = self.config.get("hotkey")
                listener_active = self.listener_thread and self.listener_thread.is_alive()
                status = "Aktiv" if listener_active and HAS_PYNPUT else "Inaktiv"
                if not HAS_PYNPUT: status = "Fehler (pynput fehlt)"
                display_text = f"Hotkey: {hotkey} ({status})"
                if not listener_active and HAS_PYNPUT and self.config.get("hotkey"): display_text += " - Fehler?"
            self.status_label.config(text=display_text)
        except tk.TclError: pass # Ignore if destroyed

    def setup_tray_icon(self):
        if not HAS_PYSTRAY or not HAS_PILLOW: self.tray_icon = None; return
        try:
            icon_path = resource_path(DEFAULT_ICON_NAME)
            icon_image = Image.open(icon_path) if os.path.exists(icon_path) else create_default_icon()
            if not icon_image: print("Error: Tray icon image not found or created."); self.tray_icon = None; return
            menu_items = []
            cb_state = HAS_PYPERCLIP; menu_items.append(pystray.MenuItem('Lesen aus Zwischenablage', self.on_tray_read_clipboard, enabled=cb_state))
            menu_items.extend([ pystray.MenuItem('Datei lesen...', self.on_tray_read_file), pystray.MenuItem('Einstellungen...', self.on_tray_open_settings), pystray.MenuItem(f'Hotkey: {self.config.get("hotkey")}', None, enabled=False), pystray.MenuItem('Beenden', self.on_tray_quit) ])
            tray_menu = pystray.Menu(*menu_items)
            self.tray_icon = pystray.Icon("SpeedReader", icon=icon_image, title="Speed Reader", menu=tray_menu)
            print("System tray icon configured.")
        except Exception as e: print(f"Error setting up tray icon: {e}"); traceback.print_exc(); self.tray_icon = None

    def run_tray_icon(self):
        if self.tray_icon:
            print("Starting pystray icon loop...");
            try: self.tray_icon.run()
            except Exception as e: print(f"Error running pystray icon: {e}")
            finally: print("Pystray icon loop finished.")
        else: print("Tray icon not available.")

    # --- Tray Menu Action Wrappers ---
    def on_tray_read_clipboard(self, icon=None, item=None):
        print("Tray action: Read clipboard"); self.root.after(0, self.read_from_clipboard)
    def on_tray_read_file(self, icon=None, item=None):
        print("Tray action: Read file"); self.root.after(0, self.read_from_file)
    def on_tray_open_settings(self, icon=None, item=None):
        print("Tray action: Open settings"); self.root.after(0, self.open_settings)
    def on_tray_quit(self, icon=None, item=None):
        print("Tray action: Quit");
        if self.tray_icon: self.tray_icon.stop()
        self.root.after(0, self.quit_app)

    # --- Hotkey Listener Methods ---
    def start_hotkey_listener(self):
        if not HAS_PYNPUT: self.update_status_label("Hotkey Fehler: pynput fehlt!"); return
        self.stop_hotkey_listener(); hotkey_str = self.config.get("hotkey")
        if not hotkey_str: self.update_status_label("Hotkey nicht konfiguriert"); return
        print(f"Attempting to register hotkey: {hotkey_str}")
        def on_activate():
            print(f"Hotkey '{hotkey_str}' activated!")
            if HAS_PYPERCLIP: self.root.after(0, self.read_from_clipboard)
            else: self.root.after(0, lambda: messagebox.showwarning("Fehlende Bibliothek", "'pyperclip' wird benötigt."))
        def listener_thread_func():
            nonlocal hotkey_str
            try:
                self.hotkey_listener = keyboard.GlobalHotKeys({ hotkey_str: on_activate })
                print(f"Hotkey listener starting with: {hotkey_str}"); self.hotkey_listener.run()
            except Exception as e:
                 error_msg = f"Fehler beim Registrieren/Ausführen des Hotkeys '{hotkey_str}':\n{e}"; print(f"Error in listener thread: {error_msg}"); traceback.print_exc()
                 self.root.after(0, lambda: messagebox.showerror("Hotkey Fehler", error_msg)); self.update_status_label(f"Hotkey Fehler: {hotkey_str}")
            finally: print("Hotkey listener thread finished."); self.hotkey_listener = None; self.update_status_label()
        self.listener_thread = threading.Thread(target=listener_thread_func, daemon=True); self.listener_thread.start()
        time.sleep(0.2); self.update_status_label()

    def stop_hotkey_listener(self):
        """Stops the global hotkey listener thread if it exists."""
        listener = self.hotkey_listener # Local ref for safety
        # --- KORREKTUR: Check if listener exists before stopping ---
        if listener:
            print("Stopping hotkey listener...")
            try:
                listener.stop()
                self.hotkey_listener = None # Clear after stopping
            except Exception as e:
                print(f"Error stopping hotkey listener: {e}")
        # --- Ende Korrektur ---
        else:
             print("Hotkey listener was not running.") # Info message

        thread = self.listener_thread
        if thread and thread.is_alive():
             print("Waiting for listener thread to join...")
             thread.join(timeout=0.5)
             if thread.is_alive(): print("Warning: Listener thread did not stop gracefully.")
        self.listener_thread = None
        print("Hotkey listener stopped.") # This message might be slightly inaccurate if it never started
        self.update_status_label()


    # --- Core Application Logic Methods ---
    def open_settings(self):
        """Opens the settings window, ensuring visibility even with hidden root."""
        if self.settings_window_instance and self.settings_window_instance.winfo_exists():
            print("Settings window already open."); self.settings_window_instance.focus_set(); self.settings_window_instance.lift(); return
        print("Opening settings window...")
        def settings_closed_callback():
            print("Settings window closed."); self.settings_window_instance = None
            print("Restarting hotkey listener...");
            if HAS_PYNPUT: self.start_hotkey_listener()
            # Apply changes potentially affecting reading window
            if self.reading_window_instance and self.reading_window_instance.winfo_exists():
                 print("Applying settings to reading window..."); self.reading_window_instance.update_display_settings()
            self.update_status_label()
        root_was_hidden = False
        try:
            if self.root.state() == 'withdrawn': root_was_hidden = True; print("Temp deiconify root..."); self.root.deiconify(); self.root.update_idletasks(); time.sleep(0.05)
            self.settings_window_instance = SettingsWindow(self.root, self.config, settings_closed_callback)
            print("SettingsWindow instance created.")
            self.root.update_idletasks()
            if self.settings_window_instance and self.settings_window_instance.winfo_exists():
                 print("Forcing settings window visibility..."); self.settings_window_instance.deiconify(); self.settings_window_instance.lift(); self.settings_window_instance.focus_force()
            else: print("Settings window instance invalid after creation."); self.settings_window_instance = None
        except Exception as e: print("!!! Error creating/showing SettingsWindow !!!"); traceback.print_exc(); messagebox.showerror("Fenster Fehler", f"Einstellungen konnten nicht erstellt/angezeigt werden:\n{e}"); self.settings_window_instance = None
        finally:
            if root_was_hidden: print("Re-withdrawing root..."); self.root.withdraw()

    def _initiate_reading(self, text):
        """Helper function to create and start the reading window."""
        parent_window = self.root
        if not text: messagebox.showwarning("Kein Text", "Kein Text zum Lesen bereitgestellt.", parent=parent_window); return
        if self.reading_window_instance and self.reading_window_instance.winfo_exists(): print("Closing existing reading window."); self.reading_window_instance.close_window(); self.reading_window_instance = None
        print("Initiating new reading window...")
        root_was_hidden_read = False
        try:
            if self.root.state() == 'withdrawn': root_was_hidden_read = True; self.root.deiconify(); self.root.update_idletasks(); time.sleep(0.05)
            self.reading_window_instance = ReadingWindow(parent_window, self.config)
            self.root.update_idletasks()
            if self.reading_window_instance.winfo_exists():
                 self.reading_window_instance.deiconify(); self.reading_window_instance.lift()
                 self.reading_window_instance.start_reading(text)
                 print("ReadingWindow instance created and reading started.")
            else: print("Reading window instance invalid after creation."); self.reading_window_instance = None
        except Exception as e: print("!!! Error creating/starting ReadingWindow !!!"); traceback.print_exc(); messagebox.showerror("Fenster Fehler", f"Lesefenster konnte nicht erstellt/gestartet werden:\n{e}"); self.reading_window_instance = None
        finally:
             if root_was_hidden_read: self.root.withdraw()

    def read_from_clipboard(self):
        if not HAS_PYPERCLIP: messagebox.showerror("Fehler", "'pyperclip' fehlt."); return
        print("Reading from clipboard...")
        try:
            text = pyperclip.paste();
            if text: self._initiate_reading(text)
            else: messagebox.showinfo("Zwischenablage leer", "Kein Text in Zwischenablage.")
        except Exception as e: error_msg = f"Fehler beim Clipboard-Zugriff:\n{e}"; print(error_msg); traceback.print_exc(); messagebox.showerror("Fehler", error_msg)

    def read_from_file(self):
        print("Opening file dialog...")
        filepath = None; root_visible = self.root.state() != 'withdrawn'
        try:
            parent = self.root if root_visible else None; filepath = filedialog.askopenfilename(title="Textdatei öffnen", filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")], parent=parent)
        except tk.TclError as e:
             print(f"TclError opening file dialog: {e}");
             try: filepath = filedialog.askopenfilename(title="Textdatei öffnen", filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")])
             except Exception as e_fallback: print(f"Error opening file dialog w/o parent: {e_fallback}"); messagebox.showerror("Dialog Fehler", f"Dateidialog Fehler:\n{e_fallback}"); return
        if not filepath: print("File selection cancelled."); return
        print(f"Reading from file: {filepath}")
        try:
            try:
                with open(filepath, 'r', encoding='utf-8') as f: text = f.read()
            except UnicodeDecodeError: print("UTF-8 failed, trying default encoding...");
            with open(filepath, 'r', encoding=sys.getdefaultencoding()) as f: text = f.read()
            self._initiate_reading(text)
        except Exception as e: error_msg = f"Datei konnte nicht gelesen werden:\n{filepath}\n\nFehler: {e}"; print(error_msg); traceback.print_exc(); messagebox.showerror("Fehler Dateizugriff", error_msg)

    def quit_app(self):
        """Cleans up resources and closes the application."""
        print("Quit requested. Cleaning up...")
        self.stop_hotkey_listener()
        if self.tray_icon: print("Stopping tray icon..."); self.tray_icon.stop()
        if self.tray_thread and self.tray_thread.is_alive(): print("Waiting for tray thread..."); self.tray_thread.join(timeout=0.5)

        print("Closing open windows...")
        # Use try-except for destroying specific instances (Corrected syntax)
        if self.settings_window_instance and self.settings_window_instance.winfo_exists():
             print("Destroying settings window instance...")
             try: self.settings_window_instance.destroy()
             except tk.TclError: pass # Ignore error if already destroyed
        if self.reading_window_instance and self.reading_window_instance.winfo_exists():
             print("Destroying reading window instance...")
             try: self.reading_window_instance.destroy()
             except tk.TclError: pass # Ignore error if already destroyed

        # Destroy other Toplevels associated with root (Corrected syntax)
        if self.root.winfo_exists():
             children = list(self.root.winfo_children())
             for widget in children:
                  if isinstance(widget, tk.Toplevel):
                       print(f"Destroying other Toplevel: {widget.title()}")
                       try: widget.destroy()
                       except tk.TclError: pass # Ignore error if already destroyed

        print("Destroying Tkinter root...")
        try:
            if self.root.winfo_exists(): self.root.destroy(); print("Tkinter root destroyed.")
        except tk.TclError as e: print(f"TclError destroying root: {e}")

        print("Application cleanup finished. Exiting.")
        # os._exit(0) # Force exit only if absolutely necessary


# --- Application Entry Point ---
if __name__ == "__main__":
    # Simple check if another instance might be running (optional, basic)
    # This is not foolproof, uses a simple lock file concept
    lock_file_path = os.path.join(os.getenv('TEMP', '/tmp'), 'speedreader_instance.lock')
    lock_file = None
    try:
        # Try to create lock file exclusively
        lock_file = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        print("Lock file created.")
    except FileExistsError:
         print("Another instance might be running (lock file exists). Exiting.")
         # Optionally show a message box
         root_check = tk.Tk(); root_check.withdraw(); messagebox.showerror("SpeedReader", "Eine andere Instanz von SpeedReader läuft bereits."); root_check.destroy()
         sys.exit(1)
    except Exception as e:
         print(f"Error creating lock file: {e}")
         # Continue execution even if lock file fails? Or exit? Let's continue for now.
         pass # Continue without lock file guarantee

    print("Starting Speed Reader Application...")
    if not HAS_PYNPUT: root_check = tk.Tk(); root_check.withdraw(); messagebox.showerror("Kritischer Fehler", "'pynput' fehlt.\nInstallieren: pip install pynput"); root_check.destroy(); sys.exit("Fehler: pynput nicht gefunden.")
    root = tk.Tk()
    app = SpeedReaderApp(root)
    print("Starting Tkinter main loop...")
    try: root.mainloop()
    except KeyboardInterrupt: print("\nKeyboardInterrupt. Shutting down..."); app.quit_app()
    except Exception as e: print("\nUnhandled exception in main loop:"); traceback.print_exc();
    finally:
         # Ensure lock file is removed on exit
         if lock_file is not None:
              try:
                   os.close(lock_file)
                   os.remove(lock_file_path)
                   print("Lock file removed.")
              except Exception as e_lock:
                   print(f"Error removing lock file: {e_lock}")
         # Attempt cleanup again if mainloop failed before quit_app
         try:
              if root.winfo_exists(): # Check if quit_app already destroyed it
                   app.quit_app()
         except Exception as quit_e: print(f"Error during final shutdown: {quit_e}")

    print("Application exited.")

