# -*- coding: utf-8 -*-
"""Complete repo catalog. Every row: (repo, license, verdict, html description).
verdict: core | use | study | care | skip
A leading '*' on the repo string marks a fact re-verified on the web today."""

S = []

def sec(num, title, lede, rows, flag=None, note=None):
    S.append(dict(num=num, title=title, lede=lede, rows=rows, flag=flag, note=note))

# ---------------------------------------------------------------- 00
sec("00", "Your own repositories",
 "The fourteen that already exist under CultureReset. These are the things you are not "
 "cloning from anyone, and the reason the rest of this list is an assembly job rather than a "
 "build-from-zero. Names as they appear in the session; rename freely.",
 [
  ("CultureReset/the-ghost-ai-", "—", "core",
   "<b>The box.</b> Where this record, the platform assembly map, the Quadlet unit files and the "
   "flow/runner/pack code live. The repository the appliance is cut from."),
  ("CultureReset/cybercheck-core", "—", "core",
   "<b>The private truth.</b> Business record, observations, canonical values, provenance. The one "
   "place data is authoritative and the one place it is never published from."),
  ("CultureReset/cybercheck-node", "—", "core",
   "<b>The node runtime.</b> Runs identically on the box or in the cloud free tier. Same code, "
   "different address — this is what makes the free tier a real product and not a demo."),
  ("CultureReset/cybercheck-cloud", "—", "core",
   "<b>The hosted half.</b> The node when the customer has no hardware yet. Your entire first "
   "twenty-five customers live here before a single box ships."),
  ("CultureReset/cybercheck-orchestrator", "—", "core",
   "<b>The brain.</b> Model routing, capability dispatch, the four-state result. What you actually "
   "sell when you say you are selling the harness."),
  ("CultureReset/cybercheck-marketplace", "—", "core",
   "<b>The app store.</b> The index, the trust ladder, the manifests. Part VI is its spec."),
  ("CultureReset/cybercheck-web", "—", "use",
   "<b>The public projection.</b> Read-only, write-incapable by construction. The signed static "
   "half that the world sees."),
  ("CultureReset/App-build-", "—", "use",
   "<b>App scaffolding.</b> The generator for a new VAPP — manifest, three targets, the surfaces. "
   "This is what a third-party developer starts from."),
  ("CultureReset/API-layer-unified", "—", "use",
   "<b>The seam.</b> One contract in front of everything so the apps do not learn nine different "
   "shapes. The place the capability list is enforced rather than documented."),
  ("CultureReset/gcr-api-clean", "—", "use",
   "<b>API, cleaned.</b> Keep as the reference implementation of the contract above; fold what "
   "survives into API-layer-unified rather than running two."),
  ("CultureReset/gcr-unified", "—", "study",
   "<b>Earlier unification attempt.</b> Read it for the decisions you already made and forgot, "
   "then let it go. Two unified layers is zero unified layers."),
  ("CultureReset/Admin-dashboard-main", "—", "use",
   "<b>Your console.</b> Fleet state, drift alerts, the re-map queue. The screen you sit in front "
   "of on the Tuesday an app vendor ships a redesign."),
  ("CultureReset/Dashboards-users-", "—", "use",
   "<b>The owner's console.</b> Deliberately not the same product as yours. Theirs answers \"is my "
   "stuff right\"; yours answers \"which four hundred boxes just broke\"."),
  ("CultureReset/Landing-pages-", "—", "use",
   "<b>The front door.</b> Also the per-business public page generator. One codebase, two jobs — "
   "worth keeping that way."),
 ],
 note="Verdicts here are about role in the assembly, not code quality — I have not read these "
      "repositories, only the session's description of them.")

# ---------------------------------------------------------------- 01
sec("01", "The OS image and the update spine",
 "The Red Hat trick, mechanically: the operating system is a signed OCI image, updates are image "
 "pulls, and a failed boot rolls itself back without a phone call. Everything in this layer exists "
 "so that shipping an update is a push and not a visit.",
 [
  ("*bootc-dev/bootc", "Apache-2.0", "core",
   "<b>The whole thesis in one binary.</b> Boots a container image as the operating system and "
   "updates it transactionally. Note the org moved — it is <span class='mono'>bootc-dev/bootc</span> "
   "now, not <span class='mono'>containers/bootc</span>; the old path still redirects, which is "
   "exactly how you end up with a stale reference in a build script."),
  ("ostreedev/ostree", "LGPL-2.1", "use",
   "<b>The layer underneath bootc.</b> Content-addressed filesystem trees with atomic swap and "
   "rollback. You will rarely call it directly, but every strange bootc behaviour is explained here."),
  ("osbuild/osbuild", "Apache-2.0", "use",
   "<b>Image assembly.</b> Turns a manifest into a bootable artifact — ISO, qcow2, raw disk."),
  ("osbuild/bootc-image-builder", "Apache-2.0", "core",
   "<b>Container image → installable disk.</b> The step between \"I built an image\" and \"I have "
   "something to put on a USB stick.\" This is your factory."),
  ("fedora-iot/greenboot", "LGPL-2.1", "core",
   "<b>Health check on boot, automatic rollback on failure.</b> The single component that makes "
   "remote updates to unattended hardware in four hundred restaurants a survivable business rather "
   "than a support catastrophe. Write real health checks, not <span class='mono'>exit 0</span>."),
  ("rauc/rauc", "LGPL-2.1", "study",
   "<b>The A/B update alternative.</b> Embedded-grade, bundle-signed, very mature. Correct choice "
   "if you ever ship something too small for a container runtime. Not both — pick one."),
  ("mendersoftware/mender", "Apache-2.0", "care",
   "<b>OTA update platform with a managed server.</b> Good technology, but the server is the "
   "business model; you are building the server. Study the client-side delta logic, skip the rest."),
  ("canonical/ubuntu-core", "—", "study",
   "<b>The snap-based immutable appliance.</b> The closest commercial analogue to what you are "
   "doing. Study the store-and-brand-account model in particular — it is a working example of the "
   "control you say you want the least of."),
  ("home-assistant/operating-system", "Apache-2.0", "study",
   "<b>Read this one end to end before you commit.</b> A consumer appliance OS shipped to hundreds "
   "of thousands of non-technical households, with the update system, the recovery path and the "
   "\"never show a terminal\" discipline already solved in public."),
  ("home-assistant/core", "Apache-2.0", "study",
   "<b>The integration model.</b> Two thousand integrations maintained by strangers without the "
   "project collapsing. That governance pattern is your app store's future problem, already solved."),
  ("ublue-os/bluefin", "Apache-2.0", "study",
   "<b>Universal Blue's daily driver.</b> Proof that image-based desktop Linux is usable by normal "
   "people today. Their build pipeline is a working template."),
  ("ublue-os/main", "Apache-2.0", "study",
   "<b>The base images.</b> How to layer your own thing on top of a distro without forking it."),
  ("ublue-os/image-template", "Apache-2.0", "use",
   "<b>Start here on day one.</b> A working custom-bootc-image repo with CI already wired. Saves a "
   "week of GitHub Actions archaeology."),
 ],
 flag=("The one decision in this layer",
  "bootc or RAUC, and you cannot hedge. bootc gives you one artifact format from laptop to "
  "appliance and a registry you already run for everything else. RAUC gives you a smaller, older, "
  "more certain thing that works on hardware a container runtime would not fit on. Pick bootc for "
  "a mini-PC appliance; the rest of this catalog assumes you did."))

# ---------------------------------------------------------------- 02
sec("02", "The comparable, read closely",
 "Omarchy is the project you were pointed at first, and it remains the closest thing to your "
 "opinionated-Linux-for-humans idea that has actually shipped and found an audience.",
 [
  ("basecamp/omarchy", "MIT", "study",
   "<b>The original.</b> DHH's opinionated Arch + Hyprland setup. The lesson is not the window "
   "manager; it is that taste, defaults and a name did more than any feature."),
  ("omacom-io/omarchy", "MIT", "study",
   "<b>The current home.</b> Check which org is canonical before you cite it anywhere public — "
   "this moved once already."),
  ("omacom-io/omarchy-pkgs", "MIT", "study",
   "<b>Their package overlay.</b> How a curated distro layer is maintained by a very small team."),
  ("omacom-io/omarchy-mirror", "MIT", "study",
   "<b>Their mirror.</b> Small, but it is the shape of distribution infrastructure you will need — "
   "and cheaper to copy than to design."),
 ],
 flag=("Why it is study and not use",
  "Omarchy is mutable Arch with excellent taste. You need immutable, signed and self-rolling-back, "
  "because your user is a restaurant owner and your update runs while the dinner rush is on. Take "
  "the taste and the positioning. Leave the architecture."))

