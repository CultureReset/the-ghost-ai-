/* The shell's views.
 *
 * Every number on this screen comes from GET /api/home. There is no constant
 * in this file that a business would recognise as its own -- no sales figure,
 * no review count, no box name. If the database is empty the screen says so
 * rather than showing a pleasant fiction, because a dashboard that looks
 * healthy when nothing is connected is worse than no dashboard.
 */
import { I, heroArt } from "./art.js";

const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g,
  c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;" }[c]));
const money = c => "$" + (c / 100).toLocaleString(undefined,
  { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const money0 = c => "$" + Math.round(c / 100).toLocaleString();
const ago = s => { if (!s) return "never";
  const m = Math.floor((Date.now() - new Date(s.replace(" ", "T") + "Z")) / 60000);
  if (m < 1) return "just now";
  if (m < 60) return m + " min ago";
  if (m < 1440) return Math.floor(m / 60) + " hr ago";
  const d = Math.floor(m / 1440);
  return d === 1 ? "yesterday" : d + " days ago"; };
const hhmm = t => { if (!t) return "";
  const [h, m] = String(t).slice(-5).split(":").map(Number);
  const ap = h >= 12 ? "PM" : "AM";
  return `${((h + 11) % 12) + 1}:${String(m).padStart(2, "0")} ${ap}`; };

let D = {};              // everything the server knows
let TAB = "home";
let HUB = "overview";

/* ------------------------------------------------------------- pieces */
const dot = k => `<span class="dot ${k}"></span>`;
const ico = (glyph, color, size = "") =>
  `<span class="ico ${size}" style="background:${color}">${glyph}</span>`;

function statCard(o) {
  return `<button class="stat">
    ${ico(I[o.icon]({ w: 19, s: "#fff" }), o.color, "sm")}
    <div>
      <div class="cap">${esc(o.label)}</div>
      <div class="n">${o.value}${o.delta || ""}</div>
      <div class="k">${esc(o.sub || "")}</div>
    </div>
    <span class="chev">${I.caret()}</span>
  </button>`;
}

function head(title, more) {
  return `<div class="shead"><h2>${esc(title)}</h2>
    <span class="caret">${I.caret({ w: 12 })}</span>
    ${more ? `<a class="more">${esc(more)} ${I.caret({ w: 11 })}</a>` : ""}</div>`;
}

function appTile(a) {
  const state = { connected: "ok", active: "ok", running: "ok",
                  approval: "warn", waiting: "idle", down: "bad" }[a.state] || "idle";
  return `<button class="tile">
    ${ico(I[a.icon] ? I[a.icon]({ w: 20, s: "#fff" }) : esc(a.initial || "?"), a.color)}
    <div class="body">
      <div class="name">${esc(a.name)}</div>
      <div class="desc">${esc(a.desc || "")}</div>
      ${a.status ? `<div class="foot">${dot(state)}${esc(a.status)}</div>` : ""}
    </div>
    ${a.kebab === false ? "" : `<span class="kebab">···</span>`}
  </button>`;
}

/* --------------------------------------------------------------- hero */
function hero(o) {
  return `<div class="hero">
    <div class="art">${heroArt(o.art)}</div>
    ${o.eyebrow ? `<div class="eyebrow">${esc(o.eyebrow)}</div>` : ""}
    <h1>${esc(o.title)}</h1>
    <div class="sub">${esc(o.sub)}</div>
    ${o.side ? `<div class="heroside">
        <b>${esc(o.side.name)}</b><span>${esc(o.side.meta)}</span>
        <button class="ghostbtn">${esc(o.side.action)} ${I.caret({ w: 11 })}</button>
      </div>` : `<div class="tagline">${esc(D.meta?.tagline || "")}<hr></div>`}
  </div>`;
}

/* ========================================================== views: home */
function viewHome() {
  const h = D.home || {};
  return hero({
      art: "ridge", title: h.greeting || "Hello.",
      sub: "Everything that matters today, in one place." })
  + `<div class="stats">
      ${statCard({ icon: "cal", color: "var(--t-blue)", label: "",
        value: h.events_today ?? 0, sub: "on today's schedule" })}
      ${statCard({ icon: "check", color: "var(--t-green)", label: "",
        value: h.tasks_due ?? 0, sub: "need a person" })}
      ${statCard({ icon: "mail", color: "var(--t-slate)", label: "",
        value: h.unread ?? 0, sub: "unread messages" })}
      ${statCard({ icon: "spark", color: "var(--t-indigo)", label: "",
        value: h.automations_active ?? 0, sub: "automations running" })}
    </div>`
  + `<section>${head("Needs Attention", "View all")}
      <div class="rail">${(D.attention || []).map(appTile).join("")
        || empty("Nothing is waiting on you.")}</div></section>`
  + `<section>${head("Your Businesses", "Manage")}
      <div class="rail">${(D.entities || []).map(e => appTile({
        name: e.name, desc: e.where_ || e.kind,
        icon: "ship", color: tintFor(e.id),
        status: e.devices + (e.devices === 1 ? " box" : " boxes"),
        state: e.devices ? "connected" : "waiting",
      })).join("") || empty("No business enrolled yet.")}</div></section>`
  + `<section>${head("My Apps", "Open App Store")}
      <div class="rail">${(D.apps || []).slice(0, 8).map(appTile).join("")
        || empty("No apps installed.")}</div></section>`
  + `<section>${head("Automations", "Manage")}
      <div class="rail">${(D.automations || []).map(appTile).join("")
        || empty("No automations yet.")}</div></section>`;
}

/* ========================================================== views: apps */
function viewApps() {
  const groups = D.appgroups || [];
  return hero({ art: "ridge", title: "Apps",
                sub: "Everything you can open, all in one place." })
  + `<section>
      <div class="cbox" style="max-width:560px;margin:0 0 4px">
        <span style="color:var(--ink-3)">${I.search({ w: 17 })}</span>
        <input placeholder="Search apps, tools, and more..." id="appq">
      </div>
    </section>`
  + groups.map(g => `<section>${head(g.title, g.more)}
      <div class="grid">${g.items.map(appTile).join("")}</div></section>`).join("")
  + (groups.length ? "" : `<section>${empty("No apps installed on this box.")}</section>`);
}

/* ======================================================== views: agents */
function viewAgents() {
  const a = D.agentpage || {};
  return hero({ art: "ridge", title: "Your agents, ready to work.",
                sub: "Ask, delegate, and get things done." })
  + `<div class="stats">
      ${statCard({ icon: "bot", color: "var(--t-violet)", label: "",
        value: (a.available ?? 0), sub: "agents available" })}
      ${statCard({ icon: "play", color: "var(--t-green)", label: "",
        value: (a.running ?? 0), sub: "automations running" })}
      ${statCard({ icon: "clock", color: "var(--t-blue)", label: "",
        value: (a.done_today ?? 0), sub: "tasks completed today" })}
      ${statCard({ icon: "spark", color: "var(--t-indigo)", label: "",
        value: "Learning", sub: "agents learn from your work" })}
    </div>`
  + `<section>${head("Your Agents", "Manage agents")}
      <div class="rail">${(a.agents || []).map(appTile).join("")
        || empty("No agents installed.")}</div></section>`
  + `<section>${head("Automations Running", "View all")}
      <div class="rail">${(D.automations || []).map(appTile).join("")
        || empty("Nothing running.")}</div></section>`
  + `<section>${head("Recent Activity", "View all activity")}
      <div class="card"><div class="list">${
        (D.sysactivity || []).map(activityRow).join("")
        || `<div class="row"><div class="body"><div class="q">Nothing yet.</div></div></div>`
      }</div></div></section>`;
}

/* =================================================== views: automations */
function viewAutomations() {
  return hero({ art: "ridge", title: "Automations",
                sub: "Work that runs whether or not you are looking." })
  + `<section>${head("Running")}
      <div class="grid">${(D.automations || []).map(appTile).join("")
        || empty("Nothing running.")}</div></section>`
  + `<section>${head("Held for a person", "The gate")}
      <div class="card"><div class="list">${
        (D.approvals || []).map(r => `<div class="row">
          ${ico(I.alert({ w: 17, s: "#fff" }), "var(--t-amber)", "sm")}
          <div class="body">
            <div class="t">${esc(r.capability)}
              <span class="chip warn">needs you</span></div>
            <div class="q">${esc(r.business || "")} · ${esc(r.args || "")}</div>
          </div>
          <span class="when">${ago(r.requested_at)}</span>
          <button class="btn go">Approve</button>
          <button class="btn">Deny</button>
        </div>`).join("")
        || `<div class="row"><div class="body"><div class="q">Nothing is held. Every
             request either ran or was refused out loud.</div></div></div>`
      }</div></div></section>`;
}

/* ======================================================== views: files */
function viewFiles() {
  return hero({ art: "ridge", title: "Files",
                sub: "What this box holds, and where it came from." })
  + `<section>${head("Content on this box")}
      <div class="grid">${(D.content || []).map(c => appTile({
          name: c.kind, desc: c.detail, icon: "folder",
          color: "var(--t-slate)", status: c.version, state: "connected",
        })).join("") || empty("No content pulled yet.")}</div></section>`;
}

/* ============================================== views: business hub */
const HUBNAV = [["overview","Overview","home"],["sales","Sales & Orders","chart"],
  ["reviews","Reviews","star"],["customers","Customers","people"],
  ["marketing","Marketing","mega"],["inventory","Inventory","box"],
  ["team","Team","people"],["settings","Settings","gear"]];

function viewHub() {
  const b = D.hub || {};
  const body = HUB === "overview" ? hubOverview(b) : hubSection(b);
  return `<div class="withside">
    <aside>
      <button class="wsback">${I.back({ w: 14 })} All Workspaces</button>
      <div class="wscur">
        ${ico(I.ship({ w: 18, s: "#fff" }), "var(--t-blue)", "sm")}
        <div><div class="name">Business Hub</div>
             <p class="sub">${esc(b.name || "No business")}</p></div>
      </div>
      <div class="snav">${HUBNAV.map(([k, label, g]) =>
        `<button data-hub="${k}" aria-current="${k === HUB}">
           ${I[g]({ w: 17 })} ${esc(label)}</button>`).join("")}</div>
      <div class="asidecard">
        ${ico(I.spark({ w: 15, s: "#fff" }), "var(--t-indigo)", "xs")}
        <div style="margin-top:8px;color:var(--ink-2)">Your AI team
          <div style="color:var(--ink-3)">for a stronger business.</div></div>
      </div>
    </aside>
    <div>${body}</div>
  </div>`;
}

function hubOverview(b) {
  return hero({
      art: "room", eyebrow: "Business Workspace", title: "Business Hub",
      sub: `Run and grow your ${esc(b.vertical || "business")}, all in one place.`,
      side: b.name ? { name: b.name, meta: b.meta || "",
                       action: "View Business Profile" } : null })
  + `<div class="stats">
      ${statCard({ icon: "chart", color: "var(--t-green)", label: "Today's Sales",
        value: money(b.sales_today || 0),
        delta: b.sales_delta == null ? "" :
          `<span class="delta ${b.sales_delta >= 0 ? "up" : "down"}">
             ${b.sales_delta >= 0 ? "↑" : "↓"} ${Math.abs(b.sales_delta)}%</span>`,
        sub: "vs. yesterday" })}
      ${statCard({ icon: "star", color: "var(--t-amber)", label: "Reviews to Reply",
        value: b.reviews_open ?? 0, sub: (b.reviews_new ?? 0) + " new this week" })}
      ${statCard({ icon: "box", color: "var(--t-orange)", label: "86'd Items",
        value: b.eightysixed ?? 0, sub: "off the menu right now" })}
      ${statCard({ icon: "cal", color: "var(--t-blue)", label: "On the Schedule",
        value: b.events ?? 0, sub: "today" })}
    </div>`
  + `<section>${head("Connected Apps", "Manage Apps")}
      <div class="rail">${(D.apps || []).map(appTile).join("")
        + appTile({ name: "Connect More Apps", desc: "Find new integrations",
                    icon: "grid", color: "var(--t-slate)", kebab: false })}
      </div></section>`
  + `<section>${head("Quick Actions")}
      <div class="rail">${(b.quick || []).map(q => appTile({
          name: q.label, desc: q.sub, icon: q.icon, color: "var(--panel-hi)",
          kebab: false })).join("")}</div></section>`
  + `<section><div class="cols2">
      <div class="card">
        <div class="cardhead"><h3>Recent Activity</h3><a class="more">View All →</a></div>
        <div class="list">${(D.activity || []).map(activityRow).join("")
          || `<div class="row"><div class="body"><div class="q">Quiet so
               far.</div></div></div>`}</div>
      </div>
      <div class="card">
        <div class="cardhead"><h3>Today at a Glance</h3><a class="more">View All →</a></div>
        <div class="agenda">${(b.agenda || []).map(a => `<div class="ag">
            <span class="pip">${dot("ok")}</span>
            <span class="time">${esc(hhmm(a.starts_at))}</span>
            <div><div class="t">${esc(a.title)}</div>
                 <div class="d">${esc(a.body || "")}</div></div>
          </div>`).join("") || `<div class="ag"><div class="d">Nothing
               scheduled.</div></div>`}</div>
      </div>
    </div></section>`
  + `<section>${head("Tasks Needing Attention", "View All")}
      <div class="rail">${(D.attention || []).map(appTile).join("")
        || empty("Nothing needs you.")}</div></section>`;
}

function hubSection(b) {
  const title = (HUBNAV.find(h => h[0] === HUB) || [])[1] || "";
  const rows = (D.hubsections || {})[HUB] || [];
  return hero({ art: "room", eyebrow: "Business Workspace", title,
                sub: b.name || "", side: null })
  + `<section><div class="card"><div class="list">${
      rows.map(r => `<div class="row">
        ${ico(I[r.icon || "doc"]({ w: 17, s: "#fff" }), r.color || "var(--t-slate)", "sm")}
        <div class="body"><div class="t">${esc(r.t)}
          ${r.chip ? `<span class="chip ${r.chipkind || ""}">${esc(r.chip)}</span>` : ""}
        </div><div class="q">${esc(r.q || "")}</div></div>
        <span class="when">${esc(r.when || "")}</span>
      </div>`).join("")
      || `<div class="row"><div class="body"><div class="q">Nothing here
           yet.</div></div></div>`
    }</div></div></section>`;
}

function activityRow(a) {
  return `<div class="row">
    ${ico(I[a.icon || "doc"]({ w: 17, s: "#fff" }), a.color || "var(--t-slate)", "sm")}
    <div class="body">
      <div class="t">${esc(a.title)}${a.stars
        ? ` <span style="color:var(--t-amber)">${"★".repeat(a.stars)}</span>` : ""}
        ${a.chip ? `<span class="chip ${a.chipkind || ""}">${esc(a.chip)}</span>` : ""}
      </div>
      ${a.detail ? `<div class="q">${esc(a.detail)}</div>` : ""}
    </div>
    <span class="when">${ago(a.at)}</span>
    ${a.action ? `<button class="btn">${esc(a.action)}</button>` : ""}
    <span class="kebab" style="color:var(--muted)">···</span>
  </div>`;
}

const empty = msg => `<div class="card pad" style="color:var(--ink-2)">${esc(msg)}</div>`;
const tintFor = id => {
  const t = ["--t-blue","--t-teal","--t-violet","--t-orange","--t-green","--t-pink"];
  let h = 0; for (const c of String(id)) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return `var(${t[h % t.length]})`;
};

/* ------------------------------------------------------------- chrome */
const TABS = [["home","Home"],["apps","Apps"],["agents","Agents"],
              ["automations","Automations"],["files","Files"],["hub","Business"]];

function chrome() {
  const m = D.meta || {};
  $("#top").innerHTML = `
    <div class="mark">${esc(m.brand || "GHOST")}</div>
    <nav class="navpills">${TABS.map(([k, l]) =>
      `<button data-tab="${k}" aria-current="${k === TAB}">${esc(l)}</button>`).join("")}
    </nav>
    <div class="topright">
      <button class="iconbtn">${I.search()}</button>
      <button class="iconbtn">${I.gear()}</button>
      <div class="who"><span class="avatar">${esc((m.user || "?")[0])}</span>
        <span>${esc(m.user || "")}</span>${I.caret({ w: 12 })}</div>
    </div>`;
  $("#composer").innerHTML = `<div class="cbox">
      <span class="spark">${I.spark({ w: 19 })}</span>
      <select><option>Ask ${esc(m.brand || "GHOST")}</option><option>Agents</option>
        <option>Apps</option></select>
      <input placeholder="${TAB === "hub"
        ? "What do you want to do for your business today?"
        : "What do you need?"}">
      <button class="iconbtn">${I.clip()}</button>
      <button class="send">${I.up({ w: 17 })}</button>
    </div>`;
  $("#status").innerHTML = `<span class="mark">${esc(m.brand || "GHOST")}</span>
    <span>${esc(m.tagline || "")}</span>
    <span class="right">${dot(m.online ? "ok" : "bad")}
      ${esc(m.online ? "All systems online" : "Degraded")}</span>`;
}

function render() {
  chrome();
  const v = { home: viewHome, apps: viewApps, agents: viewAgents,
              automations: viewAutomations, files: viewFiles, hub: viewHub }[TAB];
  $("#view").innerHTML = v();
  document.querySelectorAll("[data-tab]").forEach(b =>
    b.onclick = () => { TAB = b.dataset.tab; window.scrollTo(0, 0); render(); });
  document.querySelectorAll("[data-hub]").forEach(b =>
    b.onclick = () => { HUB = b.dataset.hub; window.scrollTo(0, 0); render(); });
}

async function load() {
  try {
    D = await (await fetch("/api/home")).json();
  } catch (e) {
    D = { meta: { brand: "GHOST", tagline: "offline", online: false } };
  }
  render();
}

load();
setInterval(load, 30000);
