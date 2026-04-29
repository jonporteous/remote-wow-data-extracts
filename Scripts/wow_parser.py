from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class WeightRecord:
    eid: str
    recorded: datetime
    weight: float
    paddock: str


@dataclass
class GrowthRecord:
    eid: str
    recorded: datetime
    growth: float
    paddock: str


@dataclass
class AnimalData:
    eid: str
    weights: List[WeightRecord] = field(default_factory=list)
    growths: List[GrowthRecord] = field(default_factory=list)

    @property
    def first_weight(self) -> Optional[float]:
        return self.weights[0].weight if self.weights else None

    @property
    def last_weight(self) -> Optional[float]:
        return self.weights[-1].weight if self.weights else None

    @property
    def weight_change(self) -> Optional[float]:
        if self.first_weight is not None and self.last_weight is not None:
            return self.last_weight - self.first_weight
        return None

    @property
    def avg_growth(self) -> Optional[float]:
        vals = [g.growth for g in self.growths if g.growth is not None]
        return sum(vals) / len(vals) if vals else None

    @property
    def observation_days(self) -> Optional[int]:
        all_dates = [r.recorded for r in self.weights] + [r.recorded for r in self.growths]
        if len(all_dates) < 2:
            return None
        return (max(all_dates) - min(all_dates)).days


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    s = str(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Cannot parse datetime: {s!r}")


def _get(row, *keys, default=None):
    """Try multiple possible field names, return first match."""
    for k in keys:
        if k in row and row[k] is not None and row[k] != "":
            return row[k]
    return default


def _flatten(row: dict) -> dict:
    """Flatten Power Query style {'Column1': {'eid': ...}} or {'Column1.eid': ...} into plain keys."""
    flat = {}
    for k, v in row.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                flat[sub_k] = sub_v
        else:
            # Strip 'Column1.' prefix if present
            clean_k = k.split(".")[-1] if "." in k else k
            flat[clean_k] = v
    return flat


def parse_weights(data: list) -> List[WeightRecord]:
    records = []
    for raw in data:
        row = _flatten(raw)
        eid = _get(row, "eid")
        weight_val = _get(row, "weight", "cleansed_weight", "validated_weight")
        recorded = _get(row, "recorded", "datetime", "date_time", "timestamp")
        paddock = _get(row, "paddock_name", "paddock", "unit", default="")

        if not eid or weight_val is None or not recorded:
            continue
        try:
            w = float(weight_val)
            if w <= 0:
                continue
            records.append(WeightRecord(
                eid=str(eid).strip(),
                recorded=_parse_dt(recorded),
                weight=w,
                paddock=str(paddock),
            ))
        except (ValueError, TypeError):
            continue
    return records


def parse_growth(data: list) -> List[GrowthRecord]:
    records = []
    for raw in data:
        row = _flatten(raw)
        eid = _get(row, "eid")
        growth_val = _get(row, "growth", "reported_weight", "polynomial_regression", "value", "growth_rate")
        recorded = _get(row, "recorded", "datetime", "date_time", "timestamp")
        paddock = _get(row, "paddock_name", "paddock", "unit", default="")

        if not eid or growth_val is None or not recorded:
            continue
        try:
            records.append(GrowthRecord(
                eid=str(eid).strip(),
                recorded=_parse_dt(recorded),
                growth=float(growth_val),
                paddock=str(paddock),
            ))
        except (ValueError, TypeError):
            continue
    return records


def build_animals(weight_records: List[WeightRecord], growth_records: List[GrowthRecord]) -> List[AnimalData]:
    animals: dict[str, AnimalData] = {}

    for w in weight_records:
        if w.eid not in animals:
            animals[w.eid] = AnimalData(eid=w.eid)
        animals[w.eid].weights.append(w)

    for g in growth_records:
        if g.eid not in animals:
            animals[g.eid] = AnimalData(eid=g.eid)
        animals[g.eid].growths.append(g)

    for animal in animals.values():
        animal.weights.sort(key=lambda r: r.recorded)
        animal.growths.sort(key=lambda r: r.recorded)

    return sorted(animals.values(), key=lambda a: a.eid)
