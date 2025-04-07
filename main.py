# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os
import sys
import traceback # For detailed error messages

# --- Dependency Imports ---
try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    print("FATAL ERROR: 'pynput' library not found. Hotkey functionality will not work.")
    print("Install with: pip install pynput")
    # sys.exit("pynput is required.") # Exit if critical

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False
    print("Warning: 'pyperclip' library not found. Reading from clipboard will not work.")
    print("Install with: pip install pyperclip")

# System Tray Icon related imports
try:
    import pystray
    from PIL import Image # Pillow is also needed by utils.create_default_icon
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False
    if 'pystray' not in sys.modules:
         print("Warning: 'pystray' library not found. System tray icon functionality is disabled.")
         print("Install with: pip install pystray")


# --- Local Module Imports ---
# Ensure these files exist in the same directory
try:
    from config import ConfigManager, DEFAULT_SETTINGS # Import defaults for initial check
    from utils import create_default_icon, DEFAULT_ICON_NAME, HAS_PILLOW # Pillow check needed for tray
    from settings_window import SettingsWindow
    from reading_window import ReadingWindow
except ImportError as e:
     print(f"FATAL ERROR: Could not import local modules: {e}")
     print("Please ensure config.py, utils.py, settings_window.py, and reading_window.py are in the same directory.")
     # Show Tkinter error box before exiting
     root_err = tk.Tk()
     root_err.withdraw()
     messagebox.showerror("Import Fehler", f"Lokales Modul konnte nicht importiert werden: {e}\nStellen Sie sicher, dass alle .py Dateien im selben Ordner liegen.")
     root_err.destroy()
     sys.exit(f"Import Error: {e}")


