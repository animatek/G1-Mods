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

async function init() {
  bundle = await (await fetch("bundle.json")).json();
  renderModules();
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
