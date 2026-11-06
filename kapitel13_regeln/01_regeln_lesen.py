"""Kapitel 13: Regeln auflisten und ihren Aufbau lesen."""
import os

from openhab import OpenHABClient, Rules

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
rules = Rules(client)

for r in rules.getRules(summary=True):
    print(f"{r['uid']:<12} {r['name']:<14} {r['status']['status']:<6} "
          f"Tags {r.get('tags', [])}")

# Der Aufbau einer Regel: Trigger, Bedingungen, Aktionen – jeweils Module
uid = "restbuch-1"
print(f"\nRegel {uid}:")
for art, module in (("Trigger", rules.getTriggers(uid)),
                    ("Bedingung", rules.getConditions(uid)),
                    ("Aktion", rules.getActions(uid))):
    for m in module:
        konfig = str(m["configuration"])
        print(f"  {art:<10} {m['id']:<7} {m['type']:<26} {konfig[:44]}…")

skript = rules.getModuleConfigParam(uid, "actions", "script", "script")
print("\nSkript der Aktion:", skript.strip().replace("\n", " | ")[:100])