# --- Main Application Class ---
class SpeedReaderApp:
    """
    The main application class coordinating UI, configuration, and background tasks.
    """
    def __init__(self, root):
        """
        Initializes the main application.

        Args:
            root (tk.Tk): The main Tkinter root window.
        """
        self.root = root
        self.config = ConfigManager() # Load settings immediately

        # --- Restore original logic for hiding main window ---
        self.hide_main_window_flag = HAS_PYSTRAY and self.config.get("hide_main_window")

        # --- Application State Variables ---
        self.hotkey_listener = None
        self.listener_thread = None
        self.reading_window_instance = None
        self.settings_window_instance = None
        self.tray_icon = None
        self.tray_thread = None

        # --- Configure UI based on flag ---
        if self.hide_main_window_flag:
            print("Hiding main window, running from system tray.")
            self.root.withdraw() # Hide the main window
            self.status_label = None # No status label if window is hidden
            self.menu_bar = None
        else:
            # Configure the visible main window
            print("Main window will be visible.")
            self.root.title("Speed Reader Steuerung")
            self.root.geometry("350x150") # Small control window
            self.root.protocol("WM_DELETE_WINDOW", self.quit_app) # Handle closing

            # --- Menu Bar (only if window is visible) ---
            self.menu_bar = tk.Menu(root)
            root.config(menu=self.menu_bar)

            file_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="Datei", menu=file_menu)
            file_menu.add_command(label="Datei lesen...", command=self.read_from_file)
            if HAS_PYPERCLIP:
                 file_menu.add_command(label="Aus Zwischenablage lesen", command=self.read_from_clipboard)
            else:
                 file_menu.add_command(label="Aus Zwischenablage lesen", state="disabled")
            file_menu.add_separator()
            file_menu.add_command(label="Beenden", command=self.quit_app)

            settings_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="Optionen", menu=settings_menu)
            settings_menu.add_command(label="Einstellungen...", command=self.open_settings)

            # --- Status Label (only if window is visible) ---
            self.status_label = ttk.Label(root, text="Initialisiere...", padding=10, anchor="center")
            self.status_label.pack(pady=20, fill="x", expand=True)


        # --- Initialize Components ---
        if HAS_PYNPUT:
            self.start_hotkey_listener()
        else:
             if hasattr(self, 'status_label') and self.status_label: self.update_status_label("Hotkey Fehler: pynput fehlt!")

        # Tray Icon Setup
        if HAS_PYSTRAY and HAS_PILLOW:
            self.setup_tray_icon()
            if self.tray_icon:
                self.tray_thread = threading.Thread(target=self.run_tray_icon, daemon=True)
                self.tray_thread.start()
            else:
                 print("Tray icon setup failed, tray thread not started.")
                 if hasattr(self, 'status_label') and self.status_label: self.update_status_label("Tray Fehler: Icon Setup")
        elif HAS_PYSTRAY and not HAS_PILLOW:
             print("Warning: Cannot start system tray icon because Pillow is missing.")
             if hasattr(self, 'status_label') and self.status_label: self.update_status_label("Tray Fehler: Pillow fehlt!")
        elif not HAS_PYSTRAY:
             print("Info: pystray not found, tray icon disabled.")
             if hasattr(self, 'status_label') and self.status_label: self.update_status_label("Tray nicht verfügbar")

        if hasattr(self, 'status_label') and self.status_label: self.update_status_label()


    def update_status_label(self, message=None):
        """Updates the status label in the main window if it's visible and exists."""
        if not hasattr(self, 'status_label') or not self.status_label: return
        # Check if widget exists before configuring
        try:
            if not self.status_label.winfo_exists(): return
        except tk.TclError:
            return # Widget has been destroyed

        if message: display_text = message
        else:
            hotkey = self.config.get("hotkey")
            listener_active = self.listener_thread and self.listener_thread.is_alive()
            status = "Aktiv" if listener_active and HAS_PYNPUT else "Inaktiv"
            if not HAS_PYNPUT: status = "Fehler (pynput fehlt)"
            cb_status = "OK" if HAS_PYPERCLIP else "N/V"
            tray_status = "Aktiv" if self.tray_icon and self.tray_icon.visible else "Inaktiv"
            if HAS_PYSTRAY and not HAS_PILLOW: tray_status = "Fehler (Pillow fehlt)"
            if not HAS_PYSTRAY: tray_status = "N/V"
            display_text = f"Hotkey: {hotkey} ({status})"
            if not listener_active and HAS_PYNPUT and self.config.get("hotkey"): display_text += " - Fehler?"
        try:
            self.status_label.config(text=display_text)
        except tk.TclError:
            print("Warning: Could not update status label (likely destroyed).")


    # --- System Tray Methods ---
    def setup_tray_icon(self):
        """Creates the pystray Icon object and its menu."""
        if not HAS_PYSTRAY or not HAS_PILLOW:
            self.tray_icon = None; return
        try:
            icon_image = create_default_icon()
            if not icon_image:
                 print("Error: Failed to load or create icon image for system tray."); self.tray_icon = None; return
            menu_items = []
            if HAS_PYPERCLIP: menu_items.append(pystray.MenuItem('Lesen aus Zwischenablage', self.on_tray_read_clipboard))
            else: menu_items.append(pystray.MenuItem('Lesen aus Zwischenablage', None, enabled=False))
            menu_items.extend([
                pystray.MenuItem('Datei lesen...', self.on_tray_read_file),
                pystray.MenuItem('Einstellungen...', self.on_tray_open_settings),
                pystray.MenuItem(f'Hotkey: {self.config.get("hotkey")}', None, enabled=False),
                pystray.MenuItem('Beenden', self.on_tray_quit)
            ])
            tray_menu = pystray.Menu(*menu_items)
            self.tray_icon = pystray.Icon("SpeedReader", icon=icon_image, title="Speed Reader", menu=tray_menu)
            print("System tray icon configured.")
        except Exception as e:
            print(f"Error setting up system tray icon: {e}"); traceback.print_exc(); self.tray_icon = None

    def run_tray_icon(self):
        """Starts the pystray event loop (blocking). Should be run in a thread."""
        if self.tray_icon:
            print("Starting pystray icon loop...")
            try: self.tray_icon.run()
            except Exception as e: print(f"Error running pystray icon: {e}")
            finally: print("Pystray icon loop finished.")
        else: print("Tray icon not available, cannot run loop.")


    # --- Tray Menu Action Wrappers ---
    def on_tray_read_clipboard(self, icon=None, item=None):
        print("Tray action: Read from clipboard")
        if HAS_PYPERCLIP: self.root.after(0, self.read_from_clipboard)
        else:
             print("Pyperclip not available.")
             if self.tray_icon:
                  try: self.tray_icon.notify("Pyperclip nicht installiert.", "Zwischenablage Fehler")
                  except Exception as e_notify: print(f"Could not send tray notification: {e_notify}")

    def on_tray_read_file(self, icon=None, item=None):
        print("Tray action: Read from file")
        self.root.after(0, self.read_from_file)

    def on_tray_open_settings(self, icon=None, item=None):
        print("Tray action: Open settings")
        self.root.after(0, self.open_settings) # Schedule in main thread

    def on_tray_quit(self, icon=None, item=None):
        print("Tray action: Quit")
        if self.tray_icon: self.tray_icon.stop()
        self.root.after(0, self.quit_app)


    # --- Hotkey Listener Methods ---
    def start_hotkey_listener(self):
        if not HAS_PYNPUT:
            print("Cannot start hotkey listener: pynput library is missing.")
            if hasattr(self, 'status_label') and self.status_label: self.update_status_label("Hotkey Fehler: pynput fehlt!")
            return
        self.stop_hotkey_listener()
        hotkey_str = self.config.get("hotkey")
        if not hotkey_str:
            print("Hotkey is not configured. Listener not started.")
            if hasattr(self, 'status_label') and self.status_label: self.update_status_label("Hotkey nicht konfiguriert")
            return
        print(f"Attempting to register hotkey: {hotkey_str}")
        def on_activate():
            print(f"Hotkey '{hotkey_str}' activated!")
            if HAS_PYPERCLIP: self.root.after(0, self.read_from_clipboard)
            else:
                 print("Hotkey activated, but pyperclip is missing.")
                 self.root.after(0, lambda: messagebox.showwarning("Fehlende Bibliothek", "Hotkey aktiviert, aber 'pyperclip' wird benötigt, um aus der Zwischenablage zu lesen."))
        def listener_thread_func():
            nonlocal hotkey_str
            try:
                self.hotkey_listener = keyboard.GlobalHotKeys({ hotkey_str: on_activate })
                print(f"Hotkey listener starting with: {hotkey_str}")
                self.hotkey_listener.run() # Blocking call
            except Exception as e:
                 error_msg = f"Fehler beim Registrieren/Ausführen des Hotkeys '{hotkey_str}':\n{e}\n\nPrüfen Sie die Einstellungen oder versuchen Sie eine andere Kombination."
                 print(f"Error in listener thread: {error_msg}"); print(traceback.format_exc())
                 self.root.after(0, lambda: messagebox.showerror("Hotkey Fehler", error_msg))
                 if hasattr(self, 'status_label') and self.status_label: self.root.after(0, self.update_status_label, f"Hotkey Fehler: {hotkey_str}")
            finally:
                print("Hotkey listener thread finished.")
                self.hotkey_listener = None
                if hasattr(self, 'status_label') and self.status_label: self.root.after(0, self.update_status_label)
        self.listener_thread = threading.Thread(target=listener_thread_func, daemon=True)
        self.listener_thread.start()
        time.sleep(0.2)
        if hasattr(self, 'status_label') and self.status_label: self.update_status_label()

    def stop_hotkey_listener(self):
        listener = self.hotkey_listener
        if listener:
            print("Stopping hotkey listener...")
            try: listener.stop(); self.hotkey_listener = None
            except Exception as e: print(f"Error stopping hotkey listener: {e}")
        thread = self.listener_thread
        if thread and thread.is_alive():
             print("Waiting for listener thread to join...")
             thread.join(timeout=0.5)
             if thread.is_alive(): print("Warning: Listener thread did not stop gracefully.")
        self.listener_thread = None
        print("Hotkey listener stopped.")
        if hasattr(self, 'status_label') and self.status_label: self.update_status_label()


    # --- Core Application Logic Methods ---

    def open_settings(self):
        """Opens the settings window, ensuring visibility even with hidden root."""
        if self.settings_window_instance and self.settings_window_instance.winfo_exists():
            print("Settings window already open. Bringing to front.")
            self.settings_window_instance.focus_set(); self.settings_window_instance.lift()
            return

        print("Opening settings window...")

        def settings_closed_callback():
            print("Settings window closed.")
            self.settings_window_instance = None
            print("Restarting hotkey listener after settings change...")
            if HAS_PYNPUT: self.start_hotkey_listener()
            else: print("Cannot restart listener - pynput missing.")
            if self.reading_window_instance and self.reading_window_instance.winfo_exists():
                 print("Applying updated settings to reading window...")
                 self.reading_window_instance.update_display_settings()
            if hasattr(self, 'status_label') and self.status_label: self.update_status_label()

        # --- Temporarily show root if hidden, create window, then hide root again ---
        root_was_hidden = False
        try:
            # Check if root is withdrawn
            if self.root.state() == 'withdrawn':
                 root_was_hidden = True
                 print("Temporarily deiconifying root...")
                 self.root.deiconify()
                 self.root.update_idletasks()
                 time.sleep(0.05) # Small delay

            # Create the window instance
            self.settings_window_instance = SettingsWindow(self.root, self.config, settings_closed_callback)
            print("SettingsWindow instance created.")

            # Ensure window is visible and focused
            self.root.update_idletasks()
            if self.settings_window_instance and self.settings_window_instance.winfo_exists():
                 print("Forcing settings window deiconify, lift, focus...")
                 self.settings_window_instance.deiconify()
                 self.settings_window_instance.lift()
                 self.settings_window_instance.focus_force()
            else:
                 print("Settings window instance does not exist after creation attempt.")
                 self.settings_window_instance = None

        except Exception as e:
             print("!!! Error creating or showing SettingsWindow instance !!!")
             print(traceback.format_exc())
             messagebox.showerror("Fenster Fehler", f"Konnte das Einstellungsfenster nicht erstellen/anzeigen:\n{e}")
             self.settings_window_instance = None
        finally:
            # --- Hide root again ONLY if it was originally hidden ---
            if root_was_hidden:
                 print("Re-withdrawing root window...")
                 self.root.withdraw()


    def _initiate_reading(self, text):
        """Helper function to create and start the reading window."""
        parent_window = self.root
        if not text:
            messagebox.showwarning("Kein Text", "Es wurde kein Text zum Lesen bereitgestellt.", parent=parent_window)
            return

        if self.reading_window_instance and self.reading_window_instance.winfo_exists():
            print("Closing existing reading window.")
            self.reading_window_instance.close_window(); self.reading_window_instance = None

        print("Initiating new reading window...")
        root_was_hidden_read = False
        try:
            if self.root.state() == 'withdrawn':
                 root_was_hidden_read = True
                 self.root.deiconify(); self.root.update_idletasks(); time.sleep(0.05)

            self.reading_window_instance = ReadingWindow(parent_window, self.config)
            self.root.update_idletasks()
            if self.reading_window_instance.winfo_exists():
                 self.reading_window_instance.deiconify()
                 self.reading_window_instance.lift()
                 self.reading_window_instance.start_reading(text)
                 print("ReadingWindow instance created and reading started.")
            else:
                 print("Reading window instance does not exist after creation attempt.")
                 self.reading_window_instance = None

        except Exception as e:
             print("!!! Error creating or starting ReadingWindow instance !!!")
             print(traceback.format_exc())
             messagebox.showerror("Fenster Fehler", f"Konnte das Lesefenster nicht erstellen/starten:\n{e}")
             self.reading_window_instance = None
        finally:
             if root_was_hidden_read:
                  self.root.withdraw()


    def read_from_clipboard(self):
        """Reads text from the system clipboard and starts reading."""
        if not HAS_PYPERCLIP:
             messagebox.showerror("Fehler", "'pyperclip' Bibliothek nicht gefunden.")
             return
        print("Reading from clipboard...")
        try:
            text = pyperclip.paste()
            if text: self._initiate_reading(text)
            else: messagebox.showinfo("Zwischenablage leer", "Die Zwischenablage enthält keinen Text.")
        except pyperclip.PyperclipException as e:
             error_msg = f"Fehler beim Zugriff auf die Zwischenablage:\n{e}"
             print(error_msg); messagebox.showerror("Fehler Zwischenablage", error_msg)
        except Exception as e:
            error_msg = f"Unerwarteter Fehler beim Lesen aus der Zwischenablage:\n{e}"
            print(error_msg); traceback.print_exc(); messagebox.showerror("Fehler", error_msg)


    def read_from_file(self):
        """Opens a file dialog, reads text from the selected file, and starts reading."""
        print("Opening file dialog...")
        filepath = None
        root_visible = self.root.state() != 'withdrawn'
        try:
            parent = self.root if root_visible else None
            filepath = filedialog.askopenfilename(
                title="Textdatei öffnen",
                filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")],
                 parent=parent
            )
        except tk.TclError as e:
             print(f"TclError opening file dialog: {e}")
             try:
                  filepath = filedialog.askopenfilename(
                      title="Textdatei öffnen",
                      filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")]
                  )
             except Exception as e_fallback:
                  print(f"Error opening file dialog without parent: {e_fallback}")
                  messagebox.showerror("Dialog Fehler", f"Dateidialog konnte nicht geöffnet werden:\n{e_fallback}")
                  return

        if not filepath: print("File selection cancelled."); return

        print(f"Reading from file: {filepath}")
        try:
            try:
                with open(filepath, 'r', encoding='utf-8') as f: text = f.read()
            except UnicodeDecodeError:
                print("UTF-8 decoding failed, trying system default encoding...")
                with open(filepath, 'r', encoding=sys.getdefaultencoding()) as f: text = f.read()
            self._initiate_reading(text)
        except Exception as e:
            error_msg = f"Datei konnte nicht gelesen werden:\n{filepath}\n\nFehler: {e}"
            print(error_msg); traceback.print_exc(); messagebox.showerror("Fehler beim Lesen der Datei", error_msg)


    def quit_app(self):
        """Cleans up resources and closes the application."""
        print("Quit requested. Cleaning up...")
        self.stop_hotkey_listener()
        if self.tray_icon: print("Stopping tray icon..."); self.tray_icon.stop()
        if self.tray_thread and self.tray_thread.is_alive(): print("Waiting for tray thread to join..."); self.tray_thread.join(timeout=0.5)

        print("Closing open windows...")
        # Use try-except for destroying specific instances
        if self.settings_window_instance and self.settings_window_instance.winfo_exists():
             print("Destroying settings window instance...")
             try: self.settings_window_instance.destroy()
             except tk.TclError: pass # Ignore error if already destroyed
        if self.reading_window_instance and self.reading_window_instance.winfo_exists():
             print("Destroying reading window instance...")
             try: self.reading_window_instance.destroy()
             except tk.TclError: pass

        # Destroy other Toplevels associated with root (safer approach)
        if self.root.winfo_exists():
             # Iterate over a copy of the children list as destroying modifies the list
             children = list(self.root.winfo_children())
             for widget in children:
                  if isinstance(widget, tk.Toplevel):
                       print(f"Destroying other Toplevel: {widget.title()}")
                       try: widget.destroy()
                       except tk.TclError: pass # Ignore error if already destroyed

        print("Destroying Tkinter root...")
        try:
            if self.root.winfo_exists(): self.root.destroy(); print("Tkinter root destroyed.")
        except tk.TclError as e: print(f"TclError destroying root (already destroyed?): {e}")

        print("Application cleanup finished. Exiting.")
        # os._exit(0) # Force exit only if absolutely necessary


# --- Application Entry Point ---
if __name__ == "__main__":
    print("Starting Speed Reader Application...")
    if not HAS_PYNPUT:
         root_check = tk.Tk(); root_check.withdraw(); messagebox.showerror("Kritischer Fehler", "Die Bibliothek 'pynput' fehlt.\n\nInstallieren: pip install pynput"); root_check.destroy(); sys.exit("Fehler: pynput nicht gefunden.")
    root = tk.Tk()
    app = SpeedReaderApp(root)
    print("Starting Tkinter main loop...")
    try: root.mainloop()
    except KeyboardInterrupt: print("\nKeyboardInterrupt received. Shutting down..."); app.quit_app()
    except Exception as e:
         print("\nUnhandled exception in Tkinter main loop:"); print(traceback.format_exc())
         try: app.quit_app()
         except Exception as quit_e: print(f"Error during shutdown after main loop exception: {quit_e}")
    print("Application has exited.")