# ---------------------------------------------------------------- 03
sec("03", "Boot chain and hardware root of trust",
 "You said you want the least control possible. The way to hold almost none while still being able "
 "to prove the box is yours is to put the trust in hardware and in signatures, not in an account "
 "you can log into.",
 [
  ("torvalds/linux", "GPL-2.0", "use",
   "<b>The kernel.</b> Relevant decision: stay on in-tree drivers. The moment you need an "
   "out-of-tree module for the GPU, image-based updates stop being simple. AMD's in-tree "
   "<span class='mono'>amdgpu</span> is most of why Strix Halo is the right silicon."),
  ("systemd/systemd", "LGPL-2.1", "use",
   "<b>Init, services, sockets, sysext, credentials.</b> Learn <span class='mono'>systemd-sysext</span> "
   "and the credentials system specifically — they solve per-device configuration on a read-only OS "
   "without a mutable <span class='mono'>/etc</span>."),
  ("tpm2-software/tpm2-tss", "BSD-2-Clause", "use",
   "<b>TPM access.</b> Seal the disk key to the measured boot state. The customer's data is "
   "unreadable if the drive walks out of the building, and you never hold a key."),
  ("Foxboron/sbctl", "MIT", "use",
   "<b>Secure Boot key management that a human can operate.</b> Makes signed boot a build step "
   "rather than a research project."),
  ("OP-TEE/optee_os", "BSD-2-Clause", "study",
   "<b>ARM TrustZone TEE.</b> Only relevant if you go ARM. On x86 the TPM covers your needs."),
  ("fwupd/fwupd", "LGPL-2.1", "use",
   "<b>Firmware updates on Linux, properly.</b> The layer below your OS updates. Ignoring it means "
   "shipping known-vulnerable firmware to four hundred businesses."),
  ("fwupd/lvfs-website", "GPL-2.0", "study",
   "<b>The firmware distribution service.</b> A working model of exactly the thing you are "
   "building — signed artifacts, vendor accounts, staged rollout, public metadata. Read the design "
   "documents even if you never upload a cab file."),
 ])

# ---------------------------------------------------------------- 04
sec("04", "Apps on the box, and the naming trap",
 "How software that is not the operating system gets onto and off of an immutable machine, and how "
 "the box describes what it has to a human being.",
 [
  ("flatpak/flatpak", "LGPL-2.1", "use",
   "<b>Sandboxed desktop apps on an immutable OS.</b> The answer to \"the customer wants Chrome on "
   "it\" that does not involve mutating the base image."),
  ("flatpak/xdg-desktop-portal", "LGPL-2.1", "use",
   "<b>The permission broker.</b> How a sandboxed app asks for a file or the camera and the user "
   "answers. Your first-party apps go through the same door as third-party ones — that rule is "
   "worth more than any marketing claim about privacy."),
  ("PackageKit/PackageKit", "GPL-2.0", "use",
   "<b>Distro-neutral package operations.</b> The thing a graphical installer talks to so your UI "
   "never has to know what a package manager is."),
  ("ximion/appstream", "LGPL-2.1", "care",
   "<b>The freedesktop metadata standard</b> for describing software to a store UI — icons, "
   "screenshots, summaries, categories. Use the format. <b>Do not use the word.</b> Between this "
   "and RHEL's AppStream repository you already have two; a third called yours will cost you a week "
   "of confused conversations."),
  ("89luca89/distrobox", "GPL-3.0", "use",
   "<b>Any distro's tooling inside a container on an immutable host.</b> How your own developers "
   "keep working on a machine that will not let them install a compiler."),
 ])

# ---------------------------------------------------------------- 05
sec("05", "The kiosk surface",
 "The wall-mounted screen is where \"a Linux computer made simple\" either holds up or dies in "
 "front of everyone who works there. Nothing in this layer may ever show a terminal, an error "
 "dialog or a login prompt.",
 [
  ("cage-kiosk/cage", "MIT", "core",
   "<b>A Wayland compositor that runs exactly one application fullscreen.</b> No desktop, no "
   "shortcut to a desktop, no way out. That constraint is the product."),
  ("swaywm/sway", "MIT", "study",
   "<b>The tiling compositor cage is built from.</b> Read it when cage cannot do the one thing you "
   "need, not before."),
  ("Quickshell/quickshell", "LGPL-3.0", "study",
   "<b>QML shell toolkit.</b> Relevant if the kiosk grows past a single fullscreen view into "
   "panels and overlays. Omarchy-adjacent territory."),
  ("NoriginMedia/Norigin-Spatial-Navigation", "Apache-2.0", "use",
   "<b>Arrow-key navigation for TV interfaces.</b> You said smart-TV layout, and this is the "
   "unglamorous library that makes a remote control feel right. Nobody notices it working; everyone "
   "notices it missing."),
 ],
 flag=("The rule for this layer",
  "If a customer can reach a shell by accident, you have shipped a Linux box. If they cannot reach "
  "one at all, you have broken your own promise that they own it. The resolution is a deliberate, "
  "documented, slightly hidden way in — held down, typed in, never discovered by a dropped tray."))

# ---------------------------------------------------------------- 06
sec("06", "Containers, sandboxes and the isolation ladder",
 "Third-party apps run on a machine sitting in a business's back office, holding that business's "
 "operational data. Isolation is not a feature here; it is the whole liability position.",
 [
  ("containers/podman", "Apache-2.0", "core",
   "<b>Daemonless, rootless containers with systemd integration.</b> Quadlet — writing "
   "<span class='mono'>.container</span> files that systemd manages as units — is why this beats "
   "Docker on an appliance. No daemon to die, no socket to secure."),
  ("containers/buildah", "Apache-2.0", "use",
   "<b>Build images without a daemon.</b> Scriptable, minimal, pairs with podman."),
  ("containers/skopeo", "Apache-2.0", "use",
   "<b>Move and inspect images between registries without pulling them.</b> Your mirroring and "
   "promotion tool."),
  ("containers/image", "Apache-2.0", "study",
   "<b>The library underneath skopeo and podman.</b> Read when you write your own promotion logic."),
  ("containers/storage", "Apache-2.0", "study",
   "<b>The layer store.</b> Same reason."),
  ("containers/bubblewrap", "LGPL-2.0", "use",
   "<b>Unprivileged sandboxing primitive.</b> What Flatpak uses underneath. The cheapest real "
   "isolation you can put around a helper process."),
  ("google/gvisor", "Apache-2.0", "use",
   "<b>A user-space kernel.</b> Syscall interception, so a container escape hits gVisor instead of "
   "your kernel. The right default for third-party code that touches customer data."),
  ("google/nsjail", "Apache-2.0", "study",
   "<b>Process jail.</b> Lighter than gVisor, less complete. Good for short-lived tooling."),
  ("firecracker-microvm/firecracker", "Apache-2.0", "care",
   "<b>MicroVMs with ~125ms boot.</b> The strongest isolation short of separate hardware, and real "
   "operational weight. Justified only for untrusted code from a developer you have never met — "
   "which, if the app store works, is eventually most of it."),
  ("google/crosvm", "BSD-3-Clause", "study",
   "<b>The ChromeOS VMM.</b> Read for how a consumer appliance runs untrusted guests without the "
   "user ever hearing the word virtualization."),
  ("microsandbox/microsandbox", "Apache-2.0", "study",
   "<b>MicroVM sandboxing aimed specifically at agent-generated code.</b> Newer and smaller — "
   "watch it rather than depend on it."),
  ("bytecodealliance/wasmtime", "Apache-2.0", "use",
   "<b>WebAssembly runtime with capability-based security.</b> A plugin gets exactly the "
   "capabilities you hand it and cannot ask for more. This is the enforcement layer the Agent "
   "Plugins spec explicitly does not have."),
  ("extism/extism", "BSD-3-Clause", "core",
   "<b>The practical wrapper around Wasm plugins.</b> Host SDKs in a dozen languages, plugins in "
   "any language that compiles to Wasm. If you want third-party code without third-party risk, "
   "this plus wasmtime is the answer — and it is the difference between your store and Grok's."),
  ("e2b-dev/infra", "Apache-2.0", "study",
   "<b>Open infrastructure for AI code sandboxes.</b> Someone else's production answer to the same "
   "question. Read their isolation boundaries."),
  ("apple/container", "Apache-2.0", "study",
   "<b>Apple's container tooling.</b> Only interesting as a read on where the platform you are "
   "positioned against is heading."),
  ("apple/containerization", "Apache-2.0", "study", "<b>The framework under it.</b> Same."),
 ],
 flag=("Where the ladder actually lands",
  "First-party app: container + gVisor. Verified third-party app: the same, no exceptions and no "
  "shortcuts — identical treatment is the claim. Unverified community app: Wasm via Extism, with a "
  "capability list, or a microVM if it genuinely needs a filesystem. Never: a plugin that runs "
  "as a subprocess with the node's environment."))

