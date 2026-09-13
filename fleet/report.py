#!/usr/bin/env python3
"""Enroll this box and report in.

    python3 -m fleet.report --db node.sqlite --enroll --entity e_fb --label "Dock office"
    python3 -m fleet.report --db node.sqlite          # a heartbeat, run on a timer

Everything it writes is read off the machine it is running on:

  serial      /etc/machine-id, which is stable across reboots and unique
  os_version  /etc/os-release, or the booted bootc image digest
  channel     /etc/anextgent/channel, default 'stable'
  content     the sha256 of what is actually in the content directories
  health      greenboot's verdict if greenboot ran, else 'ok'

No argument can make it claim a version it is not running. A fleet table whose
rows can be typed is a fleet table that tells you what somebody meant to deploy
rather than what is deployed.
"""
import argparse, hashlib, json, os, sqlite3, subprocess, sys, uuid

CONTENT = {
    "contracts":  ("ANEXTGENT_CONTRACTS",  "/usr/lib/anextgent/contracts"),
    "appmaps":    ("ANEXTGENT_APPMAPS",    "/var/lib/anextgent/appmaps"),
    "vendormaps": ("ANEXTGENT_MAPS",       "/var/lib/anextgent/maps"),
}


def _id(p): return f"{p}_{uuid.uuid4().hex[:12]}"


def serial():
    """Stable and unique per machine. Falls back to a file we create once, so
    a developer box still gets a consistent identity instead of a new one on
    every run."""
    for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            v = open(p).read().strip()
            if v:
                return v[:32]
        except OSError:
            pass
    local = os.path.expanduser("~/.anextgent-machine-id")
    try:
        return open(local).read().strip()
    except OSError:
        v = uuid.uuid4().hex
        try:
            with open(local, "w") as f:
                f.write(v)
        except OSError:
            pass
        return v


def os_version():
    """The booted image if this is a bootc box, else the OS release."""
    try:
        out = subprocess.run(["bootc", "status", "--json"], capture_output=True,
                             timeout=5, text=True)
        if out.returncode == 0:
            st = json.loads(out.stdout)
            booted = (st.get("status") or {}).get("booted") or {}
            img = (booted.get("image") or {})
            tag = (img.get("image") or {}).get("image") or img.get("imageDigest")
            if tag:
                return str(tag)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    try:
        for line in open("/etc/os-release"):
            if line.startswith("VERSION_ID="):
                return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return os.uname().release


def channel():
    try:
        return open("/etc/anextgent/channel").read().strip() or "stable"
    except OSError:
        return os.environ.get("ANEXTGENT_CHANNEL", "stable")


def dir_sha(path):
    """A stable digest of a content directory: every file's relative path and
    bytes, in sorted order. Two boxes on the same content get the same digest,
    which is what makes 'these three are behind' answerable."""
    if not path or not os.path.isdir(path):
        return None
    h = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            h.update(os.path.relpath(full, path).encode())
            try:
                with open(full, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
            except OSError:
                return None
    return h.hexdigest()


def content_version(path):
    """A VERSION file if the publisher shipped one, else the digest's prefix.
    An unversioned bundle still gets a name you can compare."""
    if not path or not os.path.isdir(path):
        return None, None
    sha = dir_sha(path)
    try:
        v = open(os.path.join(path, "VERSION")).read().strip()
    except OSError:
        v = (sha or "")[:12] or None
    return v, sha


def health():
    """greenboot's verdict, not ours. If greenboot never ran we do not get to
    call the box healthy -- we say we do not know."""
    try:
        out = subprocess.run(["systemctl", "is-active",
                              "greenboot-healthcheck.service"],
                             capture_output=True, timeout=5, text=True)
        state = out.stdout.strip()
        if state == "active":
            return "ok"
        if state in ("failed", "inactive"):
            return "degraded" if state == "failed" else "unknown"
    except (OSError, subprocess.SubprocessError):
        pass
    return os.environ.get("ANEXTGENT_HEALTH", "unknown")


def enroll(db, entity_id, label, kind="box"):
    s = serial()
    row = db.execute("SELECT id FROM device WHERE serial=?", (s,)).fetchone()
    did = row[0] if row else _id("dv")
    db.execute("""INSERT INTO device(id,entity_id,label,kind,serial,os_version,
                                     channel,health,last_seen_at)
                  VALUES (?,?,?,?,?,?,?,?,datetime('now'))
                  ON CONFLICT(serial) DO UPDATE SET
                    entity_id=COALESCE(excluded.entity_id, device.entity_id),
                    label=COALESCE(excluded.label, device.label),
                    os_version=excluded.os_version, channel=excluded.channel""",
               (did, entity_id, label, kind, s, os_version(), channel(),
                health()))
    db.commit()
    return did


def beat(db, detail=None):
    """One heartbeat. Refuses rather than inventing a device: a box that was
    never enrolled has no business appearing in a fleet."""
    s = serial()
    row = db.execute("SELECT id FROM device WHERE serial=?", (s,)).fetchone()
    if not row:
        return None, f"this machine ({s[:12]}…) is not enrolled — run --enroll"
    did = row[0]
    h = health()
    db.execute("""INSERT INTO heartbeat(id,device_id,at,health,detail)
                  VALUES (?,?,datetime('now'),?,?)""",
               (_id("hb"), did, h, detail))
    db.execute("""UPDATE device SET last_seen_at=datetime('now'), health=?,
                                    os_version=?, channel=? WHERE id=?""",
               (h, os_version(), channel(), did))
    for kind, (env, default) in CONTENT.items():
        path = os.environ.get(env) or default
        v, sha = content_version(path)
        if not v:
            continue
        db.execute("""INSERT INTO device_content(device_id,kind,version,sha256,
                                                 applied_at)
                      VALUES (?,?,?,?,datetime('now'))
                      ON CONFLICT(device_id,kind) DO UPDATE SET
                        version=excluded.version, sha256=excluded.sha256,
                        applied_at=CASE WHEN device_content.sha256 IS excluded.sha256
                                        THEN device_content.applied_at
                                        ELSE excluded.applied_at END""",
                   (did, kind, v, sha))
    db.commit()
    return did, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--enroll", action="store_true")
    ap.add_argument("--entity", help="the business this box belongs to")
    ap.add_argument("--label", help="where it physically sits")
    ap.add_argument("--kind", default="box", choices=["box", "handset"])
    ap.add_argument("--detail", help="note attached to this heartbeat")
    a = ap.parse_args()
    db = sqlite3.connect(a.db, timeout=15)
    db.execute("PRAGMA foreign_keys=ON")

    if a.enroll:
        did = enroll(db, a.entity, a.label, a.kind)
        print(f"enrolled {did}  serial {serial()[:12]}…  {os_version()}")
    did, h = beat(db, a.detail)
    if not did:
        print(h, file=sys.stderr)
        return 1
    print(f"{did}  health {h}")
    for r in db.execute("""SELECT kind, version, substr(sha256,1,12)
                             FROM device_content WHERE device_id=?
                            ORDER BY kind""", (did,)):
        print(f"  {r[0]:<11} {r[1]:<14} {r[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
