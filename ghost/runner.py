"""Run a flow on a real phone and prove what happened.

Two rules the runner will not bend:

  1. Check the fingerprint before touching anything. If the screen is not the
     screen the flow was mapped against, stop. An app redesign must fail loudly
     on the first machine, not quietly change the wrong field on four hundred.

  2. Read the result back off the screen. The flow finishing is not proof the
     thing changed.
"""

import json
import os
import time
from datetime import datetime, timezone

from .device import Device, DeviceError
from .flow import Flow, FlowError

OK = "ok"
DRIFTED = "drifted"      # screen is not what we mapped — app probably changed
FAILED = "failed"        # a step could not run
UNVERIFIED = "unverified"  # steps ran, read-back did not confirm


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Result:
    def __init__(self, flow, variables):
        self.flow = flow.name
        self.version = flow.version
        self.digest = flow.digest
        self.variables = dict(variables)
        self.started = _now()
        self.finished = None
        self.status = None
        self.detail = ""
        self.steps = []
        self.checks = []
        self.shots = []

    def record(self, verb, arg, status, detail="", ms=0):
        self.steps.append({"verb": verb, "arg": arg, "status": status,
                           "detail": detail, "ms": ms})

    def to_dict(self):
        return {
            "flow": self.flow, "version": self.version, "digest": self.digest,
            "variables": self.variables, "started": self.started,
            "finished": self.finished, "status": self.status, "detail": self.detail,
            "steps": self.steps, "checks": self.checks, "screenshots": self.shots,
        }

    def save(self, directory):
        os.makedirs(directory, exist_ok=True)
        stamp = self.started.replace(":", "").replace("-", "")
        path = os.path.join(directory, f"{self.flow}-{stamp}.json")
        with open(path, "w") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return path

    @property
    def ok(self):
        return self.status == OK


