"""View 2: grafische Oberfläche mit Tkinter (Standardbibliothek)."""

from __future__ import annotations

import queue
import tkinter as tk
from tkinter import ttk

from .controller import Controller
from .model import Item, ItemModel


class TkView:
    def __init__(self, model: ItemModel, controller: Controller):
        self.model, self.controller = model, controller
        self._aenderungen: "queue.Queue[Item]" = queue.Queue()
        self.root = tk.Tk()
        self.root.title("openHAB – Wohnzimmer")
        self._werte: dict[str, tk.StringVar] = {}
        model.anmelden(self)

    def aufbauen(self) -> None:
        rahmen = ttk.Frame(self.root, padding=12)
        rahmen.grid()
        for zeile, item in enumerate(self.model):
            ttk.Label(rahmen, text=item.label, width=18).grid(
                row=zeile, column=0, sticky="w"
            )
            wert = self._werte[item.name] = tk.StringVar(value=item.state)
            ttk.Label(rahmen, textvariable=wert, width=14).grid(row=zeile, column=1)
            if item.type == "Switch":
                ttk.Button(
                    rahmen,
                    text="umschalten",
                    command=lambda n=item.name: self.controller.umschalten(n),
                ).grid(row=zeile, column=2)
            elif item.type in ("Dimmer", "Rollershutter"):
                regler = ttk.Scale(rahmen, from_=0, to=100, length=140)
                regler.bind(
                    "<ButtonRelease-1>",
                    lambda e, n=item.name, r=regler: self.controller.senden(
                        n, str(round(r.get()))
                    ),
                )
                regler.grid(row=zeile, column=2)
        ttk.Button(rahmen, text="Gute Nacht",
                   command=lambda: self.controller.szene("restbuch-1")).grid(
            row=len(list(self.model)), column=2, pady=(8, 0))
        self.root.after(100, self._abarbeiten)

    def item_geaendert(self, item: Item, alt: str) -> None:
        # Wird im Thread des Ereignisstroms aufgerufen! Tk darf nur aus dem
        # Hauptthread verändert werden – deshalb nur in eine Queue legen.
        self._aenderungen.put(item)

    def _abarbeiten(self) -> None:
        while not self._aenderungen.empty():
            item = self._aenderungen.get_nowait()
            if item.name in self._werte:
                self._werte[item.name].set(item.state)
        self.root.after(100, self._abarbeiten)

    def starten(self) -> None:
        self.aufbauen()
        self.root.mainloop()