# ---------------------------------------------------------------- 07
sec("07", "Registry, fleet and entitlement — the Red Hat machine",
 "This is the part you are actually copying. Not the operating system: the apparatus that turns "
 "'we publish updates' into a subscription business, with content on one side and entitlement on "
 "the other.",
 [
  ("project-zot/zot", "Apache-2.0", "core",
   "<b>A minimal OCI-native registry.</b> Runs on the box, runs in the cloud, stores your OS images, "
   "your app bundles and your flow packs as OCI artifacts. Small enough to understand completely."),
  ("quay/quay", "Apache-2.0", "study",
   "<b>Red Hat's registry.</b> Overkill for you now. Read the organisation, robot-account and "
   "vulnerability-feed model — that is the shape a developer-facing registry needs eventually."),
  ("pulp/pulp", "GPL-2.0", "study",
   "<b>Content repository management: mirror, version, promote, publish.</b> The dev → staging → "
   "production channel pattern you need, already built by people who ship to enterprises."),
  ("theforeman/foreman", "GPL-3.0", "study",
   "<b>Lifecycle management for fleets of machines.</b> Heavy. Read the host-group and "
   "content-view concepts and implement a hundredth of it."),
  ("Katello/katello", "GPL-2.0", "study",
   "<b>Foreman + Pulp + Candlepin together.</b> This combination <i>is</i> Red Hat Satellite, and "
   "Satellite is how Red Hat actually delivers what customers pay for. The single most useful thing "
   "in this section to read."),
  ("candlepin/candlepin", "GPL-2.0", "core",
   "<b>Subscription and entitlement management.</b> Who is paid up, what are they entitled to pull, "
   "when does it expire. You are building a subscription business for updates; this is that "
   "business's ledger, and it already exists."),
  ("flightctl/flightctl", "Apache-2.0", "core",
   "<b>Red Hat's edge device management for image-based hosts.</b> Declarative device state, "
   "staged rollout, rollback. Built for exactly your deployment shape — one image, many "
   "unattended machines, no on-site staff. The closest thing to a drop-in for your fleet plane."),
  ("cockpit-project/cockpit", "LGPL-2.1", "care",
   "<b>Web admin for a Linux host.</b> Useful for you during development; a promise you do not "
   "want to make to a customer. If they can reach Cockpit, they can break the appliance, and the "
   "call comes to you."),
  ("fleetdm/fleet", "MIT", "study",
   "<b>Device management and reporting at scale via osquery.</b> Read the reporting model — you "
   "need fleet visibility without fleet access, and this is the closest working example."),
  ("oras-project/oras", "Apache-2.0", "core",
   "<b>Push and pull arbitrary artifacts to an OCI registry.</b> The reason your flow packs, app "
   "bundles and model manifests all live in the same signed, mirrored, content-addressed place as "
   "your OS. One distribution mechanism for everything."),
  ("google/go-containerregistry", "Apache-2.0", "use",
   "<b>The library for registry work in Go.</b> <span class='mono'>crane</span> is in here and is "
   "the tool you will actually type."),
 ],
 flag=("The four pieces that matter",
  "zot holds the bits. ORAS puts non-image things in it. Candlepin says who may pull. flightctl "
  "decides which devices get it and in what order. That is the subscription business, and every "
  "one of those four is open source and already written."))

# ---------------------------------------------------------------- 08
sec("08", "The pipeline and the policy gate",
 "How a change becomes a signed artifact that four hundred machines are allowed to pull, with a "
 "gate that says no on its own without you in the room.",
 [
  ("tektoncd/pipeline", "Apache-2.0", "study",
   "<b>Kubernetes-native CI.</b> Correct if you are already on Kubernetes. You are not, and you "
   "should not start for this. Read the task/pipeline decomposition and do the same shape in "
   "whatever you already run."),
  ("konflux-ci/konflux-ci", "Apache-2.0", "study",
   "<b>Red Hat's full supply-chain build service.</b> Enormous. Read what it enforces — provenance, "
   "SBOM, policy — and steal the checklist, not the system."),
  ("conforma/cli", "Apache-2.0", "core",
   "<b>The policy gate, formerly Enterprise Contract.</b> Verifies signature, provenance and "
   "policy before an artifact is allowed to be promoted. This is the machine that lets you say "
   "\"nothing unsigned reaches a customer\" as a fact rather than a policy."),
  ("enterprise-contract/ec-cli", "Apache-2.0", "study",
   "<b>The former name.</b> Noted so an old link in a bookmark does not read as a different tool."),
  ("argoproj/argo-cd", "Apache-2.0", "care",
   "<b>GitOps continuous delivery.</b> Excellent, and Kubernetes-shaped. Take the "
   "declared-state-in-git discipline; skip the cluster."),
 ])

# ---------------------------------------------------------------- 09
sec("09", "Supply chain: signing, transparency, SBOM, scanning",
 "The evidence layer. Every claim you make about what is on the box has to be checkable by someone "
 "who does not trust you — including, eventually, a customer's insurer.",
 [
  ("sigstore/cosign", "Apache-2.0", "core",
   "<b>Sign and verify container images and arbitrary artifacts.</b> Keyless signing via OIDC "
   "means you are not managing a private key on a laptop, which is where signing schemes usually "
   "die. Non-negotiable for anything that reaches a customer machine."),
  ("sigstore/rekor", "Apache-2.0", "core",
   "<b>The transparency log.</b> An append-only public record of what you signed and when. Put "
   "constitution versions and app-map promotions in here, not just OS images — those are the "
   "claims that actually need third-party verification. It is also your defence on the day someone "
   "alleges you changed a business's data."),
  ("sigstore/sigstore", "Apache-2.0", "study",
   "<b>The client libraries.</b> For when signing has to happen inside your own code."),
  ("theupdateframework/python-tuf", "Apache-2.0 / MIT", "study",
   "<b>TUF: the formal answer to compromised update servers.</b> Role separation, key rotation, "
   "rollback and freeze attack resistance. Sigstore covers most of it in practice; read TUF for the "
   "threat model you will be asked about by the first serious customer."),
  ("anchore/syft", "Apache-2.0", "use",
   "<b>Generate an SBOM from an image or directory.</b> One command. Do it on every build from the "
   "first build, because retrofitting SBOMs across a year of releases is a month of work."),
  ("anchore/grype", "Apache-2.0", "use",
   "<b>Scan that SBOM for known vulnerabilities.</b> Pairs with syft. The pair is your \"we patch "
   "it\" claim made mechanical."),
  ("aquasecurity/trivy", "Apache-2.0", "use",
   "<b>Broader scanner</b> — images, filesystems, IaC, secrets. Overlaps grype; run one in CI and "
   "the other as an independent check, since agreeing scanners tell you little."),
  ("trufflesecurity/trufflehog", "AGPL-3.0", "use",
   "<b>Finds committed secrets, and verifies whether they are live.</b> Run it over every "
   "third-party app bundle before it enters the store. Note the AGPL: fine as a CI tool you "
   "execute, a problem if you link it into a service you distribute."),
  ("aboutcode-org/scancode-toolkit", "Apache-2.0", "use",
   "<b>License and origin detection across a codebase.</b> You are assembling a hundred and eighty "
   "projects into hardware you sell. This is how you find the GPL component someone vendored into "
   "a dependency three levels down, before a customer's lawyer does."),
  ("CycloneDX/cyclonedx-cli", "Apache-2.0", "use",
   "<b>SBOM format conversion and merging.</b> You will need one merged SBOM per released image, "
   "not forty."),
  ("spdx/tools-python", "Apache-2.0", "study",
   "<b>The other SBOM standard.</b> Emit whichever the asking party wants; the tooling to convert "
   "exists, so do not hold a religious position."),
 ],
 flag=("The claim this layer buys you",
  "\"I cannot see your data\" is architecture. \"You can verify what I sent you\" is signing plus "
  "transparency. The second is the one that survives a hostile question, because the person asking "
  "can check it without your cooperation."))

