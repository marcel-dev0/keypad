# Keypad – AutoKey-Scripts mit Ebenen (Layern)

AutoKey-Scripts für das 9-Tasten-Keypad **SDINNOVATION SIDE-KEYBOARD**
(USB `0816:2471`). Das Keypad bekommt mehrere Ebenen ("Layer") mit je 9
belegbaren Tasten. Die Tastenbeleuchtung zeigt per Farbe, welche Ebene aktiv
ist.

- Tasten 1–9 lösen je nach aktiver Ebene beliebige Aktionen aus: Programme
  starten, Tastenkombinationen senden, Text tippen.
- Ebene hoch/runter wechseln, aktuelle Belegung als Benachrichtigung anzeigen.
- Jede Ebene hat eine eigene Beleuchtungsfarbe.
- Die Belegung steht komplett in einer Datei (`layers.py`), Texte in einer zweiten Datei (`phrases.json`).

## Voraussetzungen

- Linux mit **X11** (die Scripts nutzen XTest; unter Wayland funktioniert das
  nicht)
- [AutoKey](https://github.com/autokey/autokey) (getestet mit 0.95.10, GTK)
- Python 3 (getestet mit 3.12) und `python3-xlib`
- `notify-send` (Paket `libnotify-bin`) für die Layer-Anzeige

```bash
sudo apt install autokey-gtk python3-xlib libnotify-bin
```

## Installation

1. Repository in den AutoKey-Datenordner klonen:

   ```bash
   git clone <URL> ~/.config/autokey/data/Keypad
   ```

2. Eigene Texte anlegen:

   ```bash
   cd ~/.config/autokey/data/Keypad
   erstelle phrases.json
   ```

3. Zugriff auf das Keypad für die Beleuchtung erlauben. Als
   `/etc/udev/rules.d/70-sdinnovation-keypad.rules`:

   ```
   SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0816", ATTRS{idProduct}=="2471", MODE="0660", GROUP="plugdev"
   ```

   Danach `sudo udevadm control --reload && sudo udevadm trigger`, dein
   Benutzer muss in der Gruppe `plugdev` sein, und das Keypad einmal
   abziehen und wieder einstecken.

4. AutoKey neu starten. Der Ordner "Keypad" erscheint mit allen Scripts.

## Was das Keypad senden muss

Die Scripts reagieren auf Hotkeys, die das Keypad selbst senden muss. Das
stellst du in der Herstellersoftware (WebHID-Konfigurator) ein:

| Taste am Keypad | sendet             | Script         |
|-----------------|--------------------|----------------|
| Taste 1–9       | Strg+Alt+Umschalt+1 … 9 | `Action 1–9.py` |
| Layer hoch      | Keycode 191        | `Layer Up.py`  |
| Layer anzeigen  | Keycode 192        | `Show Layer.py`|
| Layer runter    | Keycode 193        | `Layer Down.py`|

Andere Tasten oder Kombinationen kannst du in AutoKey an den jeweiligen
Scripts ändern (Hotkey im Script-Eintrag).

## Belegung ändern

Alles steht in **`layers.py`**. Jede Taste hat ein Label (für die Anzeige)
und eine Liste von Schritten, die der Reihe nach ausgeführt werden:

| Schritt | Wirkung |
|---------|---------|
| `("launch", ["firefox", "https://…"])` | Programm starten |
| `("hotkey", ["Alt_L", "F4"], {"repeat": 1, "hold_ms": 20})` | Tastenkombination über XTest. Nötig für globale Fenstermanager-Shortcuts (Alt+F4, Alt+Tab, Super+…). |
| `("send_keys", "<ctrl>+c")` | `keyboard.send_keys()` von AutoKey. Reicht für Tastenkürzel innerhalb einer Anwendung. Text wird geparst: `<ctrl>` usw. sind Sondertasten. |
| `("phrase", "danke")` | Tippt den Text aus `phrases.json` |

Die Farbe pro Ebene steht in `LAYER_COLORS` am Ende von `layers.py`. Neue
Ebenen fügst du in `LAYERS` und `LAYER_COLORS` hinzu.

### Texte (`phrases.json`)

```json
{
  "danke": "Vielen Dank für Ihre Antwort.",
  "passwort": "HIER-EINTRAGEN"
}
```

`phrases.json` steht in der `.gitignore` und wird nicht hochgeladen. Der Text
geht über stdin an `type_text.py`, damit er nicht in der Prozessliste (`ps`)
auftaucht.

Grenzen von `phrase`: Zeilenumbrüche, Tabs und Emojis lassen sich
nicht tippen, weil sie im Tastaturlayout keine eigene Taste haben. Zeichen
müssen im aktuell eingestellten Layout erreichbar sein (Umlaute und AltGr-Zeichen
funktionieren).

## Dateien

| Datei | Zweck |
|-------|-------|
| `layers.py` | Belegung und Farben, die einzige Datei, die du normalerweise änderst |
| `phrases.json` | Texte für `("phrase", …)`, nicht im Repository (siehe oben) |
| `Action 1–9.py` | Tasten 1–9, rufen nur `run_key(n, keyboard)` auf |
| `Layer Up.py`, `Layer Down.py`, `Show Layer.py` | Ebene wechseln bzw. anzeigen |
| `functions/keypad_config.py` | Ebenenzustand, Entprellung, Schrittausführung |
| `functions/send_hotkey.py` | Tastenkombination per XTest senden |
| `functions/type_text.py` | Text per XTest tippen |
| `functions/set_keypad_color.py` | Beleuchtung des Keypads per HID steuern |
| `functions/scan_keypad_indices.py` | Hilfsprogramm: Tastenindizes der Beleuchtung durchprobieren |
| `.*.json` | AutoKey-Metadaten der Scripts (Hotkeys) |

Die aktive Ebene und die Entprellung liegen in `~/.cache/keypad_layer` und
`~/.cache/keypad_debounce.json`.

## Beleuchtung

`functions/set_keypad_color.py` steuert die RGB-Beleuchtung direkt über
`/dev/hidraw*`. Das Protokoll stammt aus einem Mitschnitt (usbmon) der
Herstellersoftware und ist im Kopf der Datei dokumentiert. Das Projekt steht in
keiner Verbindung zum Hersteller. Die Nutzung erfolgt auf eigene Gefahr, denn
es werden rohe HID-Reports an das Gerät geschickt.

```bash
functions/set_keypad_color.py effect breath 255 0 0 --speed 2 --mono
functions/set_keypad_color.py key 3 0 255 0
```

## Lizenz

[MIT](LICENSE)
