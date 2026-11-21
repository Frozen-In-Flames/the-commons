"""Shared Nation Kit alert convention: flag-and-alert, record-not-operate.

One alert record shape is shared by the-shield, the-commons, and
the-safety-net, the three cores whose job includes flagging a condition
for a human decision. An alert records a flagged condition; it never
acts on it. Enforcement, dispatch, and payment decisions stay with the
operators of each core, exactly as each core README states.

Record shape (identical in all three cores):
  alert_id     deterministic id, ALRT- plus 12 hex characters of the
               SHA-256 of the canonical alert content
  source_core  the repo name that produced the alert
  kind         the flagged condition, in the producing core vocabulary
  subject_id   the record the alert is about
  severity     low, medium, high, or critical, in the producing core
               vocabulary
  detail       human readable statement of the flagged condition
  action       always the string record-not-operate
  status       always flagged on creation
  recorded_at  ISO 8601 UTC timestamp of the flagging
"""

import datetime
import hashlib
import json

ACTION = "record-not-operate"


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def make_alert(source_core, kind, subject_id, severity, detail,
               recorded_at=None):
    """Build one alert record in the shared shape. Pure function."""
    core = {
        "source_core": source_core,
        "kind": kind,
        "subject_id": subject_id,
        "severity": severity,
        "detail": detail,
        "action": ACTION,
        "status": "flagged",
    }
    digest = hashlib.sha256(
        json.dumps(core, sort_keys=True).encode("utf-8")).hexdigest()
    rec = dict(core)
    rec["alert_id"] = "ALRT-" + digest[:12]
    rec["recorded_at"] = recorded_at or _utcnow()
    return rec
