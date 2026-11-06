"""Kapitel 15: Änderungen auf einer Sitemap-Seite live verfolgen."""
import os
import threading
import time

from openhab import OpenHABClient, Items, Sitemaps, UI, iterSSELines, parseSSEData

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
sitemaps, items = Sitemaps(client), Items(client)
SITEMAP = "buch_tablet"                    # aus 02_sitemap_anlegen.py
fertig = threading.Event()

# 1. Abonnement anlegen und an eine Seite binden: die Seite einmal mit der ID abrufen
abo = sitemaps.subscribeToSitemapEvents()["subscriptionID"]
seite = sitemaps.getSitemapPage(SITEMAP, SITEMAP, subscriptionID=abo)
print(f"Abonnement {abo[:8]}… für Seite »{seite['title']}«")


def schalten() -> None:
    """Läuft parallel und ändert Items, die auf der Seite zu sehen sind."""
    time.sleep(1)
    dimmer = items.getItemState("Wohnzimmer_Dimmer")
    items.sendCommand("Wohnzimmer_Dimmer", "35" if dimmer != "35" else "65")
    tuer = items.getItemState("Flur_Haustuer")
    items.postUpdate("Flur_Haustuer", "CLOSED" if tuer == "OPEN" else "OPEN")
    time.sleep(1)
    fertig.set()
    items.postUpdate("Flur_Haustuer", tuer)        # letztes Ereignis weckt die Schleife


# 2. Den Ereignisstrom der Seite öffnen. Achtung: openHAB antwortet erst mit dem
#    ersten Ereignis – deshalb muss der Thread, der etwas ändert, schon laufen.
threading.Thread(target=schalten, daemon=True).start()
strom = sitemaps.getSitemapEvents(abo, SITEMAP, SITEMAP)
with strom:
    for zeile in iterSSELines(strom):
        e = parseSSEData(zeile)            # Sitemap-Ereignisse haben kein "topic"
        if e and e.get("widgetId"):
            zustand = e["item"]["state"]
            print(f"  Widget {e['widgetId']:<5} {e['label']:<24} Zustand {zustand}")
        if fertig.is_set():
            break

print("Sitemap löschen:", UI(client).deleteUIComponent("system:sitemap", SITEMAP))
