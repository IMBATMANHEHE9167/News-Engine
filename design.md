# Design: VIDRAKSH News Engine

The locked system for `index.html`. Every change to the page reads this first. Change it on purpose; the file is the rule.
Method: Unslop and Hallmark (v2, the Kiln theme adapted to VIDRAKSH), then Impeccable (Operate mode, colorize, craft
floor) and Taste Skill (colour, type and contrast rules) for the colourway refinement. Brand values come from the
VIDRAKSH logo and are not negotiable.

## Direction

- **Product.** An hourly register of what Pune's press reports about crime and public order, joined into cases, for an
  analyst who needs to know what happened, where, when, and how far the record can be trusted.
- **Mode.** Operate: a working tool. Standard controls, scannable registers, colour that does jobs.
- **Character.** Exact, physical, unhurried.
- **World.** The logo's three materials: ink, paper, copper. Copper glows where more happened (the heat ramp).
- **Moments.** The statement band and 60-day heat strip at the top of each tab, the case file, the maps, the findings.
- **Signature.** The short copper rule from under the wordmark. It also marks severity under a record's time (fatal:
  copper; injured: light copper). Never decoration.

## Colour

Neutrals carry only a trace of warmth (chroma near zero) so copper is the one colour on the page. No other hue, except a
toned red for a failed data check. Light and dark are each composed, not inverted.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `--shell` | #181818 | #090908 | the ink band across the top (wordmark, tabs, scan line), both colourways |
| `--shell-ink` / `-2` | #F2F0EC / #ABA69E | #EEEBE6 / #A49E96 | text on the band |
| `--shell-copper` | #D08E5A | #D2925F | wordmark क्ष, its rule, the switch, "Next scan in progress" |
| `--paper` | #E7E5E1 | #151413 | the ground under the work |
| `--paper-2` | #F8F7F5 | #1E1D1B | sheets, cards, the case file, inputs |
| `--paper-3` | #DCD9D4 | #2A2826 | wells, chips, empty heat cells |
| `--ink` | #181818 | #EEEBE6 | primary text (brand ink) |
| `--ink-2` | #3D3B38 | #C5C0B9 | secondary text, values |
| `--ink-3` | #5C5853 | #969089 | meta, labels (4.6:1 or more on every surface) |
| `--rule` / `--rule-2` | ink 12% / 24% | ink 10% / 20% | hairlines / control outlines |
| `--copper` | #9C5A2B | #C98652 | active tab fill, key figures, focus ring, map marks, leading series |
| `--copper-text` | #8A4D22 | #DA9B69 | copper as text (5.2:1 or more) |
| `--neg` | #A3322A | #EE8573 | a failed data check, nothing else |

**Heat ramp** `--h0`..`--h6`: one copper hue, lightness stepping, chroma reduced near paper and near ink. Light runs pale
copper to deep copper-brown; dark runs dim copper to pale copper. Never maroon, red or cream. Text on a cell: `hInk()`
(ink up to step 3, `--on-copper` from step 4). Maps stop at step 5 so labels stay legible.

**Basemap.** OpenFreeMap positron (light) / dark, desaturated by `--tile-filter` so only the copper marks carry colour.

**Browser surfaces.** `color-scheme` per theme, themed scrollbars, copper caret and accent, copper selection,
`theme-color` = `--shell`.

## Type

- Display figures and statement headings: **Boska**. Every headline and all interface text: **Mukta** (carries
  Devanagari). Times and counts in registers: **JetBrains Mono** (data only). Marathi display: Tiro Devanagari Marathi.
- Sentence case everywhere; no tracked capitals. Nothing under 12px except numbers inside heat cells (11px).

## Space, shape, depth

- 4px grid. Radius: pills for controls (`--r-ctl`), 14px wells, 22px sheets and cards.
- Depth from surface steps (paper, paper-2, paper-3) and hairlines; one soft shadow for floating things (case file,
  map, popups). In dark the shadow adds a faint 1px ring so edges hold.

## Shell and layout

- Ink band (64px, sticky): wordmark, the five tabs in their fixed order (Reports, Map & patterns, Situations, Organised
  crime, Analytics), scan line, theme switch. Scope bar on paper under it: Area, Period, the stamp.
- Under 1024px the band stacks (brand row, sticky tab row, scan line), all on the ink band.

## States and motion

- Every control has hover, `:focus-visible` (2px copper outline; shell copper on the band), active and disabled.
- Motion: colour and opacity only, 160ms, `cubic-bezier(.22,1,.36,1)`. Reduced motion removes transitions.

## Contracts the design never touches

`INCIDENTS = EVENTS.filter(e => !e.orphan && !e.uv)` is what is counted, mapped and graphed. Data field names are the
collector's contract (report `u` is the article link). Element ids read by the script, the scan line, Analytics > Data
checks and the refresh/self-reload logic stay.

## Exports

The tokens live in `:root` of `index.html` (single-file page). Credits: Unslop by Damir Sokolovsky (CC BY 4.0);
Hallmark by Together AI; Impeccable by Paul Bakaus (Apache 2.0); Taste Skill by Leonxlnx (MIT).
