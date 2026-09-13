"""Browser, via Playwright. Used to VERIFY, not to write.

The verifier must not be the executor. When a map writes through Android, the
read-back comes through here — a different route, different software, so the
result is evidence instead of a claim.

    pip install playwright && playwright install chromium
"""
NAME = "browser"

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


class Driver:
    def __init__(self, headless=True):
        self.headless, self._pw, self.page = headless, None, None

    def available(self):
        if sync_playwright is None:
            return False, "playwright not installed (pip install playwright)"
        return True, "chromium"

    def open(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        return self

    def close(self):
        if self._pw:
            self.browser.close(); self._pw.stop()

    def read_at(self, url, sel, timeout_ms=15000):
        self.page.goto(url, timeout=timeout_ms)
        loc = self.page.locator(sel["css"]) if "css" in sel else self.page.get_by_text(sel["text"])
        return loc.first.inner_text(timeout=timeout_ms).strip()

    def screenshot(self, path):
        self.page.screenshot(path=path, full_page=True); return path
