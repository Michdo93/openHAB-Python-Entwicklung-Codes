"""Kapitel 13: Zeitgesteuerte Regeln mit Skript-Aktion und Zeitplan-Vorschau."""
import os
import time
from datetime import datetime, timedelta

from openhab import OpenHABClient, Items, Rules

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items, rules = Items(client), Rules(client)
UID = "buch_lueften"

# Rules-DSL-Skript als Aktion: läuft werktags um 7:30 und 17:30
skript = """
val feuchte = Werkstatt_Feuchte.state
if (feuchte instanceof QuantityType
        && (feuchte as QuantityType<?>).toUnit("%").doubleValue > 60) {
    Werkstatt_Luefter.sendCommand(ON)
    Haus_Status.postUpdate("Werkstatt wird gelüftet")
}
"""
rules.deleteRule(UID)
print(rules.createRule({
    "uid": UID, "name": "Werkstatt lüften", "tags": ["Buch", "Schedule"],
    "triggers": [{"id": "morgens", "type": "timer.GenericCronTrigger",
                  "configuration": {"cronExpression": "0 30 7 ? * MON-FRI"}},
                 {"id": "abends", "type": "timer.GenericCronTrigger",
                  "configuration": {"cronExpression": "0 30 17 ? * MON-FRI"}}],
    "actions": [{"id": "skript", "type": "script.ScriptAction",
                 "configuration": {"type": "application/vnd.openhab.dsl.rule",
                                   "script": skript}}],
}))

# Wann läuft was? openHAB simuliert den Zeitplan aller Regeln mit dem Tag "Schedule"
heute = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
plan = rules.simulateSchedule((heute + timedelta(days=1)).isoformat(),
                              (heute + timedelta(days=8)).isoformat())
for eintrag in plan:
    if eintrag["rule"]["uid"] == UID:
        text = " ".join(eintrag["date"].split())          # z. B. "Nov 6, 2026, 7:30:00 AM"
        zeit = datetime.strptime(text, "%b %d, %Y, %I:%M:%S %p")
        tag = "Mo Di Mi Do Fr Sa So".split()[zeit.weekday()]
        print(f"  {tag} {zeit:%d.%m. %H:%M}  {eintrag['rule']['name']}")

# Nicht bis morgen warten: Werkstatt feucht machen und die Regel sofort ausführen
items.postUpdate("Werkstatt_Feuchte", "72 %")
rules.runNow(UID)
time.sleep(2)            # DSL-Skripte werden beim ersten Lauf übersetzt
print("Status:", items.getItemState("Haus_Status"))
print("Lüfter:", items.getItemState("Werkstatt_Luefter"),
      "(autoupdate=false: erst das Gerät bestätigt den Command, siehe Kapitel 18)")

print("löschen:", rules.deleteRule(UID))
