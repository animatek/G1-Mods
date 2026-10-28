// The G1-Mods web builder: bundle.json (made by make_bundle.py) holds the builder's Python and
// the modules; Pyodide runs it on the ROM the user picks. Nothing leaves the browser.
const $ = (id) => document.getElementById(id);
const ROM_SIZE = 512 * 1024;
const ROM_SHA256 = "d9b199f2";   // as tools/g1rom.py
let py = null, bundle = null, rom = null, built = [];

function status(el, text, kind) { el.textContent = text; el.className = "status " + kind; }

async function sha256(bytes) {
  const h = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return [...h].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function ticked() {
  return [...document.querySelectorAll("#grid input:checked")].map((i) => i.value);
}

function renderModules() {
  $("grid").innerHTML = "";
  for (const m of bundle.modules) {
    const label = document.createElement("label");
    label.className = "mod";
    label.innerHTML = `<input type="checkbox" value="${m.folder}"${m.real_g1 ? "" : " checked"}>
      <span><span class="name"></span><div class="meta"></div><div class="sum"></div></span>`;
    label.querySelector(".name").textContent = m.name;
    label.querySelector(".meta").textContent = `Type ${m.type} · ${m.kind} · ${m.author} · v${m.version}`;
    label.querySelector(".sum").textContent = m.summary;
    if (m.real_g1) {                     // a module known to fail on real hardware
      const w = document.createElement("div");
      w.className = "warnline";
      w.textContent = "⚠ G1-Emu only: " + m.real_g1;
      label.querySelector(".sum").after(w);
    }
    label.querySelector("input").addEventListener("change", refresh);
    $("grid").appendChild(label);
  }
}

// The room bar: a real build of what is ticked when there is a ROM (it takes a moment), the
// count alone before.
async function refresh() {
  const sel = ticked();
  syncBuildUI();
  canBuild();
  if (!rom || !py || !sel.length) {
    $("meter").style.width = "0";
    status($("roomText"), `${sel.length} of ${bundle.modules.length} modules ticked.`, "wait");
    return;
  }
  try {
    const r = run(sel);
    const pct = Math.min(100, (100 * r.bytes) / bundle.room);
    $("meter").style.width = pct + "%";
    status($("roomText"), `${sel.length} modules, ${(r.bytes / 1024).toFixed(1)} KB of the ` +
      `${(bundle.room / 1024).toFixed(1)} KB the OS has room for.`, "ok");
  } catch (e) {
    $("meter").style.width = "100%";
    status($("roomText"), message(e), "bad");
  }
}

function message(e) {
  const m = String(e.message || e).match(/BuildError: (.*)/);
  return m ? m[1] : String(e.message || e);
}

function run(sel) {
  const build = py.globals.get("builder").build;
  const r = build(py.toPy(rom), py.toPy(sel));
  const out = {
    rom: r.get("rom").toJs(), os: r.get("os") ? r.get("os").toJs() : null, noOs: r.get("no_os"),
    bytes: r.get("bytes"),
    types: r.get("types").toJs(),
  };
  r.destroy();
  return out;
}

function canBuild() {
  $("go").disabled = !(py && rom && ticked().length && $("agree").checked);
}

async function pickRom(file) {
  const bytes = new Uint8Array(await file.arrayBuffer());
  const hash = await sha256(bytes);
  if (bytes.length !== ROM_SIZE || !hash.startsWith(ROM_SHA256)) {
    rom = null;
    status($("romStatus"), `${file.name} is not the rack's 3.03 ROM (512 KB, sha256 ${ROM_SHA256}…).`, "bad");
  } else {
    rom = bytes;
    status($("romStatus"), `${file.name}: the rack's 3.03 ROM. Good.`, "ok");
  }
  refresh();
}

function offer(link, bytes, name) {
  if (link.href) URL.revokeObjectURL(link.href);
  link.href = URL.createObjectURL(new Blob([bytes], { type: "application/octet-stream" }));
  link.download = name;
  link.textContent = "⬇ " + name;
}

function doBuild() {
  const sel = ticked();
  try {
    const r = run(sel);
    const tag = sel.length === bundle.modules.length ? "all" : `${sel.length}mods`;
    offer($("dlRom"), r.rom, `g1mods-${tag}-rom.bin`);
    const emuOnly = bundle.modules.filter((m) => m.real_g1 && sel.includes(m.folder)).map((m) => m.name);
    const os = r.os && !emuOnly.length ? r.os : null;
    if (os) offer($("dlOs"), os, `g1mods-${tag}-os.bin`);
    $("dlOs").hidden = !os;
    $("noOs").textContent = os ? "" : emuOnly.length
      ? `Not with ${emuOnly.join(", ")}: it is for G1-Emu only for now. Untick it to get one.`
      : "Not with these modules: " + r.noOs;
    $("downloads").classList.add("show");
    status($("buildStatus"), `Built: types ${r.types.join(", ")}. Version 3.09 on connecting.`, "ok");
  } catch (e) {
    $("downloads").classList.remove("show");
    status($("buildStatus"), message(e), "bad");
  }
}


// ---------- the site around the builder ----------
// To add a link, add a row here: group, label, address, one line about it, two letters for its badge.
const LINKS = [
  { group: "Code", items: [
    { name: "G1-Mods", url: "https://github.com/animatek/G1-Mods", note: "This project: the modules, the tools and the tests.", ic: "GM" },
    { name: "Animatek NME", url: "https://github.com/animatek/Animatek-NME", note: "The modern editor for the Nord Modular G1.", ic: "NME" },
    { name: "G1-Emu", url: "https://github.com/animatek/G1-Emu", note: "The G1 emulated, as a plugin and standalone.", ic: "EM" },
    { name: "Report a problem", url: "https://github.com/animatek/G1-Mods/issues", note: "Issues: what you saw and what you did before.", ic: "!" },
  ]},
  { group: "Support & community", items: [
    { name: "Patreon", url: "https://www.patreon.com/c/animatek", note: "Guides, videos and the making of. The software stays open.", ic: "P" },
    { name: "Donate (PayPal)", url: "https://www.paypal.com/donate/?hosted_button_id=YATW56VC46ENE", note: "A one-off donation to keep the project going.", ic: "$" },
    { name: "Animatek", url: "https://animatek.net", note: "Courses, articles and the rest of the work.", ic: "A" },
    { name: "YouTube", url: "https://www.youtube.com/@animatek", note: "Guides, demos and the making of, on video.", ic: "YT" },
    { name: "Nord Modular Editor", url: "https://nordmodulareditor.com", note: "The online editor and patch archive for the G1 and G2: browse and share patches.", ic: "NM" },
  ]},
  { group: "Thanks", items: [
    { name: "Gearmulator", url: "https://github.com/dsp56300/gearmulator", note: "The DSP56300 core G1-Emu is built on.", ic: "GE" },
  ]},
];

const ROUTES = {
  "": "Overview", modules: "All modules", builder: "Build your OS", install: "Install guide",
  recovery: "Going back & fixes", "turing-scale": "First patch", "nme-g1emu": "Connect NME to G1-Emu",
  "clock-reset": "Clock & reset", modular: "Nord Modular G1", links: "Links", contribute: "Contribute", about: "About & legal",
};
const BASE_DESC = "New module types for the Nord Modular G1, built into your own copy of its OS. Module library, web builder, guides and links.";
const DESCRIPTIONS = {
  "": BASE_DESC,
  modules: "Every G1-Mods module: its picture, ports, controls and example patches.",
  builder: "Build your own G1 OS with the modules you want, right in the browser.",
  install: "Installing G1-Mods: build your OS, try it in G1-Emu, install it on a real G1.",
  recovery: "Going back to Clavia's OS, and what to do when something goes wrong.",
  "turing-scale": "First patch: the Turing Machine and the Scale Quantizer into an oscillator.",
  "nme-g1emu": "Connect Animatek NME to G1-Emu — the safe way in before a real G1.",
  "clock-reset": "Clock & reset: how the sequencers, the 5-Step Seq and the 8Counter stay in step.",
  modular: "The Nord Modular G1: its history, its three models, and how a patch runs on its DSPs.",
  links: "The code, the editor, the emulator and the people behind G1-Mods.",
  contribute: "Help build G1-Mods: how a module is made, tested in G1-Emu first.",
  about: "About G1-Mods and the legal bits.",
};
function setMeta(title, desc) {
  document.title = title;
  const m = document.querySelector('meta[name="description"]');
  if (m) m.content = desc;
}
let kindFilter = "all";

function route() {
  const r = location.hash.replace(/^#\/?/, "").split("?")[0];
  const isMod = r.startsWith("module/");
  const name = isMod ? "module" : r in ROUTES ? r : "";
  if (isMod) renderModulePage(decodeURIComponent(r.slice(7)));
  document.querySelectorAll("section.view").forEach((v) => v.classList.toggle("on", v.dataset.view === name));
  document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("on", (a.dataset.route === name) || (isMod && a.dataset.route === "modules")));
  $("crumb").textContent = isMod ? "Module" : ROUTES[name];
  if (!isMod) setMeta(name === "" ? "G1-Mods · modules for the Nord Modular G1" : `${ROUTES[name]} · G1-Mods`, DESCRIPTIONS[name] || BASE_DESC);
  window.scrollTo(0, 0);
}

// a tiny deterministic "panel": knobs and jacks drawn from the type number, so each card has its own face
function panelSvg(type) {
  let s = type * 2654435761 >>> 0, out = "";
  const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  const knobs = 3 + Math.floor(rnd() * 3);
  for (let i = 0; i < knobs; i++) {
    const x = 30 + i * (240 / knobs), a = rnd() * 4.4 - 2.2;
    out += `<circle cx="${x}" cy="26" r="13" fill="none" stroke="var(--accent)" stroke-width="2" opacity=".85"/>` +
      `<line x1="${x}" y1="26" x2="${x + 9 * Math.sin(a)}" y2="${26 - 9 * Math.cos(a)}" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round"/>`;
  }
  const leds = 4 + Math.floor(rnd() * 5);
  for (let i = 0; i < leds; i++)
    out += `<rect x="${16 + i * 12}" y="50" width="8" height="5" rx="2" fill="var(--accent)" opacity="${rnd() > .5 ? 1 : .25}"/>`;
  for (let i = 0; i < 4; i++)
    out += `<circle cx="${236 + (i % 2) * 22}" cy="${48 + Math.floor(i / 2) * 14}" r="4.5" fill="none" stroke="var(--muted)" stroke-width="1.6"/>`;
  return `<svg viewBox="0 0 300 70" aria-hidden="true">${out}</svg>`;
}

function renderLibrary() {
  const q = $("q").value.trim().toLowerCase();
  const list = bundle.modules.filter((m) =>
    (kindFilter === "all" || m.kind === kindFilter) &&
    (!q || [m.name, m.fullname, m.summary, m.kind, String(m.type)].join(" ").toLowerCase().includes(q)));
  $("mcards").innerHTML = "";
  for (const m of list.slice().sort((a, b) => a.type - b.type)) {
    const c = document.createElement("article");
    c.className = "mcard";
    c.dataset.folder = m.folder;
    c.innerHTML = `<div class="art"><div class="t"><span></span><span></span></div>${m.images.length ? `<img alt="" loading="lazy" style="width:100%;height:96px;object-fit:contain;image-rendering:auto;margin-top:6px">` : panelSvg(m.type)}</div>
      <div class="body"><div class="head"><h3><span class="n"></span><small></small></h3><button class="add" type="button"></button></div><div class="full"></div><div class="sum"></div>
      <div class="row"><span class="by"></span><span><a class="open" href="#">Open page →</a></span></div></div>`;
    const t = c.querySelectorAll(".t span");
    t[0].textContent = m.kind; t[1].textContent = "type " + m.type;
    if (m.images.length) c.querySelector(".art img").src = m.images[0];
    c.querySelector(".n").textContent = m.name;
    c.querySelector("h3 small").textContent = "v" + m.version;
    c.querySelector(".full").textContent = m.fullname;
    c.querySelector(".sum").textContent = m.summary;
    c.querySelector(".by").innerHTML = `<span class="pill ${m.real_g1 ? "warn" : m.kind}"></span>`;
    c.querySelector(".pill").textContent = m.real_g1 ? "G1-Emu only" : m.author;
    c.querySelector("a").href = "#/module/" + m.folder;
    const box = document.querySelector(`#grid input[value="${m.folder}"]`);
    const add = c.querySelector(".add");
    const paint = () => {
      const on = box && box.checked;
      add.textContent = on ? "✓" : "+";
      add.classList.toggle("on", on);
      add.title = on ? "In your build: press to remove" : "Add to your build";
      add.setAttribute("aria-pressed", on ? "true" : "false");
      add.setAttribute("aria-label", (on ? "Remove " : "Add ") + m.name);
      c.classList.toggle("in", on);
    };
    add.onclick = () => { box.checked = !box.checked; refresh(); };
    paint();
    $("mcards").appendChild(c);
  }
  $("mempty").hidden = list.length > 0;
}

// the + buttons, the bar and the sidebar box follow the builder's ticks, which are the one truth
function syncBuildUI() {
  if (!bundle) return;
  const n = ticked().length;
  $("barCount").textContent = n;
  const ma = $("modAdd");
  if (ma) {
    const box = document.querySelector(`#grid input[value="${ma.dataset.folder}"]`);
    const on = box && box.checked;
    ma.textContent = on ? "✓ In my build" : "+ Add to my build";
    ma.setAttribute("aria-pressed", on ? "true" : "false");
  }
  $("mbText").textContent = `My build · ${n} of ${bundle.modules.length} modules`;
  document.querySelectorAll(".mcard").forEach((c) => {
    const add = c.querySelector(".add");
    const folder = c.querySelector("a").href.split("/").pop();
    const box = document.querySelector(`#grid input[value="${folder}"]`);
    const on = box && box.checked;
    add.textContent = on ? "✓" : "+";
    add.classList.toggle("on", on);
    add.title = on ? "In your build: press to remove" : "Add to your build";
    add.setAttribute("aria-pressed", on ? "true" : "false");
    c.classList.toggle("in", on);
  });
}

function renderFilters() {
  const kinds = ["all", ...new Set(bundle.modules.map((m) => m.kind))];
  $("filters").innerHTML = "";
  for (const k of kinds) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "chip" + (k === kindFilter ? " on" : "");
    b.textContent = k === "all" ? "All" : k[0].toUpperCase() + k.slice(1);
    b.onclick = () => { kindFilter = k; renderFilters(); renderLibrary(); };
    $("filters").appendChild(b);
  }
}

