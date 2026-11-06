"""
Gemeinsame Fixtures: eine Verbindung zu einem echten openHAB.

Die Integrationstests schalten Items wirklich – am besten gegen eine eigene
Testinstanz mit der Übungskonfiguration aus openhab-conf/. Adresse und Token
kommen aus OPENHAB_URL und OPENHAB_TOKEN; ist openHAB nicht erreichbar,
werden die Integrationstests übersprungen.
"""
import os
import sys
from pathlib import Path

import pytest
from openhab import OpenHABClient

# Die MVC-Anwendung aus Kapitel 17 importierbar machen (für die Unit-Tests)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "kapitel17_philosophie1"))


@pytest.fixture(scope="session")
def client():
    c = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                      token=os.environ.get("OPENHAB_TOKEN"), timeout=5)
    if not c.isLoggedIn:
        pytest.skip("openHAB nicht erreichbar – Integrationstests übersprungen")
    return c
