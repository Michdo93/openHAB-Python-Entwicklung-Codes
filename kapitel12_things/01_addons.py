"""Kapitel 12: Welche Add-ons sind installiert, welche gibt es?"""
import os
from collections import Counter

from openhab import OpenHABClient, Addons

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
addons = Addons(client)

alle = addons.getAddons(language="de")
installiert = [a for a in alle if a.get("installed")]
print(f"{len(alle)} Add-ons verfügbar, {len(installiert)} installiert:")
for a in sorted(installiert, key=lambda a: a["uid"]):
    print(f"  {a['uid']:<24} {a['version']:<8} {a['label']}")

print("\nVerfügbar nach Art:", dict(Counter(a["type"] for a in alle)))

astro = addons.getAddon("binding-astro", language="de")
print(f"\n{astro['label']}: {astro['description'][:90]}…")
print("Logger-Pakete:", astro["loggerPackages"])
print("Installationsquellen:", [s["id"] for s in addons.getAddonServices()])
