# Changelog

Everything that changes in G1-Mods, newest first. Every change that goes into the repo gets its
line here, in the same commit (see `CLAUDE.md`).

## 2026-10-29

- Claude: **`run-nme.sh` is gone.** It started a special NME built from the `mods-layer` branch (a binary kept outside the
  repo), which is not needed since the layer is in NME's `main` (0.25): any NME from `main` offers the modules to a synth that
  says 3.09, and a stale copy of that binary was what made a modified Micro look unrecognised. The README says to use NME
  0.25 or later. `run-g1emu.sh` stays (it builds the ROM and starts G1-Emu with it and a flash of its own).
- Claude: **the web builder builds for the Micro Modular too.** In step 1 the file can be the rack's ROM or what a Micro has in
  its place: Clavia's Micro updater (`.exe`, or the zip that holds it, or the extracted image). `patch_rom.identify()` says which
  it is (or what is wrong with it) and `patch()` takes it from there; `g1rom.set_target()` replaces reading the target once at
  import, so the page builds for either one after the other; `g1update.extract_updater()` reads the OS out of the updater (the
  same as G1-Emu's `extract-os.py`). On the page a Micro greys out Note Out (not on the Micro), builds twelve modules, shows
  room against the Micro's 38 KB, hides the ROM box (a Micro has none) and gives one file, `g1mods-micro-all-os.bin`, marked
  experimental and not to be installed on a real Micro. The command line takes the same files without `--micro`. Checked in
  headless Chromium: a junk file is refused with a reason; the Micro updater is accepted; the page's OS update equals the
  command line's byte for byte; then the rack ROM in the same page gives `os-all.bin` and `rom-all.bin` byte for byte.
- Claude: **the modules go into the Micro Modular's OS** (experimental; in G1-Emu's Micro model only). Javier had said a modified
  Micro could not be done for lack of its ROM; but the Micro runs the same code base as the rack, relocated, and what the
  patcher takes is the OS, not the ROM. `tools/patch_rom.py --micro all <Micro 3.03b image> out.bin` builds twelve of the
  thirteen modules into the Micro's update image (Note Out is out: its two hooks are in code that differs). How: the two OSes
  lined up on 136,810 shared 24-byte runs, every OS address the patcher names translated (`MICRO_ADDR` in `g1rom.py`, 20
  addresses, each checked by its first bytes; `tools/micro_check.py` redoes it on your images), the Micro's type table
  found at `$17C09C` (31 of 31 uses of the rack's `$1C3B00` agree), the package after its smaller OS (39 KB of room against the
  rack's 8). `m68k()` translates the `jsr` and `move.l #` operands and stops on an address it does not know. Checked with the new
  `tests/check_micro.py` in G1-Emu's Micro model: it builds (393,184 bytes), says 3.09, the twelve types are registered and nothing
  else in the table changed, and every example patch is taken and plays (FlipFlop's LED moves, so its code runs). The rack
  build is byte for byte what it was, and `check_insert.py` passes. **Not tried on a real Micro**, which nobody here has: treat it as
  emulator-only. Notes in `NOTES.md` ("The Micro Modular"), roadmap and install guides updated.
- Claude: **it says that the Micro Modular is not supported.** G1-Mods builds on the rack's 3.03 ROM, and a Micro runs its own
  OS (another binary, one DSP, no ROM image to rebuild: its OS comes out of Clavia's updater), so a modified ROM
  loaded for G1-Emu's Micro model changes nothing: the Micro's own OS runs. Found by Javier trying it. Said in
  `ROADMAP.md` (what it would take: a patcher for the Micro's OS image, not started), both install guides and the
  builder's step 1 (English and Spanish). Checked: the page loads and the text shows in both languages.
- Claude: **the web is in Spanish too, with a language selector** left of the sun/moon button. It follows the browser's
  language the first time and remembers the choice; changing it redraws the page in place (the ROM, the ticked
  modules and the builder's state stay). How it is built: the HTML and the code stay English and are the source;
  `web/lang-es.json` maps each English text to its Spanish, and `web/lang.js` applies it to what is on the page and,
  with an observer, to whatever the code adds later; texts with numbers go through `tx("... %0 ...", n)`. The six
  guides are in `docs/es/` (bundled as `guides_es`) and every module has a `module.es.json` with its summary, about,
  usage, notes and patch notes in Spanish (`es` in the bundle; a module without one shows its English). Also found
  while doing it: the overview's warning had been replaced by the builder's one, restored. Checked in headless
  Chromium with the real rack ROM: the whole builder runs in Spanish (ROM accepted, 5.6 of 7.9 KB, build, downloads),
  switching to English and back keeps the ticks and the status lines, no Spanish text is left in English mode, and
  all 15 pages render; the mobile top bar fits the selector.
- Claude: **the guides say the way back can go through NME too.** Besides Clavia's own 3.03b updater, NME's *Device >
  Update Synth OS* installs Clavia's original OS image (a `.bin`; NME does not read the updater's `.exe`) the way
  it installs ours. `docs/INSTALL.md` (what you need) and `docs/RECOVERY.md` (step 3) say so, and where to get the
  image before flashing anything: the `os` folder of G1-Emu after Clavia's update, or `tools/g1update.py unpack`
  of a recorded `.syx`. It is Clavia's, so never shared. Checked: NME's file chooser takes `*.bin` only.
- Claude: **the changelog page is gone from the site.** It rendered this file into a long page that only the people
  working on the project read, and its link sat in About. The page, its route, its link and its copy in the bundle
  are removed (the bundle goes from 313 to 261 KB); `CHANGELOG.md` stays in the repository, where GitHub shows
  it. An old `#/changelog` address opens the overview. Checked: About, Contribute and the old address load and the
  builder is ready.
- Claude: **the guides and the page say the minimum is Animatek NME 0.25.** The first version with the G1-Mods layer
  (it is in NME's `main` since 2026-10-29; `Update Synth OS` is older, the modules it offers are not). Said in
  `docs/INSTALL.md` (what you need), `docs/NME-G1EMU.md`, `docs/MODULAR.md`, `CONTRIBUTING.md`, the README, the
  overview's "How it works" and the builder's step 4. NME's version number is still 0.24.0 until 0.25 is released.
- Claude: **the builder is locked until the risk is accepted.** The "I have read it" box moves from step 3 up to the
  warning at the top of the page, and steps 1 to 4 (the ROM, the modules, the build, the downloads) are dimmed and
  inert (no click, no keyboard, no file drop) until it is ticked; unticking locks them again. Its text also no
  longer says "tested only in the emulator", which contradicted the warning above it (13 modules have played on a
  real G1). Checked with the real ROM in headless Chromium: locked at load (steps inert, "Build" disabled), unlocked
  on ticking, then the ROM is accepted, the meter reads 5.6 of 7.9 KB and a build gives the OS update.
- Claude: **the builder's room meter.** It looked broken twice over. (1) Before a ROM is given the bar stayed empty
  with only "13 of 13 modules ticked"; it is now hidden and the line says what it waits for (the ROM, or the
  builder loading). (2) With a ROM it compared the modules' size *before* packing (14.6 KB) with the room for the
  *packed* package (7.9 KB), so a build that fits showed a full bar and "14.6 KB of the 7.9 KB"; `web/builder.py`
  now reads the packed size when the log gives one, so all 13 modules read **5.6 KB of the 7.9 KB**. Checked with
  the real rack ROM in headless Chromium: the ROM is accepted, the meter is at 71%, and a full build gives both the
  OS update and the ROM download.
- Claude: **the builder's module cards are minimal.** Each one in step 2 had the type, kind, author, version and the
  whole summary, a screenful of text to pick from. It is now the tick, the name, the author and a "Page →" link to the
  module's own page, where the rest is; the "G1-Emu only" warning stays on the card because it changes what the build
  gives. The grid is narrower (230 px cards) so more fit a row. Checked: headless Chromium, 13 cards in rows of three,
  the builder ready.
- Claude: **Contribute is a short page and a `CONTRIBUTING.md`.** The page had grown to four sections (setup, module
  layout, first pull request, test before you flash, house rules) typed into the HTML, and nothing in the repository
  said it to someone arriving from GitHub. That text moves, unchanged in substance, to `CONTRIBUTING.md` (the file
  GitHub shows on new pull requests); the page keeps the invitation, three buttons (How to contribute, the checklist,
  Issues) and the four rules in a line. The web page lost about 4 KB. Checked: the page loads and links the file.
- Claude: **the overview's figures are computed, not typed.** The number of modules, "X/Y played on a real G1" (the
  modules that are not marked `real_g1`, i.e. G1-Emu only), the sentence "all N modules have played in one build" and
  the free type numbers (new `free` in `bundle.json`, from `modules/registry.json`) now come from the bundle, so
  adding a module or claiming a number changes the page with no edit to it. No database: the data was already in
  the bundle, rebuilt on every deploy. The stat lost its hard-coded date. Checked: headless Chromium shows
  13/13, "all 13 modules", "5 type numbers are still free (93, 109, 116, 119, 122)" and the builder ready.
- Claude: **the site's sidebar goes from 14 entries to 8.** The four short guides (First patch, Connect NME to G1-Emu,
  Clock & reset, The Nord Modular G1) sit behind one **Guides** entry that lists them; **Compare** is a link on the
  module library; **Links** is a section of **About** (which also links the changelog). Every old address still works
  (`#/links` opens About; the others keep their page and light up their parent entry). The overview's builder tile no
  longer says "a ROM for the emulator and an update for a G1". Checked: all 16 routes load in headless Chromium with
  the right entry lit and "The builder is ready"; every external link in the site and the docs answers (18 checked).
- Claude: **the page and the install guide say which file is for what.** The OS update is for G1-Emu and a real G1
  and loads only through update mode (G1-Emu: Settings > OS... > Update mode; a real G1: Shift + Store at power-on,
  then NME's Update Synth OS); the ROM is for G1-Emu alone and loads from Settings > ROM > Choose... A table at the
  top of `docs/INSTALL.md` (which the site renders) and the two download boxes spell it out; the README follows.
  `CLAUDE.md` no longer says NME's layer is local: it is in NME's `main`. Checked: the page loads.
- Claude: **the whole-ROM download is back** (Javier: the ROM does work in G1-Emu: it shows the MOD badge once G1-Emu
  restarts with it; I had taken it out on a wrong reading). The page again gives the OS update first and the ROM
  second, with where each goes (the ROM: G1-Emu's *Settings > ROM > Choose...*, which now restarts with it,
  `G1-Emu` 958713f; not for NME's Update Synth OS). `ROADMAP.md` keeps only the G1-Emu build with more modules and
  expanded memory. Checked: the page loads.
- Claude: **the web builder gives only the OS update.** The whole-ROM download is gone from the page: it only booted
  G1-Emu, it was the file that got mixed up with the OS update, and a G1-Emu build with more modules and an
  expanded memory is not built yet. That is now `ROADMAP.md`. When there is no update image the page says why and
  offers nothing; `docs/INSTALL.md` follows (G1-Emu in update mode takes the same file as a real G1; the ROM way
  is `./run-g1emu.sh` from a clone). Checked: the page loads.
- Claude: **(earlier today) one file for G1-Emu and a real G1.** The builder now offers the OS update (`…-os.bin`) as *the*
  download: G1-Emu put in update mode takes it through NME's Update Synth OS exactly like a real G1, so a ROM of
  its own was only a second file to mix up (it was: a whole ROM went into Update Synth OS and was refused). The
  whole ROM stays, folded away as "only if you boot G1-Emu from a ROM file", and becomes the main download only
  when there is no update image (too many modules, or a module only G1-Emu has), with the reason beside it.
  `docs/INSTALL.md` says the same. Checked: the page loads ("The builder is ready"); the show/hide logic was
  not clicked through by an automated run.
- Claude: **the builder's two downloads say which is which.** A whole ROM (512 KB, `…-rom.bin`) went into NME's
  Update Synth OS instead of the OS update (`…-os.bin`) and was refused as too big: the page listed the ROM
  first and gave no hint where each file goes. The OS update (for a real G1, what NME's Update Synth OS takes)
  is now first, the ROM is labelled "for G1-Emu only" with that warning. File names unchanged, so the guides
  still match. NME's own message for a whole ROM now says the same (`Animatek-NME` 795d8c3).
- Claude: **fix: the web builder did not load** ("can't access property textContent, add is null"). The compare
  view, added earlier today, reuses the `mcard` class, and the sync of the "+" buttons walked every `.mcard`
  expecting each to have one; the compare cards have none, so `init()` died before the builder was ready. It now
  walks only the library's cards (`#mcards .mcard`). Checked: headless Chromium on `#/builder` went from "The
  builder did not load" to "The builder is ready."
- Claude: **a Discord link** to the G1-Mods channel, in the sidebar's Community group and on the Links page
  (the same `https://discord.gg/CMw5mbWe58`).
- Claude: **a changelog page and a compare view**. The changelog (`#/changelog`) renders `CHANGELOG.md` like the
  guides; the compare view (`#/compare`) shows any two modules side by side (picture, tags, summary, ports, controls).
  Both are in the nav. Rendering the long changelog at 360 px exposed a 15 px overflow, fixed by letting `.shell`'s
  column shrink (`minmax(0, 1fr)`) and `.guide` break long tokens (`overflow-wrap: anywhere`). The Spanish version
  stays a separate, later job. Checked in headless Chromium at 360 px.

## 2026-10-28

- Claude: **sharing and finding**. Open Graph and Twitter cards with a 1200×630 preview image (`web/og.png`,
  made with the site's colours), page titles and descriptions that follow the route (a module's name and summary, a
  guide's own title), and a fuller LINKS page: Animatek's **YouTube** and the **Nord Modular Editor**, the
  community's online patch archive (nordmodular.com, named in the plan, no longer answers). The `#/module/<folder>`
  addresses stay as they are. Checked in headless Chromium: the title and description change per route and the two
  new links are on the page.
- Claude: **more on each module page**. Each example `.pch` now says what it does, not only its file name
  (`patch_notes` in `module.json`, written for all 15 patches, shown under the link); a **video slot** per module
  (`video` in `module.json`, a YouTube embed, empty until Javier has one); and **image captions** (`image_captions`)
  so a second panel picture can be labelled (the thumbnails already switch). The texts flagged as "read from the
  code, not played" were re-checked against G1-Emu: the Mix1-1A chain adds its channel (the chained output is 6 dB
  over one channel, and Off leaves the chain passing) and the Note Out's Note (0 units is E4, +12 an octave) and
  Gate thru are as written — `check_mix1_1a.py` and `check_note_out.py` pass, nothing changed. Looked at in headless
  Chromium at 360 px.
- Claude: **usage guides under Learn**. Four new pages, each a `docs/*.md` rendered by `make_bundle.py` like the
  install and recovery guides: **First patch** (Turing Machine → Scale Quantizer → OscA, with a new
  `patches/turing-scale.pch`), **Connect NME to G1-Emu** (the safe way in), **Clock & reset** (how the G1's
  sequencers, the 5-Step Seq and the 8Counter stay in step, pointing at the existing `seq5-ctrlseq.pch` and
  `counter8.pch`), and a fuller **Nord Modular G1** page (history, the three models, how a patch runs on the DSPs,
  control vs audio rate). The Learn group in the nav now lists all six, `app.js` has the routes, and `make_bundle.py`'s
  `GUIDES` covers them. Checked in headless Chromium at 360 px (all six render, no overflow, nav highlights); the new
  patch played in `g1patchtest` (output 1, the pitch stepping as the Turing clocked).
- Claude: **one copy of each guide**. The install and going-back pages lived twice — in `web/index.html` and in
  `docs/INSTALL.md` — and had already drifted. The web now renders them from the Markdown: `docs/INSTALL.md`
  (install, no longer carries the going-back part) and the new `docs/RECOVERY.md` (going back & fixes) are turned
  into HTML by `web/make_bundle.py` (Python-Markdown; tables get the site's scrolling wrapper) and carried in
  `bundle.json` under `guides`; `app.js` fills the two pages, whose sections in `index.html` are now empty. `README.md`
  points at both, and the Pages workflow installs `markdown`. Checked by building the bundle and in headless Chromium
  at 360 px: both pages render with their headings, the "Experimental" notice and the fixes table, and neither overflows.
- Claude: **the module page no longer overflows a 360 px phone**. `.mlayout`'s mobile breakpoint was
  `grid-template-columns: 1fr`, which is `minmax(auto, 1fr)` and would not let the column shrink below the controls
  table's min-content, pushing `main` and the sidebar to 412 px and the page into a sideways scroll. It is now
  `minmax(0, 1fr)`, so the table scrolls inside its own `.tablewrap`. Checked in headless Chromium at 360 px: every
  route stays 360 px wide and the controls table scrolls; desktop is unchanged.
- Javier and Claude: **`WEB-PLAN.md`**, the written plan for what is left on the web (check the live site, one copy of
  each guide, usage guides, more on module pages, sharing, later ideas).
- Javier and Claude: **text for every module's page** (`about`, `usage`, `notes`, and `credits` on the Random) in the
  13 `module.json`, written from each `.asm` header and `PORTING.md`; and the page's button now **adds or removes
  the module from "My build"** (it followed the builder's ticks, as the cards' + do) instead of only linking to the
  builder. Checked in headless Chromium at desktop and phone widths; `tests/check_insert.py` OK.

- Javier and Claude: **the 13 module panel pictures** (Javier's NME captures) are in each
  `modules/<name>/images/panel.png`; the web shows them on the cards (whole, not cropped) and on each module's page.

- Javier and Claude: **a page for every module** (`#/module/<folder>` on the web): picture, data sheet (type, kind,
  version, author, licence, real-G1 status, DSP/memory load), ports and lights, controls with range and default,
  example patches and the next/previous module. Ports, controls and load are read from each `nme-modules.xml`
  by `web/make_bundle.py`; pictures go in `modules/<name>/images/` (the first is the panel) and optional text
  (`about`, `usage`, `notes`, `credits`, `status`) in `module.json` (`modules/README.md`). Without a picture the
  page shows the generated panel. Checked in headless Chromium.

- Javier and Claude: **Patreon and Donate moved to the sidebar's foot** (where the theme button was), and the
  **theme switch is a sun/moon icon in the top bar**, light or dark (it follows the system until it is clicked;
  the choice is remembered). On phones the two links sit at the end of the menu strip. Looked at in headless Chromium.
- Javier and Claude: **Patreon and Donate (PayPal) buttons in the top bar**, right of the "OS 3.03 → 3.09" badge
  (the same PayPal link as the repo's GitHub Sponsors), and the PayPal one in the Links page. Looked at in headless
  Chromium at desktop and phone widths.
- Javier and Claude: **the module library has a + on every card** to add the module to the ROM (it
  ticks the builder's box, so both stay in step), a bar with the count, Add all / Clear and a link to the
  builder, and a "My build" box in the sidebar. New **Contribute** page (set up to develop, how a
  module is laid out, the limits, a first pull request step by step, testing before flashing, house
  rules), shaped after elekloader's contributor pages and written for this repo. Checked in headless
  Chromium; the click path itself was not exercised.
- Javier and Claude: **the web is redesigned as a small site**, Modwerk-like in layout and Animatek's in colour
  (blue `#2C7FFF`, Inter and JetBrains Mono, dark and light, a theme button): a sidebar (a strip on phones),
  search, an overview, a **module library** with cards and a kind filter, the builder (unchanged logic), the
  install and way-back guides, a page on the Nord Modular G1, and a **links page** driven by the `LINKS` list at
  the top of `web/app.js` (add a row to add a link). Checked in headless Chromium at desktop and phone widths.

## 2026-10-27

- Javier and Claude: **the web builder is live on GitHub Pages** at
  <https://animatek.github.io/G1-Mods/>: a Pages workflow (`.github/workflows/deploy-pages.yml`)
  packs `web/bundle.json` in CI from the committed DSP caches (`out/dspasm-*.json`, now in git)
  and deploys `web/`. The repo is public. README and `CLAUDE.md` say so.
- Javier and Claude: **the web builder links to the repository, G1-Emu and Animatek NME** — now in the
  header, restyled to Animatek's look (blue `#2C7FFF`, Inter, the Animatek logo).
- Javier and Claude: **the warning colour is rose** (`#e11d48`) instead of orange, in the notice
  ("Experimental on a real G1") and the module warnings.

## 2026-10-26

- Claude: **`docs/INSTALL.md`**, the install guide: build, G1-Emu, a real G1 with NME's update,
  the way back with Clavia's 3.03b updater, and what each failure looks like. **PORTING.md,
  "Before publishing"**: what is left, in order (G1-Emu's RAM noise, NME's image limit, the
  guide, a beta, publishing together, Modwerk, the 3.03b). Linked from the README and the page.
- Javier and Claude: **all 13 modules in one build play on the real G1**: `os-all.bin` (packed,
  Note Out guarded) booted and everything worked. Kept in `Roms/works-on-real-g1/all-os.bin`.
- Javier and Claude: **Note Out works on the real G1** with the guarded scan: Note Out alone
  booted and its notes came out of the MIDI OUT. Every module has now played on the hardware.
  Its "G1-Emu only" mark is gone from `module.json`, README and the web page.
- Claude: **Note Out's scan guarded against power-on garbage**: a module pointer is followed only
  if it lies in RAM, is even, and its section's DSP is 0-3 (the likely reason it hung a real G1:
  G1-Emu's RAM starts at zero, a real one's does not). Checked in G1-Emu (`check_note_out.py`);
  not yet on the hardware (`Roms/tests/noteout-os.bin`). The web page marks modules that fail on
  a real G1 (`real_g1` in `module.json`): Note Out shows a warning, starts unticked, and with it
  ticked the page gives the G1-Emu ROM only.
- Javier and Claude: **twelve modules play on the real G1**: every one but Note Out, packed
  (`all-but-noteout-os.bin`), booted and played; so the unpacker works on the hardware. The full
  set had hung twice: **Note Out hangs a real G1** at power-on (its main-loop hook, cause open).
  README and the web page say so. `Roms/works-on-real-g1/` keeps only the images that booted
  on the hardware.
- Claude: **all 13 modules fit an OS update, packed**: `tools/lz.py` packs the package (LZSS)
  when it does not fit as it is, and `tools/unlz.s` (66 bytes of 68k, `tools/unlz.m68k`)
  unpacks it at boot from the flash. 14,896 bytes into 5,718. Builds that fit as they are do not
  change (the FlipFlop one is byte for byte the one that played on the real G1). `run-nme.sh`
  now runs NME's mods build from `~/.local/share/Animatek/G1-Mods/` (it was in a temporary folder).
  Checked: every module's test on the packed `all` build in G1-Emu; the packer round-trips.
- Javier and Claude: **the FlipFlop plays on a real G1**, the first module of ours on the
  hardware: `flipflop-os.bin` (new layout) installed with NME's update, booted, NME offered the
  module and a patch of Javier's played with its LED. Before it, Clavia's factory OS alone
  (385,024 bytes) booted the same way. README and the web page now say "experimental on a real
  G1" instead of "does not boot".
- Claude: **the package now fits an OS update** when it is up to 8,140 bytes: stored right after
  Clavia's OS (`$15DFE0`), the bootstrap at `$15FFAC` copying it from the flash's copy of the
  image. Bigger builds (all 13 modules, 14,896 bytes) keep the old layout, G1-Emu only. The
  module tests take `G1MODS_BUILD` to build a chosen set. NOTES.md, "The first real G1". Checked:
  the `all` ROM unchanged byte for byte; every module's test passes on new-layout builds, in
  three groups; the 8 KB measured untouched at boot in `g1boot` first.
- Claude: **the first real G1: our OS does not boot there.** `Roms/os-all.bin` went into Javier's
  G1 with NME's *Update Synth OS*; it shows its version and hangs. Clavia's 3.03b went back the
  same way (`Roms/clavia-original/clavia-3.03b-os.bin`, the capture unpacked) and the G1 is fine.
  README and the web page now say a real G1 does not boot it; NOTES.md, "The first real G1",
  lists what to look at.
- Claude: **why an update failed: the boot ROM's utility erases sectors 0-5 only** (ROM `$55C4`,
  the loop at `$5894`), so an OS image holds at most 393,184 bytes; ours were 458,716, written over
  sector 6 unerased (fine while it was blank, a Write Error once our package was there).
  `g1update.py fromrom` now cuts the image at its last byte in use and refuses one over that;
  `run-g1emu.sh` and the web builder still give the ROM for G1-Emu and say why there is no OS
  image. The package (at `$166574`, past the limit) has to move before any build can go into a
  real G1. NOTES.md, "The first real G1". Checked: Clavia's factory OS gives 384,992 bytes; every
  build is refused with its size; the web builder (Pyodide) returns the ROM and the reason.
- Claude: **a web builder, on this computer** (`web/`, `web/serve.sh`): pick your 3.03 ROM, tick
  modules, get the ROM for G1-Emu and the OS update image, all in the browser. It runs the same
  Python through Pyodide 0.26.4: `patch_rom.py`'s work is now a function, `patch()`, that both
  call, and `web/builder.py` wraps it with `g1update.from_rom`. `web/make_bundle.py` packs the
  tools, the modules and their assembled DSP code into `web/bundle.json` (ignored). Each
  `module.json` gains a `summary`, the README's line. Checked: under Pyodide (Node), every module
  gives `Roms/rom-all.bin` and `Roms/os-all.bin` byte for byte, flipflop+mux8 gives the command
  line's ROM, no module is refused; the page loads the builder in headless Chromium.
- Claude: **the builds, in one place: `Roms/`** (ignored, as before). `rom-all.bin` (G1-Emu),
  `os-all.bin` (the same OS as an update image), `flash-all.bin`, Clavia's 3.03b update kept as
  the way back in `clavia-original/`, and the earlier experiments in `old/`; they were all mixed
  in `out/`. `run-g1emu.sh` now builds into `Roms/` and rebuilds the OS image with the ROM, so
  both stay in step. README, "Where the builds are". Checked: rebuilding both from G1-Emu's ROM
  gives the moved files byte for byte (13 types).

## 2026-10-25

- Claude: **`g1update.py fromrom`**: the OS a ROM built by `patch_rom.py` carries, as an update
  image, so a G1-Mods build goes into a flash like any OS (NME's Device > Update Synth OS, or
  `g1update.py build`). The ROM's OS runs to its end, 0x73800 bytes, more than a flash holds;
  past `$16FFE0` it is all $FF in the rack's 3.03 ROM and in our builds (they end at `$169FD7`),
  so it is cut there, and a build that went past would be refused. Checked: `out/rom-all.bin` (13
  types) gives a 458,716-byte image that differs from the factory OS in the modules' 14,763 bytes;
  NME (branch `mods-layer-2`) installed it into G1-Emu in update mode, the OS kept was that image
  byte for byte, and after the restart G1-Emu said 3.09 and NME offered the modules (Javier).
- Claude: **the OS update protocol, solved, and `tools/g1update.py`**, which builds the MIDI
  stream that installs an OS into a G1's flash (`build`) and turns a recorded one back into its
  image (`unpack`): messages 00/70/71/73, the update utility's 8-to-7 packing and its byte
  scrambling, read from the boot ROM and from a capture of Clavia's 3.03b updater in G1-Emu.
  NOTES.md, "The update protocol". Checked: the capture unpacks into the 3.03b image byte for byte
  with its checksum; `build` on that image gives the updater's messages byte for byte but the
  last one's padding; and our stream, sent with `aseqsend -i 60` (3 min 27 s), was taken by G1-Emu
  in update mode, which answered the checksum as right (`F0 33 00 06 7F F7`).

## 2026-10-19

- Claude: **Note Out: the module after it ran on its data** (found by Javier: a second NoteSeq
  stood still, a ClkDivFix added live silenced the MIDI). Its DSP code left r3 at its own X
  words; it now moves it past them, as every module must. And a Gate thru output. Checked:
  `check_note_out.py` with a new case (an LFO after it into Note: the notes follow it), a patch
  with two NoteSeqs (the second steps), a ClkDivFix added live (the MIDI goes on).
- Claude: **type 60, Note Out**, after the G2's NoteSend: Note and Gate in, Chan and Vel; a note
  on at Gate's rising edge, its note off at the falling one, out of the G1's MIDI OUT. The DSP
  packs the gate's edges and the note into one X word (`noteout.asm`); a 68k routine of ours,
  the first in real assembly (`noteout_poll.s`, GNU as for the CPU32 in Digitakt-Mods' Docker
  image: `tools/m68kasm.sh`), takes the OS's main loop's first call (`Build.redirect_call`),
  finds the modules by their type a few pointers a turn, reads each word and queues the notes
  where the OS's own note senders do. NOTES.md, "Type 60: Note Out". Checked:
  `check_note_out.py` in G1-Emu (an LFO into Gate gives `90 40 64` / `80 40 40`; a Constant of
  +12, Chan 3, Vel 90 gives `92 4C 5A`; Chan changed live; nothing without the module), and
  every module's test and `check_insert.py` pass with it built in (`check_mark.py` and
  `check_nme_data.py` read NME's `mods-layer` branch, not checked out).
- Claude: NOTES, flashing a real G1: **Shift + Store at power-on enters the MIDI update mode**,
  confirmed by Javier on his G1, so a bad OS of ours has a way back; and Shift + Patch/Load
  boots the ROM's factory OS (tried too): two ways back from a bad OS.
- Claude: NOTES, **an OS update keeps the patch banks** in G1-Emu: Clavia's 3.03b updater over a
  flash with the factory OS, then a plain restart; the banks' bytes compared with a copy taken
  before, unchanged.
- Claude: NOTES, **Clavia's 3.03b flashed over itself on Javier's real G1**: the whole procedure
  (Shift + Store, Safe (Slower), the G1's own Store to confirm), as the rehearsal before an OS of
  ours.
- Claude: NOTES, **a MIDI Out module as the G2's** (idea): how the G2's NoteSend works (a DSP
  mailbox the CPU polls). Then read in the G1's OS: the MIDI-out sender and its queues, the
  keyboard model's unused note senders, and why the lights' poll does not do for notes (active
  slot only, with an editor); the plan, a poll of our own from the main loop. Testing is ready:
  G1-Emu's plugin now has the MIDI OUT as its MIDI output (G1-Emu PR #79).

## 2026-10-18

- Claude: **a README**: what G1-Mods is and how it works, the twelve modules, the layout, how to
  try it, who is responsible for what, firmware and rights, licence (GPLv3, the `LICENSE` file
  added, as G1-Emu's) and credits (Gearmulator), from PORTING's notices agreed with Javier on
  2026-10-17. On GitHub as `animatek/G1-Mods`, private for now.

- Claude: **the mark**: every build with modules says version 3.09 in its IAm instead of 3.03
  (`VERSION_MARK`, one `move.b` at `$10B288`), so NME tells it apart synth by synth on
  connecting (after Javier: with several synths, a Clavia OS sits next to a modified one).
  Clavia's editor 3.03 still connects to it (it takes 3.00-3.09). NOTES.md, "The mark". Checked:
  `tests/check_mark.py` boots both in G1-Emu (3.03 and 3.09, NME looking for 9); the `all` ROM
  differs from before in that byte only.

- Claude: **NME's layer**: `tools/make_nme_data.py --layer <NME's data>` writes
  `mods-modules.xml` and `mods-theme.xml`, the modules alone, which NME's `mods-layer` branch
  loads on top of Clavia's files and offers only to a synth ticked "OS with G1-Mods modules" in
  MIDI Setup (per synth, after Javier: with several synths, a Clavia OS sits next to a modified one).
  `tests/check_nme_data.py` now checks that layer as it is on disk (and that it is not stale),
  and that NME's ParameterEncoder has no case of its own for the types (their widths come from
  data). `run-nme.sh` builds from `mods-layer`. Checked: `check_nme_data.py` passes, 12 types.

- Claude: **one folder per module** (`modules/<name>/`: `module.json`, `build.py`, its DSP code,
  NME's entries whole, its test and patches) and **a registry of types**
  (`modules/registry.json`), steps 1 and 2 of PORTING's "Next: opening it up". What every build
  uses moved to `tools/g1rom.py`; `patch_rom.py` reads the folders, and takes a list of them
  (`flipflop,mux8`) as well as an experiment; `make_nme_data.py` places each folder's entries
  (928 lines to 53; Mix1-1A's entry, cloned from the Mixer (3)'s, now written whole). Checked:
  the four ROMs (`all`, `stringtest`, `audiotest`, `mixer3-silent`) and NME's two files come out
  byte for byte as before, and `tests/run_all.py` passes in G1-Emu.

## 2026-10-17

- Claude: `PORTING.md`, open and free for good: nothing of the mods exclusive to Patreon or paid,
  Gearmulator credited everywhere (Javier).

- Claude: `PORTING.md`, "The builder and the catalogue": a Modwerk-like site building in the
  browser from the user's own OS, one C++ core (WebAssembly and NME), NME showing the mods only
  with a modified OS, and who is responsible for what: tested only on the emulator, each owner
  responsible for their G1, no hardware support, community modules in their authors' repos and
  linked after a review, with draft notices (agreed with Javier).

- Claude: `PORTING.md`, "Next: opening it up": a folder per module, a type registry, GitHub, the
  builder in NME (agreed with Javier).

- Claude: `PORTING.md`, the modules asked for after the first post, in one entry.

- Javier (Claude wrote it down): **the ROM with the package at `$1C6000` works**, played in
  G1-Emu.

- Claude: **more room for the package**: it runs from `$1C6000` (136 KB the OS never touches,
  found by replaying NME's 2.1 MB session with the RAM filled with a pattern) and is stored in
  both 19 KB runs of the OS image, copied by a 52-byte bootstrap: 38 KB in all, 24 KB left (was
  under 900 bytes). The 97 KB after the old room are OS buffers, not free. Checked: all tests
  pass; a ROM split over both runs by force plays bit for bit as the normal one. `NOTES.md`,
  "More room".

- Claude: `PORTING.md`, the Osc String next to the G2's (no pluck of its own, Cent and KBT): add
  Cent and KBT to ours, keeping Trig and Exc (Javier likes ours).

- Javier (Claude wrote it down): **the Osc String works**, played in G1-Emu.

- Claude: **type 56, Osc String** (`dsp/string.asm`), a plucked string (Karplus-Strong), the
  first audio-rate type: `audio_type` and `write_audio_x_routine` (checked first on a VCA, the
  `audiotest` experiment), a 1,024-word line the code clears itself, the period from Note and
  Pitch by a cubic and shifts, Damp's delay taken from it (`damp_routine`). NME `g1-mods`
  `93d31ca`. New `tests/check_string.py`: in tune within a cent from A1 to A5, from the keyboard,
  at any Damp; all tests pass. Under 900 bytes of room left; six free types.

- Claude: `PORTING.md`, the builder picks among the new modules only (Javier); swapping all the
  G1's modules for the G2's noted as not recommended, and why.

- Claude: `PORTING.md`, Javier's idea of an OS builder (pick the modules, a bar for the room
  left, build from the user's own OS), with the rules it needs.

- Claude: `NOTES.md`, starting the String: **only 2.3 KB of room for code are left** (the package
  runs from 14 KB the OS never touches; the eleven types take 12 KB), how the OS writes a
  parameter to a module's audio X (`$10C4B0` and `$10C248`), and the G1 Delay's memory as the
  measure of a string's buffer. `PORTING.md`: room for code as the second limit.

- Claude: **type 55, Envelope** (`dsp/env.asm`): the G2's ADDSR, H, D and AHD from one engine,
  Gate/Trig, Attack, Decay 1, Level 1, Decay 2, Sustain, Release, Env and End. NME `g1-mods`
  `8bee1f9`. New `tests/check_env.py` (levels, release time to a sample of the model, End, Trig)
  passes; all tests pass. Seven free types left.

- Claude: **type 42, Level** (`dsp/level.asm`): the G2's ModAmt, MinMax, T&H and WindSw in one
  module with a Mode selector, A, B, Out 1, Out 2, Amount, Lo and Hi. **The Random gets a Bi/Uni
  button** (Javier), its seventh parameter. NME `g1-mods` `fba49d5`. New `tests/check_level.py`
  (every sample of each mode) and a Uni case in `check_random.py` pass; all tests pass. Eight
  free types left.

- Claude: **type 41, Bits** (`dsp/bits.asm`): the G2's BinCounter, ADConv and DAConv in one module
  with a Mode selector (Count, A>D, D>A) and all their connectors, Out, eight bits and eight LEDs.
  NME data in "Logic (mods)" (NME `g1-mods` `3a23de3`). New `tests/check_bits.py` passes;
  `bits.pch` starts in D>A for `check_insert.py`. All tests pass. Nine free types left.

- Claude: `PORTING.md`, ideas from Javier's first tries: the Random's range and a Uni/Bi button
  to check, one NME and one G1-Emu that tell the modified OS by themselves, and the mods tabs
  under their family's.

- Javier (Claude wrote it down): **the Random's Poly works**, checked by ear in G1-Emu: each voice
  plays its own sequence.

- Claude: **type 6, Random** (`dsp/random.asm`): the G2's randoms in one clocked module, Clk, Rst,
  Out, Trig, with Seed, Poly (a seed per voice: the Seed routine gets the voice), Step, Edge,
  Prob and Length. NME data in "LFO (mods)" (NME `g1-mods` `5847ad1`). New
  `tests/check_random.py`: the values match a Python model of the module one by one; Length, Rst,
  Prob, Step and Edge checked; Poly by ear only. All tests pass. Ten free types left.

- Claude: `PORTING.md`: the plan for the free types, revised with Javier: the switches go into
  the Mux8-1's type and the G2 mixers into the Mix1-1A's, so four new types cover the small
  families and seven are left for big modules (oscillators, effects), one a type.

- Claude: **the Mixer Inv (119) and the Noise S&H (122) are out**, to free their types (Javier:
  the first was a test, the second is easy to patch with G1 modules). Their code, notes and tests
  stay in git history; `tests/mixer-demo.pch`, `noise-sh.pch` and `check_noise_sh.py` go.
  Eleven free types now. `PORTING.md` has the plan agreed with Javier: a type per family (Random,
  Switches, Conversion, Level, Envelopes, G2 mixers, one big oscillator and one effect, three kept
  back) and virtual modules in NME (one type, several panels), to do.

- Claude: **type 101, Mux8-1** (`dsp/mux8.asm`): the G2's Mux8-1 and Sw8-1 in one type, In 1–8,
  Ctrl, Out, a Sel knob that Ctrl adds to (8 units a step) and eight LEDs. **Found: the G1 has
  128 types and only nine are left free** (6, 41, 42, 55, 56, 60, 93, 109, 116); 127 is Clavia's
  PolyAreaIn and 128 does not exist. `FREE_TYPES` in `patch_rom.py`, which refuses any other;
  `PORTING.md` says how to spend them. NME `g1-mods` `c7980d6`, `60c29ca` (its mods test knew only
  119 and above). New `tests/check_mux8.py` passes; all tests pass.

- Claude: **type 126, 8Counter** (`dsp/counter8.asm`), the G2's: Clk, Rst (as the 5-Step Seq's,
  so it keeps in step with the G1's sequencers), eight outputs, one high a step, and eight step
  LEDs. NME data in "Logic (mods)" (NME `g1-mods` `0fdcd0c`). New `tests/check_counter8.py` (every
  sample against a model of the counter, Rst included, and the step LEDs) passes; all tests pass.

- Claude: **type 125, Scale Quantizer** (`dsp/quant.asm`, Javier's idea, after JW-Modules'
  Quantizer): In, Out, Root (C..B), Scale (16 by name) and Octave (−4..+4). A table per scale
  written by the Scale routine (`write_table_routine`, `Param(table=)`). Found on the way: 0 at a
  pitch input is an E, and n2 is not free between modules. NME data in "Control (mods)" (NME
  `g1-mods` `3f849f8`). New `tests/check_quant.py` (every scale, sample by sample) passes;
  `check_nme_data.py` checks the scale names; `check_turing.py` reads only whole Meters messages
  (the PC Port log cut one once). All tests pass.

- Claude: **the Turing Machine grows** (Javier): eight gate outputs, bits 0–7 while Clk is high
  (the Gate output goes: it was gate 1), a Scale knob for CV, and eight LEDs with the register's
  low byte, through the meter (`bits_routine`, `control_type`'s `bits`; NME `g1-mods` `led-array`
  with `bits="true"`). Height 5. `tests/check_turing.py` now also checks gates 1, 4 and 8, Scale
  64 and the byte in the Meters messages; all tests pass.

- Claude: **a meter carries 14 bits**, read in the OS's meter poll and sender (`NOTES.md`): the
  value routine's word goes out as two 7-bit values, so the Turing Machine's 8 LEDs fit in one
  module's meter. `PORTING.md`: a Mutator inside the synth, as an idea (the G1's morph already
  interpolates).

- Claude: **the Turing Machine's Prob is bipolar**, as the original's big knob (Javier: a 0..127
  knob locked at both ends confused): centre random, right locked, left the pattern inverted each
  pass; NME draws it from the centre (`value-64`, default 64). `tests/check_turing.py` updated
  and passing. `PORTING.md`: a bigger Turing Machine with the expander's outputs, as an idea.

## 2026-10-16

- Claude: **type 124, Turing Machine** (`dsp/turing.asm`), after Music Thing Modular's: Clk in,
  CV (the register's low byte as a level) and Gate (bit 0 while Clk is high) out, Prob, Length
  1–16 and Lock. Built with `control_type`; NME data in "Sequencer (mods)" (NME `g1-mods`
  `7f91264`). New `tests/check_turing.py` (repeats every Length with Prob 0 or Lock, inverted at
  the top, drifting at 64, the Gate) passes, and every other test; `check_insert.py` plays it
  too. Without its 8 LEDs yet.

- Claude: **the 5-Step Seq's Rst works as the G1's sequencers'** (Javier: the sequencers would
  not sync). Measured against a CtrlSeq on the same clock and reset: Clavia's Rst arms the
  sequencer and the next clock goes to the first step, and it starts on the last step; ours
  jumped to the first at the Rst edge, a step ahead. Now the same. `tests/check_seq5.py` plays
  both (`tests/seq5-ctrlseq.pch`, Rst between clocks) and they stay on the same step; all tests
  pass. `PORTING.md`: G2 patches on a G1, as an idea.

- Claude: **type 123, 5-Step Seq** (`dsp/seq5.asm`): Clk, Rst, Out and five bipolar knobs
  (−64…+63), after Buchla's five-stage sequencers, with a row of five step LEDs (a led-array on
  the OS's meter list, `$1169BA`, as the CtrlSeq's; `value_routine` and `connection_routine`'s
  `meter`). Built with `control_type`. NME data in "Sequencer (mods)". New `tests/check_seq5.py`
  (order, Rst, a knob live, the step LEDs) passes, and every other test with it;
  `check_insert.py` plays it too.

- Claude: **a control type is described once** (`control_type` and `Param` in `patch_rom.py`):
  DSP file, X words, parameters and LED, and the counts, parameter table and routines, `+$08`,
  connection routine and descriptor derived from them, instead of fields copied from a donor and
  fixed by hand (where the day's three bugs came from). The FlipFlop and the Noise S&H use it.
  New `tests/check_nme_data.py` (the OS and NME agree on each type's parameters, widths, inputs
  and outputs; it catches a changed maximum) and `tests/run_all.py`. All tests pass.

- Claude: **fixed patches breaking when a module was added live** next to a Noise S&H (Javier: the
  oscillators stopped, only clicks). The descriptor's word at `+$24` is the size of the module's
  record in the OS's RAM; the Noise S&H had CompareAB's (no parameters) with two, so the next
  record was written over its parameters. Now every type's is computed from its parameters.
  `tests/check_insert.py` (a FilterE added live to each test patch) passes, and so do the others.
  Found with G1-Emu's new `--add-module-at`, `G1_WATCH_PC` and `G1_RAMDUMP`. `NOTES.md`: a module's
  record.
- Claude: **fixed the Noise S&H's knobs doing nothing when turned** (Javier): before a live change
  the OS asks the type's `+$08`, and CompareAB's left `d0` as it was; now ClkDiv's (`clr.b d0`).
  Both tests gain a live case with G1-Emu's new `--param-at` (Range 1 → 5 octaves, Bi → Uni;
  FlipFlop D → RS) and pass. `NOTES.md`: how a parameter reaches the DSP live. `PORTING.md`: a
  Scope, as an idea.
- Claude: the Noise S&H's panel in NME gets a knob for Range next to its display (Javier: the
  display alone could not be changed). NME `g1-mods`.
- Claude: **Noise S&H gets Range (1–5 octaves) and Uni/Bi**, with parameter routines of our own
  (`param_routines`, `write_x_routine`); a semitone measured as one control unit at a pitch input.
  `tests/check_noise_sh.py` checks 1 and 5 octaves Bi and 3 Uni (spans, mirror, edges) and passes;
  so do the FlipFlop's and the Mix1-1A's. NME `g1-mods`: a display for Range and a button for
  Bi/Uni.
- Claude: **type 122, Noise S&H** (our own: a sample and hold with its own noise, Out and Inv),
  `dsp/noise_sh.asm` on CompareAB. `tests/check_noise_sh.py` passes (Out changes on every edge and
  only there, 285 values of both signs in 288 edges, Inv its negation); the FlipFlop's and the
  Mix1-1A's tests still pass. NME's `g1-mods` branch has it, and now the Patch Mutator too
  (`mutator-g2` merged in, NME `b24fe26`).
- Claude: **the FlipFlop lights Q's LED**: a value routine reading Q through the DSP's host port,
  registered with `$116832` (the OS keeps one LED per module). `tests/check_flipflop.py` gains a
  sixth case (LED 0 on and off in the Lights messages, logged with G1-Emu's new
  `G1_PCPORT_LOG`); all pass. `make_nme_data.py`: the FlipFlop's panel laid out like the G2's, with
  the LED. `NOTES.md`: plain LEDs.
- Claude: **fixed the FlipFlop's NotQ sharing a word with the next module's output** (Javier: on
  the G2 demo the two outputs alternate; here one gave fast triggers unrelated to the clock). The
  descriptor's output count (`+$08`) was ClkDiv's 1; now 2. `tests/check_flipflop.py` has a fifth
  case, a Constant right after the FlipFlop, which stays constant now and changed with NotQ before.
  All cases pass, and the Mix1-1A's test too.
- Claude: **fixed the modified OS hanging on its second boot.** The package crossed `$70000` in
  the flash, where the patch banks start and which the OS formats on its first boot, erasing the
  registration routine. Now it is stored at `$166574`, inside the OS's sectors, and a bootstrap
  copies it to `$170000` at boot. Checked: three boots on the same flash, the old hanging flash,
  both module tests, and a replayed 2 MB NME session (package intact). `NOTES.md` corrected.
- Claude: with a fresh flash the G1-Emu window boots the G1-Mods ROM (checked by Javier), so the
  blank display came from the old `out/flash-all.bin` (kept aside). Noted in `NOTES.md` as an open
  problem to solve before a real G1.
- Claude: `patch_rom.py` writes the ROM under a temporary name and renames it, so an emulator
  starting while a test rebuilds it never reads half a ROM; `dspasm.py` keeps each source's
  assembled words in `out/` (keyed by its text), so a build without code changes does not load
  the index. Checked: the same ROM with and without the cache. Done while chasing a G1-Emu window
  that showed a blank display with the G1-Mods ROM (that ROM boots in `g1boot` and `g1patchtest`;
  the window's flash, `out/flash-all.bin`, was set aside to try a fresh one).
- Claude: **the FlipFlop is complete** (the G2's: D/RS Type, Clk, In, Rst, Q, NotQ), with DSP code
  written in assembly (`dsp/flipflop.asm`) and a small assembler (`tools/dspasm.py`) that finds
  encodings in an index of G1-Emu's disassembler. ClkDiv is the donor; the Type is written to X by
  a routine of ours; the connection routine is generated from the code's marks.
  `tests/check_flipflop.py` checks four cases (D, toggle, reset, set) and passes; so does
  `check_mix1_1a.py`. `make_nme_data.py` takes whole entries (the FlipFlop's). Also in `NOTES.md`:
  how a module's lights reach the editor (from the CtrlSeq), and the plan to flash a real G1;
  in `PORTING.md`: G1 and G2 sequencers compared, and new modules of our own (Noise S&H, 5-step
  sequencer, small reverb, Turing Machine). `tools/__pycache__` out of Git.
- Claude: `PORTING.md`, the porting checklist: every G2-only module and the G2 versions that do
  more than the G1's, with their DSP size in the demo, whether a real G1 can run them (the limit:
  each DSP has 4K program and 2K+2K data words, no external RAM, so long delays and the reverb
  are emulator-only) and their status; and the order proposed.
- Claude: `make_nme_data.py` puts each new type in "<donor's family> (mods)" ("Mixer (mods)",
  "Logic (mods)"), which NME's `g1-mods` branch lists right after the family in the module bar,
  the browser and the right-click Add Module menu (NME `8d72735`).
- Claude: **Mix1-1A gets its Ch 1 button** (mutes the channel, not the chain): parameter 1 to Y[0],
  9-word code with its own connection routine, and a parameter table of its own (`Level` 127,
  `Ch 1` 1). Found why a first try hung the OS: a parameter's width comes from its maximum (NME's
  `modules.xml`, the OS's `+$1C` table) and the two disagreed. `tests/check_mix1_1a.py` now checks
  both buttons too; all pass, and so does the FlipFlop's. `make_nme_data.py` replaces a type it
  made before instead of skipping it. `NOTES.md`: the button, the widths, and what the Lin/dB/Exp
  curves need.
- Claude: **type 121, Mix1-1A** (the G2's Mixer 1-1 A: one input with its level plus a chain
  input), on the Mixer (3)'s routines with code of our own and 1 parameter, 2 inputs, 1 output.
  `tests/check_mix1_1a.py`: same level as the Mixer (3) at 100, 64 and 0, +6.0 dB chained.
  `NOTES.md`: how a parameter reaches the DSP. `patch_rom.py` builds Mixer (3) variants with
  one function (`mixer3_variant`); `make_nme_data.py` can drop connectors and knobs.
- Claude: `tests/mixer-demo.pch`, the Mixer (3) and the Mixer Inv side by side on one oscillator:
  output 1 at −63.5 dBFS, output 2 silent (cancelled); with one input on the Mixer Inv it gives
  −69.5 dBFS, 6 dB under the sum. The two mixers work in one patch. Launchers for both apps in
  the maintainer's desktop (outside the repo), noted in `NOTES.md`.
- Claude: **type 120, a D flip-flop, works** (`NOTES.md`, "Type 120"): own DSP code and X data,
  CompareAB's entry with our descriptor and its connection routine patching the output at word
  17. `tests/check_flipflop.py` checks it in G1-Emu: Q changes 8 times for 8 crossings of D, each
  on a clock edge, and equals D at all 283 edges checked. `tools/patch_rom.py` rewritten: types
  are laid out from `$16FB80` and registered by one routine; experiment `all` (119 and 120).
  **Fixed** in type 119: the two nop-offset bytes after `+$24` were not copied (the next module
  of audio would have been placed 78 words away). `tools/make_nme_data.py` (replaces
  `make_modules_xml.py`) adds the types to NME's `modules.xml` and classic theme. `run-g1emu.sh`
  and `run-nme.sh` to try them by hand. `NOTES.md`, "How a module's data is loaded", from the
  loader.
- Claude: **the first new module type works.** `tools/patch_rom.py type119-mixinv` registers a
  type 119 (the Mixer (3) with input 1 inverted) with a hand-assembled routine hooked to the end of
  the registration list; `tools/make_modules_xml.py` writes a `modules.xml` with it for NME and the
  test bench. Checked in G1-Emu: the OS registers it (RAM dump), the battery measures it at
  −61.8 dBFS against −52.3 for the Mixer (3) (−9.54 dB predicted), and the original ROM refuses
  the same patch. `NOTES.md`, "The first new type: 119".
- Claude: `NOTES.md`, "The registration list": the boot routine that empties the 128 entries,
  the list of 110 `jsr` at `$10DC90` (ROM `$1A490`) with the type each one registers, what
  `$10DC42` does, and the ~15 KB the OS leaves untouched at the end of its RAM image
  (`$16FB7F`–`$1737FF`) for code of ours. Types 63, 65 and 77 are registered after all (the
  earlier note was wrong). Plan for the first new type. Checked by walking the list in the ROM and
  comparing a RAM dump after boot with the ROM.
- Claude: repo created, apart from G1-Emu so the emulator stays Clavia's OS untouched
  (`CLAUDE.md`: the rules). `NOTES.md`, "Module types in the OS", moved here from G1-Emu before
  it was pushed: one 48-byte entry per type at `$1C3B00`, filled by a registration routine per
  type; the counts of parameters, inputs and outputs; the DSP descriptor with the module's code;
  18 free type numbers. `tools/patch_rom.py` applies an experiment to a copy of the user's ROM;
  the first, `mixer3-silent`, gives the same ROM as the hand-made one the battery found silent
  (checked with `cmp`). `git status` shows no ROM.
