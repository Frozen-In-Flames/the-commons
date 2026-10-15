"""the-commons: Post class.

USPS's one job: every address is reachable. This class is the nation's
address registry plus a route optimizer: addresses are registered with a
locality and a delivery point type, the optimizer groups them by locality
into delivery routes, and coverage reports the share of addresses on an
active route. It records and routes; it does not carry the mail. Delivery
is a separate job.
"""

import datetime
import json
import os

SOURCE_LABEL = "nation address registry"

POINT_TYPES = ("residential", "business", "po_box")


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Post:
    """Address registry with locality-based route optimization."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "addresses.json")
        self._rpath = os.path.join(data_dir, "routes.json")
        self._load()

    # -- persistence ----------------------------------------------------
    def _load(self):
        if os.path.exists(self._path):
            with open(self._path) as f:
                self.addresses_doc = json.load(f)
        else:
            self.addresses_doc = {"source": SOURCE_LABEL, "addresses": []}
        if os.path.exists(self._rpath):
            with open(self._rpath) as f:
                self.routes_doc = json.load(f)
        else:
            self.routes_doc = {"source": SOURCE_LABEL, "routes": []}

    def _save(self):
        with open(self._path, "w") as f:
            json.dump(self.addresses_doc, f, indent=2)
        with open(self._rpath, "w") as f:
            json.dump(self.routes_doc, f, indent=2)

    # -- address registry -----------------------------------------------
    def register_address(self, addr_id, locality, point_type):
        """Register one delivery address.

        point_type is one of: residential, business, po_box.
        Returns the record.
        """
        if point_type not in POINT_TYPES:
            raise ValueError("point_type must be one of %s" % (POINT_TYPES,))
        if any(a["id"] == addr_id for a in self.addresses_doc["addresses"]):
            raise ValueError("address %s already registered" % addr_id)
        rec = {
            "id": addr_id,
            "locality": locality,
            "point_type": point_type,
            "registered_at": _utcnow(),
        }
        self.addresses_doc["addresses"].append(rec)
        self._save()
        return rec

    def addresses(self, locality=None):
        """List registered addresses, optionally filtered by locality."""
        addrs = self.addresses_doc["addresses"]
        if locality is not None:
            addrs = [a for a in addrs if a["locality"] == locality]
        return list(addrs)

    # -- route optimizer --------------------------------------------------
    @staticmethod
    def _route_id(locality):
        slug = "".join(c if c.isalnum() else "-" for c in locality.lower())
        return "R-" + slug.strip("-")

    def build_routes(self):
        """Group addresses by locality into one route per locality.

        Existing routes are kept; new localities get new routes. Returns
        the list of routes.
        """
        existing = {r["id"] for r in self.routes_doc["routes"]}
        by_locality = {}
        for a in self.addresses_doc["addresses"]:
            by_locality.setdefault(a["locality"], []).append(a["id"])
        for locality, members in sorted(by_locality.items()):
            rid = self._route_id(locality)
            if rid not in existing:
                self.routes_doc["routes"].append({
                    "id": rid,
                    "locality": locality,
                    "addresses": sorted(members),
                    "active": True,
                    "built_at": _utcnow(),
                })
                existing.add(rid)
        self._save()
        return self.routes()

    def routes(self, active_only=False):
        """List delivery routes."""
        routes = self.routes_doc["routes"]
        if active_only:
            routes = [r for r in routes if r["active"]]
        return list(routes)

    def set_route_active(self, route_id, active):
        """Activate or deactivate a route. Returns the route."""
        for r in self.routes_doc["routes"]:
            if r["id"] == route_id:
                r["active"] = bool(active)
                self._save()
                return r
        raise ValueError("unknown route %s" % route_id)

    # -- coverage ---------------------------------------------------------
    def coverage(self):
        """Share of registered addresses on an active route.

        Returns {"total_addresses", "routed_addresses", "coverage"} where
        coverage is a float in [0, 1], or None when no addresses exist.
        """
        total = len(self.addresses_doc["addresses"])
        if total == 0:
            return {"total_addresses": 0, "routed_addresses": 0,
                    "coverage": None}
        routed_ids = set()
        for r in self.routes_doc["routes"]:
            if r["active"]:
                routed_ids.update(r["addresses"])
        registered = {a["id"] for a in self.addresses_doc["addresses"]}
        routed = len(routed_ids & registered)
        return {"total_addresses": total, "routed_addresses": routed,
                "coverage": routed / total}