function renderLinks() {
  $("links").innerHTML = "";
  for (const g of LINKS) {
    const d = document.createElement("div");
    d.className = "linkgroup";
    d.innerHTML = `<h3></h3><div class="linkgrid"></div>`;
    d.querySelector("h3").textContent = g.group;
    for (const l of g.items) {
      const a = document.createElement("a");
      a.className = "link"; a.href = l.url; a.target = "_blank"; a.rel = "noopener";
      a.innerHTML = `<div class="ic"></div><div><b></b><span></span></div>`;
      a.querySelector(".ic").textContent = l.ic;
      a.querySelector("b").textContent = l.name;
      a.querySelector("span").textContent = l.note;
      d.querySelector(".linkgrid").appendChild(a);
    }
    $("links").appendChild(d);
  }
}

// the guide pages (install, recovery, …) are rendered from docs/*.md by make_bundle.py and
// live in bundle.guides; the sections in index.html are empty until they are filled here.
function renderGuides() {
  for (const [key, html] of Object.entries(bundle.guides || {})) {
    const el = document.querySelector(`.guide[data-guide="${key}"]`);
    if (el) el.innerHTML = html;
  }
}

// light or dark; with nothing chosen it follows the system. The icon shows the one a click goes to.
const darkNow = () => document.documentElement.dataset.theme === "dark";

