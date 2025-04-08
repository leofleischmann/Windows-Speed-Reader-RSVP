# SpeedReader (RSVP-Anwendung)

**SpeedReader** ist eine einfache, aber leistungsfähige Windows-Anwendung zur Beschleunigung des Lesens mittels **RSVP** (Rapid Serial Visual Presentation). Sie funktioniert auch **ohne Administratorrechte**, liest Texte aus der Zwischenablage oder aus Dateien (`.txt`, `.docx`, `.pdf`) und zeigt sie Wort für Wort oder in Wortgruppen an – schnell, fokussiert und augenschonend. SpeedReader läuft dezent im System-Tray und lässt sich bequem per Hotkey steuern.

![Screenshot der Anwendung im Lesemodus](example.png)  
*Ein Rechtsklick auf das Symbol öffnet das Menü.*

![Beispiel eines abgespielten Textes](video.gif)  
*Textwiedergabe mit 500 WPM im Lesemodus*

---

## 🔑 Hauptfunktionen

### 📖 RSVP-Anzeige
- Textanzeige Wort für Wort oder in Wortgruppen (Chunking, 1–10 Wörter).
- Darstellung auf einem präzisen Canvas-Widget für stabile Positionierung.
- Minimiert Augenbewegungen durch festen Anzeigepunkt.

### ⚙️ Einstellbare Lesegeschwindigkeit & Timing
- **WPM**: Standard: 300 WPM, Bereich: 50–1500 WPM. Steuerbar über Schieberegler, direkte Eingabe und `+/-`-Tasten (±10 WPM).
- **Startverzögerung**: Konfigurierbare Wartezeit (in ms), bevor der erste Textblock erscheint.
- **Wortlängen-Verzögerung**: Zusätzliche Anzeigezeit pro Zeichen (nach Schwellenwert), um lange Wörter besser erfassbar zu machen.

### 📚 Kontext & ORP
- **Kontext-Anzeige**: Optional vorheriger und nächster Chunk sichtbar (horizontal oder vertikal).
- **Optimal Recognition Point (ORP)**: Optionaler roter Buchstabe als Fixationspunkt (nur bei Chunk-Größe 1).
  - Position einstellbar (0–100 %).
  - Horizontale Zentrierung für stabilen Blickpunkt.

### ⏱️ Pausenmanagement
- Konfigurierbare Zusatzpausen (in ms) für:
  - Satzenden (`.`, `!`, `?`, `:`)
  - Kommas (`,`)
  - Absätze (Leerzeilen)

### 🎨 Anpassbares Aussehen
- Frei wählbare **Schriftart** und **-größe**.
- Benutzerdefinierte Farben für Text, Hintergrund und ORP (inkl. Hell-/Dunkelmodus).
- Optional **rahmenloses Lesefenster** mit „Immer im Vordergrund“-Funktion.

---

## 🖱️ Steuerung & Integration

- Läuft im Hintergrund mit **System-Tray-Symbol**.
- Menüfunktionen im Tray:
  - Lesen aus Zwischenablage oder Datei
  - Einstellungen
  - Info (Version, Autor, Link)
  - Beenden
- **Globaler Hotkey** (Standard: `Strg + Alt + R`) zum Lesen aus der Zwischenablage.
- **Unterstützte Dateiformate**: `.txt`, `.docx`, `.pdf`
- Einstellungen werden gespeichert unter: %APPDATA%\SpeedReader\
- Optionale **Autostart-Funktion** beim Windows-Login.

---

## 🧭 Steuerung im Lesefenster

| Taste             | Funktion                                                              |
|------------------|-----------------------------------------------------------------------|
| Leertaste         | Pause / Weiter                                                        |
| Escape            | Fenster schließen                                                     |
| Pfeil Links       | Zum Anfang des aktuellen oder vorherigen Satzes springen (pausiert)   |
| Pfeil Rechts      | Zum Anfang des nächsten Satzes springen (pausiert)                    |
| `+` / Numpad `+`  | Geschwindigkeit erhöhen (+10 WPM)                                     |
| `-` / Numpad `-`  | Geschwindigkeit verringern (-10 WPM)                                  |
| Enter             | Fenster schließen (nur wenn "`--- Ende ---`" angezeigt wird)          |

---

## 💾 Installation

1. Lade die neueste Version von der [Releases-Seite](#) herunter.
2. Verschiebe `SpeedReader.exe` an einen gewünschten Ort (z. B. Desktop oder Tools-Ordner).
3. Starte die Anwendung per Doppelklick auf `SpeedReader.exe`.
4. Die Anwendung startet im Hintergrund und erscheint im Infobereich (Tray).

---

## 💡 Mitwirken

Beiträge, Verbesserungsvorschläge und Bug-Reports sind willkommen!  
Bitte öffne ein [Issue](https://github.com/leofleischmann/Windows-Speed-Reader-RSVP/issues) oder erstelle einen Pull Request.

---

## ❗ Bekannte Probleme / Hinweise

- Die Textextraktion aus **PDF-Dateien** ist nicht immer perfekt und kann bei komplexen Layouts oder Sonderzeichen fehlerhaft sein.
- Die **ORP-Darstellung** funktioniert nur bei **lateinischer Schrift** zuverlässig.
- Bei sehr großen Texten kann es zu kurzen **Verzögerungen beim Start** kommen.

---

## 🔍 Hinweis zur Code-Erstellung

> **Hinweis**: Der Großteil des Quellcodes (ca. 99 %) wurde mithilfe von **Gemini (Google AI)** generiert und iterativ angepasst.

---