# ---------------------------------------------------------------- 10
sec("10", "The execution layer — remote control of a real phone",
 "The core of the product and the only row in the whole catalog with no upstream that does the "
 "whole job. Everything here is a part of the mechanism: see the screen, read the tree, act, and "
 "prove the act landed.",
 [
  ("*Genymobile/scrcpy", "Apache-2.0", "core",
   "<b>Mirror and control an Android device over USB or TCP with no app installed on it.</b> Low "
   "latency, rock solid, enormous install base. This is what makes \"they can see their own phone "
   "on their iPhone\" a weekend of work instead of a product."),
  ("NetrisTV/ws-scrcpy", "MIT", "use",
   "<b>scrcpy in a browser over WebSocket.</b> The owner-facing viewer, without shipping a native "
   "app to anyone."),
  ("*openatx/uiautomator2", "MIT", "core",
   "<b>Python control of Android's UIAutomator: dump the view hierarchy, find elements, tap, type, "
   "wait.</b> This is the executor. It is also precisely what <span class='mono'>ghost/device.py</span> "
   "was reimplementing — replace that file with this library and delete about three hundred lines "
   "you now have to maintain."),
  ("openatx/adbutils", "MIT", "use",
   "<b>ADB from Python without shelling out.</b> The layer under uiautomator2; use it directly for "
   "device discovery, install, screenshot and file transfer."),
  ("*mobile-dev-inc/maestro", "Apache-2.0", "core",
   "<b>Declarative YAML flows for mobile UI, with element matching and implicit waits that "
   "actually work.</b> The hardest, least interesting problem in this whole build is \"wait until "
   "the screen is really ready\", and Maestro has solved it in public. Verified today: still "
   "Apache-2.0, ~15.3k stars, releasing every few weeks."),
  ("mobile-dev-inc/maestro-studio", "Apache-2.0", "core",
   "<b>Point at an element, get a selector, record a flow.</b> This is your factory tool — the "
   "thing you use on the Tuesday an app vendor ships a redesign and you have to re-map before the "
   "fleet notices. It is also what <span class='mono'>ghost/recorder.py</span> was rebuilding."),
  ("appium/appium", "Apache-2.0", "study",
   "<b>The old guard of mobile automation.</b> Heavier than you need, but the driver architecture "
   "is the reference for supporting a second platform later."),
  ("appium/appium-inspector", "Apache-2.0", "use",
   "<b>A GUI for inspecting a live app's element tree.</b> Free debugging for the day a selector "
   "matches nothing and the screenshot looks identical."),
  ("appium/appium-uiautomator2-driver", "Apache-2.0", "study",
   "<b>Their Android driver.</b> Read it when uiautomator2 does something you cannot explain."),
  ("google-research/android_world", "Apache-2.0", "study",
   "<b>A benchmark of 116 tasks across 20 real Android apps.</b> Use it as your regression suite. "
   "Also use its published success rates as the honest ceiling on what unattended UI automation "
   "achieves — which is the number your fingerprint gate exists to work around."),
  ("OpenBMB/AgentCPM-GUI", "Apache-2.0", "study",
   "<b>An on-device GUI agent model.</b> Interesting later, when a flow needs to survive a layout "
   "change without a human re-mapping it. Not the v1 mechanism; your v1 advantage is that you do "
   "<i>not</i> need a model to tap a button."),
  ("bytedance/UI-TARS", "Apache-2.0", "study",
   "<b>A GUI agent model with real benchmark numbers.</b> Same category, further along. Read the "
   "failure analysis rather than the headline scores."),
  ("microsoft/OmniParser", "MIT", "study",
   "<b>Turns a screenshot into structured, labelled elements.</b> The fallback when there is no "
   "accessibility tree — for example inside a WebView or a game-engine UI."),
  ("simular-ai/Agent-S", "Apache-2.0", "study",
   "<b>An agent framework for computer use.</b> Read the memory and retry design."),
  ("mobile-next/mobile-mcp", "Apache-2.0", "use",
   "<b>Mobile control exposed as an MCP server.</b> Not an alternative executor — a projection. "
   "This is how an assistant asks your device layer to do something without being handed ADB."),
  ("*droidrun/mobilerun", "Apache-2.0", "study",
   "<b>LLM-agnostic mobile agent: inspect UI state, read screenshots, tap, swipe, type, plan.</b> "
   "Verified today as a live project. The closest public thing to your executor — read it for "
   "their tool surface, and note how much of their complexity comes from letting a model decide."),
  ("*callstackincubator/agent-device", "MIT", "use",
   "<b>Mobile automation and verification for coding agents — CLI, MCP server and typed Node "
   "API across iOS, Android, TV, web, macOS and Linux.</b> Note the correct org: it is "
   "<span class='mono'>callstackincubator</span>, not <span class='mono'>callstack</span>. The "
   "word <i>verification</i> in their own description is the interesting part; read how they do it."),
  ("sktyou/OpenGUI", "—", "study",
   "<b>An Android GUI agent framework for phone-use AI.</b> Verified to exist; small and young. "
   "Read, do not depend."),
  ("yashab-cyber/opendroid", "—", "care",
   "<b>Appeared in the session's search results.</b> I could not re-verify its scope today — "
   "GitHub is unreachable from this environment. Treat as a lead, not a part, until you have "
   "opened it yourself."),
  ("waydroid/waydroid", "GPL-3.0", "care",
   "<b>Android in a container on Linux.</b> Tempting: no physical phone. But it defeats the entire "
   "premise — the customer's own SIM, the customer's own logged-in accounts, a real device they can "
   "pick up. Useful for your test rig, wrong for the product."),
  ("block/trailblaze", "Apache-2.0", "study",
   "<b>Android UI automation aimed at agents.</b> Small, recent, directly on your path."),
  ("google/device-infra", "Apache-2.0", "study",
   "<b>Google's own device lab infrastructure.</b> Read when you have fifty phones on a rack and "
   "the problem becomes logistics rather than automation."),
  ("textbee/textbee", "GPL-3.0", "use",
   "<b>Turns an Android phone into an SMS gateway over its own SIM.</b> This is the text-message "
   "marketing channel, sent from the business's real number, with no Twilio in the path and no "
   "per-message rake. Note the GPL-3.0 before it goes in a shipped image."),
  ("google/artemis", "—", "skip",
   "<b>Appeared in the session as a mobile-automation reference.</b> I cannot verify it today and "
   "cannot confirm the repository is what it was described as. Do not put it in a plan until you "
   "have looked."),
 ],
 flag=("The row with no upstream",
  "Fingerprint-gated, independently verified remote control is the one job in this catalog that "
  "nothing here does. Every project above will happily tap a button and report success. None of "
  "them refuse to act because the screen is not the screen they were mapped against, and none read "
  "the result back on a different path to prove it landed. That gate and that read-back are the "
  "product. Everything else is a part you did not have to build."))

# ---------------------------------------------------------------- 11
sec("11", "The other two execution paths",
 "The verifier must not be the executor. If you write through Android and read back through "
 "Android, you have built self-certification with extra steps. These are the independent paths.",
 [
  ("microsoft/playwright", "Apache-2.0", "core",
   "<b>Browser automation that is reliable enough to bet on.</b> Two jobs: the vendors that have a "
   "usable web interface, and — more importantly — the independent read-back path that proves an "
   "Android write actually landed."),
  ("microsoft/playwright-mcp", "Apache-2.0", "use",
   "<b>Playwright as an MCP server.</b> Same projection logic as mobile-mcp: the assistant asks, "
   "it does not drive."),
  ("browser-use/browser-use", "MIT", "care",
   "<b>Let a model drive a browser.</b> Genuinely useful for mapping a new site quickly. Keep it "
   "in the factory, out of the runtime — a model improvising on a customer's live booking system "
   "is the exact failure mode your whole design avoids."),
  ("trycua/cua", "MIT", "study",
   "<b>Computer-use agents in sandboxed VMs.</b> Read the sandbox boundary."),
  ("OpenHands/OpenHands", "MIT", "study",
   "<b>Formerly OpenDevin.</b> Read the execution-and-verification loop; ignore the coding focus."),
  ("openinterpreter/open-interpreter", "AGPL-3.0", "care",
   "<b>Natural language to executed code, locally.</b> Instructive, and the AGPL makes it a "
   "distribution problem for a box you sell."),
  ("ydotool/ydotool", "AGPL-3.0", "care",
   "<b>Input automation on Wayland.</b> Sometimes the only way to drive a stubborn desktop app. "
   "Check the licence against your shipping plan."),
 ],
 flag=("Say it in the manifest",
  "Each capability should name its write path and its verify path, and the two must differ. "
  "\"Wrote via Android, verified via browser\" is a sentence a customer understands and a claim a "
  "sceptic can test. It is also the difference between a run record and a receipt."))