// ---------- one module's page ----------
const SIGNALS = { audio: "audio", control: "control", logic: "logic", slave: "slave" };
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
function rangeOf(c) { return `${c.minValue ?? 0} – ${c.maxValue ?? 127}`; }
function youtubeEmbed(url) {
  const m = String(url).match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{6,})/);
  return m ? `https://www.youtube-nocookie.com/embed/${m[1]}` : url;
}

function portList(title, list) {
  const d = el("div", "ports");
  d.append(el("h4", null, title));
  if (!list.length) d.append(el("div", "p", "none"));
  for (const p of list) { const r = el("div", "p"); r.append(el("b", null, p.name), el("span", null, p.signal || "")); d.append(r); }
  return d;
}
function section(title, open) {
  const d = el("details", "sec"); if (open) d.open = true;
  d.append(el("summary", null, title)); const inner = el("div", "in"); d.append(inner); return [d, inner];
}
function paras(x) { return (Array.isArray(x) ? x : x ? [x] : []).map((t) => el("p", null, t)); }

function renderModulePage(folder) {
  const root = $("modpage"); root.innerHTML = "";
  const m = bundle && bundle.modules.find((x) => x.folder === folder);
  if (!m) { root.append(el("p", "empty", bundle ? "No such module." : "Loading…")); return; }
  setMeta(`${m.name} · G1-Mods`, m.summary);
  const back = el("a", "back", "← All modules"); back.href = "#/modules"; root.append(back);

  const head = el("div", "mhead"); const l = el("div");
  const tags = el("div", "tags");
  tags.append(el("span", "pill " + m.kind, m.kind), el("span", "pill", "type " + m.type), el("span", "pill", "v" + m.version));
  if (m.category) tags.append(el("span", "pill", m.category));
  if (m.real_g1) tags.append(el("span", "pill warn", "G1-Emu only"));
  l.append(tags, el("h1", null, m.name), el("p", "lead", m.fullname));
  head.append(l);
  const act = el("div", "cta");
  const b = el("button", "btn primary"); b.type = "button"; b.id = "modAdd"; b.dataset.folder = m.folder;
  b.onclick = () => { const box = document.querySelector(`#grid input[value="${m.folder}"]`); if (box) { box.checked = !box.checked; refresh(); } };
  act.append(b);
  const go = el("a", "btn", "Build your OS →"); go.href = "#/builder"; act.append(go);
  const s = el("a", "btn", "Source ↗"); s.href = "https://github.com/animatek/G1-Mods/tree/main/modules/" + m.folder; s.target = "_blank"; s.rel = "noopener"; act.append(s);
  head.append(act); root.append(head);

  const lay = el("div", "mlayout"); root.append(lay);
  // left: the picture(s) and the text
  const left = el("div"); lay.append(left);
  const shot = el("div", "shot"); left.append(shot);
  if (m.images.length) {
    const big = el("img"); big.src = m.images[0]; big.alt = m.name + " panel"; shot.append(big);
    const caps = m.image_captions || [];
    const cap = el("div", "cap"); cap.textContent = caps[0] || ""; cap.hidden = !caps[0]; shot.append(cap);
    if (m.images.length > 1) {
      const th = el("div", "thumbs");
      m.images.forEach((src, i) => {
        const t = el("img", i ? "" : "on"); t.src = src; t.alt = caps[i] || "";
        t.onclick = () => { big.src = src; cap.textContent = caps[i] || ""; cap.hidden = !caps[i];
          th.querySelectorAll("img").forEach((x) => x.classList.remove("on")); t.classList.add("on"); };
        th.append(t);
      });
      shot.append(th);
    }
  } else {
    const ph = el("div", "ph"); ph.innerHTML = panelSvg(m.type); shot.append(ph);
    shot.append(el("div", "cap", "Panel picture coming. Add one as modules/" + m.folder + "/images/panel.png."));
  }
  if (m.video) {
    const v = el("div", "video");
    v.innerHTML = `<iframe src="${youtubeEmbed(m.video)}" title="${m.name} video" loading="lazy" allowfullscreen
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe>`;
    left.append(v);
  }
  const [about, aIn] = section("About", true);
  (m.about ? paras(m.about) : [el("p", null, m.summary)]).forEach((p) => aIn.append(p));
  if (m.credits) paras(m.credits).forEach((p) => aIn.append(p));
  left.append(about);
  if (m.usage) {
    const [u, uIn] = section("How to use it", true);
    const ol = el("ol"); (Array.isArray(m.usage) ? m.usage : [m.usage]).forEach((t) => ol.append(el("li", null, t))); uIn.append(ol); left.append(u);
  }
  const [pt, ptIn] = section(`Ports & lights`, true);
  const cols = el("div", "portcols");
  cols.append(portList("Inputs", m.inputs || []), portList("Outputs", m.outputs || []));
  if ((m.lights || []).length) cols.append(portList("Lights", m.lights.map((x) => ({ name: x.name, signal: x.type }))));
  ptIn.append(cols); left.append(pt);
  if ((m.controls || []).length) {
    const [cs, csIn] = section(`Controls`, true);
    const t = el("table"); t.innerHTML = "<tr><th>Control</th><th>Range</th><th>Default</th><th>Shown as</th></tr>";
    for (const c of m.controls) {
      const r = el("tr"); r.append(el("td", "mono", c.name), el("td", "mono", rangeOf(c)), el("td", "mono", c.defaultValue ?? "0"), el("td", "mono", c.formatter || "—"));
      t.append(r);
    }
    const w = el("div", "tablewrap"); w.append(t); csIn.append(w); left.append(cs);
  }
  if (m.notes) { const [n, nIn] = section("Notes & limits", false); paras(m.notes).forEach((p) => nIn.append(p)); left.append(n); }

  // right: the data sheet
  const right = el("div"); lay.append(right);
  const sheet = el("div", "panel"); right.append(sheet);
  sheet.append(el("h3", null, "Data sheet")); sheet.firstChild.style.marginTop = "0";
  const dl = el("dl", "fact");
  const row = (k, v) => { dl.append(el("dt", null, k), el("dd", null, v)); };
  row("Type", String(m.type)); row("Kind", m.kind + (m.kind === "audio" ? " rate" : " rate")); row("Version", m.version);
  row("Author", m.author); row("Licence", m.licence);
  row("Real G1", m.real_g1 ? "Not yet: " + m.real_g1 : "Played on a real G1");
  if (m.status) row("Status", m.status);
  sheet.append(dl);
  const ld = m.load || {};
  const meters = [["cycles", "DSP cycles"], ["prog-mem", "Program memory"], ["x-mem", "X memory"]].filter(([k]) => ld[k] != null);
  if (meters.length) {
    sheet.append(el("h3", null, "Load (as NME lists it)"));
    const g = el("div", "loads");
    for (const [k, label] of meters) {
      const v = parseFloat(ld[k]); const c = el("div", "load");
      c.innerHTML = "<b></b><span></span><i><u></u></i>";
      c.querySelector("b").textContent = v; c.querySelector("span").textContent = label;
      c.querySelector("u").style.width = Math.min(100, v * 100 / (k === "cycles" ? 4 : 6)) + "%";
      g.append(c);
    }
    sheet.append(g);
  }
  if ((m.patches || []).length) {
    sheet.append(el("h3", null, "Example patches"));
    const ul = el("ul");
    for (const p of m.patches) {
      const li = el("li"), a = el("a", null, p);
      a.href = `https://raw.githubusercontent.com/animatek/G1-Mods/main/modules/${m.folder}/${p}`; a.download = p; li.append(a);
      const note = (m.patch_notes || {})[p];
      if (note) li.append(el("span", "pnote", " — " + note));
      ul.append(li);
    }
    sheet.append(ul);
    sheet.append(el("p", "cap", "Open them in Animatek NME, on a synth or G1-Emu with these modules."));
  }
  // neighbours
  const sorted = bundle.modules.slice().sort((a, b) => a.type - b.type);
  const i = sorted.indexOf(m), nav = el("div", "cta");
  for (const [o, label] of [[sorted[i - 1], "←"], [sorted[i + 1], "→"]]) if (o) {
    const a = el("a", "btn", label === "←" ? `← ${o.name}` : `${o.name} →`); a.href = "#/module/" + o.folder; nav.append(a);
  }
  right.append(nav);
  syncBuildUI();
}

