"""the-commons: Spectrum class.

The FCC's one job: signals don't jam each other. This class is the
nation's spectrum allocation registry: allocations record a band, a
licensee, a purpose, and a region, and the overlap detector flags any
two allocations in the same band and region held by different
licensees. It records and flags; it does not police the airwaves.
Enforcement is a separate job.
"""

import datetime
import json
import os

SOURCE_LABEL = "nation spectrum registry"


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _norm(s):
    return s.strip().lower()


class Spectrum:
    """Spectrum allocation registry with overlap detection."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "allocations.json")
        self._load()

    # -- persistence ----------------------------------------------------
    def _load(self):
        if os.path.exists(self._path):
            with open(self._path) as f:
                self.doc = json.load(f)
        else:
            self.doc = {"source": SOURCE_LABEL, "allocations": []}

    def _save(self):
        with open(self._path, "w") as f:
            json.dump(self.doc, f, indent=2)

    def _next_id(self):
        existing = {a["id"] for a in self.doc["allocations"]}
        n = 1
        while "A-%d" % n in existing:
            n += 1
        return "A-%d" % n

    # -- allocation registry ----------------------------------------------
    def allocate(self, band, licensee, purpose, region):
        """Register one spectrum allocation. Returns the record."""
        for field, value in (("band", band), ("licensee", licensee),
                             ("purpose", purpose), ("region", region)):
            if not value or not value.strip():
                raise ValueError("%s must not be empty" % field)
        rec = {
            "id": self._next_id(),
            "band": band.strip(),
            "licensee": licensee.strip(),
            "purpose": purpose.strip(),
            "region": region.strip(),
            "allocated_at": _utcnow(),
        }
        self.doc["allocations"].append(rec)
        self._save()
        return rec

    def allocations(self, region=None):
        """List allocations, optionally filtered by region."""
        allocs = self.doc["allocations"]
        if region is not None:
            allocs = [a for a in allocs
                      if _norm(a["region"]) == _norm(region)]
        return list(allocs)

    def revoke(self, alloc_id):
        """Remove an allocation. Returns True if it existed."""
        before = len(self.doc["allocations"])
        self.doc["allocations"] = [a for a in self.doc["allocations"]
                                   if a["id"] != alloc_id]
        self._save()
        return len(self.doc["allocations"]) < before

    # -- overlap detector ---------------------------------------------------
    def overlaps(self):
        """Flag allocations sharing a band and region across licensees.

        Returns a list of {"band", "region", "allocations": [ids]} groups
        where two or more allocations in the same normalized band and
        region are held by different licensees.
        """
        groups = {}
        for a in self.doc["allocations"]:
            key = (_norm(a["band"]), _norm(a["region"]))
            groups.setdefault(key, []).append(a)
        hits = []
        for (band, region), allocs in sorted(groups.items()):
            licensees = {_norm(a["licensee"]) for a in allocs}
            if len(allocs) >= 2 and len(licensees) >= 2:
                hits.append({
                    "band": allocs[0]["band"],
                    "region": allocs[0]["region"],
                    "allocations": [a["id"] for a in allocs],
                    "licensees": sorted({a["licensee"] for a in allocs}),
                })
        return hits