class Runner:
    def __init__(self, device: Device, run_dir="runs", shots=True, verbose=True):
        self.dev = device
        self.run_dir = run_dir
        self.shots = shots
        self.verbose = verbose

    def say(self, msg):
        if self.verbose:
            print(msg, flush=True)

    def _shot(self, result, tag):
        if not self.shots:
            return
        os.makedirs(self.run_dir, exist_ok=True)
        stamp = result.started.replace(":", "").replace("-", "")
        path = os.path.join(self.run_dir, f"{result.flow}-{stamp}-{tag}.png")
        try:
            self.dev.screenshot(path)
            result.shots.append({"tag": tag, "path": path})
        except DeviceError as e:
            self.say(f"  (could not screenshot: {e})")

    # ---- pre-flight ------------------------------------------------------

    def check_fingerprint(self, fingerprint, timeout=20.0):
        """Every selector in the fingerprint must be on screen before we act."""
        for sel in fingerprint:
            sel = _as_selector(sel)
            node = self.dev.wait_for(sel, timeout=timeout)
            if node is None:
                return False, f"expected {_describe(sel)} on screen, not found"
        return True, ""

    # ---- running ---------------------------------------------------------

    def run(self, flow: Flow, variables=None):
        variables = variables or {}
        result = Result(flow, variables)
        plan = flow.resolved(variables)

        self.say(f"» {flow.name} v{flow.version} ({flow.digest})")

        try:
            if flow.app:
                self.dev.launch(flow.app)
                time.sleep(2.0)

            if plan["fingerprint"]:
                ok, why = self.check_fingerprint(plan["fingerprint"])
                self._shot(result, "preflight")
                if not ok:
                    result.status = DRIFTED
                    result.detail = why
                    self.say(f"  ✗ drifted — {why}")
                    self.say("  refusing to act on a screen this flow was not mapped against")
                    return self._finish(result)
                self.say("  ✓ fingerprint matches")

            for i, step in enumerate(plan["steps"], 1):
                verb, arg = next(iter(step.items()))
                t0 = time.time()
                try:
                    detail = self._step(verb, arg)
                except (DeviceError, FlowError) as e:
                    ms = int((time.time() - t0) * 1000)
                    result.record(verb, arg, FAILED, str(e), ms)
                    result.status = FAILED
                    result.detail = f"step {i} ({verb}): {e}"
                    self.say(f"  ✗ step {i} {verb}: {e}")
                    self._shot(result, "failed")
                    return self._finish(result)
                ms = int((time.time() - t0) * 1000)
                result.record(verb, arg, OK, detail, ms)
                self.say(f"  · {verb} {_short(arg)} ({ms}ms)")

            self._shot(result, "after")

            if plan["verify"]:
                verified, checks = self._verify(plan["verify"])
                result.checks = checks
                if verified:
                    result.status = OK
                    self.say(f"  ✓ verified ({len(checks)} check(s) read back off the screen)")
                else:
                    result.status = UNVERIFIED
                    bad = [c["expected"] for c in checks if not c["found"]]
                    result.detail = "not confirmed on screen: " + ", ".join(bad)
                    self.say(f"  ✗ unverified — {result.detail}")
            else:
                result.status = UNVERIFIED
                result.detail = "flow declares no verify block"
                self.say("  ! no verify block — ran, but nothing was proved")

        except DeviceError as e:
            result.status = FAILED
            result.detail = str(e)
            self.say(f"  ✗ device error: {e}")

        return self._finish(result)

    def _finish(self, result):
        result.finished = _now()
        path = result.save(self.run_dir)
        self.say(f"  → {result.status.upper()}  record: {path}")
        return result

    def _step(self, verb, arg):
        d = self.dev

        if verb == "launch":
            d.launch(arg)
            time.sleep(2.0)
            return f"launched {arg}"

        if verb == "stop":
            d.stop(arg)
            return f"stopped {arg}"

        if verb == "sleep":
            time.sleep(float(arg))
            return f"slept {arg}s"

        if verb == "back":
            d.back()
            time.sleep(0.6)
            return "back"

        if verb == "home":
            d.home()
            time.sleep(0.6)
            return "home"

        if verb == "scroll":
            if str(arg).lower() == "up":
                w, h = d.size()
                d.swipe(w // 2, h // 3, w // 2, h * 2 // 3, 400)
            else:
                d.scroll_down()
            time.sleep(0.8)
            return f"scrolled {arg}"

        if verb == "wait":
            sel = _as_selector(arg)
            timeout = float(arg.get("timeout", 15)) if isinstance(arg, dict) else 15
            node = d.wait_for(sel, timeout=timeout)
            if node is None:
                raise FlowError(f"waited {timeout}s for {_describe(sel)}, never appeared")
            return f"found {node.label!r}"

        if verb == "tap":
            sel = _as_selector(arg)
            timeout = float(arg.get("timeout", 12)) if isinstance(arg, dict) else 12
            node = d.wait_for(sel, timeout=timeout)
            if node is None:
                raise FlowError(f"nothing matching {_describe(sel)} to tap")
            d.tap_node(node)
            time.sleep(float(arg.get("settle", 1.0)) if isinstance(arg, dict) else 1.0)
            return f"tapped {node.label!r} at {node.center}"

        if verb == "clear":
            sel = _as_selector(arg)
            node = d.wait_for(sel, timeout=12)
            if node is None:
                raise FlowError(f"nothing matching {_describe(sel)} to clear")
            d.clear_field(node)
            return f"cleared {node.label!r}"

        if verb == "type":
            if not isinstance(arg, dict) or "value" not in arg:
                raise FlowError("type needs a value:")
            sel = _as_selector({k: v for k, v in arg.items() if k != "value"})
            if sel:
                node = d.wait_for(sel, timeout=12)
                if node is None:
                    raise FlowError(f"no field matching {_describe(sel)}")
                d.tap_node(node)
                time.sleep(0.4)
            d.type(str(arg["value"]))
            time.sleep(0.5)
            return f"typed {arg['value']!r}"

        if verb == "assert":
            sel = _as_selector(arg)
            timeout = float(arg.get("timeout", 10)) if isinstance(arg, dict) else 10
            node = d.wait_for(sel, timeout=timeout)
            if node is None:
                raise FlowError(f"assert failed: {_describe(sel)} not on screen")
            return f"asserted {node.label!r}"

        raise FlowError(f"unknown verb {verb}")

    # ---- verification ----------------------------------------------------

    def _verify(self, checks):
        """Read the screen back. This is the only thing that counts as proof."""
        out = []
        all_found = True
        for check in checks:
            sel = _as_selector(check)
            timeout = float(check.get("timeout", 12)) if isinstance(check, dict) else 12
            node = self.dev.wait_for(sel, timeout=timeout)
            found = node is not None
            all_found = all_found and found
            out.append({
                "expected": _describe(sel),
                "found": found,
                "observed": node.label if node else None,
            })
        return all_found, out


# ---- helpers -------------------------------------------------------------

_SEL_KEYS = ("text", "id", "desc", "cls", "contains", "clickable")


def _as_selector(arg):
    if isinstance(arg, str):
        return {"text": arg}
    if isinstance(arg, dict):
        return {k: v for k, v in arg.items() if k in _SEL_KEYS}
    raise FlowError(f"cannot read {arg!r} as a selector")


def _describe(sel):
    return ", ".join(f"{k}={v!r}" for k, v in sel.items()) or "anything"


def _short(arg):
    s = arg if isinstance(arg, str) else _describe(_as_selector(arg)) if isinstance(arg, dict) else str(arg)
    return s if len(s) <= 52 else s[:49] + "..."