# ---------------------------------------------------------------- 12
sec("12", "Their screen, on their phone",
 "The feature that makes an owner feel they own the thing: pick up an iPhone, see the Android "
 "device sitting in the back office, take over.",
 [
  ("LizardByte/Sunshine", "GPL-3.0", "care",
   "<b>Self-hosted low-latency desktop streaming host.</b> GPL-3.0 matters if it ships on hardware "
   "you sell — read it properly before it is load-bearing."),
  ("moonlight-stream/moonlight-qt", "GPL-3.0", "study",
   "<b>The client side.</b> Same licence note."),
  ("Genymobile/scrcpy", "Apache-2.0", "core",
   "<b>Listed again deliberately.</b> For the phone specifically, scrcpy plus ws-scrcpy is a "
   "simpler and better answer than a desktop streaming stack. Use the streaming pair only if you "
   "ever need to show the box's own screen."),
 ])

# ---------------------------------------------------------------- 13
sec("13", "Agent protocols and the orchestration layer",
 "You are selling the harness. This is the wiring the harness is made of — and the standards "
 "question is now settled enough to build on.",
 [
  ("modelcontextprotocol/modelcontextprotocol", "MIT", "core",
   "<b>MCP, the specification.</b> The way a customer's own data becomes available to an assistant "
   "without leaving their machine. Your 'attach it and it stays on their computer' promise is this "
   "protocol, implemented honestly."),
  ("modelcontextprotocol/servers", "MIT", "use",
   "<b>Reference servers.</b> Read three, then write yours; the patterns are more useful than the "
   "code."),
  ("modelcontextprotocol/python-sdk", "MIT", "use", "<b>Python SDK.</b> The node speaks this."),
  ("modelcontextprotocol/typescript-sdk", "MIT", "use", "<b>TypeScript SDK.</b> The surfaces speak this."),
  ("*a2aproject/A2A", "Apache-2.0", "core",
   "<b>Agent-to-agent communication.</b> This is the wire for your zero-data developer story: the "
   "developer's agent talks to the business's agent, the answer crosses, the data does not. "
   "Verified today: the protocol landscape has converged under Linux Foundation governance, with "
   "IBM's ACP folded into this effort rather than competing with it."),
  ("agentclientprotocol/agent-client-protocol", "Apache-2.0", "study",
   "<b>The editor-to-agent protocol.</b> Adjacent; read for the handshake design."),
  ("IBM/mcp-context-forge", "Apache-2.0", "core",
   "<b>ContextForge: an MCP gateway and registry.</b> Federates many MCP servers behind one "
   "endpoint with auth, rate limits and an admin view. You will have dozens of MCP servers per "
   "node; without a gateway that becomes unmanageable around server number six."),
  ("i-am-bee/beeai-framework", "Apache-2.0", "care",
   "<b>IBM's multi-agent framework, now under the Linux Foundation.</b> Verified today: real "
   "governance, real backing. Still moving fast — read the agent/workflow decomposition, and keep "
   "your orchestrator's core independent of it so a breaking release is an afternoon, not a quarter."),
  ("i-am-bee/beeai-platform", "Apache-2.0", "study",
   "<b>The platform around the framework.</b> Discovery and run management for agents from "
   "different frameworks. Closest public analogue to your orchestrator's job."),
  ("i-am-bee/beeai-code-interpreter", "Apache-2.0", "study",
   "<b>Sandboxed code execution for agents.</b> Compare against Extism before choosing."),
  ("NousResearch/hermes-agent", "Apache-2.0", "study",
   "<b>An agent harness built around tool use.</b> Read the tool-calling loop."),
  ("langchain-ai/langgraph", "MIT", "care",
   "<b>Graph-structured agent workflows with checkpointing.</b> The state machine is the good "
   "idea. Take it; resist the rest of the ecosystem, which is a dependency surface you do not need "
   "on an appliance."),
  ("block/goose", "Apache-2.0", "study",
   "<b>A local, extensible agent.</b> Read the extension model — it is close to what your VAPP "
   "contract has to do."),
 ],
 flag=("Where the dumb agent lives",
  "MCP is how it reaches data. A2A is how it talks to someone else's agent without handing over "
  "the data. ContextForge is how you survive having thirty MCP servers per node. Everything else "
  "in this section is reading."))

# ---------------------------------------------------------------- 14
sec("14", "Workflow, events and durable execution",
 "A flow that taps four screens across two apps and dies halfway has to be explainable, resumable "
 "and — where it cannot resume — compensable. That is a durability problem, not an automation one.",
 [
  ("temporalio/temporal", "MIT", "core",
   "<b>Durable execution: workflows survive crashes, restarts and deploys, with full history.</b> "
   "The compensating-action problem — a price change applied to two of four destinations is worse "
   "than one that failed cleanly — is exactly what this is built for. The run history is also your "
   "audit trail for free."),
  ("restatedev/restate", "BUSL-1.1", "care",
   "<b>Durable execution, lighter to operate.</b> Note the BUSL licence: source-available, not open "
   "source, with a delayed conversion. That is a business-model decision you would be adopting, not "
   "just a library."),
  ("nats-io/nats-server", "Apache-2.0", "use",
   "<b>Messaging with JetStream persistence, in a single small binary.</b> The right size for a "
   "box in a restaurant. Kafka is the wrong size by two orders of magnitude."),
  ("apache/kafka", "Apache-2.0", "skip",
   "<b>Not for an appliance.</b> Listed because it came up, and because knowing why you said no is "
   "worth a line."),
  ("apache/flink", "Apache-2.0", "skip", "<b>Same.</b> Stream processing at a scale you will never have on one node."),
  ("ansible/ansible", "GPL-3.0", "use",
   "<b>Agentless configuration and orchestration.</b> Your provisioning tool for the factory bench, "
   "not something that runs on a customer's box."),
  ("ansible/awx", "Apache-2.0", "study",
   "<b>The upstream of Automation Controller.</b> Read the job-template and credential model."),
  ("ansible/event-driven-ansible", "Apache-2.0", "study",
   "<b>Rules that fire actions from events.</b> The shape of your drift-detected → re-map-queued "
   "pipeline."),
  ("activepieces/activepieces", "MIT", "study",
   "<b>Open-source automation with an MCP story.</b> Read the piece/connector model — it is close "
   "to your VAPP shape and genuinely MIT."),
  ("ComposioHQ/composio", "Apache-2.0", "study",
   "<b>A large managed catalogue of tool integrations for agents.</b> Read how they handle auth "
   "per-tool; that problem will eat a month of your life."),
  ("node-red/node-red", "Apache-2.0", "study",
   "<b>Flow-based programming with a visual editor.</b> Twelve years of evidence about what "
   "non-programmers can and cannot assemble. Relevant the day an owner wants to change a flow."),
  ("n8n-io/n8n", "Sustainable Use", "skip",
   "<b>Not open source.</b> The Sustainable Use Licence restricts commercial hosting. It gets "
   "called open source constantly, including by people selling advice. Using it inside a product "
   "you sell is a licensing conversation you do not want to have late."),
 ])

