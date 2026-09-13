"""Bundle flows and publish them as an OCI artifact.

This is the push. Toast moves a button, you re-map one flow, you cut a new pack,
every box pulls it. One fix, everyone fixed.

A flow pack is not a bespoke format with its own distribution system. It is an
OCI artifact, so it rides the infrastructure that already exists:

    build  →  cosign sign  →  rekor  →  Quay  →  Candlepin entitlement
                                            →  Foreman / Edge Manager  →  box

The registry, the signature, the transparency log and the entitlement check are
all borrowed. The only thing here is the bundling.
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


ARTIFACT_TYPE = "application/vnd.ghost.flowpack.v1+json"
LAYER_TYPE = "application/vnd.ghost.flowpack.layer.v1+json"


def publish(pack_path, ref, sign_after=True, key=None):
    """Push the pack into an OCI registry as an artifact.

    Flows land in the same warehouse as container images, which means Quay on
    the cloud side and a zot mirror on the box, with no second delivery path to
    build or secure.
    """
    if not shutil.which("oras"):
        return False, ("oras not installed — get it from oras.land. "
                       "Flows ship as OCI artifacts so they ride Quay/zot "
                       "instead of a bespoke channel.")
    directory = os.path.dirname(os.path.abspath(pack_path))
    filename = os.path.basename(pack_path)
    argv = ["oras", "push", ref,
            "--artifact-type", ARTIFACT_TYPE,
            f"{filename}:{LAYER_TYPE}"]
    p = subprocess.run(argv, capture_output=True, cwd=directory)
    if p.returncode != 0:
        return False, p.stderr.decode(errors="replace").strip()
    pushed = p.stdout.decode(errors="replace").strip()

    if sign_after:
        ok, detail = sign_ref(ref, key=key)
        return True, f"{pushed}\n  {'signed: ' if ok else 'UNSIGNED: '}{detail}"
    return True, pushed


def sign_ref(ref, key=None):
    """cosign sign the pushed artifact. Goes to rekor unless you opt out."""
    if not shutil.which("cosign"):
        return False, "cosign not installed — artifact is unsigned"
    argv = ["cosign", "sign", "--yes", ref]
    if key:
        argv = ["cosign", "sign", "--yes", "--key", key, ref]
    p = subprocess.run(argv, capture_output=True)
    if p.returncode != 0:
        return False, p.stderr.decode(errors="replace").strip()
    return True, ref


def verify_ref(ref, key=None, identity=None, issuer=None):
    """What the box runs before it installs anything."""
    if not shutil.which("cosign"):
        return False, "cosign not installed — cannot verify signature"
    argv = ["cosign", "verify", ref]
    if key:
        argv += ["--key", key]
    else:
        if identity:
            argv += ["--certificate-identity", identity]
        if issuer:
            argv += ["--certificate-oidc-issuer", issuer]
    p = subprocess.run(argv, capture_output=True)
    if p.returncode != 0:
        return False, p.stderr.decode(errors="replace").strip()
    return True, "signature and transparency log entry check out"


def pull(ref, dest_dir):
    """Fetch a pack from the registry onto a box."""
    if not shutil.which("oras"):
        return None, "oras not installed"
    os.makedirs(dest_dir, exist_ok=True)
    p = subprocess.run(["oras", "pull", ref], capture_output=True, cwd=dest_dir)
    if p.returncode != 0:
        return None, p.stderr.decode(errors="replace").strip()
    for name in os.listdir(dest_dir):
        if name.endswith(".json"):
            return os.path.join(dest_dir, name), "pulled"
    return None, "pull succeeded but no pack file landed"


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
