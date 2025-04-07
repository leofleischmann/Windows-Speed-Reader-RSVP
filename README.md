# SpeedReader

**SpeedReader** ist eine einfache, aber leistungsfähige Windows-Anwendung zur Beschleunigung des Lesens mittels **RSVP** (Rapid Serial Visual Presentation). Die Anwendung liest Texte aus der Zwischenablage oder aus Dateien und zeigt sie Wort für Wort oder in Gruppen an – schnell, fokussiert und augenschonend. SpeedReader läuft dezent im System-Tray und lässt sich bequem per Hotkey steuern.


---

## 🔑 Hauptfunktionen

### 📖 RSVP-Anzeige
- Textanzeige Wort für Wort oder in Wortgruppen.
- Darstellung auf einem präzisen Canvas-Widget.
- Minimiert Augenbewegungen durch festen Anzeigepunkt.

### ⚙️ Einstellbare Lesegeschwindigkeit
- Standard: **300 WPM**, Bereich: **50–1500 WPM**.
- Geschwindigkeit über Schieberegler und direkte Eingabe steuerbar.
- Anpassung auch während des Lesens mit `+`/`-` Tasten (jeweils ±10 WPM).

### 📚 Wortgruppen (Chunking)
- Anzeige von **1–10 Wörtern** gleichzeitig.
- Optionale Kontextanzeige (vorheriger/nächster Chunk) horizontal oder vertikal.

### 🎯 Optimal Recognition Point (ORP)
- Markiert Fixationspunkt pro Wort mit **rotem Buchstaben**.
- Position frei einstellbar (0–100%).
- Bei Chunk-Größe 1 wird das Wort automatisch zentriert.

### ⏱️ Pausenmanagement
- Zusatzpausen für:
  - **Satzende (.)**
  - **Kommas (,)**  
  - **Absätze**
- Millisekunden-genau konfigurierbar.

### 🎨 Anpassbares Aussehen
- Frei wählbare Schriftart und -größe.
- Anpassbare Farben (Text, Hintergrund, ORP).
- **Dark Mode** für augenschonendes Lesen.
- Optional rahmenloses Fenster mit "Immer im Vordergrund"-Modus.

---

## 🧭 Steuerung & Bedienung

### System-Tray
- Läuft im Hintergrund mit Tray-Symbol.
- Lesestart aus Zwischenablage oder Datei via Tray-Menü.
- Globaler Hotkey (Standartmäßig **Strg + Alt + R**) zum Lesen der Zwischenablage.

### Lesefenster
| Taste         | Funktion                                 |
|---------------|------------------------------------------|
| Leertaste     | Pause / Weiter                           |
| Escape        | Fenster schließen                        |
| Pfeiltasten   | Vorheriger / nächster Satz               |
| `+` / `-`     | Geschwindigkeit anpassen (±10 WPM)       |
| Enter         | Fenster schließen (am Leseende)          |

---

## 🖥️ Systemintegration

- Optionale **Autostart-Funktion** beim Windows-Login.
- Alle Einstellungen werden unter  
  `%APPDATA%\SpeedReader\` gespeichert.

---

## 💡 Mitwirken

Beiträge, Verbesserungsvorschläge und Bug-Reports sind willkommen!  
Bitte öffne ein Issue.

---

## ❗ Bekannte Probleme

- Die ORP-Darstellung funktioniert nur bei lateinischer Schrift zuverlässig.
- Bei sehr großen Texten kann es zu kurzen Verzögerungen beim Start kommen.

---

