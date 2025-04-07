# -*- coding: utf-8 -*-

import sys
import os

# --- Konstante für Registry ---
APP_NAME = "SpeedReaderApp" # Eindeutiger Name für den Registry-Eintrag

def resource_path(relative_path):
    """ Ermittelt den korrekten Pfad zu einer Ressource (z.B. Icon),
        egal ob als Skript oder als gepackte PyInstaller-Anwendung ausgeführt.
    """
    try:
        # PyInstaller erstellt einen temporären Ordner und speichert den Pfad in _MEIPASS
        base_path = sys._MEIPASS
        # print(f"Resource: Running bundled, MEIPASS={base_path}") # Debug
    except AttributeError:
        # Nicht gepackt, wir sind im normalen Skriptverzeichnis
        base_path = os.path.abspath(".")
        # print(f"Resource: Running as script, base_path={base_path}") # Debug

    return os.path.join(base_path, relative_path)

# --- Windows Registry Funktionen (nur für Windows) ---
if sys.platform == 'win32':
    import winreg
    import sys # Import sys again inside platform check for sys.executable

    # Pfad zum Autostart-Schlüssel im HKEY_CURRENT_USER Hive
    RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def add_to_startup(executable_path):
        """ Fügt die Anwendung zum Windows-Autostart hinzu (Aktueller Benutzer). """
        if not executable_path:
             print("Error: Executable path is empty, cannot add to startup.")
             return False
        # Pfad in Anführungszeichen setzen, falls er Leerzeichen enthält
        quoted_path = f'"{executable_path}"'
        try:
            # Öffne den Run-Key zum Schreiben
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, quoted_path)
            print(f"Successfully added '{APP_NAME}' to startup: {quoted_path}")
            return True
        except OSError as e:
            print(f"Error adding to startup: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error adding to startup: {e}")
            return False

    def remove_from_startup():
        """ Entfernt die Anwendung aus dem Windows-Autostart (Aktueller Benutzer). """
        try:
            # Öffne den Run-Key zum Schreiben/Löschen
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, APP_NAME)
            print(f"Successfully removed '{APP_NAME}' from startup.")
            return True
        except FileNotFoundError:
            # Eintrag existiert nicht, das ist okay
            print(f"'{APP_NAME}' was not found in startup (OK).")
            return True
        except OSError as e:
            print(f"Error removing from startup: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error removing from startup: {e}")
            return False

    def is_in_startup():
        """ Prüft, ob die Anwendung im Windows-Autostart ist (Aktueller Benutzer). """
        try:
            # Öffne den Run-Key zum Lesen
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_NAME)
            return True # Wert existiert
        except FileNotFoundError:
            return False # Wert existiert nicht
        except OSError as e:
            print(f"Error checking startup status: {e}")
            return False # Fehler beim Lesen
        except Exception as e:
            print(f"Unexpected error checking startup: {e}")
            return False

else:
    # Dummy-Funktionen für andere Betriebssysteme
    def add_to_startup(executable_path):
        print("Info: Autostart-Funktion nur unter Windows verfügbar.")
        return False
    def remove_from_startup():
        print("Info: Autostart-Funktion nur unter Windows verfügbar.")
        return False
    def is_in_startup():
        return False

