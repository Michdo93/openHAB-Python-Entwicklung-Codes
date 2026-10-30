"""Kapitel 10: Fehler erkennen – die Bibliothek liefert Fehlerobjekte."""
from openhab import Items

from buchlib import create_client


class OpenHABFehler(Exception):
    """Wird geworfen, wenn openHAB eine Anfrage ablehnt."""


def pruefe(antwort):
    """Wandelt das Fehlerobjekt der Bibliothek in eine Ausnahme um."""
    if isinstance(antwort, dict) and "error" in antwort:
        raise OpenHABFehler(antwort["error"])
    return antwort


items = Items(create_client())

for name, command in [("Wohnzimer_Licht", "ON"),      # Tippfehler im Namen
                      ("Wohnzimmer_Licht", "HALB"),     # ungültiger Command
                      ("Flur_Haustuer", "OPEN"),        # Contact: kein Command
                      ("Wohnzimmer_Licht", "OFF")]:     # korrekt
    try:
        pruefe(items.sendCommand(name, command))
        print(f"OK      {name} <- {command}")
    except OpenHABFehler as fehler:
        print(f"FEHLER  {name} <- {command}: {fehler}")
