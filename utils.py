# -*- coding: utf-8 -*-

import re
import os
import sys # Import sys for platform check if needed
import tkinter as tk
from tkinter import font

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    if 'PIL' not in sys.modules:
        print("Warning: 'Pillow' library not found. Default icon creation might fail.")
        print("Install with: pip install Pillow")

DEFAULT_ICON_NAME = "speedreader_icon.png"

# --- Hilfsfunktionen ---

def calculate_delay(wpm):
    """Calculates the display duration per word based on WPM."""
    if wpm <= 0: return float('inf')
    return 60.0 / wpm

def calculate_orp_index(word, position_float=0.3): # Renamed arg for clarity
    """
    Calculates the Optimal Recognition Point (ORP) index within a word.

    Args:
        word (str): The word to calculate the ORP for.
        position_float (float): The relative position (0.0 to 1.0) for the ORP.
                                (Note: Settings window might use 0-100 for UI).

    Returns:
        int: The calculated index for the ORP character. Returns -1 for empty words.
    """
    n = len(word)
    if n == 0: return -1
    # Ensure position is float between 0 and 1
    position = max(0.0, min(1.0, position_float))
    index = max(0, int(n * position))
    return min(index, n - 1) # Clamp index to valid range

def preprocess_text(text):
    """
    Prepares the text for display: handles abbreviations, splits into words,
    and inserts special markers for pauses.

    Args:
        text (str): The raw input text.

    Returns:
        list: A list of words and pause markers.
    """
    if not isinstance(text, str): return []

    # --- NEU: Pre-processing for common abbreviations with periods ---
    # Replace known patterns with placeholders that won't be split by \S+
    # Using placeholders without periods avoids splitting issues.
    # We don't necessarily need to convert them back, displaying "z_B" might be acceptable.
    # Or use a more complex regex in findall. Let's try placeholders first.
    replacements = {
        r'\b(z\.B\.)\b': 'z_B',
        r'\b(usw\.)\b': 'usw',     # usw. often doesn't need the dot kept
        r'\b(u\.a\.)\b': 'u_a',
        r'\b(d\.h\.)\b': 'd_h',
        r'\b(o\.Ä\.)\b': 'o_Ä',
        r'\b(etc\.)\b': 'etc',     # etc. often doesn't need the dot kept
        r'\b(bzw\.)\b': 'bzw',     # bzw. often doesn't need the dot kept
        # Add more common abbreviations as needed
    }
    processed_text = text
    for pattern, replacement in replacements.items():
        processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)

    # --- Existing processing ---
    processed_text = processed_text.replace('\n\n', ' __PARAGRAPH__ ')
    processed_text = processed_text.replace('\n', ' ')
    processed_text = processed_text.replace('—', ' -- ') # Em dash
    processed_text = processed_text.replace('–', ' - ')  # En dash

    # Split into sequences of non-whitespace characters or the paragraph marker
    # \S+ should now handle the placeholders correctly as single "words"
    raw_words = re.findall(r'\S+|__PARAGRAPH__', processed_text)

    # Filter out any potential empty strings
    final_words = [w for w in raw_words if w]

    return final_words


def create_default_icon(filename=DEFAULT_ICON_NAME):
    """Creates or loads the default icon using Pillow."""
    if not HAS_PILLOW:
        print("Pillow library required for icons. Returning None.")
        return None # Return None if Pillow is missing

    if os.path.exists(filename):
        try:
            img = Image.open(filename)
            if img.size == (64, 64): print(f"Loaded existing icon '{filename}'."); return img
            else: print(f"Existing icon '{filename}' has wrong size. Recreating.")
        except Exception as e: print(f"Error opening icon '{filename}': {e}. Recreating.")

    try:
        img = Image.new('RGB', (64, 64), color='lightblue'); d = ImageDraw.Draw(img)
        fnt = None
        try: fnt = ImageFont.truetype("arial.ttf", 50)
        except IOError: print("Arial font not found, using default PIL font."); fnt = ImageFont.load_default()
        except Exception as e_font: print(f"Could not load font: {e_font}.")
        if fnt: d.text((10, 5), "R", font=fnt, fill='darkblue')
        else: d.rectangle((10, 10, 54, 54), fill='darkblue')
        img.save(filename); print(f"Default icon '{filename}' created."); return img
    except NameError as ne: print(f"Error creating icon: {ne}. Pillow components missing?"); return None
    except Exception as e: print(f"Could not create default icon '{filename}': {e}"); return None

