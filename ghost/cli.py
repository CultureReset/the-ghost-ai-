"""ghost — map a flow once, run it anywhere, push the fix to everyone."""

import argparse
import json
import os
import sys

from .device import Device, DeviceError
from .flow import Flow, FlowError, load_dir
from .pack import build, install, publish, pull, sign, verify, verify_ref
from .recorder import record, screen_menu
from .runner import Runner


def pick_device(args):
    serial = args.serial
    if not serial:
        found = Device.list(adb=args.adb)
        if not found:
            raise SystemExit("no device. plug the phone in, enable USB debugging, "
                             "and accept the prompt on the handset.")
        if len(found) > 1 and not args.serial:
            raise SystemExit("more than one device attached — pass --serial:\n  " +
                             "\n  ".join(found))
        serial = found[0]
    return Device(serial=serial, adb=args.adb)


def cmd_devices(args):
    found = Device.list(adb=args.adb)
    if not found:
        print("no devices attached")
        return 1
    for s in found:
        d = Device(serial=s, adb=args.adb)
        try:
            w, h = d.size()
            app = d.current_app()
            print(f"{s}  {w}x{h}  foreground: {app or '?'}")
        except DeviceError as e:
            print(f"{s}  (error: {e})")
    return 0


def cmd_screen(args):
    dev = pick_device(args)
    nodes = dev.dump()
    if args.json:
        print(json.dumps([n.to_dict() for n in nodes if n.text or n.desc or n.clickable],
                         indent=2))
        return 0
    menu = screen_menu(nodes)
    print(f"{dev.current_app()}  —  {len(menu)} elements\n")
    for i, n in enumerate(menu):
        kind = "input" if "EditText" in n.cls else ("tap  " if n.clickable else "text ")
        sel = n.id.split("/")[-1] if ":id/" in n.id else ""
        print(f"[{i:>2}] {kind} {n.label[:52]!r:<56} {sel}")
    return 0


def cmd_shot(args):
    dev = pick_device(args)
    path = dev.screenshot(args.out)
    print(path)
    return 0


def cmd_record(args):
    dev = pick_device(args)
    flow = record(dev, args.name, app=args.app, out_path=args.out)
    return 0 if flow else 1


def cmd_run(args):
    dev = pick_device(args)
    variables = {}
    for pair in args.var or []:
        if "=" not in pair:
            raise SystemExit(f"--var wants name=value, got {pair!r}")
        k, v = pair.split("=", 1)
        variables[k] = v

    paths = args.flow
    if len(paths) == 1 and os.path.isdir(paths[0]):
        flows = load_dir(paths[0])
    else:
        flows = [Flow.load(p) for p in paths]

    runner = Runner(dev, run_dir=args.runs, shots=not args.no_shots)
    worst = 0
    for f in flows:
        missing = f.missing_vars(variables)
        if missing:
            print(f"» {f.name}: skipped — needs --var {' --var '.join(missing)}")
            worst = max(worst, 2)
            continue
        result = runner.run(f, variables)
        if not result.ok:
            worst = max(worst, 1 if result.status == "unverified" else 2)
    return worst


def cmd_check(args):
    """Fingerprint only. Answers: has this app changed under us?"""
    dev = pick_device(args)
    paths = args.flow
    flows = load_dir(paths[0]) if len(paths) == 1 and os.path.isdir(paths[0]) \
        else [Flow.load(p) for p in paths]
    runner = Runner(dev, run_dir=args.runs, shots=False, verbose=False)
    drifted = 0
    for f in flows:
        if not f.fingerprint:
            print(f"?  {f.name:<40} no fingerprint — cannot tell")
            continue
        if f.app:
            dev.launch(f.app)
        ok, why = runner.check_fingerprint(f.fingerprint, timeout=args.timeout)
        if ok:
            print(f"ok {f.name:<40} v{f.version}")
        else:
            drifted += 1
            print(f"!! {f.name:<40} DRIFTED — {why}")
    if drifted:
        print(f"\n{drifted} flow(s) drifted. Re-map them before the fleet runs them.")
    return 1 if drifted else 0


def cmd_lint(args):
    flows = load_dir(args.dir)
    bad = 0
    for f in flows:
        notes = []
        if not f.fingerprint:
            notes.append("no fingerprint (will act on any screen)")
        if not f.verify:
            notes.append("no verify block (cannot prove it worked)")
        if not f.app:
            notes.append("no app declared")
        if notes:
            bad += 1
            print(f"!! {f.name} v{f.version}")
            for n in notes:
                print(f"     - {n}")
        else:
            print(f"ok {f.name} v{f.version}  {f.digest}  "
                  f"{len(f.steps)} steps, {len(f.verify)} checks")
    print(f"\n{len(flows)} flow(s), {bad} with warnings")
    return 1 if bad else 0