function applyTheme(t) {
  try { localStorage.setItem("g1mods-theme", t); } catch (e) {}
  document.documentElement.dataset.theme = t;
  $("theme").title = $("theme").ariaLabel = t === "dark" ? "Switch to light" : "Switch to dark";
}

window.addEventListener("hashchange", route);
$("barAll").addEventListener("click", () => { document.querySelectorAll("#grid input").forEach((i) => (i.checked = true)); refresh(); });
$("barNone").addEventListener("click", () => { document.querySelectorAll("#grid input").forEach((i) => (i.checked = false)); refresh(); });
$("q").addEventListener("input", () => {
  if (bundle && location.hash !== "#/modules") location.hash = "#/modules";
  if (bundle) renderLibrary();
});
$("theme").addEventListener("click", () => applyTheme(darkNow() ? "light" : "dark"));
{
  let t = null;
  try { t = localStorage.getItem("g1mods-theme"); } catch (e) {}
  applyTheme(t === "light" || t === "dark" ? t : matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}
renderLinks();
route();

async function init() {
  bundle = await (await fetch("bundle.json")).json();
  $("navCount").textContent = bundle.modules.length;
  $("sMods").textContent = bundle.modules.length;
  renderModules();
  renderFilters();
  renderLibrary();
  renderGuides();
  route();
  syncBuildUI();
  refresh();
  py = await loadPyodide();
  for (const [path, b64] of Object.entries(bundle.files)) {
    const full = "/g1mods/" + path;
    py.FS.mkdirTree(full.slice(0, full.lastIndexOf("/")));
    py.FS.writeFile(full, Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)));
  }
  py.runPython(`
import sys
sys.path[:0] = ["/g1mods/tools", "/g1mods/web"]
import builder
`);
  status($("buildStatus"), "The builder is ready.", "wait");
  refresh();
}

$("file").addEventListener("change", (e) => e.target.files[0] && pickRom(e.target.files[0]));
const drop = $("drop");
drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => {
  e.preventDefault(); drop.classList.remove("over");
  if (e.dataTransfer.files[0]) pickRom(e.dataTransfer.files[0]);
});
$("all").addEventListener("click", () => { document.querySelectorAll("#grid input").forEach((i) => (i.checked = true)); refresh(); });
$("none").addEventListener("click", () => { document.querySelectorAll("#grid input").forEach((i) => (i.checked = false)); refresh(); });
$("agree").addEventListener("change", canBuild);
$("go").addEventListener("click", doBuild);
init().catch((e) => status($("buildStatus"), "The builder did not load: " + message(e), "bad"));