# ---------------------------------------------------------------- 15
sec("15", "Models and inference — the terabyte of specialists",
 "A terabyte of specialised models on the box, one endpoint in front of them, and something that "
 "swaps them fast enough that a customer never feels it.",
 [
  ("ggml-org/llama.cpp", "MIT", "core",
   "<b>The engine room.</b> Quantised inference on ordinary hardware, with an OpenAI-compatible "
   "server built in. MIT, no strings, runs on the AMD unified-memory part you picked."),
  ("mostlygeek/llama-swap", "MIT", "core",
   "<b>Hot-swaps models behind one endpoint, each in its own process.</b> This is the specific "
   "piece that makes 'a terabyte of specialists' work instead of being a directory of files. "
   "Process isolation matters: one bad model cannot take the endpoint down."),
  ("ggml-org/whisper.cpp", "MIT", "use",
   "<b>Speech recognition, same engine family.</b> Use when you want one runtime rather than two."),
  ("vllm-project/vllm", "Apache-2.0", "care",
   "<b>High-throughput serving.</b> Built for many concurrent users on server GPUs. You have one "
   "business per box. Right answer for your cloud tier, wrong answer for the appliance."),
  ("ollama/ollama", "MIT", "care",
   "<b>The easiest local-model experience there is</b> — and a wrapper around llama.cpp. Perfect "
   "for your laptop this week. On a product you sell, go one layer down so you control quantisation, "
   "memory and swap behaviour yourself."),
  ("BerriAI/litellm", "MIT", "use",
   "<b>One API shape in front of every provider, local or hosted.</b> Your neutrality claim, in "
   "code: the customer can point at your local models, or their own OpenAI key, and nothing "
   "upstream changes."),
  ("open-webui/open-webui", "BSD-3-Clause", "study",
   "<b>A polished local-model UI.</b> Read the model-management screens; that is a UI problem you "
   "would otherwise solve badly."),
  ("huggingface/huggingface_hub", "Apache-2.0", "use",
   "<b>Fetch and cache models programmatically.</b> Your model catalogue's download path — and "
   "worth mirroring into your own registry so a customer's box does not depend on someone else's "
   "uptime."),
  ("instructlab/instructlab", "Apache-2.0", "study",
   "<b>Community model tuning with synthetic data generation.</b> The path from 'the restaurant "
   "vertical needs its own adapter' to actually having one, without a research team."),
  ("ibm-granite/granite-guardian", "Apache-2.0", "use",
   "<b>A small model that checks other models' inputs and outputs for harm.</b> Cheap insurance on "
   "a device that writes to a business's public presence."),
  ("ibm-granite/granite-speech-models", "Apache-2.0", "study", "<b>Speech models, Apache-2.0.</b> An alternative to Whisper with a clean licence."),
  ("ibm-granite/granite-vision-models", "Apache-2.0", "study", "<b>Vision models.</b> Relevant for reading a screenshot when the accessibility tree fails."),
  ("ibm-granite/granite-tsfm", "Apache-2.0", "study", "<b>Time-series foundation models.</b> Demand forecasting, much later."),
  ("meta-llama/llama-stack", "MIT", "study",
   "<b>A standardised API surface for inference, safety and agents.</b> Build to the Responses API "
   "shape whether or not you adopt the stack — it is becoming the common denominator."),
  ("kserve/kserve", "Apache-2.0", "skip", "<b>Kubernetes model serving.</b> Wrong deployment shape for a box."),
  ("llm-d/llm-d", "Apache-2.0", "skip", "<b>Distributed serving on Kubernetes.</b> Same."),
  ("ROCm/ROCm", "MIT", "use",
   "<b>AMD's compute stack.</b> The reason the hardware choice and the software choice are the same "
   "decision. Verify your exact part is supported by the exact ROCm version before you buy a pallet."),
  ("NVIDIA/Personal-AI-Router", "Apache-2.0", "study",
   "<b>Routing between local and remote models.</b> Read the routing policy; you need the same "
   "decision made on cost, privacy and latency."),
  ("agentscope-ai/QwenPaw", "Apache-2.0", "study", "<b>An agent runtime worth a read, not a dependency.</b>"),
  ("xai-org/grok-1", "Apache-2.0", "study",
   "<b>The weights release.</b> Relevant only as evidence of what 'open' means to the company you "
   "are positioning against."),
 ],
 flag=("The swap trick worth knowing",
  "Loading a different model costs five to eight seconds. Swapping a LoRA adapter on a loaded base "
  "costs roughly two hundred milliseconds. If your verticals can be adapters over one base rather "
  "than twenty separate models, the box feels instant and the terabyte becomes a library rather "
  "than a queue."))

# ---------------------------------------------------------------- 16
sec("16", "Voice",
 "Wake word, endpointing, transcription, speech. Four small models and one protocol that lets them "
 "be swapped independently. This is also the demo people remember.",
 [
  ("rhasspy/wyoming", "MIT", "core",
   "<b>The protocol that lets each voice piece be a separate service.</b> Swap the TTS without "
   "touching the wake word. Home Assistant runs on this in production across a very large install "
   "base."),
  ("dscripka/openWakeWord", "Apache-2.0", "use",
   "<b>Wake word detection, trainable on your own phrase.</b> \"Hey Ghost\" is a training run, not "
   "a licensing negotiation."),
  ("snakers4/silero-vad", "MIT", "use",
   "<b>Voice activity detection.</b> Tiny, fast, and the difference between a system that knows "
   "when you stopped talking and one that interrupts people."),
  ("SYSTRAN/faster-whisper", "MIT", "use",
   "<b>Whisper via CTranslate2 — several times faster, much less memory.</b> The practical "
   "transcription choice."),
  ("*rhasspy/piper", "MIT", "skip",
   "<b>Archived 6 October 2025.</b> Verified today. It is still the top result everywhere and still "
   "in a great many build guides. Do not start here."),
  ("*OHF-Voice/piper1-gpl", "GPL-3.0", "care",
   "<b>Where Piper's development actually moved.</b> Verified today — and note the licence change "
   "from MIT to GPL-3.0. If you were planning on Piper because it was MIT, that reason no longer "
   "exists, and this is exactly the kind of thing that is expensive to discover after you have "
   "shipped hardware."),
  ("hexgrad/kokoro", "Apache-2.0", "core",
   "<b>82M parameters, genuinely good voice, Apache-2.0.</b> The right default now: small enough "
   "for the box, clean enough for a product you sell."),
  ("speaches-ai/speaches", "MIT", "use",
   "<b>An OpenAI-compatible server for speech-to-text and text-to-speech.</b> One familiar API in "
   "front of the whole voice stack."),
  ("pipecat-ai/pipecat", "BSD-2-Clause", "use",
   "<b>Real-time voice conversation orchestration</b> — interruption, turn-taking, barge-in. The "
   "things that separate a voice demo from a phone agent that does not infuriate callers."),
  ("livekit/livekit", "Apache-2.0", "use",
   "<b>WebRTC infrastructure, self-hostable.</b> The transport when the voice agent has to answer "
   "an actual phone call."),
  ("livekit/agents", "Apache-2.0", "study", "<b>Their agent framework on top.</b> Read the turn-taking implementation."),
  ("fonoster/fonoster", "MIT", "study",
   "<b>Open-source programmable telephony.</b> The self-hosted answer to the question you already "
   "asked out loud — why am I paying Twilio."),
  ("home-assistant/hassil", "Apache-2.0", "use",
   "<b>Template-based intent matching.</b> Most voice commands in a business are eight fixed "
   "sentences. Matching them with templates is faster, cheaper and more predictable than asking a "
   "model, and it never hallucinates a reservation."),
 ])

