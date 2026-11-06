"""Startet die MVC-Anwendung:  python -m ohapp [--gui] [--demo SEKUNDEN]"""

import argparse
import logging
import os
import threading
import time

from openhab import OpenHABClient, Events, Items, Rules, iterSSEEvents

from .controller import Controller
from .model import ItemModel
from .view_console import ConsoleView

WOHNZIMMER = ["Wohnzimmer_Licht", "Wohnzimmer_Dimmer", "Wohnzimmer_Temperatur",
              "Kueche_Rollladen", "Flur_Haustuer", "Haus_Status"]


def ereignisse_lesen(client: OpenHABClient, model: ItemModel,
                     verbunden: threading.Event) -> None:
    """Hintergrund-Thread: Momentaufnahme laden, dann jedem statechanged folgen."""
    items = Items(client)
    while True:
        strom = Events(client).getEvents("openhab/items/*/statechanged")
        if isinstance(strom, dict):                         # openHAB nicht erreichbar
            logging.warning("Ereignisstrom: %s", strom["error"])
            time.sleep(5)
            continue
        model.laden(items.getItems(fields="name,type,label,state"))   # Momentaufnahme
        verbunden.set()
        try:
            for e in iterSSEEvents(strom):
                model.setze_zustand(e["topic"].split("/")[2], e["payload"]["value"])
        except Exception as fehler:                         # Abbruch: neu verbinden
            logging.warning("Ereignisstrom unterbrochen: %s", fehler)
        verbunden.clear()
        time.sleep(2)


def demo(controller: Controller) -> None:
    """Spielt einen Benutzer, der ein paar Knöpfe drückt (für --demo)."""
    for schritt in (lambda: controller.umschalten("Wohnzimmer_Licht"),
                    lambda: controller.senden("Wohnzimmer_Dimmer", "70"),
                    lambda: controller.senden("Kueche_Rollladen", "50"),
                    lambda: controller.szene("restbuch-1")):
        time.sleep(1)
        schritt()


def main() -> None:
    parser = argparse.ArgumentParser(description="openHAB-MVC-Beispiel")
    parser.add_argument("--gui", action="store_true", help="Tkinter-Oberfläche starten")
    parser.add_argument("--demo", type=float, default=0,
                        help="Konsole: Knöpfe automatisch drücken, nach N s beenden")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)

    client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                           token=os.environ.get("OPENHAB_TOKEN"))
    model = ItemModel(WOHNZIMMER)                                    # Model
    controller = Controller(Items(client), Rules(client), model)     # Controller
    ConsoleView(model)                                               # View 1

    verbunden = threading.Event()
    threading.Thread(target=ereignisse_lesen, args=(client, model, verbunden),
                     daemon=True).start()
    verbunden.wait(5)

    if args.gui:
        from .view_tk import TkView                                  # View 2
        TkView(model, controller).starten()
    else:
        print("Konsole aktiv – Änderungen erscheinen hier. Strg+C beendet.")
        if args.demo:
            threading.Thread(target=demo, args=(controller,), daemon=True).start()
        try:
            threading.Event().wait(args.demo or None)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
