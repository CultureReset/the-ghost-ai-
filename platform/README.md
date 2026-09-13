# Platform assembly

Every job below is done by an upstream project that already exists. The
projects in the Red Hat / IBM column were built to compose with each other —
Foreman with Katello with Pulp with Candlepin, Backstage with Keycloak,
Sigstore with OCI registries. That is the reason to take the ecosystem instead
of stitching together unrelated repos that each solve one piece.

**Only one row in this table has no upstream implementation.** That row is the
entire reason this company exists.

## Distribution and lifecycle

| Job | Project | Runs where | Status |
|---|---|---|---|
| Base OS image | **bootc** (`bootc-dev/bootc`) | box | take |
| Turn image into installable media | **bootc-image-builder** | factory | take |
| Run apps isolated | **Podman** + quadlet | box | take |
| Build OCI images | **Buildah** | factory | take |
| Move / inspect / sign images | **Skopeo** | factory | take |
| Container registry (warehouse) | **Quay** | cloud | take |
| Container registry (edge mirror) | **zot** | box | take |
| Package / content repositories | **Pulp** | cloud | take |
| Release channels, content views | **Katello** | cloud | take |
| Fleet inventory and provisioning | **Foreman** | cloud | take |
| Edge fleet, OTA, zero-touch | **Red Hat Edge Manager** (flightctl) | cloud + box | investigate before writing any fleet code |
| Entitlement — *what did they buy* | **Candlepin** | cloud | take |
| Usage metering — *what are they using* | IBM License Service model | cloud | build thin, model exists |
| Signing | **cosign** | factory | take |
| Transparency log | **rekor** | cloud | take |
| SBOM | **syft** | factory | take |
| Vulnerability / dependency risk | Trusted Profile Analyzer model, **grype** | cloud | take |
| Policy gate into stable channel | **Conforma / Enterprise Contract** | factory | take |
| Build pipelines | **Tekton**, **Konflux** | factory | take |
| Desired-state deployment | **Argo CD** | cloud + box | take |
| Local admin UI | **Cockpit** | box | take |
| Heavier multi-service apps | **MicroShift** | box | optional second lane |

## Foundation services

Shared once, not reimplemented by every app. This is the IBM Cloud Pak
foundational-services pattern.

| Job | Project | Status |
|---|---|---|
| Identity, SSO, MFA, roles | **Keycloak** | take |
| Relationship authorization | **SpiceDB** or **OpenFGA** | take |
| Certificates | **cert-manager** | take |
| Data | **PostgreSQL** | take |
| Search and logs | **OpenSearch** | take |
| Event bus | **Kafka** | take |
| Developer portal / app catalog | **Backstage** (Developer Hub) | take — ships Keycloak integration |
| MCP / agent / tool gateway | **IBM ContextForge** (`IBM/mcp-context-forge`) | take |
| Agent runtime | **BeeAI** (`i-am-bee/beeai-framework`) | take, behind your own runtime contract |
| Inference | **vLLM** | take |
| Guardrail model | **Granite-Guardian** | take |
| Document parsing | **Docling** | take |

## Action and automation

| Job | Project | Status |
|---|---|---|
| Perform operational tasks | **Ansible** | take |
| event → rule → action | **Event-Driven Ansible** | take — this is your deterministic action system |
| Packaged, versioned automation | **Ansible Collections** / Automation Hub model | take — this is the shape a VAPP should ship in |
| Browser execution | **Playwright** | take |
| Phone mirroring / manual control | **scrcpy** | take |
| Android UI primitives | **uiautomator2**, **ADB** | take |
| Flow authoring / recording | **Maestro** + Maestro Studio | take, on the mapping workstation |

## The one row with no upstream

| Job | Project | Status |
|---|---|---|
| **Drive a business's real apps on a real handset, refuse to act when the screen changed, and read the result back as proof** | *none* | **`ghost/` — build** |

Ansible has no module for this. Maestro is a test framework that fails fast;
this has to refuse to act and then prove the world changed. Nobody upstream
does fingerprint-gated, verified remote control of third-party mobile apps
across a fleet.

That is the product. Everything above it is assembly.

## How `ghost/` plugs in

The flow engine stays. What changes is that it stops carrying its own
distribution system:

```
map a flow            ghost record  /  Maestro Studio
     ↓
build + gate          Tekton  →  syft (SBOM)  →  Conforma (policy)
     ↓
sign                  cosign  →  rekor
     ↓
publish               oras push → Quay          (flows are OCI artifacts,
                                                  same warehouse as apps)
     ↓
entitle               Candlepin: is this box allowed this flow pack?
     ↓
deliver               Foreman / Edge Manager → box
     ↓
install               ghost pack install
     ↓
run                   ghost run  → fingerprint → steps → verify → record
     ↓
watch                 ghost check (nightly)  → Event-Driven Ansible rulebook
                                                → re-map → new pack
```

`ghost/pack.py` now publishes flow packs as **OCI artifacts** into the same
registry as everything else, signed with cosign. It is no longer a bespoke file
format with its own hashing scheme — the registry, the signature, and the
entitlement check are all borrowed.

## Starting the spine

`platform/quadlet/` holds Podman quadlet units for the core services so you can
bring the foundation up on one box without Kubernetes anywhere:

```bash
mkdir -p ~/.config/containers/systemd
cp platform/quadlet/*.container platform/quadlet/*.network ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start ghost-postgres ghost-keycloak ghost-zot ghost-contextforge
```

Pulp, Candlepin, Foreman and Quay are cloud-side and are deployed from their own
upstream installers — they are not part of the box spine.

## Selection rule

From the architecture notes, and worth keeping as the standing rule:

> Prefer a mature upstream ecosystem where projects were intentionally built to
> compose, over an isolated repository that duplicates the same capability.

Apps can be isolated repos. Identity, entitlement, updates, signing and
permissions belong to the foundation, and the foundation is Red Hat's.
