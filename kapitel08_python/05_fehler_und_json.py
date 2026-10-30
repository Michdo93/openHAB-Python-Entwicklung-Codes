"""Kapitel 8: Ausnahmen, Kontextmanager und JSON."""
import json
from pathlib import Path

antwort = ('{"name": "Wohnzimmer_Licht", "state": "ON", '
           '"tags": ["Switch", "Light"]}')

item = json.loads(antwort)                  # Text -> dict
print(item["name"], item["tags"])
print(json.dumps(item, indent=2, ensure_ascii=False))   # dict -> Text

try:
    kaputt = json.loads('{"name": "X", ')
except json.JSONDecodeError as fehler:
    print("Ungültiges JSON:", fehler)
else:
    print("wird nur ohne Fehler ausgeführt")
finally:
    print("wird immer ausgeführt")


class OpenHABFehler(Exception):
    """Eigene Ausnahme für Fehler im Umgang mit openHAB."""


def pruefe(antwort: dict) -> dict:
    if "error" in antwort:
        raise OpenHABFehler(antwort["error"])
    return antwort

try:
    pruefe({"error": "Item not found."})
except OpenHABFehler as fehler:
    print("Abgefangen:", fehler)

# Kontextmanager: Datei wird garantiert geschlossen
pfad = Path("zustaende.json")
with pfad.open("w", encoding="utf-8") as datei:
    json.dump({"Wohnzimmer_Licht": "ON"}, datei)
print(json.loads(pfad.read_text(encoding="utf-8")))
pfad.unlink()
