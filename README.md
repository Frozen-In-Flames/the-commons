# the-commons

Infrastructure core for a new nation. Step 5 of the Nation Kit's 17-to-1
reverse-SDG build sequence.

## The idea

Every federal agency is one class with one job. This build centralizes the
three infrastructure classes:

- `Post` — one job: every address is reachable. Address registry
  (id, locality, delivery point type) plus a route optimizer that groups
  addresses by locality into delivery routes and reports coverage: the
  share of addresses on an active route.
- `Grid` — one job: the power stays on. Generator records (name, fuel
  type, capacity MW, status) plus load observations (timestamp, demand
  MW). The supply/demand readout compares the latest demand against
  committed online capacity and flags shortfall risk when demand
  approaches it.
- `Spectrum` — one job: signals don't jam each other. Allocation
  registry (band, licensee, purpose, region) with an overlap detector
  that flags two allocations in the same band and region held by
  different licensees.

## SDGs unlocked

This build unlocks **SDG 7 (Affordable and Clean Energy)**, **SDG 9
(Industry, Innovation and Infrastructure)**, and **SDG 11 (Sustainable
Cities and Communities)**:

- `Grid` maps to 7: a nation cannot have clean, affordable energy without
  knowing what its generators can produce and what its people demand.
- `Post` and `Spectrum` map to 9: delivery routes and a clean airwave
  plan are the physical and electromagnetic infrastructure everything
  else runs on.
- `Post` and `Grid` map to 11: a city is sustainable when every address
  in it is reachable and its power stays on.

It is step 5 of the 17-to-1 sequence because shared infrastructure comes
after the prerequisites are secured: honest books (step 1), trustworthy
records (step 2), a living population on livable land (step 3), and a
defended border (step 4). Infrastructure is what a protected, recorded,
solvent nation builds next, and it is what the welfare outcomes of step
6 (the-safety-net) stand on.

## Usage

```bash
# Post: register addresses, build routes, check coverage
python3 commons_cli.py post register --id A-1 --locality Springfield --type residential
python3 commons_cli.py post register --id A-2 --locality Springfield --type business
python3 commons_cli.py post register --id B-1 --locality Shelbyville --type po_box
python3 commons_cli.py post build-routes
python3 commons_cli.py post coverage
python3 commons_cli.py post deactivate --route R-shelbyville
python3 commons_cli.py post coverage

# Grid: register generators, record load, read supply vs demand
python3 commons_cli.py grid add-gen --name Sunfield --fuel solar --capacity 120
python3 commons_cli.py grid add-gen --name Riverbend --fuel hydro --capacity 300
python3 commons_cli.py grid load --demand 380
python3 commons_cli.py grid readout
python3 commons_cli.py grid set-status --name Riverbend --status maintenance
python3 commons_cli.py grid readout

# Spectrum: allocate bands, detect overlaps
python3 commons_cli.py spectrum allocate --band "700 MHz" --licensee "Carrier One" --purpose mobile --region North
python3 commons_cli.py spectrum allocate --band "700 MHz" --licensee "Carrier Two" --purpose mobile --region North
python3 commons_cli.py spectrum overlaps
python3 commons_cli.py spectrum revoke --id A-2
python3 commons_cli.py spectrum overlaps
```

Data lives in `data/` (JSON). `--data-dir` overrides the location.

## Data sources and labels

All records are the nation's own registry entries. Every record carries a
`source` label ("nation address registry", "nation grid registry", or
"nation spectrum registry") and UTC timestamps (`registered_at`,
`built_at`, `observed_at`, `allocated_at`). No external data, no
estimates.

## Honest limits

These are registries. They record and alert; they do not operate.

- `Post` optimizes routes and reports coverage. Carrying the mail,
  maintaining vehicles, and staffing routes are delivery, a separate
  job.
- `Grid` flags shortfall risk. Running power plants, dispatching
  generation, and shedding load are grid operations, a separate job.
  The readout uses the latest recorded demand only; it does not
  forecast.
- `Spectrum` detects overlaps. Policing the airwaves, fining
  violators, and clearing bands are enforcement, a separate job.
  Overlap is exact band-and-region matching; it does not model
  adjacent-band interference or signal propagation.

Route coverage counts addresses on active routes only. Deactivated
routes drop out of the numerator, never out of the registry.

## Tests

```bash
python3 -m unittest discover -s tests
```

33 tests, no network access. TRL 8: complete, tested, demonstrated,
released. The gap to 9 is operational use by a real infrastructure
authority.
