from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Provider(str, Enum):
    IRYO = "iryo"
    OUIGO = "ouigo"
    RENFE = "renfe"


@dataclass
class Train:
    service_id: int | None
    departure_time: datetime
    arrival_time: datetime
    price: float | None
    provider: Provider

    def __str__(self):
        departure = self.departure_time.isoformat()
        arrival = self.arrival_time.isoformat()
        provider = self.provider.capitalize()
        return f"{departure} - {arrival}: {self.price}€ ({provider})"

    def __lt__(self, other):
        self_key = float("inf") if self.price is None else self.price
        other_key = float("inf") if other.price is None else other.price
        return self_key < other_key
