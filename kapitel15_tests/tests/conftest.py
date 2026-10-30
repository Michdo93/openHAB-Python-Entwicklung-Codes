"""
Gemeinsame Fixtures für alle Tests.

Ist die Umgebungsvariable OPENHAB_TEST_URL gesetzt, laufen die
Integrationstests gegen diese (Test-)Instanz. Sonst startet pytest
automatisch den Mock-Server aus mock/ auf einem freien Port.
"""

import os
import sys
import threading
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "mock"), str(REPO / "kapitel13_mvc")]


@pytest.fixture(scope="session")
def openhab_url():
    if os.environ.get("OPENHAB_TEST_URL"):
        yield os.environ["OPENHAB_TEST_URL"]
        return
    from werkzeug.serving import make_server
    import mock_openhab

    mock_openhab.load_items()
    server = make_server("127.0.0.1", 0, mock_openhab.app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="session")
def client(openhab_url):
    from openhab import OpenHABClient

    token = os.environ.get("OPENHAB_TEST_TOKEN")
    c = (
        OpenHABClient(openhab_url, token=token)
        if token
        else OpenHABClient(openhab_url)
    )
    assert c.isLoggedIn, f"openHAB unter {openhab_url} nicht erreichbar"
    return c