# ---------------------------------------------------------------- 17
sec("17", "The data plane",
 "Private truth on the node, signed projections on the read-only edge, and a backup the customer "
 "controls and you cannot read.",
 [
  ("postgres/postgres", "PostgreSQL", "core",
   "<b>The node's database.</b> One node per business, no tenant_id column anywhere — the isolation "
   "is the deployment, which is a far stronger claim than a WHERE clause."),
  ("pgvector/pgvector", "PostgreSQL", "use",
   "<b>Vectors inside Postgres.</b> One database to back up, one to restore, one to reason about."),
  ("asg017/sqlite-vec", "Apache-2.0 / MIT", "use",
   "<b>Vector search in SQLite.</b> For the small edge case where Postgres is too much machinery."),
  ("benbjohnson/litestream", "Apache-2.0", "use",
   "<b>Continuous streaming replication of SQLite to object storage.</b> Disaster recovery for the "
   "small database, with no server."),
  ("restic/restic", "BSD-2-Clause", "core",
   "<b>Encrypted, deduplicated backup to a destination the customer chooses.</b> Their NAS, their "
   "bucket, their key. They are protected from a dead drive; you still hold nothing. This one "
   "component is most of the 'no data, no liability' position made real."),
  ("meilisearch/meilisearch", "MIT", "use",
   "<b>Fast, typo-tolerant search with almost no operational burden.</b> The right size for 'who "
   "has crab legs nearby' across one town."),
  ("qdrant/qdrant", "Apache-2.0", "study", "<b>A dedicated vector database.</b> Only if pgvector stops being enough, which it will not for a long time."),
  ("opensearch-project/OpenSearch", "Apache-2.0", "skip", "<b>Too heavy for a box.</b> Noted so the question stays answered."),
  ("supabase/supabase", "Apache-2.0", "care",
   "<b>Postgres plus auth, storage and realtime, self-hostable.</b> A fast start and a large "
   "surface. If you adopt it, adopt it deliberately as the node's platform rather than letting it "
   "arrive one feature at a time."),
 ],
 flag=("The thing you cannot add later",
  "Provenance. If you write canonical values for six months and then decide you want to know where "
  "each one came from, you have six months of data with no origin and no way to reconstruct it. "
  "The observation table goes in before the first ingestion runs, not after the first dispute."))

# ---------------------------------------------------------------- 18
sec("18", "Getting the data in — email as the universal API",
 "Every vendor already emails the business: the booking confirmation, the daily sales summary, the "
 "payout notice. That inbox is an integration nobody can revoke.",
 [
  ("apache/tika", "Apache-2.0", "use",
   "<b>Extracts text and metadata from a thousand file formats.</b> The unglamorous front door for "
   "every PDF a vendor sends."),
  ("docling-project/docling", "MIT", "core",
   "<b>Turns PDFs into structured documents — tables as tables, not as mangled text.</b> A daily "
   "sales summary is a table in a PDF; this is the component that makes it a row in your database."),
  ("google/langextract", "Apache-2.0", "use",
   "<b>Structured extraction from unstructured text, with the source span recorded.</b> That last "
   "part is the point: every canonical value can point at the exact sentence it came from."),
  ("google/magika", "Apache-2.0", "use",
   "<b>Reliable file-type detection.</b> The first check on anything arriving from outside."),
  ("google/schema-dts", "Apache-2.0", "use",
   "<b>Typed schema.org for TypeScript.</b> How the public projection becomes machine-readable, "
   "which is how a business shows up correctly in an assistant's answer instead of an index's."),
 ],
 flag=("Rank the setup paths by friction",
  "First: add your address as a second notification email inside the vendor's own settings — Toast, "
  "Square and FareHarbor all allow it, and Gmail is never involved. Second: a Gmail filter and a "
  "verified forwarding address, two minutes in a UI they already know. Last resort: an Apps Script. "
  "\"Run this script\" kills conversion at the exact moment the product needs to feel like nothing."))

# ---------------------------------------------------------------- 19
sec("19", "Identity, authorization, policy, secrets",
 "One login, many apps — and a permission model the Agent Plugins specification openly says it does "
 "not have. This layer is where your store stops being a copy of someone else's.",
 [
  ("zitadel/zitadel", "Apache-2.0", "core",
   "<b>Identity and access management, self-hostable, multi-tenant, Apache-2.0.</b> Lighter than "
   "Keycloak to run and operate. This is 'one login, many apps' with nothing phoning home."),
  ("keycloak/keycloak", "Apache-2.0", "care",
   "<b>The heavyweight, Red Hat's SSO.</b> More capable, more to run. Choose it only if you need "
   "something Zitadel lacks, and write down what that was."),
  ("authzed/spicedb", "Apache-2.0", "core",
   "<b>Google Zanzibar-style fine-grained authorization.</b> Relationship-based permissions — this "
   "user, this business, this capability, this app. The enforcement point for capability lists, and "
   "the reason an app cannot quietly read something it was not granted."),
  ("openfga/openfga", "Apache-2.0", "study",
   "<b>The CNCF alternative.</b> Same model, different trade-offs. Pick one and never run both."),
  ("open-policy-agent/opa", "Apache-2.0", "use",
   "<b>Policy as code, evaluated anywhere.</b> The gate that decides whether a capability call is "
   "allowed given the constitution, the consent state and the time of day."),
  ("openbao/openbao", "MPL-2.0", "core",
   "<b>The open fork of Vault.</b> Secrets, dynamic credentials, rotation. The customer's vendor "
   "logins live here, on their node, encrypted to hardware — not in a config file and not in your "
   "cloud."),
 ],
 flag=("The gap you are filling, stated plainly",
  "The Agent Plugins specification says, in its own words, that it contains no explicit capability "
  "or permission system. Grok's install command is <span class='mono'>--trust</span>, and trust is "
  "binary. Fine on a developer's laptop; not fine on a machine holding a business's operational "
  "data. SpiceDB plus OPA plus Extism is the answer, and it is the most defensible thing you are "
  "building."))

# ---------------------------------------------------------------- 20
sec("20", "Reaching the box without owning it",
 "You need to support a machine in someone's back office without a standing door into their "
 "network — and without a VPN account you could be compelled to use.",
 [
  ("juanfont/headscale", "BSD-3-Clause", "use",
   "<b>A self-hosted control plane for Tailscale clients.</b> You run the coordination, the "
   "customer runs the node, and the traffic is still end-to-end encrypted between devices."),
  ("tailscale/tailscale", "BSD-3-Clause", "study",
   "<b>The client, and the hosted service.</b> Read the ACL model even if you self-host the control "
   "plane."),
  ("netbirdio/netbird", "BSD-3-Clause", "study",
   "<b>The all-in-one alternative.</b> Simpler to stand up, one more thing you operate."),
 ],
 flag=("Support access is a design decision, not a default",
  "The strongest version: no standing access at all. The customer grants a session, it expires, and "
  "the grant is recorded in the transparency log. That is harder to build and much easier to say "
  "out loud in a sales conversation — and it is the same argument you are already making about data."))

# ---------------------------------------------------------------- 21
sec("21", "Money",
 "Zero percent of the platform, one percent of the payment volume, and a spread you renegotiate as "
 "the volume grows. That arrangement needs metering you can defend.",
 [
  ("getlago/lago", "AGPL-3.0", "use",
   "<b>Open-source usage-based billing and metering.</b> The AGPL is survivable here because you "
   "run it as a service rather than distributing it — but make that call deliberately."),
  ("killbill/killbill", "Apache-2.0", "study",
   "<b>Mature subscription billing.</b> Heavier, Apache-2.0, fifteen years of edge cases already "
   "found by other people."),
  ("dubinc/dub", "AGPL-3.0", "study",
   "<b>Link attribution.</b> The referral and co-op loyalty mechanics need attribution that "
   "survives a click; this is a working implementation to read."),
  ("candlepin/candlepin", "GPL-2.0", "core",
   "<b>Listed again on purpose.</b> Lago meters usage. Candlepin decides entitlement — whether this "
   "box may pull this update today. Two different jobs, and conflating them is how subscription "
   "businesses end up unable to answer 'is this customer paid up' from a single source."),
 ],
 flag=("The number to watch",
  "With destination charges the platform carries dispute liability by default, plus negative "
  "balances when a business closes holding deposits. Budget 0.1–0.3% of volume for disputes and "
  "reserves. That is what turns a one-point spread into roughly seven tenths of one."))

