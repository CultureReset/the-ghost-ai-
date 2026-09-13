# executor

The one job in the whole catalogue with no upstream: drive a business's real
apps on a real handset, **refuse to act when the screen changed**, and read the
result back as proof.

```bash
# with a phone attached
pip install uiautomator2
python3 -m executor.run --db node.sqlite --action ac_xxx --driver android

# with no hardware at all
ANEXTGENT_MOCK=executor/appmaps/_screens.mock.json \
python3 -m executor.run --db node.sqlite --action ac_1 \
  --driver mock --as android --verifier mock --verifier-as browser
```

## Five steps, no way around them

```
fingerprint   refuse to act on a screen the map does not recognise
execute       replay the recorded procedure
settle        a surface does not reflect a change instantly
verify        read it back on a DIFFERENT path than wrote it
record        both dimensions of state, plus evidence, append-only
```

## What it does not do

It does not reimplement a device layer. `drivers/android.py` is a thin adapter
over **openatx/uiautomator2**, which already has xpath, hierarchical selectors,
implicit waits and an input method that handles text `adb shell input` mangles.
`drivers/browser.py` is the same over **Playwright**. Rewriting those was a
mistake made once already in this repo.

## Maps are data

`appmaps/*.json`, keyed on `app × app_version × map_version`. When Toast moves a
button the fix is a new file, signed and pulled — not a code release. Same
reason vendor parsers are data.

Validation refuses two things outright:

- **a map with no fingerprint**, which cannot refuse to act on a screen it does
  not recognise
- **a coordinate selector**, which breaks the moment anything moves

A map in `candidate` state is never run against a customer. Promotion is
deliberate.

## Drivers

| | |
|---|---|
| `android` | uiautomator2. Reports plainly when no device or library is present rather than pretending a tap happened. |
| `browser` | Playwright. Verifies; never writes. |
| `mock` | A scripted screen, so the whole chain — including the drift and contradiction paths — is testable with no hardware. |

`--driver` is what actually drives; `--as` is the executor kind it stands in
for. They differ only for the mock.

## Verified behaviour

| | |
|---|---|
| happy path | 9 steps, 4 surfaces, `VERIFIED 4/4` |
| app redesigned | `DRIFTED` — names the absent markers, records app 4.13.0 against a map written for 4.12.0, **writes nothing** |
| verifier is the executor | refused: *"that is self-certification"* |
| write silently didn't land | `FAILED` at the assert step, before any surface is claimed |
| action still awaiting approval | refused: *"a person has not said yes"* |

Verifying an action and knowing where a business is inconsistent are the same
act — `_verify` writes `surface_state`, which is what the `consistency` view
reads. CyberCheck is populated by running, not by a separate crawl.

## Not built yet

Compensation. When a change lands on three surfaces and not the fourth, the
capability's declared `on_partial` (`rollback` / `drive_forward` / `escalate`)
is recorded in the ledger and **not executed**. Until it is, a partial result is
escalated rather than silently accepted.
