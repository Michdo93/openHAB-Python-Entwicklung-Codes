"""
Kapitel 15: Vorab-Test vor einer Roboterfahrt durch das Smart Home.

Prüft in Sekunden alles, was der zehnminütige Ablauf voraussetzt, und
liefert den Exit-Code 0 (alles bereit) oder 1 (nicht losfahren!).
Ideal als ExecStartPre= in einer systemd-Unit oder als CI-Schritt.
"""

import sys

from openhab_test_suite import ItemTester, RuleTester, ThingTester

from buchlib import create_client

ABLAUF = {  # was der Roboter braucht
    "items": {
        "Kueche_Rollladen": "Rollershutter",
        "Wohnzimmer_Licht": "Switch",
        "Wohnzimmer_Dimmer": "Dimmer",
        "Haus_Status": "String",
    },
    "things": ["mqtt:topic:mosquitto:werkstatt", "astro:sun:zuhause"],
    "regeln": ["restbuch-1"],
}


def main() -> int:
    client = create_client()
    it, tt = ItemTester(client), ThingTester(client)
    rules = {r["uid"] for r in __import__("openhab").Rules(client).getRules()}
    fehler = []

    for name, typ in ABLAUF["items"].items():
        if not it.doesItemExist(name):
            fehler.append(f"Item fehlt: {name}")
        elif not it.checkItemIsType(name, typ):
            fehler.append(f"Item {name} ist kein {typ}")
    for uid in ABLAUF["things"]:
        if not tt.isThingOnline(uid):
            fehler.append(f"Thing nicht ONLINE: {uid}")
    for uid in ABLAUF["regeln"]:
        if uid not in rules:
            fehler.append(f"Regel fehlt: {uid}")

    print("\n" + "=" * 50)
    if fehler:
        print("NICHT BEREIT:\n  " + "\n  ".join(fehler))
        return 1
    print(
        f"BEREIT – {len(ABLAUF['items'])} Items, {len(ABLAUF['things'])} Things, "
        f"{len(ABLAUF['regeln'])} Regel(n) geprüft"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
