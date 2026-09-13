"""A fake device with a scripted screen.

Here so the whole chain — fingerprint, execute, verify on a second path, record
both dimensions of state — can be exercised with no hardware, and so the DRIFTED
path can be tested deliberately rather than waited for.

    ANEXTGENT_MOCK=/path/to/screens.json

A screens file is what the device shows: a list of element dicts per screen,
plus what the "public page" reports back for verification.
"""
import json, os

NAME = "mock"


class Driver:
    def __init__(self, path=None):
        self.path = path or os.environ.get("ANEXTGENT_MOCK")
        self.state, self.screen, self.log, self.written = None, None, [], {}

    def available(self):
        if not self.path or not os.path.exists(self.path):
            return False, "set ANEXTGENT_MOCK to a screens file"
        self.state = json.load(open(self.path, encoding="utf-8"))
        self.screen = self.state.get("start", "home")
        return True, f"mock:{os.path.basename(self.path)}"

    def _elements(self):
        return self.state["screens"].get(self.screen, [])

    def _match(self, sel):
        for e in self._elements():
            if "text" in sel and e.get("text") == sel["text"]: return e
            if "id" in sel and e.get("id") == sel["id"]: return e
            if "desc" in sel and e.get("desc") == sel["desc"]: return e
            if "contains" in sel and sel["contains"] in (e.get("text") or ""): return e
        return None

    def launch(self, package):
        self.screen = self.state.get("start", "home"); self.log.append(("launch", package)); return True

    def present(self, sel, timeout=5):
        return self._match(sel) is not None

    def tap(self, sel, timeout=10):
        e = self._match(sel)
        if not e:
            raise LookupError(f"no element matching {sel}")
        self.log.append(("tap", sel))
        if "goto" in e:
            self.screen = e["goto"]
        return True

    def type(self, sel, text, timeout=10):
        e = self._match(sel)
        if not e:
            raise LookupError(f"no element matching {sel}")
        e["text_value"] = text
        self.written[e.get("id") or e.get("text")] = text
        self.log.append(("type", sel, text))
        return True

    def clear(self, sel, timeout=10):
        return self.type(sel, "", timeout)

    def read(self, sel, timeout=10):
        e = self._match(sel)
        if not e:
            raise LookupError(f"no element matching {sel}")
        return e.get("text_value", e.get("text"))

    def back(self): self.log.append(("back",)); return True
    def scroll(self, direction="down"): self.log.append(("scroll", direction)); return True
    def app_version(self, package): return self.state.get("app_version")

    def screenshot(self, path):
        with open(path, "w") as f:
            json.dump({"screen": self.screen, "elements": self._elements()}, f, indent=2)
        return path

    # the second path — what a verifier would see afterwards
    def public_value(self, field):
        return self.written.get(field, self.state.get("public", {}).get(field))
