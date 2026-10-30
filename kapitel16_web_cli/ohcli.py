#!/usr/bin/env python3
"""
Kapitel 16: ohcli – ein Kommandozeilenwerkzeug für openHAB.

  ohcli list [--typ Switch] [--tag Light]   Items auflisten
  ohcli get NAME                            Zustand lesen
  ohcli send NAME COMMAND                   Command senden
  ohcli update NAME STATE                   State melden
  ohcli watch [MUSTER]                      Änderungen live verfolgen
  ohcli history NAME [--stunden 24]         Verlauf ausgeben
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone

from openhab import Items, Persistence

from buchlib import EreignisListener, als_zahl, create_client


def cmd_list(items, args):
    for i in sorted(
        items.getItems(type=args.typ, tags=args.tag, fields="name,type,state"),
        key=lambda i: i["name"],
    ):
        print(f"{i['name']:<28} {i['type']:<22} {i['state']}")


def cmd_get(items, args):
    zustand = items.getItemState(args.name)
    if isinstance(zustand, dict):
        sys.exit(f"Fehler: {zustand.get('error')}")
    print(zustand)


def cmd_send(items, args):
    antwort = items.sendCommand(args.name, args.wert)
    if "error" in antwort:
        sys.exit(f"Fehler: {antwort['error']}")


def cmd_update(items, args):
    antwort = items.postUpdate(args.name, args.wert)
    if "error" in antwort:
        sys.exit(f"Fehler: {antwort['error']}")


def cmd_watch(items, args):
    listener = EreignisListener(
        items.client, f"openhab/items/{args.muster}/statechanged"
    )
    listener.anmelden(
        lambda e: print(
            f"{datetime.now():%H:%M:%S}  {e.name:<26} "
            f"{e.alter_wert} -> {e.wert}",
            flush=True,
        )
    )
    listener.starten()
    try:
        listener._stopp.wait()
    except KeyboardInterrupt:
        listener.stoppen()


def cmd_history(items, args):
    ende = datetime.now(timezone.utc)
    start = ende - timedelta(hours=args.stunden)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    daten = Persistence(items.client).getItemPersistenceData(
        args.name,
        args.dienst,
        start.strftime(fmt),
        ende.strftime(fmt),
        pageLength=1000,
    )
    for p in daten.get("data", []):
        zeit = datetime.fromtimestamp(p["time"] / 1000)
        print(f"{zeit:%d.%m. %H:%M}  {als_zahl(p['state'], p['state'])}")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="ohcli", description="openHAB auf der Kommandozeile"
    )
    sub = p.add_subparsers(dest="befehl", required=True)
    s = sub.add_parser("list")
    s.add_argument("--typ")
    s.add_argument("--tag")
    s.set_defaults(f=cmd_list)
    s = sub.add_parser("get")
    s.add_argument("name")
    s.set_defaults(f=cmd_get)
    s = sub.add_parser("send")
    s.add_argument("name")
    s.add_argument("wert")
    s.set_defaults(f=cmd_send)
    s = sub.add_parser("update")
    s.add_argument("name")
    s.add_argument("wert")
    s.set_defaults(f=cmd_update)
    s = sub.add_parser("watch")
    s.add_argument("muster", nargs="?", default="*")
    s.set_defaults(f=cmd_watch)
    s = sub.add_parser("history")
    s.add_argument("name")
    s.add_argument("--stunden", type=int, default=24)
    s.add_argument("--dienst", default="rrd4j")
    s.set_defaults(f=cmd_history)
    args = p.parse_args(argv)
    args.f(Items(create_client()), args)


if __name__ == "__main__":
    main()
