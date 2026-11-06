"""Kapitel 10: Fehler erkennen – die Bibliothek liefert Fehlerobjekte."""
import os

from openhab import OpenHABClient, Items

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items = Items(client)


def ist_fehler(antwort) -> bool:
    """Alle Methoden melden Ablehnungen als Dictionary mit dem Schlüssel 'error'."""
    return isinstance(antwort, dict) and "error" in antwort


for name, command in [("Wohnzimer_Licht", "ON"),      # Tippfehler im Namen
                      ("Wohnzimmer_Licht", "HALB"),     # ungültiger Command
                      ("Flur_Haustuer", "OPEN"),        # Contact: kein Command
                      ("Wohnzimmer_Licht", "OFF")]:     # korrekt
    antwort = items.sendCommand(name, command)
    if ist_fehler(antwort):
        print(f"FEHLER  {name} <- {command}: {antwort['error']}")
    else:
        print(f"OK      {name} <- {command}")

# Ein Item aus einer .items-Datei lässt sich steuern, aber nicht löschen
print("\nlöschen:", items.deleteItem("Wohnzimmer_Licht"))

# Netzwerkfehler: falsche Adresse, kurze Wartezeit
falsch = OpenHABClient("http://127.0.0.1:9", token="x", timeout=2)
print("anderer Server:", Items(falsch).getItemState("Wohnzimmer_Licht"))
