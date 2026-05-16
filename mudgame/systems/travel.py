"""Shuttle state machine for interplanetary travel."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ShipState = Literal["docked", "boarding", "in_transit", "arrived"]


@dataclass(slots=True)
class ShuttleRouteMachine:
    shuttle_key: str
    current_port: str = "helion_shuttle_dock"
    destination_port: str = "vanta_shuttle_dock"
    state: ShipState = "docked"
    passengers: set[str] = field(default_factory=set)

    def can_board(self) -> bool:
        return self.state in {"docked", "boarding"}

    def can_disembark(self) -> bool:
        return self.state in {"arrived", "docked"}

    def route_label(self) -> str:
        return f"{self.current_port} -> {self.destination_port}"

    def board(self, character_key: str) -> ShipState:
        if not self.can_board():
            raise ValueError("Cannot board while shuttle is in transit.")
        self.passengers.add(character_key)
        self.state = "boarding"
        return self.state

    def begin_boarding(self) -> ShipState:
        if self.state != "docked":
            raise ValueError("Boarding can only start from docked state.")
        self.state = "boarding"
        return self.state

    def depart(self) -> ShipState:
        if self.state != "boarding":
            raise ValueError("Departure requires boarding state.")
        self.state = "in_transit"
        return self.state

    def arrive(self) -> ShipState:
        if self.state != "in_transit":
            raise ValueError("Arrival requires in_transit state.")
        self.state = "arrived"
        self.current_port, self.destination_port = self.destination_port, self.current_port
        return self.state

    def reset_docked(self) -> ShipState:
        if self.state != "arrived":
            raise ValueError("Dock reset requires arrived state.")
        self.state = "docked"
        return self.state

    def get_airlock_dock_target(self) -> str:
        """Resolve dynamic shuttle airlock destination based on state."""
        if self.state in {"docked", "boarding", "arrived"}:
            return self.current_port
        return "locked"
