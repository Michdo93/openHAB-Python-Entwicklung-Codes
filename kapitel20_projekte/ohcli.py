#!/usr/bin/env python3
"""
Kapitel 20: ohcli – openHAB auf der Kommandozeile.

  ohcli info                                 Version und System
  ohcli list [--typ Switch] [--tag Light]    Items auflisten
  ohcli get NAME | send NAME CMD | update NAME STATE
  ohcli watch [MUSTER]                       Zustandsänderungen live verfolgen
  ohcli history NAME [--stunden 24] [--dienst rrd4j]
  ohcli things                               Geräte und ihr Status
  ohcli rules | run UID                      Regeln auflisten und ausführen
  ohcli sag "Schalte das Deckenlicht ein"    Text wie einen Sprachbefehl auswerten
"""
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

from openhab import (OpenHABClient, ItemEvents, Items, Persistence, Rules, Systeminfo,
                     Things, Voice, iterSSEEvents)


def pruefen(antwort):
    """Fehlerobjekte der Bibliothek in einen Exit-Code ungleich null übersetzen."""
    if isinstance(antwort, dict) and "error" in antwort:
        sys.exit(f"Fehler: {antwort['error']}")
    return antwort


def cmd_info(client, args):
    info = pruefen(Systeminfo(client).getSystemInfo())["systemInfo"]
    version = client.get("/")["runtimeInfo"]["version"]
    print(f"openHAB {version}, Java {info['javaVersion']}, "
          f"{info['osName']} {info['osVersion']}")


def cmd_list(client, args):
    for i in sorted(pruefen(Items(client).getItems(type=args.typ, tags=args.tag,
                                                   fields="name,type,state")),
                    key=lambda i: i["name"]):
        print(f"{i['name']:<28} {i['type']:<22} {i['state']}")


def cmd_get(client, args):
    print(pruefen(Items(client).getItemState(args.name)))


def cmd_send(client, args):
    pruefen(Items(client).sendCommand(args.name, args.wert, source="ohcli"))


def cmd_update(client, args):
    pruefen(Items(client).postUpdate(args.name, args.wert, source="ohcli"))


def cmd_watch(client, args):
    strom = pruefen(ItemEvents(client).ItemStateChangedEvent(args.muster))
    try:
        with strom:
            for e in iterSSEEvents(strom):
                p = e["payload"]
                print(f"{datetime.now():%H:%M:%S}  {e['topic'].split('/')[2]:<26} "
                      f"{p['oldValue']} -> {p['value']}", flush=True)
    except KeyboardInterrupt:
        pass


def cmd_history(client, args):
    ende = datetime.now(timezone.utc)
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    daten = pruefen(Persistence(client).getItemPersistenceData(
        args.name, args.dienst, iso(ende - timedelta(hours=args.stunden)), iso(ende)))
    for p in daten["data"]:
        print(f"{datetime.fromtimestamp(p['time'] / 1000):%d.%m. %H:%M}  {p['state']}")


def cmd_things(client, args):
    for t in pruefen(Things(client).getThings(summary=True)):
        s = t["statusInfo"]
        print(f"{t['UID']:<28} {s['status']:<14} {t['label']}")


def cmd_rules(client, args):
    for r in pruefen(Rules(client).getRules(summary=True)):
        print(f"{r['uid']:<20} {r['status']['status']:<14} {r['name']}")


def cmd_run(client, args):
    pruefen(Rules(client).runNow(args.uid))


def cmd_sag(client, args):
    print(pruefen(Voice(client).interpretTextBatch(args.text, ["system"], language="de")))


def main(argv=None):
    p = argparse.ArgumentParser(prog="ohcli", description="openHAB auf der Kommandozeile")
    sub = p.add_subparsers(dest="befehl", required=True)

    def befehl(name, funktion, *argumente):
        s = sub.add_parser(name)
        for a, opt in argumente:
            s.add_argument(a, **opt)
        s.set_defaults(f=funktion)

    befehl("info", cmd_info)
    befehl("list", cmd_list, ("--typ", {}), ("--tag", {}))
    befehl("get", cmd_get, ("name", {}))
    befehl("send", cmd_send, ("name", {}), ("wert", {}))
    befehl("update", cmd_update, ("name", {}), ("wert", {}))
    befehl("watch", cmd_watch, ("muster", {"nargs": "?", "default": "*"}))
    befehl("history", cmd_history, ("name", {}),
           ("--stunden", {"type": int, "default": 24}), ("--dienst", {"default": "rrd4j"}))
    befehl("things", cmd_things)
    befehl("rules", cmd_rules)
    befehl("run", cmd_run, ("uid", {}))
    befehl("sag", cmd_sag, ("text", {}))
    args = p.parse_args(argv)

    client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                           token=os.environ.get("OPENHAB_TOKEN"))
    args.f(client, args)


if __name__ == "__main__":
    main()
