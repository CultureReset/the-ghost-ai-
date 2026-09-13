"""Android, via openatx/uiautomator2.

This is a thin adapter, not a device layer. uiautomator2 already does xpath,
hierarchical selectors, implicit waits and an input method that handles text
`adb shell input` mangles. Rewriting that was a mistake made once already.

    pip install uiautomator2

With no device or no library attached, `available()` is False and the runner
reports that rather than pretending a tap happened.
"""
NAME = "android"

try:
    import uiautomator2 as u2
except ImportError:
    u2 = None


class Driver:
    def __init__(self, serial=None):
        self.serial, self.d = serial, None

    def available(self):
        if u2 is None:
            return False, "uiautomator2 not installed (pip install uiautomator2)"
        try:
            self.d = u2.connect(self.serial) if self.serial else u2.connect()
            return True, self.d.device_info.get("model", "android")
        except Exception as e:
            return False, f"no device: {e}"

    # ---- what a map can ask for -------------------------------------------
    def launch(self, package):
        self.d.app_start(package, stop=True); return True

    def present(self, sel, timeout=5):
        return self._el(sel).exists(timeout=timeout)

    def tap(self, sel, timeout=10):
        self._el(sel).click(timeout=timeout); return True

    def type(self, sel, text, timeout=10):
        e = self._el(sel); e.click(timeout=timeout)
        self.d.send_keys(text, clear=False); return True

    def clear(self, sel, timeout=10):
        self._el(sel).clear_text(timeout=timeout); return True

    def read(self, sel, timeout=10):
        return self._el(sel).get_text(timeout=timeout)

    def back(self):
        self.d.press("back"); return True

    def scroll(self, direction="down"):
        getattr(self.d.swipe_ext, "__call__")(direction); return True

    def screenshot(self, path):
        self.d.screenshot(path); return path

    def app_version(self, package):
        try:
            return self.d.app_info(package).get("versionName")
        except Exception:
            return None

    def _el(self, sel):
        """Selectors are semantic. A map that taps a coordinate is rejected at
        validation time, so nothing here accepts one."""
        kw = {}
        if "text" in sel:        kw["text"] = sel["text"]
        if "contains" in sel:    kw["textContains"] = sel["contains"]
        if "id" in sel:          kw["resourceId"] = sel["id"]
        if "desc" in sel:        kw["description"] = sel["desc"]
        if "cls" in sel:         kw["className"] = sel["cls"]
        if "xpath" in sel:       return self.d.xpath(sel["xpath"])
        return self.d(**kw)
