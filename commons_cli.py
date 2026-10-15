#!/usr/bin/env python3
"""the-commons CLI: infrastructure core for a new nation.

Subcommands:
  post register --id ID --locality LOC --type TYPE
                 TYPE in: residential, business, po_box
  post addresses [--locality LOC]
  post routes [--active]
  post build-routes
  post deactivate --route RID
  post activate --route RID
  post coverage
  grid add-gen --name NAME --fuel FUEL --capacity MW [--status S]
               FUEL in: solar, wind, hydro, gas, coal, nuclear,
               geothermal, battery, other
               S in: online, offline, maintenance
  grid set-status --name NAME --status S
  grid generators [--status S]
  grid load --demand MW [--at ISO]
  grid loads
  grid readout
  spectrum allocate --band BAND --licensee L --purpose P --region R
  spectrum allocations [--region R]
  spectrum overlaps
  spectrum revoke --id A-ID

Global: --data-dir DIR (default: data/)
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from post import Post, POINT_TYPES
from grid import Grid, STATUSES, FUELS
from spectrum import Spectrum


def _pct(x):
    return "n/a" if x is None else "%.1f%%" % (100 * x)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="commons_cli.py",
                                 description="the-commons: infrastructure core")
    ap.add_argument("--data-dir", default="data/",
                    help="registry storage directory")
    sub = ap.add_subparsers(dest="area", required=True)

    # -- post -----------------------------------------------------------
    post = sub.add_parser("post")
    psub = post.add_subparsers(dest="cmd", required=True)

    p = psub.add_parser("register")
    p.add_argument("--id", required=True)
    p.add_argument("--locality", required=True)
    p.add_argument("--type", required=True, choices=list(POINT_TYPES))

    p = psub.add_parser("addresses")
    p.add_argument("--locality", default=None)

    p = psub.add_parser("routes")
    p.add_argument("--active", action="store_true")

    psub.add_parser("build-routes")

    p = psub.add_parser("deactivate")
    p.add_argument("--route", required=True)

    p = psub.add_parser("activate")
    p.add_argument("--route", required=True)

    psub.add_parser("coverage")

    # -- grid -----------------------------------------------------------
    grid = sub.add_parser("grid")
    gsub = grid.add_subparsers(dest="cmd", required=True)

    p = gsub.add_parser("add-gen")
    p.add_argument("--name", required=True)
    p.add_argument("--fuel", required=True, choices=list(FUELS))
    p.add_argument("--capacity", required=True, type=float)
    p.add_argument("--status", default="online", choices=list(STATUSES))

    p = gsub.add_parser("set-status")
    p.add_argument("--name", required=True)
    p.add_argument("--status", required=True, choices=list(STATUSES))

    p = gsub.add_parser("generators")
    p.add_argument("--status", default=None, choices=list(STATUSES))

    p = gsub.add_parser("load")
    p.add_argument("--demand", required=True, type=float)
    p.add_argument("--at", default=None)

    gsub.add_parser("loads")
    gsub.add_parser("readout")

    # -- spectrum -------------------------------------------------------
    spec = sub.add_parser("spectrum")
    ssub = spec.add_subparsers(dest="cmd", required=True)

    p = ssub.add_parser("allocate")
    p.add_argument("--band", required=True)
    p.add_argument("--licensee", required=True)
    p.add_argument("--purpose", required=True)
    p.add_argument("--region", required=True)

    p = ssub.add_parser("allocations")
    p.add_argument("--region", default=None)

    ssub.add_parser("overlaps")

    p = ssub.add_parser("revoke")
    p.add_argument("--id", required=True)

    args = ap.parse_args(argv)

    if args.area == "post":
        cls = Post(args.data_dir)
        if args.cmd == "register":
            r = cls.register_address(args.id, args.locality, args.type)
            print("registered address %s in %s (%s)"
                  % (r["id"], r["locality"], r["point_type"]))
        elif args.cmd == "addresses":
            for a in cls.addresses(args.locality):
                print("%s | %s | %s" % (a["id"], a["locality"],
                                        a["point_type"]))
        elif args.cmd == "routes":
            for r in cls.routes(active_only=args.active):
                print("%s | %s | addresses=%d | %s"
                      % (r["id"], r["locality"], len(r["addresses"]),
                         "active" if r["active"] else "inactive"))
        elif args.cmd == "build-routes":
            for r in cls.build_routes():
                print("route %s covers %s (%d addresses)"
                      % (r["id"], r["locality"], len(r["addresses"])))
        elif args.cmd == "deactivate":
            cls.set_route_active(args.route, False)
            print("deactivated route %s" % args.route)
        elif args.cmd == "activate":
            cls.set_route_active(args.route, True)
            print("activated route %s" % args.route)
        elif args.cmd == "coverage":
            c = cls.coverage()
            print("coverage %s (%d of %d addresses on an active route)"
                  % (_pct(c["coverage"]), c["routed_addresses"],
                     c["total_addresses"]))

    elif args.area == "grid":
        cls = Grid(args.data_dir)
        if args.cmd == "add-gen":
            g = cls.add_generator(args.name, args.fuel, args.capacity,
                                  args.status)
            print("registered generator %s (%s, %.1f MW, %s)"
                  % (g["name"], g["fuel_type"], g["capacity_mw"],
                     g["status"]))
        elif args.cmd == "set-status":
            g = cls.set_generator_status(args.name, args.status)
            print("%s now %s" % (g["name"], g["status"]))
        elif args.cmd == "generators":
            for g in cls.generators(args.status):
                print("%s | %s | %.1f MW | %s"
                      % (g["name"], g["fuel_type"], g["capacity_mw"],
                         g["status"]))
        elif args.cmd == "load":
            r = cls.record_load(args.demand, args.at)
            print("recorded demand %.1f MW at %s"
                  % (r["demand_mw"], r["observed_at"]))
        elif args.cmd == "loads":
            for r in cls.loads():
                print("%.1f MW at %s" % (r["demand_mw"], r["observed_at"]))
        elif args.cmd == "readout":
            r = cls.readout()
            if r["status"] == "NO DATA":
                print("NO DATA: no load observations recorded")
            else:
                print("committed %.1f MW | demand %.1f MW | margin %.1f MW | %s"
                      % (r["committed_mw"], r["demand_mw"], r["margin_mw"],
                         r["status"]))

    elif args.area == "spectrum":
        cls = Spectrum(args.data_dir)
        if args.cmd == "allocate":
            a = cls.allocate(args.band, args.licensee, args.purpose,
                             args.region)
            print("allocated %s: %s to %s in %s for %s"
                  % (a["id"], a["band"], a["licensee"], a["region"],
                     a["purpose"]))
        elif args.cmd == "allocations":
            for a in cls.allocations(args.region):
                print("%s | %s | %s | %s | %s"
                      % (a["id"], a["band"], a["licensee"], a["region"],
                         a["purpose"]))
        elif args.cmd == "overlaps":
            hits = cls.overlaps()
            if not hits:
                print("no overlaps detected")
            for h in hits:
                print("OVERLAP: band %s region %s: %s (%s)"
                      % (h["band"], h["region"],
                         ", ".join(h["allocations"]),
                         ", ".join(h["licensees"])))
        elif args.cmd == "revoke":
            if cls.revoke(args.id):
                print("revoked allocation %s" % args.id)
            else:
                print("no such allocation %s" % args.id)


if __name__ == "__main__":
    main()