# ---------------------------------------------------------------- 22
sec("22", "The app store layer",
 "The package format is settled, the distribution model is proven, and the trust ladder already "
 "exists in three different forms. None of this needs inventing — which is Part VI's whole argument.",
 [
  ("*agentplugins/agent-plugins-spec", "—", "core",
   "<b>Agent Plugins 1.0.0 — the package format.</b> Verified today, and better backed than the "
   "session thought: the technical steering committee is Amazon, Cursor, Microsoft, OpenAI and "
   "Vercel, under the Agentic AI Foundation. <span class='mono'>plugin.json</span>, a strict field "
   "list, Skills and MCP servers, path containment, PLUGIN_ROOT/PLUGIN_DATA isolation. Your VAPP "
   "manifest rides in <span class='mono'>extensions.io.anextgent</span>."),
  ("agentskills/agentskills", "—", "core",
   "<b>Agent Skills — the unit inside the package.</b> SKILL.md with frontmatter and progressive "
   "disclosure: about a hundred tokens of name and description loaded for every skill at startup, "
   "the body only on activation, resources only on demand. That first tier is your router, and the "
   "description field is the trigger rule."),
  ("neondatabase/agent-skills", "Apache-2.0", "study",
   "<b>A real, well-built skill set.</b> Read the descriptions specifically — they are written as "
   "phrase lists that route, which is the technique."),
  ("*vercel/skills", "—", "use",
   "<b>The installer pattern, verified today.</b> Vercel's <span class='mono'>skills</span> CLI "
   "installs across forty-plus agents using a provider registry, a <span class='mono'>.skillsrc</span> "
   "config and a <span class='mono'>.skill-lock.json</span> that compares directory tree SHAs to "
   "detect updates. That lock-file-and-tree-SHA design is what you want on the node, and it comes "
   "from a company on the specification's steering committee."),
  ("junior/skilla", "—", "care",
   "<b>The installer the session identified, with its local registry.json.</b> I could not "
   "re-verify it today — GitHub is unreachable from here and it does not surface in search. Check "
   "it yourself; if it has gone quiet, the Vercel CLI above is the better-supported pattern anyway."),
  ("xai-org/plugin-marketplace", "—", "study",
   "<b>Index, not store.</b> The catalogue entry points at someone else's repository at a pinned "
   "full-length commit SHA. xAI never hosts the code. That model costs almost nothing to run and "
   "puts liability where the code is — read it closely, it is the cheapest distribution design "
   "available to you."),
  ("xai-org/grok-build", "—", "study", "<b>The build tooling around it.</b> Read the manifest validation."),
  ("superagent-ai/grok-cli", "MIT", "study", "<b>A third-party client.</b> Evidence of what the ecosystem does once a format is published."),
  ("vercel/vercel-plugin", "—", "study", "<b>A real plugin in the wild.</b> Read one before you specify yours."),
  ("getsentry/sentry-for-ai", "—", "study", "<b>Another.</b> Two examples is enough to see the conventions."),
  ("redhat-openshift-ecosystem/redhat-marketplace-operators", "Apache-2.0", "study",
   "<b>How certified content is submitted, reviewed and published.</b> The submission pipeline for "
   "a trust ladder, already written down by people who run one."),
 ],
 flag=("The trust ladder, borrowed from people who run one",
  "Red Hat operates four distinct stores, and Automation Hub has three tiers: community content, "
  "certified content, and a private hub the customer controls. Map yours to community → verified → "
  "the business's own private index. The pinned full SHA is what makes any of it enforceable, "
  "because a tag can be moved and a forty-character commit hash cannot."))

# ---------------------------------------------------------------- 23
sec("23", "Surfaces — what the customer and the world actually see",
 "Four surfaces, one record behind them. The owner's console, the kiosk, the public page, and the "
 "agent endpoint.",
 [
  ("puckeditor/puck", "MIT", "use",
   "<b>A visual editor for React, embeddable in your own app.</b> The owner rearranges their public "
   "page without a developer and without you building a page builder from scratch."),
  ("shadcn/ui", "MIT", "use",
   "<b>Components you copy into your codebase rather than depend on.</b> No upstream that can break "
   "you, no version to chase. The right model for a product with a ten-year support horizon."),
  ("flutter/flutter", "BSD-3-Clause", "care",
   "<b>One codebase for the owner's phone app.</b> Real value if the owner app matters; a second "
   "language and toolchain for a team of one. Consider a web app first and be honest about whether "
   "anyone actually asked for an app."),
  ("microsoft/PowerToys", "MIT", "study",
   "<b>Listed because it came up.</b> Read PowerToys Run as an interaction study for the box's "
   "command surface, then move on."),
 ])

# ---------------------------------------------------------------- 24
sec("24", "Read, do not adopt — the IBM and Red Hat shelf",
 "You said Red Hat is the model and Watson was open source. Both true. These are worth reading for "
 "how a platform business is structured, and worth not adopting, because each one assumes an "
 "operating environment you do not have.",
 [
  ("IBM/watsonx-developer-hub", "Apache-2.0", "study",
   "<b>How a large vendor presents an agent platform to developers.</b> Read the onboarding path — "
   "it is the thing you are competing with for a developer's first hour."),
  ("IBM/watsonx-data", "—", "study", "<b>The data layer.</b> Read the governance vocabulary; you will need the words."),
  ("opendatahub-io/opendatahub-operator", "Apache-2.0", "study",
   "<b>The upstream of Red Hat's AI platform.</b> Kubernetes-shaped. Read the component "
   "decomposition, which is a good map of what an AI platform is made of."),
  ("cockpit-project/cockpit", "LGPL-2.1", "study",
   "<b>Listed twice deliberately.</b> As a study item it is the best example of a web UI that "
   "manages a Linux host without pretending Linux is not there."),
 ],
 flag=("What the IBM and Red Hat reading is actually for",
  "Not the code. The structure: content in one system, entitlement in another, certification as its "
  "own track, metering separate from billing, and a policy gate that can say no without a human. "
  "That structure is the business you described, and it is documented in public by a company that "
  "makes billions running it."))

# ---------------------------------------------------------------- 25
sec("25", "The live traps",
 "Things that will cost you a week or a lawyer if you find them late. Every one of these is "
 "currently a top search result for something you will search for.",
 [
  ("*rhasspy/piper", "MIT, archived", "skip",
   "<b>Archived October 2025</b>, and development moved to a <b>GPL-3.0</b> fork. Verified today. "
   "Every tutorial still points here."),
  ("n8n-io/n8n", "Sustainable Use", "skip",
   "<b>Not open source</b>, despite being described that way nearly everywhere. Commercial hosting "
   "is restricted."),
  ("ximion/appstream", "LGPL-2.1", "care",
   "<b>The name collision.</b> This project, RHEL's AppStream repository, and anything of yours "
   "called AppStream makes three. Rename yours now, while renaming is a find-and-replace."),
  ("ollama/ollama", "MIT", "care",
   "<b>Not a trap, a boundary.</b> Ship llama.cpp; develop on ollama. Shipping a wrapper means "
   "debugging someone else's defaults on a customer's box."),
  ("restatedev/restate", "BUSL-1.1", "care",
   "<b>Source-available, not open source.</b> BUSL converts to an open licence on a delay; know the "
   "date before you depend on it."),
  ("trufflesecurity/trufflehog", "AGPL-3.0", "care",
   "<b>AGPL.</b> Fine as a tool your CI runs. A distribution question if it is linked into "
   "something you ship."),
  ("openinterpreter/open-interpreter", "AGPL-3.0", "care", "<b>AGPL.</b> Same reasoning."),
  ("getlago/lago", "AGPL-3.0", "care", "<b>AGPL.</b> Run it as a service and it is fine; bundle it and it is not."),
  ("LizardByte/Sunshine", "GPL-3.0", "care",
   "<b>GPL-3.0 on hardware you sell</b> brings the anti-tivoisation provisions into play. Read them "
   "properly before this becomes load-bearing."),
  ("textbee/textbee", "GPL-3.0", "care", "<b>GPL-3.0.</b> Same question, and this one sits in the SMS marketing feature you already want."),
  ("89luca89/distrobox", "GPL-3.0", "care", "<b>GPL-3.0.</b> A developer tool rather than shipped product, which resolves it — but note it."),
  ("waydroid/waydroid", "GPL-3.0", "care", "<b>GPL-3.0, and wrong for the product anyway.</b> The customer's real SIM is the point."),
  ("google/artemis", "—", "skip",
   "<b>Unverifiable from here.</b> It was in the session's list; I could not confirm it today. "
   "Anything you cannot open is not a part."),
  ("google/CAGE", "—", "skip", "<b>Same.</b> Confirm before it appears in a plan."),
  ("yashab-cyber/opendroid", "—", "care", "<b>Same.</b> A lead until you have read it."),
  ("junior/skilla", "—", "care", "<b>Same.</b> The Vercel skills CLI is the better-supported pattern regardless."),
 ],
 flag=("Why this section exists",
  "Licences change, projects get archived, and orgs move. Three of the entries above changed after "
  "they were first written down in this project — Piper archived and relicensed, bootc moved orgs, "
  "agent-device is under callstackincubator rather than callstack. Re-check anything load-bearing "
  "before a build, not after a customer calls."))
