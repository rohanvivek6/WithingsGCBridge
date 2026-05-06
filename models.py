import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class Measurement:
    datetime: datetime.datetime
    weight: float
    percent_fat: Optional[float]
    muscle_mass: Optional[float]
    bone_mass: Optional[float] = None
