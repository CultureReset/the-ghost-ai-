"""Bundle flows into one versioned, hashed pack.

This is the push. Toast moves a button, you re-map one flow, you cut a new pack,
every box pulls it. One fix, everyone fixed.
"""

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone

from .flow import Flow, load_dir


def build(flow_dir, out_path, channel="stable", notes=""):
    flows = load_dir(flow_dir)
    if not flows:
        raise SystemExit(f"no flows found in {flow_dir}")

    entries = []
    for f in sorted(flows, key=lambda f: f.name):
        entries.append({
            "flow": f.name,
            "version": f.version,
            "app": f.app,
            "app_version": f.app_version,
            "requires": f.requires,
            "digest": f.digest,
            "has_fingerprint": bool(f.fingerprint),
            "has_verify": bool(f.verify),
            "definition": f.data,
        })

    body = {
        "pack": os.path.basename(out_path).rsplit(".", 1)[0],
        "channel": channel,
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notes": notes,
        "flows": entries,
    }
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"))
    body["digest"] = hashlib.sha256(blob.encode()).hexdigest()

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(body, fh, indent=2)

    weak = [e["flow"] for e in entries if not e["has_fingerprint"]]
    unproved = [e["flow"] for e in entries if not e["has_verify"]]
    return body, weak, unproved


def verify(pack_path):
    """Re-hash everything. Catches a tampered or truncated pack."""
    with open(pack_path) as fh:
        body = json.load(fh)
    unsigned = {k: v for k, v in body.items() if k != "digest"}
    claimed = body.get("digest")
    blob = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    actual = hashlib.sha256(blob.encode()).hexdigest()
    problems = []
    if claimed != actual:
        problems.append(f"pack digest mismatch: claims {claimed}, computes {actual}")
    for entry in body["flows"]:
        f = Flow(entry["definition"])
        if f.digest != entry["digest"]:
            problems.append(f"{entry['flow']}: digest mismatch")
    return (not problems), body, problems


def sign(pack_path, key=None):
    """Sign with cosign if it is installed. Optional, but do it before you push."""
    if not shutil.which("cosign"):
        return False, "cosign not installed — pack is unsigned"
    argv = ["cosign", "sign-blob", "--yes", pack_path,
            "--output-signature", pack_path + ".sig"]
    if key:
        argv += ["--key", key]
    p = subprocess.run(argv, capture_output=True)
    if p.returncode != 0:
        return False, p.stderr.decode(errors="replace").strip()
    return True, pack_path + ".sig"


def install(pack_path, flow_dir):
    """Unpack onto a box. This is what the appliance runs on update."""
    ok, body, problems = verify(pack_path)
    if not ok:
        raise SystemExit("refusing to install: " + "; ".join(problems))
    os.makedirs(flow_dir, exist_ok=True)
    written = []
    for entry in body["flows"]:
        f = Flow(entry["definition"])
        path = os.path.join(flow_dir, f"{f.name}.yaml")
        f.save(path)
        written.append((f.name, f.version, f.digest))
    return body, written
