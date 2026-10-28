# Web plan

What is left on the G1-Mods site (<https://animatek.github.io/G1-Mods/>, source in `web/`), in the
order to do it. Written 2026-10-28, after the redesign, the module pages and their pictures and texts.

**Done so far:** sidebar site with overview, module library (cards, search, kind filter, "+" to
build), a page for every module (picture, data sheet, ports, controls, patches, text), the
builder, install and way-back guides, a Nord Modular G1 page, Links, Contribute, About.

## 1. Check what is live (small, first)

Nothing below should be built on a page nobody has looked at.

- [ ] Open the deployed site, not a local copy, in **dark mode**: contrast of pills, the data sheet,
      tables, the "In my build" button, the module pictures on a dark card.
- [ ] Phone width (360 px): module page, controls table and ports list, the builder's bar.
- [ ] Every link on Links and in the footer opens the right place.
- [ ] A bad address (`#/module/nothing`) says so and does not leave a blank page.

Done when: no fix is left from that pass, or the fixes are in one commit.

## 2. One copy of each guide

Install and Going back live twice: in `web/index.html` and in `docs/INSTALL.md`. They will drift.

- Choose: the web reads the Markdown (a small renderer, or the pages built from it in
  `make_bundle.py`), **or** `docs/INSTALL.md` is cut down to a pointer to the web.
- Recommended: build the guide pages from `docs/*.md` in `make_bundle.py`, so the repository
  keeps the Markdown (readable on GitHub) and the web gets the same text.

Done when: changing a step in one place changes it in both.

## 3. Guides for using the modules

The part that is still thin. Each in `docs/`, shown under **Learn**.

- [ ] First patch with the Turing Machine and the Scale Quantizer into an oscillator.
- [ ] Connect Animatek NME to G1-Emu and see the modules (the safe way in, before a real G1).
- [ ] Clock and reset: how the sequencers, the 8Counter and the 5-Step Seq stay together.
- [ ] A page for the Nord Modular G1 that goes further: models (keyboard, rack, Micro), a short
      history, how a patch runs on the DSPs. No text from Clavia's manuals.

Each guide needs a patch that exists in the repository, so it can be opened and tried.

## 4. More on each module page

- [ ] A video slot (YouTube) per module, empty until Javier has one: `video` in `module.json`.
- [ ] A second picture where the module has more than one panel (the Level's modes, the Envelope).
- [ ] "Used in" patches: the example `.pch` shown with what they do, not only a file name.
- [ ] Re-read the texts written on 2026-10-28 against the synth: the Mix1-1A chain, the Note Out's
      Note and Gate thru, and the "How to use it" steps come from reading the code, not from playing.

## 5. Sharing and finding

- [ ] A preview image for when the link is pasted (Open Graph and Twitter card), one per module if
      cheap: its panel picture.
- [ ] Page titles and descriptions that change with the route (the module's name and summary).
- [ ] A `LINKS` list that is complete: YouTube, the community's place if there is one, the AUR package
      of G1-Emu once it exists.
- [ ] Short, readable addresses: today `#/module/turing-machine` works; keep them stable.

## 6. Later, only if wanted

- A changelog page, read from `CHANGELOG.md`, for people who follow the project.
- A "compare" view like Modwerk's: two modules side by side.
- A Spanish version. The repository is English by rule (`CLAUDE.md`); a translation would be a
  separate layer on the web, not a change to the repository's language.

## Rules that stay

- Nothing of Clavia's on the site: no ROM, no OS, no text or pictures from its manuals, no donor
  module images (NME's `img/modules/` are Clavia's). Pictures are our own captures.
- The builder works only in the browser; nothing is uploaded.
- Large type and the menu on top on phones: the site keeps both.
- Every change: a line in `CHANGELOG.md` in the same commit, and `cambios apuntar` for the global one.
