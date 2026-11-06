"""Integrationstests für Things, Regeln, Links, Persistenz und Sitemaps."""
import time
from datetime import datetime, timedelta, timezone

import pytest
from openhab import Items, Links
from openhab_test_suite import (ChannelTester, PersistenceTester, RuleTester,
                                SitemapTester, ThingTester)

pytestmark = pytest.mark.integration
SONNE = "astro:sun:zuhause"


def test_astro_thing_online(client):
    assert ThingTester(client).isThingOnline(SONNE)


def test_thing_abschalten_und_einschalten(client):
    tester = ThingTester(client)
    assert tester.disableThing(SONNE)
    assert tester.isThingUninitialized(SONNE)
    assert tester.enableThing(SONNE)
    time.sleep(2)
    assert tester.isThingOnline(SONNE)


def test_regel_gute_nacht(client):
    tester = RuleTester(client)
    assert tester.isRuleIdle("restbuch-1")
    assert tester.testRuleExecution("restbuch-1", "Haus_Status", "Nachtruhe")


def test_regel_abschalten(client):
    tester = RuleTester(client)
    assert tester.disableRule("restbuch-1") and tester.isRuleDisabled("restbuch-1")
    assert tester.enableRule("restbuch-1") and tester.isRuleActive("restbuch-1")


@pytest.fixture
def verlinktes_item(client):
    """Legt ein Item an, verknüpft es mit der Sonnenhöhe und räumt danach auf."""
    items, links = Items(client), Links(client)
    items.addOrUpdateItem("Test_Hoehe", {"type": "Number:Angle", "name": "Test_Hoehe"})
    links.linkItemToChannel("Test_Hoehe", f"{SONNE}:position#elevation", {})
    yield "Test_Hoehe"
    links.deleteAllLinks("Test_Hoehe")
    items.deleteItem("Test_Hoehe")


def test_link(client, verlinktes_item):
    tester = ChannelTester(client)
    assert tester.isItemLinkedToChannel(verlinktes_item, f"{SONNE}:position#elevation")
    assert not tester.isItemLinkedToAnyChannel("Wohnzimmer_Licht")
    assert not tester.hasOrphanedLinks()


def test_persistenz(client):
    Items(client).sendCommand("Wohnzimmer_Dimmer", "33")
    time.sleep(1)
    tester = PersistenceTester(client)
    jetzt = datetime.now(timezone.utc)
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    assert tester.isItemPersisted("inmemory", "Wohnzimmer_Dimmer")
    assert tester.hasDataInRange("inmemory", "Wohnzimmer_Dimmer",
                                 iso(jetzt - timedelta(minutes=1)), iso(jetzt))
    assert tester.checkLastPersistedState("inmemory", "Wohnzimmer_Dimmer", "33")


def test_sitemap(client):
    tester = SitemapTester(client)
    assert tester.doesSitemapExist("restbuch")
    assert tester.doesSitemapContainItem("restbuch", "Werkstatt_Luefter")
    assert not tester.doesSitemapContainItem("restbuch", "Gibt_es_nicht")
