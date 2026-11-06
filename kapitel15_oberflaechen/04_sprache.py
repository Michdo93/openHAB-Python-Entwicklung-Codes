"""Kapitel 15: Text wie einen Sprachbefehl auswerten lassen – ohne Mikrofon."""
import os
import time

from openhab import OpenHABClient, Audio, Items, Services, Voice

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
voice, items, services = Voice(client), Items(client), Services(client)

for i in voice.getInterpreters(language="de"):
    print(f"Interpreter {i['id']:<8} {i['label']:<26} Sprachen {i['locales']}")
print("Audio-Ausgänge:", [s["id"] for s in Audio(client).getSinks()])

# Den eingebauten Interpreter zum Standard machen – eine Systemeinstellung
config = services.getServiceConfig("org.openhab.voice")
config["defaultHLI"] = "system"
services.updateServiceConfig("org.openhab.voice", config)
print("Standard-Interpreter:", services.getServiceConfig("org.openhab.voice")["defaultHLI"])

# Er erkennt Items an ihrem Label und antwortet in der gewählten Sprache
items.sendCommand("Wohnzimmer_Licht", "OFF")
items.sendCommand("Wohnzimmer_Dimmer", "60")
for satz in ("Schalte das Deckenlicht ein",
             "Schalte das Deckenlicht ein",
             "Schalte die Leselampe aus",
             "Mach mir einen Kaffee"):
    antwort = voice.interpretText(satz, language="de")
    if isinstance(antwort, dict):
        antwort = antwort.get("error", antwort).rsplit("(", 1)[-1].rstrip(")")
    print(f"  »{satz}« -> {antwort}")
time.sleep(0.5)
print("Deckenlicht:", items.getItemState("Wohnzimmer_Licht"),
      "| Leselampe:", items.getItemState("Wohnzimmer_Dimmer"))

# Einen bestimmten Interpreter wählen, unabhängig vom Standard
print(voice.interpretTextBatch("turn off the Deckenlicht", ["system"], language="en"))
