// Language. The HTML and the code are in English and stay the source; Spanish comes from lang-es.json,
// which maps an English text, exactly as it is on the page, to its Spanish. What is on the page is
// translated when the language is chosen, and what the code adds later (cards, module pages, status
// lines) is translated as it appears, by an observer. Texts that carry numbers use tx("... %0 ...", n).
// The modules' own texts and the guides do not go through here: they come translated in the bundle.
let lang = "en";
let ES = {};
const originalText = new WeakMap();   // a text node -> what it said in English
const SKIP = new Set(["SCRIPT", "STYLE", "SVG", "SELECT", "OPTION", "TEXTAREA", "IFRAME"]);
const ATTRS = ["placeholder", "aria-label", "title", "alt"];
// Texts with a number in them: the pattern, and what it says in Spanish
const PATTERNS = [
  [/^type (\d+)$/, "tipo $1"],
  [/^Panel picture coming\. Add one as (.*)\.$/, "Imagen del panel pendiente. Añade una en $1."],
];

const norm = (h) => h.replace(/\s+/g, " ").trim();
const escapeHtml = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const unescapeHtml = (s) => s.replace(/&gt;/g, ">").replace(/&lt;/g, "<").replace(/&amp;/g, "&");

function spanishOf(s) {
  if (s in ES) return ES[s];
  const esc = escapeHtml(s);
  if (esc in ES) return ES[esc];
  for (const [re, to] of PATTERNS) if (re.test(s)) return s.replace(re, to);
  return null;
}

// A text of the code: English as it is, Spanish if the language is Spanish and there is a translation.
// %0, %1… stand for the numbers or names that change.
function tx(en, ...args) {
  let s = lang === "es" && en in ES ? ES[en] : en;
  args.forEach((a, i) => { s = s.split("%" + i).join(a); });
  return s;
}

function translateTree(root) {
  if (lang !== "es" || !root) return;
  const walk = (e) => {
    if (e.nodeType !== 1 || SKIP.has(e.tagName.toUpperCase()) || e.hasAttribute("data-nolang")) return;
    for (const a of ATTRS) {
      const v = e.getAttribute(a);
      if (v && !e.hasAttribute("data-en-" + a)) {
        const es = spanishOf(v);
        if (es != null) { e.setAttribute("data-en-" + a, v); e.setAttribute(a, unescapeHtml(es)); }
      }
    }
    if (!e.hasAttribute("data-en")) {
      const key = norm(e.innerHTML);
      const es = key && key.length < 1200 && !e.querySelector("[id]") ? spanishOf(key) : null;
      if (es != null && es !== key) { e.setAttribute("data-en", e.innerHTML); e.innerHTML = es; return; }
    }
    for (const n of [...e.childNodes]) {
      if (n.nodeType === 3) {
        const k = n.nodeValue.trim();
        const es = k ? spanishOf(k) : null;
        if (es != null && unescapeHtml(es) !== k) { originalText.set(n, n.nodeValue); n.nodeValue = n.nodeValue.replace(k, unescapeHtml(es)); }
      } else walk(n);
    }
  };
  walk(root);
}

function restoreEnglish() {
  document.querySelectorAll("[data-en]").forEach((e) => { e.innerHTML = e.getAttribute("data-en"); e.removeAttribute("data-en"); });
  document.querySelectorAll("*").forEach((e) => {
    for (const a of ATTRS) if (e.hasAttribute("data-en-" + a)) { e.setAttribute(a, e.getAttribute("data-en-" + a)); e.removeAttribute("data-en-" + a); }
  });
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) if (originalText.has(n)) { n.nodeValue = originalText.get(n); originalText.delete(n); }
}

// What the code adds to the page while it is Spanish gets translated as it comes
const watcher = new MutationObserver((records) => {
  if (lang !== "es") return;
  const roots = new Set();
  for (const r of records) {
    if (r.type === "characterData") { if (r.target.parentElement) roots.add(r.target.parentElement); continue; }
    for (const n of r.addedNodes) roots.add(n.nodeType === 1 ? n : n.parentElement);
  }
  watcher.disconnect();
  roots.forEach((n) => n && translateTree(n));
  watcher.observe(document.body, { childList: true, subtree: true, characterData: true });
});

async function setLang(l, remember = true) {
  if (l === "es" && !Object.keys(ES).length) {
    try { ES = await (await fetch("lang-es.json")).json(); } catch (e) { l = "en"; }
  }
  const was = lang;
  lang = l;
  if (remember) { try { localStorage.setItem("g1mods-lang", l); } catch (e) {} }
  document.documentElement.lang = l;
  const sel = document.getElementById("lang");
  if (sel) sel.value = l;
  watcher.disconnect();
  if (was === "es" && l === "en") restoreEnglish();
  if (typeof langChanged === "function") langChanged();   // the code re-draws what it drew
  if (l === "es") translateTree(document.body);
  watcher.observe(document.body, { childList: true, subtree: true, characterData: true });
}

function firstLang() {
  let saved = null;
  try { saved = localStorage.getItem("g1mods-lang"); } catch (e) {}
  if (saved === "en" || saved === "es") return saved;
  return (navigator.language || "en").toLowerCase().startsWith("es") ? "es" : "en";
}