def cmd_pack(args):
    if args.action == "build":
        body, weak, unproved = build(args.dir, args.out, channel=args.channel,
                                     notes=args.notes or "")
        print(f"{args.out}")
        print(f"  channel {body['channel']}  {len(body['flows'])} flows  "
              f"digest {body['digest'][:16]}")
        for e in body["flows"]:
            print(f"  · {e['flow']:<38} v{e['version']}  {e['digest']}")
        if weak:
            print(f"\n  warning: no fingerprint — {', '.join(weak)}")
        if unproved:
            print(f"  warning: no verify block — {', '.join(unproved)}")
        if args.sign:
            ok, detail = sign(args.out, key=args.key)
            print(("  signed: " if ok else "  unsigned: ") + detail)
        return 0

    if args.action == "verify":
        ok, body, problems = verify(args.pack)
        if ok:
            print(f"ok  {body['pack']}  {len(body['flows'])} flows  "
                  f"digest {body['digest'][:16]}")
            return 0
        for p in problems:
            print(f"!! {p}")
        return 1

    if args.action == "publish":
        if not args.ref:
            raise SystemExit("publish needs --ref, e.g. "
                             "--ref quay.io/anextgent/flows:2026.09.13")
        ok, detail = publish(args.pack, args.ref, sign_after=not args.no_sign,
                             key=args.key)
        print(("published " if ok else "failed: ") + detail)
        return 0 if ok else 1

    if args.action == "pull":
        if not args.ref:
            raise SystemExit("pull needs --ref")
        ok, detail = verify_ref(args.ref, key=args.key)
        print(("signature: " if ok else "REFUSING — ") + detail)
        if not ok and not args.insecure:
            return 1
        path, msg = pull(args.ref, os.path.dirname(os.path.abspath(args.pack)) or ".")
        if not path:
            print(f"failed: {msg}")
            return 1
        print(f"pulled {path}")
        body, written = install(path, args.dir)
        print(f"installed {body['pack']} ({body['channel']}) into {args.dir}")
        for name, version, digest in written:
            print(f"  · {name:<38} v{version}  {digest}")
        return 0

    if args.action == "install":
        body, written = install(args.pack, args.dir)
        print(f"installed {body['pack']} ({body['channel']}) into {args.dir}")
        for name, version, digest in written:
            print(f"  · {name:<38} v{version}  {digest}")
        return 0

    return 2


def main(argv=None):
    p = argparse.ArgumentParser(prog="ghost", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--adb", default="adb", help="path to adb")
    p.add_argument("--serial", help="device serial (see: ghost devices)")
    p.add_argument("--runs", default="runs", help="where run records go")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("devices", help="list attached handsets").set_defaults(fn=cmd_devices)

    s = sub.add_parser("screen", help="show what is on the phone right now")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_screen)

    s = sub.add_parser("shot", help="screenshot")
    s.add_argument("-o", "--out", default="screen.png")
    s.set_defaults(fn=cmd_shot)

    s = sub.add_parser("record", help="map a flow by doing it once")
    s.add_argument("name")
    s.add_argument("--app", default="", help="package to launch first")
    s.add_argument("-o", "--out", help="output path (default flows/<name>.yaml)")
    s.set_defaults(fn=cmd_record)

    s = sub.add_parser("run", help="run a flow (or a directory of them)")
    s.add_argument("flow", nargs="+")
    s.add_argument("--var", action="append", help="name=value")
    s.add_argument("--no-shots", action="store_true", help="skip screenshots")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("check", help="fingerprints only — did the app change?")
    s.add_argument("flow", nargs="+")
    s.add_argument("--timeout", type=float, default=12.0)
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("lint", help="flows missing a fingerprint or a verify block")
    s.add_argument("dir", nargs="?", default="flows")
    s.set_defaults(fn=cmd_lint)

    s = sub.add_parser("pack", help="bundle flows to push to the fleet")
    s.add_argument("action",
                   choices=["build", "verify", "publish", "pull", "install"])
    s.add_argument("--dir", default="flows")
    s.add_argument("--out", default="dist/flows.pack.json")
    s.add_argument("--pack", default="dist/flows.pack.json")
    s.add_argument("--channel", default="stable")
    s.add_argument("--notes", default="")
    s.add_argument("--sign", action="store_true", help="sign with cosign if present")
    s.add_argument("--key", help="cosign key")
    s.add_argument("--ref", help="OCI reference, e.g. quay.io/org/flows:2026.09.13")
    s.add_argument("--no-sign", action="store_true", help="publish unsigned")
    s.add_argument("--insecure", action="store_true",
                   help="install even if the signature does not verify")
    s.set_defaults(fn=cmd_pack)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except (DeviceError, FlowError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
