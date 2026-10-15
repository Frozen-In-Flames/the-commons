"""the-commons: Grid class.

Energy's one job: the power stays on. This class is the nation's grid
status monitor: generators are registered with name, fuel type, capacity
in MW, and status; load observations record demand in MW with a
timestamp; the supply/demand readout compares the latest demand against
committed capacity (online generators) and flags shortfall risk when
demand approaches it. It monitors and flags; it does not run power
plants. Generation is a separate job.
"""

import datetime
import json
import os

SOURCE_LABEL = "nation grid registry"

STATUSES = ("online", "offline", "maintenance")
FUELS = ("solar", "wind", "hydro", "gas", "coal", "nuclear", "geothermal",
         "battery", "other")

# Demand at or above this share of committed capacity is flagged AT RISK.
RISK_THRESHOLD = 0.9


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Grid:
    """Grid status monitor: generators, load observations, readout."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._gpath = os.path.join(data_dir, "generators.json")
        self._lpath = os.path.join(data_dir, "loads.json")
        self._load()

    # -- persistence ----------------------------------------------------
    def _load(self):
        if os.path.exists(self._gpath):
            with open(self._gpath) as f:
                self.gen_doc = json.load(f)
        else:
            self.gen_doc = {"source": SOURCE_LABEL, "generators": []}
        if os.path.exists(self._lpath):
            with open(self._lpath) as f:
                self.load_doc = json.load(f)
        else:
            self.load_doc = {"source": SOURCE_LABEL, "loads": []}

    def _save(self):
        with open(self._gpath, "w") as f:
            json.dump(self.gen_doc, f, indent=2)
        with open(self._lpath, "w") as f:
            json.dump(self.load_doc, f, indent=2)

    # -- generators -------------------------------------------------------
    def add_generator(self, name, fuel_type, capacity_mw, status="online"):
        """Register a generator. capacity_mw must be positive."""
        if fuel_type not in FUELS:
            raise ValueError("fuel_type must be one of %s" % (FUELS,))
        if status not in STATUSES:
            raise ValueError("status must be one of %s" % (STATUSES,))
        capacity_mw = float(capacity_mw)
        if capacity_mw <= 0:
            raise ValueError("capacity_mw must be positive")
        if any(g["name"] == name for g in self.gen_doc["generators"]):
            raise ValueError("generator %s already registered" % name)
        rec = {
            "name": name,
            "fuel_type": fuel_type,
            "capacity_mw": capacity_mw,
            "status": status,
            "registered_at": _utcnow(),
        }
        self.gen_doc["generators"].append(rec)
        self._save()
        return rec

    def set_generator_status(self, name, status):
        """Change a generator's status. Returns the record."""
        if status not in STATUSES:
            raise ValueError("status must be one of %s" % (STATUSES,))
        for g in self.gen_doc["generators"]:
            if g["name"] == name:
                g["status"] = status
                self._save()
                return g
        raise ValueError("unknown generator %s" % name)

    def generators(self, status=None):
        """List generators, optionally filtered by status."""
        gens = self.gen_doc["generators"]
        if status is not None:
            gens = [g for g in gens if g["status"] == status]
        return list(gens)

    def committed_capacity_mw(self):
        """Total MW of generators currently online."""
        return sum(g["capacity_mw"]
                   for g in self.gen_doc["generators"]
                   if g["status"] == "online")

    # -- load observations --------------------------------------------------
    def record_load(self, demand_mw, timestamp=None):
        """Record one demand observation in MW. Returns the record."""
        demand_mw = float(demand_mw)
        if demand_mw < 0:
            raise ValueError("demand_mw cannot be negative")
        rec = {"demand_mw": demand_mw,
               "observed_at": timestamp or _utcnow()}
        self.load_doc["loads"].append(rec)
        self._save()
        return rec

    def loads(self):
        """List load observations in recorded order."""
        return list(self.load_doc["loads"])

    # -- supply/demand readout ----------------------------------------------
    def readout(self):
        """Compare latest demand against committed capacity.

        Returns {"committed_mw", "demand_mw", "margin_mw", "status"}
        where status is one of: OK, AT RISK (demand at or above 90% of
        committed capacity), SHORTFALL (demand at or above committed
        capacity), or NO DATA when there are no load observations.
        """
        loads = self.load_doc["loads"]
        committed = self.committed_capacity_mw()
        if not loads:
            return {"committed_mw": committed, "demand_mw": None,
                    "margin_mw": None, "status": "NO DATA"}
        demand = loads[-1]["demand_mw"]
        margin = committed - demand
        if demand >= committed:
            status = "SHORTFALL"
        elif committed > 0 and demand >= RISK_THRESHOLD * committed:
            status = "AT RISK"
        else:
            status = "OK"
        return {"committed_mw": committed, "demand_mw": demand,
                "margin_mw": margin, "status": status}
