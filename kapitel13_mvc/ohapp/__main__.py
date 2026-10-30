"""Startet die MVC-Anwendung:  python -m ohapp [--gui]"""

import argparse
import logging
import threading

from openhab import Items

from buchlib import EreignisListener, create_client

from .controller import Controller
from .model import ItemModel
from .view_console import ConsoleView

WOHNZIMMER = [
    "Wohnzimmer_Licht",
    "Wohnzimmer_Dimmer",
    "Wohnzimmer_Temperatur",
    "Kueche_Rollladen",
    "Flur_Haustuer",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="openHAB-MVC-Beispiel")
    parser.add_argument(
        "--gui", action="store_true", help="Tkinter-Oberfläche starten"
    )
    parser.add_argument(
        "--demo",
        type=float,
        default=0,
        help="Konsole: nach N Sekunden beenden (für Tests)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)

    client = create_client()
    items = Items(client)
    model = ItemModel(WOHNZIMMER)  # Model
    controller = Controller(items, model)  # Controller
    ConsoleView(model)  # View 1 (immer dabei)

    listener = EreignisListener(
        client,
        topics="openhab/items/*/statechanged",
        bei_verbindung=lambda: model.laden(
            items.getItems(fields="name,type,label,state")
        ),
    )
    listener.anmelden(lambda e: model.setze_zustand(e.name, e.wert))
    listener.starten()
    listener.verbunden.wait(5)

    if args.gui:
        from .view_tk import TkView  # View 2

        TkView(model, controller).starten()
    else:
        print("Konsole aktiv – Änderungen erscheinen hier. Strg+C beendet.")
        stopp = threading.Event()
        try:
            stopp.wait(args.demo or None)
        except KeyboardInterrupt:
            pass
    listener.stoppen()


if __name__ == "__main__":
    main()
