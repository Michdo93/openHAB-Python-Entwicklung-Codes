"""
Kapitel 17: Eine Brücke zwischen ROS 2 und openHAB (rclpy).

  openHAB -> ROS 2:  jede Zustandsänderung eines freigegebenen Items wird
                     auf /openhab/<Item>/state (std_msgs/String) veröffentlicht.
  ROS 2 -> openHAB:  Nachrichten auf /openhab/<Item>/command werden als
                     Command gesendet (Philosophie 1).
  Roboter -> openHAB: der Akkustand (sensor_msgs/BatteryState) wird als
                     State eines eigenen Items gemeldet (Philosophie 2).

Start (ROS 2 Jazzy/Lyrical auf Ubuntu, Workspace gesourct):
  python3 openhab_bridge.py --ros-args \
      -p items:="['Wohnzimmer_Licht','Kueche_Rollladen']"
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from std_msgs.msg import String

from openhab import Items

from buchlib import Ereignis, EreignisListener, create_client

AKKU_ITEM = "Roboter_Akku"


class OpenHABBridge(Node):
    def __init__(self) -> None:
        super().__init__("openhab_bridge")
        self.declare_parameter("items", ["Wohnzimmer_Licht", "Kueche_Rollladen"])
        self.freigegeben: list[str] = self.get_parameter("items").value

        client = create_client()
        self.items = Items(client)
        self._akku_item_anlegen()

        # ROS-Publisher und -Subscriber je Item
        self.pubs = {
            n: self.create_publisher(String, f"/openhab/{n}/state", 10)
            for n in self.freigegeben
        }
        for name in self.freigegeben:
            self.create_subscription(
                String,
                f"/openhab/{name}/command",
                lambda msg, n=name: self._command(n, msg),
                10,
            )
        self.create_subscription(BatteryState, "/battery_state", self._akku, 10)

        # Ereignisstrom von openHAB (läuft in eigenem Thread)
        self.listener = EreignisListener(
            client,
            "openhab/items/*/statechanged",
            bei_verbindung=self._momentaufnahme,
        )
        self.listener.anmelden(self._state)
        self.listener.starten()
        self.get_logger().info(f"Brücke aktiv für {self.freigegeben}")

    def _akku_item_anlegen(self) -> None:
        """Philosophie 2: das Roboter-Item bei Bedarf selbst anlegen (CRUD)."""
        if "error" in self.items.getItem(AKKU_ITEM):
            self.items.addOrUpdateItem(
                AKKU_ITEM,
                {
                    "type": "Number:Dimensionless",
                    "name": AKKU_ITEM,
                    "label": "Roboter Akku",
                    "category": "battery",
                    "tags": ["Measurement", "Energy"],
                    "groupNames": ["gHaus"],
                },
            )

    def _momentaufnahme(self) -> None:
        for name in self.freigegeben:
            self.pubs[name].publish(String(data=str(self.items.getItemState(name))))

    def _state(self, e: Ereignis) -> None:
        if e.name in self.pubs:
            self.pubs[e.name].publish(String(data=e.wert))

    def _command(self, name: str, msg: String) -> None:
        self.get_logger().info(f"Command {name} <- {msg.data}")
        self.items.sendCommand(name, msg.data)

    def _akku(self, msg: BatteryState) -> None:
        if msg.percentage == msg.percentage:  # nicht NaN
            self.items.postUpdate(AKKU_ITEM, f"{msg.percentage * 100:.0f}")

    def destroy_node(self) -> None:
        self.listener.stoppen()
        super().destroy_node()


def main() -> None:
    rclpy.init()
    node = OpenHABBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
