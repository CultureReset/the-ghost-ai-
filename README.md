# ghost

Remote control for the apps a business already uses.

Map a task once on a real phone. It writes a script. Push the script to every
box. When the app changes, you re-map that one flow and push again — one fix,
everyone fixed.

No API keys. No vendor integrations. No emulator. A real handset with a real
SIM, driven over adb through the accessibility tree the device already exposes.

## Setup

```bash
# on the box
sudo apt install android-tools-adb      # or: brew install android-platform-tools
pip install pyyaml

# on the phone: Settings → About → tap Build number 7×,
# then Developer options → USB debugging. Plug it in, accept the prompt.

python3 -m ghost devices
```

## Map a flow

```bash
python3 -m ghost record google_business.update_hours \
  --app com.google.android.apps.town.businessmessaging
```

You drive the phone. Every tap is recorded as a **selector** — `{text: Save}`,
`{id: open_time}` — not a coordinate, so the script survives the button moving.

While recording:

| key | does |
|---|---|
| `3` | tap element 3 |
| `t 5 18.99` | type into element 5 |
| `f 0` | add element 0 to the **fingerprint** |
| `v 2` | add element 2 to the **verify** block |
| `s` / `u` / `b` | scroll down / up / back |
| `d` | done — write the flow |

Then open the file and swap the values that change for `{{variables}}`.

## Run it

```bash
python3 -m ghost run flows/google_business.update_hours.yaml \
  --var day=Friday --var open="9:00 AM" --var close="5:00 PM"
```

```
» google_business.update_hours v1 (5f5c6987abbe0df0)
  ✓ fingerprint matches
  · tap text='Business hours' (912ms)
  · type id='open_time' (640ms)
  · tap text='Save' (1102ms)
  ✓ verified (3 check(s) read back off the screen)
  → OK  record: runs/google_business.update_hours-20260913T0140.json
```

Every run writes a JSON record with each step, the read-back checks, and
screenshots before and after.

## The two rules the runner will not bend

**1. Fingerprint before acting.** Every flow declares one or two things that
must be on screen before the first tap. If they are not there, the run stops and
reports `DRIFTED` instead of tapping blind. An app redesign fails loudly on the
first machine rather than quietly changing the wrong field on four hundred.

**2. Read the result back.** A flow finishing is not proof. The `verify:` block
re-reads the screen and confirms the new value is actually there. No verify
block, no `OK` — the run comes back `UNVERIFIED`.

## Watch the fleet for breakage

```bash
python3 -m ghost check flows/          # fingerprints only, no side effects
```

Run this nightly against every flow. It answers one question: *did an app change
under us?* Anything that comes back `DRIFTED` gets re-mapped before customers
touch it.

## Push

```bash
python3 -m ghost lint flows/                                    # catch weak flows
python3 -m ghost pack build --dir flows --out dist/flows.pack.json --sign
python3 -m ghost pack verify --pack dist/flows.pack.json        # re-hash everything
python3 -m ghost pack install --pack dist/flows.pack.json --dir flows   # on the box
```

A pack is content-hashed end to end. Change one byte of one step and `verify`
refuses it. Sign it with cosign and the box can check the signature before it
installs anything.

## Flow format

```yaml
flow: google_business.update_hours
version: 1
app: com.google.android.apps.town.businessmessaging
requires: [day, open, close]

fingerprint:                    # must be true before we touch anything
  - text: "Business hours"

steps:
  - tap: {text: "{{day}}"}
  - clear: {id: open_time}
  - type: {id: open_time, value: "{{open}}"}
  - tap: {text: "Save"}

verify:                         # must be true afterwards, read off the screen
  - contains: "{{open}}"
```

Verbs: `launch` `stop` `tap` `type` `clear` `wait` `sleep` `back` `home`
`scroll` `assert`. That is the whole language, on purpose — a flow anyone can
read is a flow anyone can fix at 2am when an app redesigns.

Selectors: `text` (exact), `contains` (substring), `id` (resource-id, matches
the short name), `desc` (accessibility label), `cls`, `clickable`.

## Layout

```
ghost/device.py     adb: read the screen, tap, type, screenshot
ghost/flow.py       the script format, variables, content hashing
ghost/runner.py     fingerprint → steps → verify → run record
ghost/recorder.py   map a flow by doing it once
ghost/pack.py       bundle, hash, sign, install
ghost/cli.py        the commands above
flows/              the scripts
runs/               what happened, with screenshots
```
