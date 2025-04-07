# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, font
import math
import traceback # For detailed error logging

from utils import preprocess_text, calculate_delay, calculate_orp_index

# --- Dark Mode Colors ---
DARK_BG = "#2b2b2b"; DARK_FG = "#bbbbbb"; DARK_HIGHLIGHT = "#FF5555"
DARK_STATUS_BG = "#3c3f41"; DARK_STATUS_FG = "#bbbbbb"
DARK_PROGRESS_TROUGH = "#3c3f41"; DARK_PROGRESS_BAR = "#4e7cbf"
CONTEXT_FG_LIGHT = "#a0a0a0"; CONTEXT_FG_DARK = "#606060" # Context colors

INITIAL_DELAY_MS = 1500 # Verzögerung in Millisekunden vor Start

class ReadingWindow(tk.Toplevel):
    """
    RSVP window with context display (vertical/horizontal), enhanced navigation,
    Canvas ORP alignment (fixed point), chunking, dark mode, restart,
    close on enter at end, initial delay.
    """
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.parent = parent
        self.config = config_manager
        self.raw_words = []
        self.display_items = []
        self.item_to_word_start_index = {}
        self.current_item_index = 0
        self.paused = False
        self.reading_job = None
        self.widget_font = None
        self.at_end = False
        self.font_color = "#000000"
        self.highlight_color = "#FF0000"
        self.context_font_color = "#a0a0a0"

        self.title("Speed Reader")

        # --- Window Geometry and Appearance ---
        screen_width = self.winfo_screenwidth(); screen_height = self.winfo_screenheight()
        width = int(screen_width * 0.8); height = int(screen_height * 0.4)
        x = (screen_width - width) // 2; y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        if self.config.get("reader_borderless"): self.overrideredirect(True)
        if self.config.get("reader_always_on_top"): self.attributes('-topmost', True)
        self.configure(bg=self.config.get("background_color")) # Initial

        # --- Main Frame ---
        self.main_frame = tk.Frame(self); self.main_frame.pack(expand=True, fill="both")

        # --- Word Display Canvas ---
        self.word_display_canvas = tk.Canvas(self.main_frame, bd=0, highlightthickness=0)
        self.word_display_canvas.pack(expand=True, fill="both", padx=50, pady=50)

        # --- Progress Bar ---
        self.progress_var = tk.DoubleVar(); self.progress_style = ttk.Style(self)
        self.progress_style.configure("custom.Horizontal.TProgressbar", troughcolor='lightgrey', background='blue')
        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", mode="determinate", variable=self.progress_var, style="custom.Horizontal.TProgressbar")
        self.progress_bar.pack(side="bottom", pady=(0, 10), padx=50, fill="x")

        # --- Status Bar ---
        self.status_bar_frame = tk.Frame(self); self.status_bar_frame.pack(side="bottom", fill="x")
        left_status_frame = ttk.Frame(self.status_bar_frame); left_status_frame.pack(side="left", padx=10)
        self.restart_button = ttk.Button(left_status_frame, text="Neustart", command=self.restart_reading, width=8); self.restart_button.pack(side="left", padx=(0, 10))
        self.status_label_left = ttk.Label(left_status_frame, text="", anchor="w"); self.status_label_left.pack(side="left")
        self.status_label_right = ttk.Label(self.status_bar_frame, text="", anchor="e"); self.status_label_right.pack(side="right", padx=10)

        # --- Keyboard Bindings ---
        self.bind("<space>", self.toggle_pause)
        self.bind("<Escape>", self.close_window)
        self.bind("<Left>", self.rewind_to_sentence_start)
        self.bind("<Right>", self.skip_to_next_sentence_start)
        self.bind("<plus>", self.increase_speed)
        self.bind("<KP_Add>", self.increase_speed)
        self.bind("<minus>", self.decrease_speed)
        self.bind("<KP_Subtract>", self.decrease_speed)
        self.bind("<Return>", self.close_on_enter_at_end)
        self.bind("<KP_Enter>", self.close_on_enter_at_end)

        # --- Initial Setup ---
        self.update_display_settings(); self.update_status_bar()
        self.focus_set(); self.grab_set()


    def update_display_settings(self):
        """Applies font, color, and theme settings."""
        is_dark = self.config.get("dark_mode")
        bg_color = DARK_BG if is_dark else self.config.get("background_color")
        self.font_color = DARK_FG if is_dark else self.config.get("font_color") # Store class attribute
        self.highlight_color = DARK_HIGHLIGHT if is_dark else self.config.get("highlight_color") # Store class attribute
        self.context_font_color = CONTEXT_FG_DARK if is_dark else CONTEXT_FG_LIGHT # Store context color
        status_bg = DARK_STATUS_BG if is_dark else "lightgrey"; status_fg = DARK_STATUS_FG if is_dark else "black"
        prog_trough = DARK_PROGRESS_TROUGH if is_dark else 'lightgrey'; prog_bar = DARK_PROGRESS_BAR if is_dark else 'blue'
        font_family = self.config.get("font_family"); font_size = self.config.get("font_size")

        self.configure(bg=bg_color); self.main_frame.configure(bg=bg_color); self.word_display_canvas.configure(bg=bg_color)
        try: self.widget_font = font.Font(family=font_family, size=font_size)
        except tk.TclError as e: print(f"Error setting font: {e}. Using default."); self.widget_font = font.nametofont("TkDefaultFont")

        self.status_bar_frame.configure(bg=status_bg)
        status_style_name = "Status.TLabel"; status_frame_style = "Status.TFrame"
        self.progress_style.configure(status_style_name, background=status_bg, foreground=status_fg)
        self.progress_style.configure(status_frame_style, background=status_bg)
        self.status_label_left.configure(style=status_style_name); self.status_label_right.configure(style=status_style_name)
        try: self.status_label_left.master.configure(style=status_frame_style)
        except tk.TclError: pass
        self.progress_style.configure("custom.Horizontal.TProgressbar", troughcolor=prog_trough, background=prog_bar)

        if self.display_items: self.display_item()
        self.update_status_bar()

    def _generate_display_items(self):
        """Groups raw words into chunks and creates index mapping."""
        self.display_items = []; self.item_to_word_start_index = {}
        chunk_size = self.config.get("chunk_size");
        if chunk_size < 1: chunk_size = 1
        current_chunk_words = []; start_idx_for_current_chunk = 0; word_idx = 0
        while word_idx < len(self.raw_words):
            word = self.raw_words[word_idx]
            if word == "__PARAGRAPH__":
                if current_chunk_words:
                    item_index = len(self.display_items); self.display_items.append(" ".join(current_chunk_words))
                    self.item_to_word_start_index[item_index] = start_idx_for_current_chunk; current_chunk_words = []
                item_index = len(self.display_items); self.display_items.append(word)
                self.item_to_word_start_index[item_index] = word_idx
                word_idx += 1; start_idx_for_current_chunk = word_idx
            else:
                if not current_chunk_words: start_idx_for_current_chunk = word_idx
                current_chunk_words.append(word); word_idx += 1
                if len(current_chunk_words) >= chunk_size or word_idx >= len(self.raw_words):
                    item_index = len(self.display_items); self.display_items.append(" ".join(current_chunk_words))
                    self.item_to_word_start_index[item_index] = start_idx_for_current_chunk; current_chunk_words = []

    def start_reading(self, text):
        """Processes text, generates items, displays first item, then starts reading after delay."""
        self.raw_words = preprocess_text(text)
        if not self.raw_words: messagebox.showinfo("Leerer Text", "Kein Text zum Lesen gefunden.", parent=self); self.close_window(); return
        self._generate_display_items()
        if not self.display_items: messagebox.showinfo("Leerer Text", "Keine anzeigbaren Wörter nach Verarbeitung gefunden.", parent=self); self.close_window(); return
        self.restart_reading(update_ui=False); self.update_display_settings()
        self.current_item_index = 0; self.display_item(); self.update_progress(); self.update_status_bar()
        print(f"Scheduling reading start after {INITIAL_DELAY_MS}ms delay...")
        if self.reading_job: self.after_cancel(self.reading_job)
        self.reading_job = self.after(INITIAL_DELAY_MS, self.schedule_next_item)

    def restart_reading(self, event=None, update_ui=True):
        """Resets reading to the beginning."""
        print("Restarting reading..."); self.current_item_index = 0; self.paused = False; self.at_end = False
        self.progress_var.set(0.0)
        if self.reading_job: self.after_cancel(self.reading_job); self.reading_job = None
        if not self.display_items: return
        self.progress_bar.config(maximum=len(self.display_items))
        if update_ui:
            self.display_item(); self.update_status_bar()
            self.reading_job = self.after(INITIAL_DELAY_MS, self.schedule_next_item)

    def schedule_next_item(self):
        """Schedules the display of the next item."""
        if self.reading_job: self.after_cancel(self.reading_job); self.reading_job = None
        if self.paused: self.update_status_bar(); return
        if self.current_item_index >= len(self.display_items):
            self.display_item("--- Ende ---"); self.progress_var.set(len(self.display_items)); self.update_status_bar(); self.at_end = True; return

        self.at_end = False
        self.display_item(); self.update_progress() # Display item BEFORE calculating its delay
        current_item = self.display_items[self.current_item_index]
        base_delay_s = calculate_delay(self.config.get("wpm")); extra_pause_s = 0.0; words_in_item = 0
        pause_punct_s = self.config.get("pause_punctuation"); pause_comma_s = self.config.get("pause_comma"); pause_para_s = self.config.get("pause_paragraph")

        if current_item == "__PARAGRAPH__":
            extra_pause_s = pause_para_s; total_delay_s = extra_pause_s
        else:
            words_in_item = len(current_item.split())
            visible_item = current_item.rstrip(); last_visible_char = visible_item[-1] if visible_item else ''
            if last_visible_char in ('.', '!', '?', ':', ';'): extra_pause_s = pause_punct_s
            elif last_visible_char == ',': extra_pause_s = pause_comma_s
            total_delay_s = (words_in_item * base_delay_s) + extra_pause_s

        actual_delay_ms = max(10, int(total_delay_s * 1000))
        self.current_item_index += 1 # Increment AFTER calculating delay for current item
        self.reading_job = self.after(actual_delay_ms, self.schedule_next_item)
        self.update_status_bar() # Update status bar reflecting processed item


    def display_item(self, item=None):
        """Displays item on Canvas, optionally with context, maintaining ORP fixed point."""
        item_to_display = ""; is_special_message = item is not None
        prev_item_context = ""; next_item_context = ""
        safe_current_idx = max(0, min(self.current_item_index, len(self.display_items) - 1))

        if not is_special_message:
            if 0 <= safe_current_idx < len(self.display_items):
                item_to_display = self.display_items[safe_current_idx]
                if item_to_display == "__PARAGRAPH__": item_to_display = ""
                if self.config.get("show_context"):
                    prev_idx = safe_current_idx - 1
                    if 0 <= prev_idx < len(self.display_items):
                         prev_item_context = self.display_items[prev_idx]
                         if prev_item_context == "__PARAGRAPH__": prev_item_context = ""
                    next_idx = safe_current_idx + 1
                    if 0 <= next_idx < len(self.display_items):
                         next_item_context = self.display_items[next_idx]
                         if next_item_context == "__PARAGRAPH__": next_item_context = ""
        else: item_to_display = item

        canvas = self.word_display_canvas; canvas.delete("all")
        if not self.widget_font: self.update_display_settings();
        if not self.widget_font: self.widget_font = font.nametofont("TkDefaultFont")
        try: canvas_width = canvas.winfo_width(); canvas_height = canvas.winfo_height(); center_x = canvas_width / 2; center_y = canvas_height / 2
        except tk.TclError: return

        show_context = self.config.get("show_context")
        context_layout = self.config.get("context_layout")

        # Variables to store calculated boundaries of the main item
        main_word_start_x = center_x
        main_word_end_x = center_x

        # --- Draw Main Item (potentially with ORP) ---
        if item_to_display:
            # Determine if ORP should be applied
            apply_orp = (self.config.get("enable_orp") and
                         self.config.get("chunk_size") == 1 and
                         not is_special_message)

            if apply_orp:
                # Draw with centered ORP at center_x, center_y
                word_len = len(item_to_display); orp_pos_float = self.config.get("orp_position")
                orp_index = calculate_orp_index(item_to_display, orp_pos_float)
                if orp_index != -1:
                    part1 = item_to_display[:orp_index]; orp_char = item_to_display[orp_index]; part2 = item_to_display[orp_index+1:]
                    try:
                        width_before = self.widget_font.measure(part1); width_orp = self.widget_font.measure(orp_char); width_after = self.widget_font.measure(part2)
                        # Calculate positions to center the middle of the ORP character
                        x_orp_start = center_x - (width_orp / 2);
                        x_part1_start = x_orp_start - width_before;
                        x_part2_start = x_orp_start + width_orp
                        # Draw parts
                        if part1: canvas.create_text(x_part1_start, center_y, text=part1, anchor='w', font=self.widget_font, fill=self.font_color)
                        canvas.create_text(x_orp_start, center_y, text=orp_char, anchor='w', font=self.widget_font, fill=self.highlight_color)
                        if part2: canvas.create_text(x_part2_start, center_y, text=part2, anchor='w', font=self.widget_font, fill=self.font_color)
                        # Store visual boundaries
                        main_word_start_x = x_part1_start if part1 else x_orp_start
                        main_word_end_x = x_part2_start + width_after if part2 else x_orp_start + width_orp
                    except tk.TclError as e: print(f"Error measuring/drawing ORP: {e}"); apply_orp = False # Fallback to normal drawing
                    except Exception as e: print(f"Unexpected error: {e}"); traceback.print_exc(); apply_orp = False # Fallback
                else: apply_orp = False # Fallback if ORP index invalid

            # Draw normally centered if ORP not applied or failed
            if not apply_orp:
                 canvas.create_text(center_x, center_y, text=item_to_display, anchor='center', font=self.widget_font, fill=self.font_color)
                 # Estimate boundaries for context positioning
                 w_main = self.widget_font.measure(item_to_display)
                 main_word_start_x = center_x - w_main / 2
                 main_word_end_x = center_x + w_main / 2

        # --- Draw Context ---
        if show_context and not is_special_message:
            try:
                line_height = self.widget_font.metrics('linespace') * 1.1
                if context_layout == "vertical":
                    y_prev = center_y - line_height; y_next = center_y + line_height
                    if prev_item_context: canvas.create_text(center_x, y_prev, text=prev_item_context, anchor='center', font=self.widget_font, fill=self.context_font_color)
                    if next_item_context: canvas.create_text(center_x, y_next, text=next_item_context, anchor='center', font=self.widget_font, fill=self.context_font_color)
                elif context_layout == "horizontal":
                    # Draw relative to the already drawn main word boundaries
                    w_space2 = self.widget_font.measure("  ")
                    if prev_item_context:
                        w_prev = self.widget_font.measure(prev_item_context)
                        x_prev = main_word_start_x - w_space2 - w_prev
                        canvas.create_text(x_prev, center_y, text=prev_item_context, anchor='w', font=self.widget_font, fill=self.context_font_color)
                    if next_item_context:
                        x_next = main_word_end_x + w_space2
                        canvas.create_text(x_next, center_y, text=next_item_context, anchor='w', font=self.widget_font, fill=self.context_font_color)
            except Exception as e: print(f"Error drawing context: {e}")


    def update_progress(self):
        """Updates the progress bar."""
        if self.display_items:
            progress_value = self.current_item_index
            try: max_val = self.progress_bar.cget("maximum")
            except tk.TclError: max_val = len(self.display_items)
            self.progress_var.set(min(progress_value, max_val))
        else: self.progress_var.set(0.0)

    def update_status_bar(self):
        """Updates the status bar labels."""
        wpm = self.config.get("wpm"); status_text = f"{wpm} WPM"
        if self.paused: status_text += " (Pausiert)"
        try:
             if self.status_label_left.winfo_exists(): self.status_label_left.config(text=status_text)
        except tk.TclError: pass
        position_text = ""
        if self.display_items:
            current_display_idx = max(0, min(self.current_item_index, len(self.display_items) - 1))
            current_display_pos = current_display_idx + 1
            total_items = len(self.display_items)
            if self.at_end: current_display_pos = total_items
            position_text = f"Block {current_display_pos} / {total_items}"
        try:
            if self.status_label_right.winfo_exists(): self.status_label_right.config(text=position_text)
        except tk.TclError: pass

    def toggle_pause(self, event=None):
        """Toggles the paused state."""
        self.paused = not self.paused
        if not self.paused: self.at_end = False; self.schedule_next_item()
        else:
            if self.reading_job: self.after_cancel(self.reading_job); self.reading_job = None
        self.update_status_bar()

    def change_speed(self, delta):
        current_wpm = self.config.get("wpm"); new_wpm = max(10, current_wpm + delta)
        self.config.set("wpm", new_wpm); self.update_status_bar()

    def close_window(self, event=None):
        if self.reading_job: self.after_cancel(self.reading_job); self.reading_job = None
        self.grab_release(); self.destroy()

    def close_on_enter_at_end(self, event=None):
        if self.at_end: print("Closing window on Enter after end."); self.close_window()

    def _find_item_index_for_word_index(self, target_word_index):
        """Finds the display_item index containing the target raw_word index."""
        if not self.item_to_word_start_index: return 0
        if target_word_index <= 0: return 0
        target_item_index = 0
        sorted_map_items = sorted(self.item_to_word_start_index.items(), key=lambda item: item[1])
        for i, (item_idx, item_start_word) in enumerate(sorted_map_items):
            if item_start_word <= target_word_index:
                target_item_index = item_idx
                next_item_start_word = float('inf')
                if i + 1 < len(sorted_map_items): next_item_start_word = sorted_map_items[i+1][1]
                if target_word_index < next_item_start_word: break
            else:
                 if i == 0: target_item_index = 0
                 break
        # Ensure returned index is within bounds of display_items
        return max(0, min(target_item_index, len(self.display_items) - 1))


    def rewind_to_sentence_start(self, event=None):
        """Finds the start of the current/previous sentence and jumps there."""
        if not self.raw_words or not self.item_to_word_start_index or not self.display_items: return
        current_effective_item_index = self.current_item_index
        if not self.paused: current_effective_item_index = max(0, self.current_item_index - 1)
        current_effective_item_index = max(0, min(current_effective_item_index, len(self.display_items) - 1))
        start_word_idx_of_current_item = self.item_to_word_start_index.get(current_effective_item_index, 0)

        sentence_start_word_idx = 0; search_idx = start_word_idx_of_current_item - 1
        if start_word_idx_of_current_item == 0: search_idx = -1
        while search_idx >= 0:
            word = self.raw_words[search_idx]
            if word.endswith(('.', '!', '?', ':')): sentence_start_word_idx = search_idx + 1; break
            search_idx -= 1

        current_sentence_start_item_idx = self._find_item_index_for_word_index(sentence_start_word_idx)
        target_item_index = current_sentence_start_item_idx

        if self.paused and self.current_item_index == current_sentence_start_item_idx and sentence_start_word_idx > 0:
            print("Already at sentence start, finding previous sentence...")
            prev_sentence_start_word_idx = 0; search_idx = sentence_start_word_idx - 2
            while search_idx >= 0:
                word = self.raw_words[search_idx]
                if word.endswith(('.', '!', '?', ':')): prev_sentence_start_word_idx = search_idx + 1; break
                search_idx -= 1
            print(f"Found previous sentence start word index: {prev_sentence_start_word_idx}")
            target_item_index = self._find_item_index_for_word_index(prev_sentence_start_word_idx)

        print(f"Rewind: Jumping to item index {target_item_index}")
        self.paused = True
        if self.reading_job: self.after_cancel(self.reading_job); self.reading_job = None
        self.current_item_index = target_item_index
        self.at_end = False
        self.display_item(); self.update_progress(); self.update_status_bar()

    def skip_to_next_sentence_start(self, event=None):
        """Finds the start of the next sentence and jumps there."""
        if not self.raw_words or not self.item_to_word_start_index or not self.display_items: return

        safe_current_idx = max(0, min(self.current_item_index, len(self.display_items) - 1))
        start_word_idx_of_current_item = self.item_to_word_start_index.get(safe_current_idx, 0)

        if self.current_item_index >= len(self.display_items): return # Already past end

        next_sentence_start_word_idx = len(self.raw_words)
        search_start_idx = start_word_idx_of_current_item
        current_item_is_marker = self.display_items[safe_current_idx] == "__PARAGRAPH__"
        if not current_item_is_marker:
             chunk_words = self.display_items[safe_current_idx].split()
             search_start_idx += len(chunk_words)

        search_idx = search_start_idx
        while search_idx < len(self.raw_words):
            word = self.raw_words[search_idx]
            if word.endswith(('.', '!', '?', ':')): next_sentence_start_word_idx = search_idx + 1; break
            search_idx += 1

        print(f"Skip Forward: Current item index {self.current_item_index}, search start word {search_start_idx}. Found next sentence start word: {next_sentence_start_word_idx}")

        if next_sentence_start_word_idx >= len(self.raw_words):
             target_item_index = len(self.display_items)
        else: target_item_index = self._find_item_index_for_word_index(next_sentence_start_word_idx)

        if target_item_index <= self.current_item_index and self.current_item_index < len(self.display_items):
             target_item_index = self.current_item_index + 1

        print(f"Skip Forward: Jumping to item index {target_item_index}")
        self.paused = True
        if self.reading_job: self.after_cancel(self.reading_job); self.reading_job = None
        self.current_item_index = target_item_index

        self.at_end = self.current_item_index >= len(self.display_items)
        self.display_item(); self.update_progress(); self.update_status_bar()

    def increase_speed(self, event=None): self.change_speed(10)
    def decrease_speed(self, event=None): self.change_speed(-10)

