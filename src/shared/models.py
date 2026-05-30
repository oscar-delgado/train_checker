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
    price: float
    provider: Provider

    def __str__(self):
        return f"{self.departure_time.isoformat()} - {self.arrival_time.isoformat()}: {self.price}€ ({self.provider.value.capitalize()})"
