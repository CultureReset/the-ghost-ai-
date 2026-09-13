"""A flow is the script. You map it once, it runs everywhere."""

import hashlib
import json
import os
import re

import yaml

VAR = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

# Every verb the runner understands. Keep this list short on purpose — a flow
# anyone can read is a flow anyone can fix at 2am when an app redesigns.
VERBS = {
    "launch",    # launch: com.package.name
    "stop",      # stop: com.package.name
    "tap",       # tap: {text: Save}
    "type",      # type: {id: price_field, value: "18.99"}
    "clear",     # clear: {id: price_field}
    "wait",      # wait: {text: Business hours, timeout: 20}
    "sleep",     # sleep: 1.5
    "back",      # back:
    "home",      # home:
    "scroll",    # scroll: down
    "assert",    # assert: {text: Saved}
}


class FlowError(Exception):
    pass


def substitute(value, variables):
    """Replace {{name}} anywhere in a string / dict / list."""
    if isinstance(value, str):
        def repl(m):
            key = m.group(1)
            if key not in variables:
                raise FlowError(f"flow needs a value for '{key}'")
            return str(variables[key])
        return VAR.sub(repl, value)
    if isinstance(value, dict):
        return {k: substitute(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(v, variables) for v in value]
    return value


class Flow:
    def __init__(self, data, path=None):
        self.path = path
        self.data = data
        self.name = data.get("flow") or "unnamed"
        self.version = int(data.get("version", 1))
        self.app = data.get("app") or ""
        self.app_version = data.get("app_version") or "*"
        self.requires = list(data.get("requires") or [])
        self.fingerprint = list(data.get("fingerprint") or [])
        self.steps = list(data.get("steps") or [])
        self.verify = list(data.get("verify") or [])
        self._validate()

    def _validate(self):
        if not self.steps:
            raise FlowError(f"{self.name}: has no steps")
        for i, step in enumerate(self.steps, 1):
            if not isinstance(step, dict) or len(step) != 1:
                raise FlowError(f"{self.name}: step {i} must be a single verb")
            verb = next(iter(step))
            if verb not in VERBS:
                raise FlowError(
                    f"{self.name}: step {i} uses unknown verb '{verb}' "
                    f"(known: {', '.join(sorted(VERBS))})"
                )

    @property
    def digest(self):
        """Content hash. This is what a pushed flow is identified by."""
        blob = json.dumps(self.data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def missing_vars(self, variables):
        return [v for v in self.requires if v not in variables]

    def resolved(self, variables):
        """The flow with every {{var}} filled in."""
        missing = self.missing_vars(variables)
        if missing:
            raise FlowError(f"{self.name}: missing values for {', '.join(missing)}")
        return {
            "fingerprint": substitute(self.fingerprint, variables),
            "steps": substitute(self.steps, variables),
            "verify": substitute(self.verify, variables),
        }

    @classmethod
    def load(cls, path):
        with open(path) as fh:
            if path.endswith((".yaml", ".yml")):
                data = yaml.safe_load(fh)
            else:
                data = json.load(fh)
        if not isinstance(data, dict):
            raise FlowError(f"{path}: expected a flow definition at the top level")
        return cls(data, path=path)

    def save(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as fh:
            yaml.safe_dump(self.data, fh, sort_keys=False, default_flow_style=False,
                           allow_unicode=True, width=100)
        self.path = path
        return path


def load_dir(directory):
    flows = []
    for root, _dirs, files in os.walk(directory):
        for name in sorted(files):
            if name.endswith((".yaml", ".yml", ".json")):
                flows.append(Flow.load(os.path.join(root, name)))
    return flows
