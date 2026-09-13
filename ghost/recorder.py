"""Map a flow by doing it once.

You drive. Every tap is written down as a selector, not a coordinate, so the
script still works when the button moves.
"""

import time

from .device import Device
from .flow import Flow

# Prefer a resource-id: it survives copy changes and translations. Fall back to
# visible text, then the accessibility label.
def selector_for(node):
    if node.id and not node.id.endswith("/content") and ":id/" in node.id:
        return {"id": node.id.split("/")[-1]}
    if node.text:
        return {"text": node.text}
    if node.desc:
        return {"desc": node.desc}
    return None


def interesting(nodes):
    """Things a person could plausibly act on."""
    out = []
    seen = set()
    for n in nodes:
        if not n.enabled or n.area <= 0:
            continue
        if not (n.clickable or n.text or n.desc):
            continue
        key = (n.label, n.bounds)
        if key in seen:
            continue
        seen.add(key)
        out.append(n)
    return out


def screen_menu(nodes):
    items = interesting(nodes)
    # editable fields first, then clickables, then plain labels
    def rank(n):
        if "EditText" in n.cls:
            return 0
        if n.clickable:
            return 1
        return 2
    return sorted(items, key=lambda n: (rank(n), n.bounds[1], n.bounds[0]))


HELP = """
  <number>  tap that element            t <n> <text>  type into element n
  s         scroll down                 u             scroll up
  b         back                        r             refresh the screen
  w <n>     wait for element n          f <n>         add n to the fingerprint
  v <n>     add n to the verify block   d             done — write the flow
  q         quit without saving         ?             this help
"""


def record(dev: Device, name, app="", out_path=None):
    print(f"\nMapping '{name}'. Drive the phone through the task once.")
    print(HELP)

    steps = []
    fingerprint = []
    verify = []

    if app:
        print(f"launching {app} ...")
        dev.launch(app)
        time.sleep(2.5)
        steps.append({"launch": app})

    nodes = dev.dump()
    while True:
        menu = screen_menu(nodes)
        print(f"\n─── screen ({len(menu)} elements) " + "─" * 30)
        for i, n in enumerate(menu):
            kind = "input" if "EditText" in n.cls else ("tap  " if n.clickable else "text ")
            print(f"  [{i:>2}] {kind} {n.label[:58]!r}")

        try:
            raw = input("\nghost> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\naborted")
            return None
        if not raw:
            nodes = dev.dump()
            continue

        cmd, *rest = raw.split(maxsplit=1)
        tail = rest[0] if rest else ""

        if cmd == "q":
            print("nothing written")
            return None

        if cmd == "?":
            print(HELP)
            continue

        if cmd == "r":
            nodes = dev.dump()
            continue

        if cmd == "s":
            dev.scroll_down()
            steps.append({"scroll": "down"})
            time.sleep(0.9)
            nodes = dev.dump()
            continue

        if cmd == "u":
            w, h = dev.size()
            dev.swipe(w // 2, h // 3, w // 2, h * 2 // 3, 400)
            steps.append({"scroll": "up"})
            time.sleep(0.9)
            nodes = dev.dump()
            continue

        if cmd == "b":
            dev.back()
            steps.append({"back": None})
            time.sleep(0.9)
            nodes = dev.dump()
            continue

        if cmd == "d":
            break

        if cmd == "t":
            parts = tail.split(maxsplit=1)
            if len(parts) != 2 or not parts[0].isdigit():
                print("  usage: t <number> <text to type>")
                continue
            idx, text = int(parts[0]), parts[1]
            if idx >= len(menu):
                print("  no such element")
                continue
            node = menu[idx]
            sel = selector_for(node)
            if not sel:
                print("  that element has nothing stable to match on — pick another")
                continue
            dev.tap_node(node)
            time.sleep(0.4)
            dev.clear_field(node)
            dev.type(text)
            steps.append({"clear": dict(sel)})
            steps.append({"type": {**sel, "value": text}})
            print(f"  recorded: type {text!r} into {sel}")
            time.sleep(0.7)
            nodes = dev.dump()
            continue

        if cmd in ("w", "f", "v"):
            if not tail.strip().isdigit():
                print(f"  usage: {cmd} <number>")
                continue
            idx = int(tail.strip())
            if idx >= len(menu):
                print("  no such element")
                continue
            sel = selector_for(menu[idx])
            if not sel:
                print("  nothing stable to match on there")
                continue
            if cmd == "w":
                steps.append({"wait": dict(sel)})
                print(f"  recorded: wait for {sel}")
            elif cmd == "f":
                fingerprint.append(dict(sel))
                print(f"  fingerprint += {sel}")
            else:
                verify.append(dict(sel))
                print(f"  verify += {sel}")
            continue

        if cmd.isdigit():
            idx = int(cmd)
            if idx >= len(menu):
                print("  no such element")
                continue
            node = menu[idx]
            sel = selector_for(node)
            if not sel:
                print("  that element has nothing stable to match on — pick another")
                continue
            dev.tap_node(node)
            steps.append({"tap": dict(sel)})
            print(f"  recorded: tap {sel}")
            time.sleep(1.2)
            nodes = dev.dump()
            continue

        print("  ? — type ? for help")

    if not steps:
        print("no steps recorded")
        return None

    if not fingerprint:
        print("\nNo fingerprint set. Without one this flow will act on any screen.")
        print("Strongly consider re-running and marking 1-2 elements with 'f'.")

    data = {
        "flow": name,
        "version": 1,
        "app": app,
        "app_version": "*",
        "requires": [],
        "fingerprint": fingerprint,
        "steps": steps,
        "verify": verify,
    }
    flow = Flow(data)
    path = out_path or f"flows/{name}.yaml"
    flow.save(path)
    print(f"\nwrote {path}  ({len(steps)} steps, {len(verify)} checks, {flow.digest})")
    print("Open it and replace the changing values with {{variables}}, then add")
    print("those names to 'requires:'. That turns one recording into one script.")
    return flow
