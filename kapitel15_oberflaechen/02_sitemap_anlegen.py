"""Kapitel 15: Eine Sitemap per REST erzeugen – als UI-Komponente."""
import os

from openhab import OpenHABClient, Sitemaps, UI

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
ui, sitemaps = UI(client), Sitemaps(client)
UID = "buch_tablet"


def widget(art: str, item: str, **config) -> dict:
    return {"component": art, "config": {"item": item, **config}}


tablet = {
    "uid": UID, "component": "Sitemap", "config": {"label": "Tablet im Flur"},
    "slots": {"widgets": [
        {"component": "Frame", "config": {"label": "Licht"}, "slots": {"widgets": [
            widget("Switch", "Wohnzimmer_Licht", label="Decke"),
            widget("Slider", "Wohnzimmer_Dimmer", label="Leselampe"),
            widget("Switch", "gLichter", label="Alle Lichter",
                   mappings=["OFF=Alle aus"]),
        ]}},
        {"component": "Frame", "config": {"label": "Haus"}, "slots": {"widgets": [
            widget("Text", "Flur_Haustuer", label="Haustür"),
            widget("Selection", "Haus_Status", label="Modus",
                   mappings=["Alle zu Hause=Zu Hause", "Kino=Kino", "Gute Nacht=Nacht"]),
        ]}},
    ]},
}

ui.deleteUIComponent("system:sitemap", UID)            # falls schon vorhanden
print("anlegen:", ui.addUIComponent("system:sitemap", tablet)["uid"])
print("Sitemaps jetzt:", [s["name"] for s in sitemaps.getSitemaps()])

for frame in sitemaps.getSitemap(UID)["homepage"]["widgets"]:
    print(f"  {frame['label']}:", ", ".join(
        f"{w['label']} ({w['type']})" for w in frame["widgets"]))

print("UI-Komponenten:", [k["uid"] for k in ui.getUIComponents("system:sitemap")])
# Die Sitemap bleibt bestehen – 03_sitemap_ereignisse.py nutzt sie.
