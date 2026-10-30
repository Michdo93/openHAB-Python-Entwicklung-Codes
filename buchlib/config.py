"""
Zentrale Verbindungskonfiguration für alle Beispiele des Buchs.

Zugangsdaten stehen NICHT im Quellcode, sondern in Umgebungsvariablen
oder in einer Datei ».env« im Wurzelverzeichnis des Repositorys:

    OPENHAB_URL=http://openhab.local:8080
    OPENHAB_TOKEN=oh.buch.xxxxxxxx           # bevorzugt
    # alternativ Basic Authentication:
    # OPENHAB_USER=admin
    # OPENHAB_PASSWORD=geheim
"""

from __future__ import annotations

import os
from pathlib import Path

from openhab import OpenHABClient

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _load_dotenv(path: Path = _ENV_FILE) -> None:
    """Liest eine einfache .env-Datei (SCHLÜSSEL=Wert) ohne Zusatzpaket."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def create_client() -> OpenHABClient:
    """Erzeugt einen OpenHABClient aus Umgebungsvariablen oder .env."""
    _load_dotenv()
    url = os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080")
    token = os.environ.get("OPENHAB_TOKEN")
    if token:
        client = OpenHABClient(url, token=token)
    else:
        client = OpenHABClient(
            url,
            username=os.environ.get("OPENHAB_USER"),
            password=os.environ.get("OPENHAB_PASSWORD"),
        )
    if not client.isLoggedIn:
        raise ConnectionError(
            f"openHAB unter {url} nicht erreichbar " "oder Anmeldung fehlgeschlagen"
        )
    return client
