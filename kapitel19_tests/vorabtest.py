"""
Kapitel 19: Vorab-Test, bevor eine Anwendung startet.

Prüft in Sekunden alles, was das Dashboard aus Kapitel 17 und das virtuelle
Gerät aus Kapitel 18 voraussetzen, und liefert den Exit-Code 0 (bereit) oder
1 (nicht starten!). Ideal als ExecStartPre= in einer systemd-Unit oder als
Schritt in einer CI-Pipeline.
"""
import os
import sys

from openhab import OpenHABClient
from openhab_test_suite import (ItemTester, PersistenceTester, RuleTester, SitemapTester,
                                ThingTester)

ERWARTET = {
    "items": {"Wohnzimmer_Licht": "Switch", "Wohnzimmer_Dimmer": "Dimmer",
              "Kueche_Rollladen": "Rollershutter", "Werkstatt_Luefter": "Switch",
              "Werkstatt_Temperatur": "Number:Temperature", "Haus_Status": "String"},
    "things": ["astro:sun:zuhause"],
    "regeln": ["restbuch-1"],
    "sitemap": ("restbuch", ["Werkstatt_Luefter", "Wohnzimmer_Licht"]),
    "persistenz": ("inmemory", "Wohnzimmer_Dimmer"),
}


def main() -> int:
    client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                           token=os.environ.get("OPENHAB_TOKEN"), timeout=5)
    if not client.isLoggedIn:
        print("NICHT BEREIT: openHAB nicht erreichbar")
        return 1
    it, tt, rt, st = (ItemTester(client), ThingTester(client), RuleTester(client),
                      SitemapTester(client))
    fehler = []
    for name, typ in ERWARTET["items"].items():
        if not it.doesItemExist(name):
            fehler.append(f"Item fehlt: {name}")
        elif not it.checkItemIsType(name, typ):
            fehler.append(f"Item {name} ist kein {typ}")
    fehler += [f"Thing nicht ONLINE: {uid}" for uid in ERWARTET["things"]
               if not tt.isThingOnline(uid)]
    fehler += [f"Regel nicht bereit: {uid}" for uid in ERWARTET["regeln"]
               if not rt.isRuleIdle(uid)]
    sitemap, namen = ERWARTET["sitemap"]
    fehler += [f"Sitemap {sitemap} zeigt {n} nicht" for n in namen
               if not st.doesSitemapContainItem(sitemap, n)]
    dienst, item = ERWARTET["persistenz"]
    if not PersistenceTester(client).isItemPersisted(dienst, item):
        fehler.append(f"{item} wird in {dienst} nicht gespeichert")

    print("=" * 50)
    if fehler:
        print("NICHT BEREIT:\n  " + "\n  ".join(fehler))
        return 1
    print(f"BEREIT – {len(ERWARTET['items'])} Items, {len(ERWARTET['things'])} Thing, "
          f"{len(ERWARTET['regeln'])} Regel, Sitemap und Persistenz geprüft")
    return 0


if __name__ == "__main__":
    sys.exit(main())
