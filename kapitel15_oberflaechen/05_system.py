"""Kapitel 15: Systemdienste, Protokollierung, Zugänge und Symbole per REST."""
import os

from openhab import OpenHABClient, Auth, Iconsets, Logging, Services, Systeminfo

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
services, logging_api = Services(client), Logging(client)

# 1. Systemdienste und ihre Einstellungen (dieselben wie in der Main UI)
for s in services.getServices(language="de"):
    if s["category"] == "system":
        print(f"  {s['id']:<26} {s['label']}")
print("Regionale Einstellungen:", services.getServiceConfig("org.openhab.i18n"))

# 2. Log-Level eines Bindings zur Fehlersuche anheben – und zurücksetzen
LOGGER = "org.openhab.binding.astro"
print("\nvorher:", logging_api.getLogger(LOGGER)["loggers"][0]["level"])
logging_api.modifyOrAddLogger(LOGGER, "DEBUG")
print("jetzt: ", logging_api.getLogger(LOGGER)["loggers"][0]["level"])
logging_api.removeLogger(LOGGER)              # zurück auf den Standard
print("danach:", logging_api.getLogger(LOGGER)["loggers"][0]["level"])

# 3. Wer hat Zugang? API-Tokens und Sitzungen des angemeldeten Benutzers
for t in Auth(client).getAPITokens():
    print(f"\nToken {t['name']!r} (Bereich {t['scope']}) seit {t['createdTime'][:10]}")
print("offene Sitzungen:", len(Auth(client).getSessions()))

# 4. Symbolsätze und Maßeinheiten
print("Symbolsätze:", [i["label"] for i in Iconsets(client).getIconsets(language="de")])
einheiten = Systeminfo(client).getUoMInfo()["uomInfo"]["dimensions"]
print(f"{len(einheiten)} physikalische Größen, z. B.",
      ", ".join(f"{d['dimension']} [{d['systemUnit']}]" for d in einheiten[:5]))
