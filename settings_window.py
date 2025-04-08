# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, font, colorchooser, messagebox
import sys
import traceback

try:
    from pynput import keyboard
    HAS_PYNPUT_SETTINGS = True
except ImportError:
    HAS_PYNPUT_SETTINGS = False

# Import registry functions if on Windows
if sys.platform == 'win32':
     try:
          from system_utils import add_to_startup, remove_from_startup, is_in_startup
          HAS_STARTUP_FUNC = True
     except ImportError:
          print("Warning: Could not import startup functions from system_utils.")
          HAS_STARTUP_FUNC = False
else:
     # Provide dummy functions otherwise
     def add_to_startup(p): return False
     def remove_from_startup(): return False
     def is_in_startup(): return False
     HAS_STARTUP_FUNC = False


class SettingsWindow(tk.Toplevel):
    """
    Settings window with scrolling, integer inputs, dark mode, chunk size,
    context toggle, startup option, and adaptive sizing.
    """
    def __init__(self, parent, config_manager, on_close_callback):
        super().__init__(parent)
        self.config = config_manager
        self.on_close_callback = on_close_callback
        self.title("Einstellungen")

        # --- Adaptive Geometry --- KORRIGIERT ---
        try:
            # Get screen dimensions
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # Define desired proportions (adjust as needed)
            width_proportion = 0.55 # 55% of screen width
            height_proportion = 0.80 # 80% of screen height

            # Define minimum size
            min_w = 550
            min_h = 650

            # Calculate window dimensions
            win_width = max(min_w, int(screen_width * width_proportion))
            win_height = max(min_h, int(screen_height * height_proportion))

            # Optional: Define maximum size relative to screen (e.g., max 90% height)
            max_h = int(screen_height * 0.95)
            win_height = min(win_height, max_h)
            # Optional: Max width
            # max_w = 1000
            # win_width = min(win_width, max_w)


            # Calculate position for centering
            pos_x = (screen_width - win_width) // 2
            pos_y = (screen_height - win_height) // 2

            # Ensure position is not negative
            pos_x = max(0, pos_x)
            pos_y = max(0, pos_y)

            # Set geometry
            self.geometry(f"{win_width}x{win_height}+{pos_x}+{pos_y}")
            # Set minimum size after setting initial geometry
            self.minsize(min_w, min_h)
            print(f"Calculated settings window geometry: {win_width}x{win_height}+{pos_x}+{pos_y}")

        except tk.TclError as e:
             print(f"Warning: Could not get screen dimensions, using default size. Error: {e}")
             self.geometry("550x750") # Fallback size
             self.minsize(550, 650)
        # --- Ende Adaptive Geometry ---


        # self.transient(parent) # Keep REMOVED

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.settings_vars = {} # Holds original vars from config
        self.ui_vars = {}       # Holds IntVars used for UI Spinboxes (ms, %)

        self.initial_run_on_startup = self.config.get("run_on_startup")

        # --- Styling ---
        style = ttk.Style(self)
        try: style.theme_use('clam')
        except tk.TclError: print("Hinweis: 'clam' ttk-Theme nicht verfügbar."); style.theme_use('default')
        style.configure("TLabel", padding=(5, 5)); style.configure("TEntry", padding=(5, 5))
        style.configure("TButton", padding=(5, 5)); style.configure("TCheckbutton", padding=(0, 5))
        style.configure("TRadiobutton", padding=(0, 5))
        style.configure("TScale", padding=(5, 5)); style.configure("TSpinbox", padding=(5, 5))
        style.configure("TLabelframe.Label", padding=(5, 2)); style.configure("TLabelframe", padding=10)
        style.configure("Vertical.TScrollbar", padding=0)

        # --- Create Scrollable Area ---
        scrollable_outer_frame = ttk.Frame(self); scrollable_outer_frame.pack(expand=True, fill="both")
        self.canvas = tk.Canvas(scrollable_outer_frame, borderwidth=0, highlightthickness=0); self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(scrollable_outer_frame, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar"); scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.main_frame = ttk.Frame(self.canvas, padding="15"); self.main_frame_id = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        self.main_frame.bind("<Configure>", self._on_frame_configure); self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind_mousewheel(self.canvas); self.bind_mousewheel(self.main_frame)

        # --- Populate the inner frame ---
        self._populate_settings_frame()

        # --- Final steps ---
        self._update_font_preview(); self._update_wpm_label(); self._update_orp_label()
        self.wait_visibility(); self.focus_set(); self.grab_set()

    def bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", self._on_mousewheel, add='+'); widget.bind_all("<Button-4>", self._on_mousewheel, add='+'); widget.bind_all("<Button-5>", self._on_mousewheel, add='+')

    def _on_mousewheel(self, event):
        delta = 0
        if hasattr(event, 'num') and event.num == 4: delta = -1
        elif hasattr(event, 'num') and event.num == 5: delta = 1
        elif hasattr(event, 'delta'):
             if event.delta > 0: delta = -1
             elif event.delta < 0: delta = 1
        if delta != 0: self.canvas.yview_scroll(delta, "units")

    def _on_frame_configure(self, event=None): self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def _on_canvas_configure(self, event=None):
        if hasattr(self, 'main_frame_id') and self.main_frame.winfo_exists(): self.canvas.itemconfig(self.main_frame_id, width=self.canvas.winfo_width())

    def _populate_settings_frame(self):
        # --- WPM & Timing Section ---
        wpm_frame = ttk.LabelFrame(self.main_frame, text="Geschwindigkeit & Timing", padding="15"); wpm_frame.pack(fill="x", pady=(0, 15))
        self.settings_vars["wpm"] = tk.IntVar(value=self.config.get("wpm")); self.settings_vars["wpm"].trace_add("write", self._update_wpm_label)
        ttk.Label(wpm_frame, text="WPM:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        wpm_scale = ttk.Scale(wpm_frame, from_=50, to=1500, orient="horizontal", variable=self.settings_vars["wpm"]); wpm_scale.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        wpm_spinbox = ttk.Spinbox(wpm_frame, from_=50, to=1500, increment=10, textvariable=self.settings_vars["wpm"], width=6); wpm_spinbox.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.wpm_label = ttk.Label(wpm_frame, text="", width=8, anchor="e"); self.wpm_label.grid(row=0, column=3, sticky="e", padx=(5, 0), pady=5)
        self.settings_vars["initial_delay_ms"] = tk.IntVar(value=self.config.get("initial_delay_ms"))
        ttk.Label(wpm_frame, text="Startverzögerung:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=5)
        delay_spinbox = ttk.Spinbox(wpm_frame, from_=0, to=10000, increment=100, textvariable=self.settings_vars["initial_delay_ms"], width=6); delay_spinbox.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        ttk.Label(wpm_frame, text="ms").grid(row=1, column=3, sticky="w", padx=(5, 0), pady=5)
        self.settings_vars["word_length_threshold"] = tk.IntVar(value=self.config.get("word_length_threshold"))
        self.settings_vars["extra_ms_per_char"] = tk.IntVar(value=self.config.get("extra_ms_per_char"))
        ttk.Label(wpm_frame, text="Wortlängen-Schwelle:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=5)
        threshold_spinbox = ttk.Spinbox(wpm_frame, from_=1, to=20, increment=1, textvariable=self.settings_vars["word_length_threshold"], width=4); threshold_spinbox.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(wpm_frame, text="Zeichen").grid(row=2, column=2, columnspan=2, sticky="w", padx=5, pady=5)
        ttk.Label(wpm_frame, text="Extra Zeit pro Zeichen:").grid(row=3, column=0, sticky="w", padx=(0, 5), pady=5)
        extra_ms_spinbox = ttk.Spinbox(wpm_frame, from_=0, to=50, increment=1, textvariable=self.settings_vars["extra_ms_per_char"], width=4); extra_ms_spinbox.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(wpm_frame, text="ms (über Schwelle)").grid(row=3, column=2, columnspan=2, sticky="w", padx=5, pady=5)
        wpm_frame.columnconfigure(1, weight=1)

        # --- Chunk Size Section ---
        chunk_frame = ttk.LabelFrame(self.main_frame, text="Wortgruppengröße (Chunking)", padding="15"); chunk_frame.pack(fill="x", pady=(0, 15))
        self.settings_vars["chunk_size"] = tk.IntVar(value=self.config.get("chunk_size"))
        ttk.Label(chunk_frame, text="Wörter pro Anzeige:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        chunk_spinbox = ttk.Spinbox(chunk_frame, from_=1, to=10, increment=1, textvariable=self.settings_vars["chunk_size"], width=4); chunk_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(chunk_frame, text="(ORP nur bei 1 aktiv)").grid(row=0, column=2, sticky="w", padx=5, pady=5)

        # --- Pauses Section ---
        pause_frame = ttk.LabelFrame(self.main_frame, text="Pausen (Millisekunden)", padding="15"); pause_frame.pack(fill="x", pady=(0, 15))
        self.settings_vars["pause_punctuation"] = tk.DoubleVar(value=self.config.get("pause_punctuation")); self.settings_vars["pause_comma"] = tk.DoubleVar(value=self.config.get("pause_comma")); self.settings_vars["pause_paragraph"] = tk.DoubleVar(value=self.config.get("pause_paragraph"))
        self.ui_vars["pause_punctuation_ms"] = tk.IntVar(value=int(self.config.get("pause_punctuation") * 1000)); self.ui_vars["pause_comma_ms"] = tk.IntVar(value=int(self.config.get("pause_comma") * 1000)); self.ui_vars["pause_paragraph_ms"] = tk.IntVar(value=int(self.config.get("pause_paragraph") * 1000))
        pause_spinbox_width = 6; pause_increment = 100; pause_max = 5000
        ttk.Label(pause_frame, text="Bei Satzende (.,!,?):").grid(row=0, column=0, sticky="w", pady=5)
        pause_punct_spinbox = ttk.Spinbox(pause_frame, from_=0, to=pause_max, increment=pause_increment, textvariable=self.ui_vars["pause_punctuation_ms"], width=pause_spinbox_width); pause_punct_spinbox.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        ttk.Label(pause_frame, text="ms").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Label(pause_frame, text="Bei Komma (,):").grid(row=1, column=0, sticky="w", pady=5)
        pause_comma_spinbox = ttk.Spinbox(pause_frame, from_=0, to=pause_max, increment=pause_increment, textvariable=self.ui_vars["pause_comma_ms"], width=pause_spinbox_width); pause_comma_spinbox.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        ttk.Label(pause_frame, text="ms").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        ttk.Label(pause_frame, text="Bei Absatz:").grid(row=2, column=0, sticky="w", pady=5)
        pause_para_spinbox = ttk.Spinbox(pause_frame, from_=0, to=pause_max, increment=pause_increment, textvariable=self.ui_vars["pause_paragraph_ms"], width=pause_spinbox_width); pause_para_spinbox.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        ttk.Label(pause_frame, text="ms").grid(row=2, column=2, sticky="w", padx=5, pady=5)

        # --- Appearance Section ---
        appearance_frame = ttk.LabelFrame(self.main_frame, text="Erscheinungsbild", padding="15"); appearance_frame.pack(fill="x", pady=(0, 15))
        self.settings_vars["dark_mode"] = tk.BooleanVar(value=self.config.get("dark_mode"))
        dark_mode_check = ttk.Checkbutton(appearance_frame, text="Dark Mode aktivieren (im Lesefenster)", variable=self.settings_vars["dark_mode"]); dark_mode_check.grid(row=0, column=0, columnspan=3, sticky="w", pady=(2, 5))
        self.settings_vars["show_context"] = tk.BooleanVar(value=self.config.get("show_context"))
        show_context_check = ttk.Checkbutton(appearance_frame, text="Kontext anzeigen (vorheriges/nächstes Wort)", variable=self.settings_vars["show_context"]); show_context_check.grid(row=1, column=0, columnspan=3, sticky="w", pady=2)
        self.settings_vars["context_layout"] = tk.StringVar(value=self.config.get("context_layout"))
        ttk.Label(appearance_frame, text="Kontext-Layout:").grid(row=2, column=0, sticky="w", pady=(5, 2), padx=(15,0))
        context_vert_radio = ttk.Radiobutton(appearance_frame, text="Vertikal", variable=self.settings_vars["context_layout"], value="vertical"); context_vert_radio.grid(row=2, column=1, sticky="w", pady=(5,2), padx=5)
        context_horz_radio = ttk.Radiobutton(appearance_frame, text="Horizontal", variable=self.settings_vars["context_layout"], value="horizontal"); context_horz_radio.grid(row=2, column=2, sticky="w", pady=(5,2), padx=5)

        # --- Font & Colors Section ---
        font_frame = ttk.LabelFrame(self.main_frame, text="Farben & Schriftart (Hell-Modus)", padding="15"); font_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(font_frame, text="Hinweis: Diese Farben gelten für den Hell-Modus.").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0,10))
        self.settings_vars["font_family"] = tk.StringVar(value=self.config.get("font_family")); self.settings_vars["font_size"] = tk.IntVar(value=self.config.get("font_size")); self.settings_vars["font_color"] = tk.StringVar(value=self.config.get("font_color")); self.settings_vars["highlight_color"] = tk.StringVar(value=self.config.get("highlight_color")); self.settings_vars["background_color"] = tk.StringVar(value=self.config.get("background_color"))
        ttk.Label(font_frame, text="Schriftart:").grid(row=1, column=0, sticky="w", pady=5)
        available_fonts = sorted(font.families()); combo_state = "readonly"; font_combo = ttk.Combobox(font_frame, textvariable=self.settings_vars["font_family"], values=available_fonts, width=25, state=combo_state); font_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5); font_combo.bind("<<ComboboxSelected>>", self._update_font_preview)
        if combo_state != "readonly": self.settings_vars["font_family"].trace_add("write", self._update_font_preview)
        ttk.Label(font_frame, text="Größe:").grid(row=2, column=0, sticky="w", pady=5)
        font_size_spinbox = ttk.Spinbox(font_frame, from_=8, to=120, textvariable=self.settings_vars["font_size"], width=5, command=self._update_font_preview); font_size_spinbox.grid(row=2, column=1, sticky="w", padx=5, pady=5); self.settings_vars["font_size"].trace_add("write", self._update_font_preview)
        ttk.Label(font_frame, text="Textfarbe:").grid(row=3, column=0, sticky="w", pady=5)
        self.font_color_button = ttk.Button(font_frame, text="Wählen...", command=lambda: self._choose_color("font_color", self._update_font_preview)); self.font_color_button.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.font_color_preview = tk.Label(font_frame, text=" ", relief="sunken", borderwidth=1, bg=self.config.get("font_color"), width=3); self.font_color_preview.grid(row=3, column=2, sticky="w", pady=5, padx=5)
        ttk.Label(font_frame, text="Hintergrund:").grid(row=4, column=0, sticky="w", pady=5)
        self.bg_color_button = ttk.Button(font_frame, text="Wählen...", command=lambda: self._choose_color("background_color", self._update_font_preview)); self.bg_color_button.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        self.bg_color_preview = tk.Label(font_frame, text=" ", relief="sunken", borderwidth=1, bg=self.config.get("background_color"), width=3); self.bg_color_preview.grid(row=4, column=2, sticky="w", pady=5, padx=5)
        ttk.Label(font_frame, text="ORP Farbe:").grid(row=5, column=0, sticky="w", pady=5)
        self.highlight_color_button = ttk.Button(font_frame, text="Wählen...", command=lambda: self._choose_color("highlight_color")); self.highlight_color_button.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        self.highlight_color_preview = tk.Label(font_frame, text=" ", relief="sunken", borderwidth=1, bg=self.config.get("highlight_color"), width=3); self.highlight_color_preview.grid(row=5, column=2, sticky="w", pady=5, padx=5)
        ttk.Label(font_frame, text="Vorschau:").grid(row=6, column=0, sticky="nw", pady=(10, 5))
        self.font_preview_label = tk.Label(font_frame, text="Wort 123", relief="groove", borderwidth=1, padx=10, pady=5); self.font_preview_label.grid(row=6, column=1, columnspan=2, sticky="ew", pady=(10, 5), padx=5)
        font_frame.columnconfigure(1, weight=1)

        # --- ORP Section ---
        orp_frame = ttk.LabelFrame(self.main_frame, text="Optimal Recognition Point (ORP)", padding="15"); orp_frame.pack(fill="x", pady=(0, 15))
        self.settings_vars["orp_position"] = tk.DoubleVar(value=self.config.get("orp_position")); self.ui_vars["orp_position_percent"] = tk.IntVar(value=int(self.config.get("orp_position") * 100)); self.ui_vars["orp_position_percent"].trace_add("write", self._update_orp_label)
        self.settings_vars["enable_orp"] = tk.BooleanVar(value=self.config.get("enable_orp"))
        orp_check = ttk.Checkbutton(orp_frame, text="ORP hervorheben (nur bei Wortgröße 1)", variable=self.settings_vars["enable_orp"]); orp_check.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        ttk.Label(orp_frame, text="Position (%):").grid(row=1, column=0, sticky="w", pady=5)
        orp_spinbox = ttk.Spinbox(orp_frame, from_=0, to=100, increment=1, textvariable=self.ui_vars["orp_position_percent"], width=5); orp_spinbox.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.orp_label = ttk.Label(orp_frame, text="", width=5, anchor="e"); self.orp_label.grid(row=1, column=2, sticky="e", padx=(5, 0), pady=5)

        # --- Window Options Section ---
        window_frame = ttk.LabelFrame(self.main_frame, text="Fenster Optionen", padding="15"); window_frame.pack(fill="x", pady=(0, 15))
        self.settings_vars["reader_borderless"] = tk.BooleanVar(value=self.config.get("reader_borderless")); self.settings_vars["reader_always_on_top"] = tk.BooleanVar(value=self.config.get("reader_always_on_top"))
        ttk.Checkbutton(window_frame, text="Rahmenloses Lesefenster", variable=self.settings_vars["reader_borderless"]).pack(anchor="w", pady=2)
        ttk.Checkbutton(window_frame, text="Lesefenster immer im Vordergrund", variable=self.settings_vars["reader_always_on_top"]).pack(anchor="w", pady=2)
        self.settings_vars["run_on_startup"] = tk.BooleanVar(value=self.config.get("run_on_startup"))
        if sys.platform == 'win32' and HAS_STARTUP_FUNC:
             startup_check = ttk.Checkbutton(window_frame, text="Beim Windows-Start ausführen", variable=self.settings_vars["run_on_startup"])
             startup_check.pack(anchor="w", pady=(10, 2))
        else: ttk.Label(window_frame, text="Autostart nur unter Windows verfügbar.", foreground="grey").pack(anchor="w", pady=(10, 2))

        # --- Hotkey Section ---
        hotkey_frame = ttk.LabelFrame(self.main_frame, text="Tastenkürzel (Start aus Zwischenablage)", padding="15"); hotkey_frame.pack(fill="x", pady=(0, 15))
        self.settings_vars["hotkey"] = tk.StringVar(value=self.config.get("hotkey"))
        ttk.Label(hotkey_frame, text="Aktuell:").grid(row=0, column=0, sticky="w", pady=5)
        self.hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.settings_vars["hotkey"], state="readonly", width=25); self.hotkey_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        record_btn_state = "normal" if HAS_PYNPUT_SETTINGS else "disabled"; record_btn_text = "Neu aufnehmen..." if HAS_PYNPUT_SETTINGS else "Neu (pynput fehlt)"
        self.record_button = ttk.Button(hotkey_frame, text=record_btn_text, command=self._record_hotkey, state=record_btn_state); self.record_button.grid(row=0, column=2, sticky="e", padx=(5, 0), pady=5)
        hotkey_frame.columnconfigure(1, weight=1)
        self.recording_active = False; self.pressed_keys = set()

        # Bind mousewheel to all frames
        for frame in [wpm_frame, chunk_frame, pause_frame, appearance_frame, font_frame, orp_frame, window_frame, hotkey_frame]:
             self.bind_mousewheel(frame)

        # --- Bottom Buttons ---
        button_frame = ttk.Frame(self, padding="10 10 10 10"); button_frame.pack(fill="x", side="bottom")
        cancel_button = ttk.Button(button_frame, text="Abbrechen", command=self.on_close); cancel_button.pack(side="right", padx=(0, 5))
        save_button = ttk.Button(button_frame, text="Speichern & Schließen", command=self.save_and_close); save_button.pack(side="right", padx=(0, 5))


    # --- Callback Methods ---
    def _update_wpm_label(self, *args):
        try:
            current_wpm = self.settings_vars["wpm"].get()
            if hasattr(self, 'wpm_label') and self.wpm_label.winfo_exists(): self.wpm_label.config(text=f"{int(current_wpm)} WPM")
        except (ValueError, tk.TclError, AttributeError): pass
    def _update_orp_label(self, *args):
        try:
            current_orp_percent = self.ui_vars["orp_position_percent"].get()
            if hasattr(self, 'orp_label') and self.orp_label.winfo_exists(): self.orp_label.config(text=f"{current_orp_percent}%")
        except (ValueError, tk.TclError, AttributeError): pass
    def _choose_color(self, setting_key, update_callback=None):
        current_color = self.settings_vars[setting_key].get()
        try: color_code = colorchooser.askcolor(title=f"Farbe wählen für '{setting_key}'", initialcolor=current_color, parent=self)
        except tk.TclError as e: messagebox.showerror("Farbwahlfehler", f"Fehler: {e}", parent=self); return
        if color_code and color_code[1]:
            hex_color = color_code[1]; self.settings_vars[setting_key].set(hex_color)
            try:
                preview_widget = None
                if setting_key == "font_color": preview_widget = self.font_color_preview
                elif setting_key == "background_color": preview_widget = self.bg_color_preview
                elif setting_key == "highlight_color": preview_widget = self.highlight_color_preview
                if preview_widget and preview_widget.winfo_exists(): preview_widget.config(bg=hex_color)
            except tk.TclError: pass
            if update_callback: update_callback()

    # Korrekte _update_font_preview method
    def _update_font_preview(self, *args):
        """Updates the font preview label based on current settings."""
        try: # Äußerer try-Block für allgemeine Fehler
            # Widget-Existenz prüfen
            if not hasattr(self, 'font_preview_label') or not self.font_preview_label.winfo_exists(): return

            # Werte holen
            family = self.settings_vars["font_family"].get()
            size_str = self.settings_vars["font_size"].get()
            color = self.settings_vars["font_color"].get()
            bg_color = self.settings_vars["background_color"].get()

            # Größe validieren
            try: # Innerer try-Block für Größen-Validierung
                size = int(size_str)
                if size < 1: size = 1
            # Direkt folgender except-Block für Größen-Validierung
            except (ValueError, TypeError):
                self.font_preview_label.config(text="Ungültige Größe", font=font.nametofont("TkDefaultFont"), fg="red", bg="white")
                return # Funktion verlassen bei ungültiger Größe

            # Schriftart erstellen
            try: # Innerer try-Block für Schriftart-Erstellung
                preview_font_size = max(8, int(size * 0.6))
                preview_font = font.Font(family=family, size=preview_font_size)
            # Direkt folgender except-Block für Schriftart-Erstellung
            except tk.TclError:
                 self.font_preview_label.config(text="Ungültige Schriftart", font=font.nametofont("TkDefaultFont"), fg="red", bg="white")
                 return # Funktion verlassen bei ungültiger Schriftart

            # Label konfigurieren (nur wenn alles oben erfolgreich war)
            self.font_preview_label.config(
                text="Wort 123", font=preview_font, fg=color, bg=bg_color
            )

        # Except-Blöcke für den äußeren try-Block
        except tk.TclError:
             # Andere TclErrors abfangen (z.B. beim Schließen)
             pass
        except Exception as e:
            # Andere unerwartete Fehler abfangen
            print(f"Unexpected error during font preview update: {e}")
            print(traceback.format_exc())
            try:
                if hasattr(self, 'font_preview_label') and self.font_preview_label.winfo_exists():
                    self.font_preview_label.config(text="Vorschau Fehler", font=font.nametofont("TkDefaultFont"), fg="red", bg="white")
            except: pass # Fehler beim Anzeigen des Fehlers ignorieren

    # --- Hotkey Recording Methods ---
    def _record_hotkey(self):
        if not HAS_PYNPUT_SETTINGS: messagebox.showerror("Fehler", "'pynput' fehlt.", parent=self); return
        if self.recording_active: return
        self.recording_active = True; self.pressed_keys = set()
        self.hotkey_entry.config(state="normal"); self.hotkey_entry.delete(0, tk.END); self.hotkey_entry.insert(0, "Drücke Tastenkombination..."); self.hotkey_entry.config(state="readonly")
        self.record_button.config(text="Aufnahme läuft...", state="disabled")
        self.focus_set(); self.bind("<KeyPress>", self._on_key_press, add='+'); self.bind("<KeyRelease>", self._on_key_release, add='+')
    def _on_key_press(self, event):
        if not self.recording_active: return 'break'
        key_name = self._get_pynput_key_name(event)
        if key_name: self.pressed_keys.add(key_name); self._update_hotkey_entry_display()
        return 'break'
    def _on_key_release(self, event):
        if not self.recording_active: return 'break'
        key_name = self._get_pynput_key_name(event)
        is_modifier = key_name in {'ctrl', 'alt', 'shift', 'cmd'}
        if key_name and not is_modifier:
             mods = {'ctrl', 'alt', 'shift', 'cmd'}
             held_mods_on_release = self.pressed_keys.intersection(mods)
             if held_mods_on_release: self._stop_recording()
             else: messagebox.showwarning("Ungültige Eingabe", "Kombination muss Modifikatortaste enthalten.", parent=self); self._stop_recording(revert=True)
        if key_name in self.pressed_keys:
            self.pressed_keys.remove(key_name)
            if not any(k not in {'ctrl', 'alt', 'shift', 'cmd'} for k in self.pressed_keys): self._update_hotkey_entry_display()
        return 'break'
    def _get_pynput_key_name(self, event):
        key = event.keysym.lower()
        if key in ["control_l", "control_r"]: return "ctrl"
        if key in ["alt_l", "alt_r", "alt_gr"]: return "alt"
        if key in ["shift_l", "shift_r"]: return "shift"
        if key in ["super_l", "super_r", "win_l", "win_r"]: return "cmd"
        if key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24: return key
        special_keys_map = {'space': 'space', 'return': 'enter', 'kp_enter': 'enter', 'escape': 'esc','tab': 'tab', 'backspace': 'backspace', 'delete': 'delete', 'home': 'home','end': 'end', 'prior': 'page_up', 'next': 'page_down', 'up': 'up','down': 'down', 'left': 'left', 'right': 'right', 'caps_lock': 'caps_lock','num_lock': 'num_lock', 'scroll_lock': 'scroll_lock', 'insert': 'insert','print': 'print_screen', 'pause': 'pause', 'kp_0': '0', 'kp_1': '1','kp_2': '2', 'kp_3': '3', 'kp_4': '4', 'kp_5': '5', 'kp_6': '6','kp_7': '7', 'kp_8': '8', 'kp_9': '9', 'kp_decimal': '.','kp_add': '+', 'kp_subtract': '-', 'kp_multiply': '*', 'kp_divide': '/','kp_separator': ',', 'kp_equal': '=',}
        if key in special_keys_map: return special_keys_map[key]
        if len(key) == 1 and (key.isalnum() or key in '+-*/.:,;_=<>?@#$%^&!'): return key
        return None
    def _update_hotkey_entry_display(self):
        if not self.recording_active: return
        mods_ordered = ['cmd', 'ctrl', 'alt', 'shift']; pressed_mod_names = {k for k in self.pressed_keys if k in mods_ordered}; other_keys = sorted([k for k in self.pressed_keys if k not in mods_ordered]); sorted_mods = [m for m in mods_ordered if m in pressed_mod_names]
        hotkey_parts = [f"<{m}>" for m in sorted_mods] + other_keys; hotkey_str = "+".join(hotkey_parts)
        if hasattr(self, 'hotkey_entry') and self.hotkey_entry.winfo_exists(): self.hotkey_entry.config(state="normal"); self.hotkey_entry.delete(0, tk.END); self.hotkey_entry.insert(0, hotkey_str if hotkey_str else "..."); self.hotkey_entry.config(state="readonly")
    def _stop_recording(self, revert=False):
        if not self.recording_active: return
        try: self.unbind("<KeyPress>"); self.unbind("<KeyRelease>")
        except tk.TclError: pass
        self.recording_active = False
        if revert: final_hotkey_str = self.config.get("hotkey"); self.pressed_keys = set()
        else:
            mods_ordered = ['cmd', 'ctrl', 'alt', 'shift']; pressed_mod_names = {k for k in self.pressed_keys if k in mods_ordered}; other_keys = sorted([k for k in self.pressed_keys if k not in mods_ordered]); sorted_mods = [m for m in mods_ordered if m in pressed_mod_names]
            if not other_keys or not pressed_mod_names: final_hotkey_str = self.config.get("hotkey");
            if not revert: messagebox.showwarning("Ungültige Eingabe", "Kombination muss normale Taste UND Modifikator enthalten.", parent=self)
            else: final_hotkey_str = "+".join([f"<{m}>" for m in sorted_mods] + other_keys)
        self.settings_vars["hotkey"].set(final_hotkey_str)
        if hasattr(self, 'hotkey_entry') and self.hotkey_entry.winfo_exists(): self.hotkey_entry.config(state="normal"); self.hotkey_entry.delete(0, tk.END); self.hotkey_entry.insert(0, final_hotkey_str); self.hotkey_entry.config(state="readonly")
        record_btn_state = "normal" if HAS_PYNPUT_SETTINGS else "disabled";
        if hasattr(self, 'record_button') and self.record_button.winfo_exists(): self.record_button.config(text="Neu aufnehmen...", state=record_btn_state)
        self.pressed_keys = set()

    # --- Save and Close Methods ---
    def save_and_close(self):
        """Saves all settings (converting UI vars back) and handles startup registry."""
        try:
            # Convert UI IntVars back to original DoubleVars/IntVars/StringVars before saving
            orp_percent = self.ui_vars["orp_position_percent"].get()
            self.settings_vars["orp_position"].set(max(0.0, min(1.0, orp_percent / 100.0)))
            pause_punct_ms = self.ui_vars["pause_punctuation_ms"].get()
            self.settings_vars["pause_punctuation"].set(max(0.0, pause_punct_ms / 1000.0))
            pause_comma_ms = self.ui_vars["pause_comma_ms"].get()
            self.settings_vars["pause_comma"].set(max(0.0, pause_comma_ms / 1000.0))
            pause_para_ms = self.ui_vars["pause_paragraph_ms"].get()
            self.settings_vars["pause_paragraph"].set(max(0.0, pause_para_ms / 1000.0))

            # --- Validate and save all original variables ---
            for key, var in self.settings_vars.items():
                value = None
                try: value = var.get()
                except (tk.TclError, ValueError): messagebox.showerror("Ungültiger Wert", f"Konnte Wert für '{key}' nicht lesen.", parent=self); return
                # Validation based on key
                if key == "wpm":
                     if not isinstance(value, int) or not (50 <= value <= 1500): messagebox.showerror("Ungültiger Wert", f"WPM: 50-1500.", parent=self); return
                elif key == "chunk_size":
                     if not isinstance(value, int) or not (1 <= value <= 10): messagebox.showerror("Ungültiger Wert", f"Wortgruppe: 1-10.", parent=self); return
                elif key == "font_size":
                     if not isinstance(value, int) or not (8 <= value <= 120): messagebox.showerror("Ungültiger Wert", f"Schriftgröße: 8-120.", parent=self); return
                elif key == "orp_position":
                     if not isinstance(value, float) or not (0.0 <= value <= 1.0): messagebox.showerror("Ungültiger Wert", f"ORP Position: 0.0-1.0.", parent=self); return
                elif key in ["pause_punctuation", "pause_comma", "pause_paragraph"]:
                     if not isinstance(value, float) or value < 0: messagebox.showerror("Ungültiger Wert", f"Pausenwert für '{key}': >= 0.", parent=self); return
                elif key == "initial_delay_ms": # Validate delay
                     if not isinstance(value, int) or value < 0: messagebox.showerror("Ungültiger Wert", f"Startverzögerung: >= 0 ms.", parent=self); return
                # --- NEU: Validate word length delay settings ---
                elif key == "word_length_threshold":
                     if not isinstance(value, int) or value < 1: messagebox.showerror("Ungültiger Wert", f"Wortlängen-Schwelle: >= 1.", parent=self); return
                elif key == "extra_ms_per_char":
                     if not isinstance(value, int) or value < 0: messagebox.showerror("Ungültiger Wert", f"Extra Zeit pro Zeichen: >= 0 ms.", parent=self); return
                # --- Ende NEU ---
                elif key in ["dark_mode", "show_context", "enable_orp", "reader_borderless", "reader_always_on_top", "run_on_startup"]:
                     if not isinstance(value, bool): messagebox.showerror("Ungültiger Wert", f"'{key}' muss An/Aus sein.", parent=self); return
                elif key == "context_layout":
                     if value not in ["vertical", "horizontal"]: messagebox.showerror("Ungültiger Wert", f"'{key}' muss 'vertical' oder 'horizontal' sein.", parent=self); return

                # Set validated value in config manager
                self.config.set(key, value)

            # --- Handle Startup Registry Change ---
            # Compare new state with initial state loaded when window opened
            new_startup_state = False
            if sys.platform == 'win32' and HAS_STARTUP_FUNC:
                new_startup_state = self.settings_vars["run_on_startup"].get()
                if new_startup_state != self.initial_run_on_startup:
                    print(f"Run on startup changed from {self.initial_run_on_startup} to {new_startup_state}")
                    exe_path = sys.executable
                    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                         print(f"Running as bundled app: {exe_path}")
                         if new_startup_state:
                              if not add_to_startup(exe_path): messagebox.showerror("Fehler Autostart", "Konnte nicht zum Autostart hinzufügen.", parent=self)
                         else:
                              if not remove_from_startup(): messagebox.showerror("Fehler Autostart", "Konnte nicht aus Autostart entfernen.", parent=self)
                    else:
                         print("Not running as bundled app, skipping registry modification.")
                         # Revert the setting variable if change was attempted outside bundled app
                         self.settings_vars["run_on_startup"].set(self.initial_run_on_startup)
                         self.config.set("run_on_startup", self.initial_run_on_startup) # Also revert in config obj

            # Save all settings to file
            self.config.save_settings()
            # Close the window
            self.on_close()
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Einstellungen konnten nicht gespeichert werden:\n{e}", parent=self)
            print(traceback.format_exc())

    def on_close(self):
        """Handles the closing of the settings window."""
        if self.recording_active: self._stop_recording(revert=True)
        try: self.unbind("<KeyPress>"); self.unbind("<KeyRelease>")
        except tk.TclError: pass
        self.canvas.unbind_all("<MouseWheel>"); self.canvas.unbind_all("<Button-4>"); self.canvas.unbind_all("<Button-5>")
        try: self.grab_release()
        except tk.TclError: pass
        self.destroy()
        if self.on_close_callback:
            try: self.on_close_callback()
            except Exception as e: print(f"Error in settings window close callback: {e}"); print(traceback.format_exc())

