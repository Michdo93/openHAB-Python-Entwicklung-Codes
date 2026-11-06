"""Kapitel 13: Welche Bausteine kennt die Regel-Engine? Modultypen und Vorlagen."""
import os
from collections import defaultdict

from openhab import OpenHABClient, ModuleTypes, Templates

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
module = ModuleTypes(client)

nach_art = defaultdict(list)
for m in module.getModuleTypes(language="de"):
    if m.get("visibility") == "VISIBLE" and "#" not in m["uid"]:   # ohne Thing-Actions
        art = "Trigger" if "Trigger" in m["uid"] else \
              "Bedingung" if "Condition" in m["uid"] else "Aktion"
        nach_art[art].append(m)

for art in ("Trigger", "Bedingung", "Aktion"):
    print(f"{art} ({len(nach_art[art])}):")
    for m in sorted(nach_art[art], key=lambda m: m["uid"])[:7]:
        print(f"  {m['uid']:<30} {m['label']}")

typ = module.getModuleType("core.ItemCommandAction", language="de")
print(f"\n{typ['uid']} – {typ['description']}")
for p in typ["configDescriptions"]:
    pflicht = "Pflicht" if p.get("required") else "optional"
    print(f"  {p['name']:<10} {p['type']:<6} {pflicht:<8} {p['label']}")

vorlagen = Templates(client).getTemplates(language="de")
print(f"\nRegelvorlagen installiert: {len(vorlagen)}")
