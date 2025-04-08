# SpeedReader (RSVP-Anwendung)

**SpeedReader** ist eine einfache, aber leistungsfähige Windows-Anwendung zur Beschleunigung des Lesens mittels **RSVP** (*Rapid Serial Visual Presentation*). Sie funktioniert vollständig **ohne Administratorrechte**, liest Texte aus der Zwischenablage oder aus Dateien (`.txt`, `.docx`, `.pdf`) und zeigt sie Wort für Wort oder in Wortgruppen an – schnell, fokussiert und augenschonend. SpeedReader läuft dezent im System-Tray und lässt sich bequem per Hotkey steuern.

---

![Screenshot der Anwendung im Lesemodus](example.png)  
*Ein Rechtsklick auf das Symbol öffnet das Menü.*

![Beispiel eines abgespielten Textes](video.gif)  
*Textwiedergabe mit 500 WPM im Lesemodus*

---

## 🔑 Hauptfunktionen

### 📖 RSVP-Anzeige
- Darstellung von Text Wort für Wort oder in Wortgruppen (*Chunking*, 1–10 Wörter).
- Anzeige auf einem präzisen Canvas für stabile Positionierung.
- Minimiert Augenbewegungen durch festen Anzeigepunkt.

### ⚙️ Lesegeschwindigkeit & Timing
- **Geschwindigkeit**: Einstellbar von 50–1500 WPM (Standard: 300 WPM).
- Live-Anpassung über `+/-`-Tasten in 10er-Schritten.
- **Startverzögerung**: Einstellbare Pause vor Beginn (in Millisekunden).
- **Wortlängen-Verzögerung**: Extra-Lesezeit für lange Wörter (nach Zeichenlänge definierbar).

### 📚 Kontext & ORP
- **Kontextanzeige**: Optional sichtbare vorherige und nächste Wortgruppen (horizontal oder vertikal).
- **Optimal Recognition Point (ORP)**: Optionaler roter Fixationsbuchstabe (nur bei Chunk-Größe 1).
  - Prozentual verschiebbar (0–100 %).
  - Automatische Zentrierung für stabile Fixation.

### ⏱️ Pausenmanagement
- Zusatzpausen (in ms) einstellbar für:
  - **Satzende** (`.`, `!`, `?`, `:`)
  - **Kommas** (`,`)
  - **Absätze** (Leerzeilen)

### 🎨 Anpassbares Aussehen
- Frei wählbare **Schriftart** und **-größe**
- Benutzerdefinierte Farben für Text, Hintergrund und ORP
- **Dark Mode** für augenschonendes Lesen
- Optional rahmenloses Lesefenster mit „Immer im Vordergrund“-Funktion

---

## 🖱️ Steuerung & Systemintegration

- **System-Tray-Integration**:
  - Lesevorgang starten (Zwischenablage oder Datei)
  - Einstellungen öffnen
  - Info anzeigen
  - Anwendung beenden
- **Globaler Hotkey**: `Strg + Alt + R` (konfigurierbar)
- **Unterstützte Dateiformate**: `.txt`, `.docx`, `.pdf`
- **Speicherung aller Einstellungen** in: %APPDATA%\SpeedReader\
- Optionale **Autostart-Funktion** beim Windows-Login

---

## 🧭 Steuerung im Lesefenster

| Taste             | Funktion                                                              |
|------------------|-----------------------------------------------------------------------|
| Leertaste         | Pause / Fortsetzen                                                    |
| Escape            | Fenster schließen                                                     |
| Pfeil Links       | Zum vorherigen Satz springen (pausiert)                               |
| Pfeil Rechts      | Zum nächsten Satz springen (pausiert)                                 |
| `+` / Numpad `+`  | Geschwindigkeit erhöhen (+10 WPM)                                     |
| `-` / Numpad `-`  | Geschwindigkeit verringern (-10 WPM)                                  |
| Enter             | Fenster schließen (nur bei "`--- Ende ---`")                          |

---

## 💾 Installation

1. Lade die neueste Version von der [Releases-Seite](#) herunter.
2. Verschieben sie die `SpeedReader.exe` in einen Ordner Ihrer Wahl.
3. Starte `SpeedReader.exe` per Doppelklick.
4. Die Anwendung startet im Hintergrund und erscheint im System-Tray.

> 💡 SpeedReader benötigt **keine Installation** und **keine Administratorrechte**.

---

## 💡 Mitwirken

Beiträge, Bug-Reports oder Feature-Ideen sind willkommen!  
👉 Erstelle ein [Issue](https://github.com/leofleischmann/Windows-Speed-Reader-RSVP/issues) oder einen Pull Request.

---

## ❗ Bekannte Probleme

- **PDF-Textextraktion** ist bei komplexem Layout oder Sonderzeichen ggf. ungenau.
- **ORP-Darstellung** funktioniert nur zuverlässig bei **lateinischen Schriftsystemen**.
- **Große Textmengen** können beim Einlesen zu leichten Startverzögerungen führen.

---

## 🔍 Hinweis zur Code-Erstellung

> Der Großteil des Quellcodes (ca. 99 %) wurde mithilfe von **Gemini (Google AI)** generiert und anschließend manuell überprüft und erweitert.

---
