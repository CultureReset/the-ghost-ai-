"""Talking to a real Android handset over adb.

No emulator, no Appium server, no daemon. Just adb and the accessibility tree
the device already exposes through uiautomator.
"""

import re
import subprocess
import time
import xml.etree.ElementTree as ET

BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
REMOTE_DUMP = "/sdcard/ghost-ui.xml"


class DeviceError(Exception):
    pass


class Node:
    """One element on screen."""

    __slots__ = ("text", "id", "desc", "cls", "pkg", "clickable", "enabled", "bounds")

    def __init__(self, attrib):
        self.text = (attrib.get("text") or "").strip()
        self.id = attrib.get("resource-id") or ""
        self.desc = (attrib.get("content-desc") or "").strip()
        self.cls = attrib.get("class") or ""
        self.pkg = attrib.get("package") or ""
        self.clickable = attrib.get("clickable") == "true"
        self.enabled = attrib.get("enabled") == "true"
        m = BOUNDS.match(attrib.get("bounds") or "")
        self.bounds = tuple(int(g) for g in m.groups()) if m else (0, 0, 0, 0)

    @property
    def center(self):
        x1, y1, x2, y2 = self.bounds
        return (x1 + x2) // 2, (y1 + y2) // 2

    @property
    def area(self):
        x1, y1, x2, y2 = self.bounds
        return max(0, x2 - x1) * max(0, y2 - y1)

    @property
    def label(self):
        return self.text or self.desc or self.id.split("/")[-1] or self.cls.split(".")[-1]

    def matches(self, sel):
        """sel is a dict: text / id / desc / cls / contains / clickable."""
        if "text" in sel and self.text != sel["text"]:
            return False
        if "contains" in sel and sel["contains"].lower() not in self.text.lower():
            return False
        if "id" in sel and not (self.id == sel["id"] or self.id.endswith("/" + sel["id"])):
            return False
        if "desc" in sel and self.desc != sel["desc"]:
            return False
        if "cls" in sel and sel["cls"] not in self.cls:
            return False
        if sel.get("clickable") and not self.clickable:
            return False
        return True

    def to_dict(self):
        return {
            "text": self.text, "id": self.id, "desc": self.desc,
            "cls": self.cls, "clickable": self.clickable, "bounds": list(self.bounds),
        }

    def __repr__(self):
        return f"<Node {self.label!r} {self.bounds}>"


class Device:
    def __init__(self, serial=None, adb="adb"):
        self.serial = serial
        self.adb = adb

    # ---- plumbing -------------------------------------------------------

    def _argv(self, *args):
        argv = [self.adb]
        if self.serial:
            argv += ["-s", self.serial]
        return argv + list(args)

    def sh(self, *args, binary=False, timeout=90):
        try:
            p = subprocess.run(self._argv(*args), capture_output=True, timeout=timeout)
        except FileNotFoundError:
            raise DeviceError(f"{self.adb} not found on PATH — install android platform-tools")
        except subprocess.TimeoutExpired:
            raise DeviceError(f"adb timed out: {' '.join(args)}")
        if p.returncode != 0:
            err = p.stderr.decode(errors="replace").strip()
            raise DeviceError(err or f"adb failed: {' '.join(args)}")
        return p.stdout if binary else p.stdout.decode(errors="replace")

    @classmethod
    def list(cls, adb="adb"):
        try:
            out = subprocess.run([adb, "devices", "-l"], capture_output=True, timeout=30)
        except FileNotFoundError:
            raise DeviceError(f"{adb} not found on PATH — install android platform-tools")
        found = []
        for line in out.stdout.decode(errors="replace").splitlines()[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                found.append(parts[0])
        return found

    # ---- reading the screen ---------------------------------------------

    def dump(self, retries=3):
        """Return every node currently on screen."""
        last = None
        for attempt in range(retries):
            try:
                self.sh("shell", "uiautomator", "dump", REMOTE_DUMP)
                xml = self.sh("shell", "cat", REMOTE_DUMP)
                start = xml.find("<?xml")
                if start > 0:
                    xml = xml[start:]
                root = ET.fromstring(xml.strip())
                return [Node(el.attrib) for el in root.iter("node")]
            except (DeviceError, ET.ParseError) as e:
                last = e
                time.sleep(0.6)
        raise DeviceError(f"could not read the screen after {retries} tries: {last}")

    def find(self, sel, nodes=None):
        """First node matching sel, or None. Smallest match wins — it is the
        most specific thing under the finger."""
        nodes = self.dump() if nodes is None else nodes
        hits = [n for n in nodes if n.matches(sel)]
        if not hits:
            return None
        return min(hits, key=lambda n: n.area or 10**9)

    def wait_for(self, sel, timeout=15.0, poll=0.7):
        deadline = time.time() + timeout
        while True:
            node = self.find(sel)
            if node:
                return node
            if time.time() >= deadline:
                return None
            time.sleep(poll)

    def screen_text(self, nodes=None):
        nodes = self.dump() if nodes is None else nodes
        return "\n".join(n.text for n in nodes if n.text)

    def current_app(self):
        out = self.sh("shell", "dumpsys", "window", "displays")
        m = re.search(r"mCurrentFocus=.*?\{[^}]*\s+([\w.]+)/", out)
        return m.group(1) if m else ""

    # ---- acting ----------------------------------------------------------

    def tap(self, x, y):
        self.sh("shell", "input", "tap", str(x), str(y))

    def tap_node(self, node):
        x, y = node.center
        self.tap(x, y)

    def type(self, text):
        # adb input text wants escaped spaces and is literal about the rest.
        safe = text.replace("%", "%%").replace(" ", "%s")
        self.sh("shell", "input", "text", safe)

    def key(self, keycode):
        self.sh("shell", "input", "keyevent", str(keycode))

    def back(self):
        self.key(4)

    def home(self):
        self.key(3)

    def swipe(self, x1, y1, x2, y2, ms=300):
        self.sh("shell", "input", "swipe", *map(str, (x1, y1, x2, y2, ms)))

    def scroll_down(self, amount=600):
        w, h = self.size()
        self.swipe(w // 2, h * 2 // 3, w // 2, h * 2 // 3 - amount, 400)

    def clear_field(self, node, count=40):
        self.tap_node(node)
        time.sleep(0.3)
        # move to end, then delete backwards
        self.key(123)
        for _ in range(count):
            self.key(67)

    def size(self):
        out = self.sh("shell", "wm", "size")
        m = re.search(r"(\d+)x(\d+)", out)
        return (int(m.group(1)), int(m.group(2))) if m else (1080, 2400)

    def launch(self, package):
        self.sh("shell", "monkey", "-p", package,
                "-c", "android.intent.category.LAUNCHER", "1")

    def stop(self, package):
        self.sh("shell", "am", "force-stop", package)

    def screenshot(self, path):
        png = self.sh("exec-out", "screencap", "-p", binary=True)
        with open(path, "wb") as fh:
            fh.write(png)
        return path
