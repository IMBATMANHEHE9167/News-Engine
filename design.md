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
- **World.** The logo's three materials: ink, paper, copper. Copper glows where more happened.
- **Moments.** The statement band and 60-day strip at the top of each tab, the case file, the maps, the findings.
- **Logo.** विद्रक्ष with क्ष in copper and a thin copper rule centred under the whole wordmark, a third of its width
  (as in the original logo file `vidraksh-live/_samples/logo.png`). Never move the rule to one side.
- **Signature.** The short copper rule. Under a record's time it marks severity: a copper rule for a fatal case, a
  copper dot when someone was injured. Never decoration.

## Copper is sacred

Copper appears only as true copper: one value on paper (`--copper`, the brand's #9C5A2B) and one lit value on ink
(`--shell-copper` and dark-mode `--copper`, #D08A52). Never a paler, darker, browner, greyed or see-through shade of it:
no ramps, no opacity, no gradients, no copper tints behind rows. How much happened is shown by:

- **Size** on the maps (a solid copper disc whose radius grows with the count) and in heat grids (a copper square in a
  neutral well whose area is the count).
- **Height** in bar charts (the 60-day strip, reports by month, after dark, concentration), every bar the same copper.
- **Light** for the busiest: a copper glow (`--glow`, used only as emitted light) around the top discs, bars and cells.
- **Shape** for a second category: solid copper vs an open copper ring (active/quiet groups, fatal/injured in Harm).
- Everything else is neutral: empty cells, muted discs, other bars.

A browser scan (every element on every tab, chart and theme) found no copper-family colour except these values.

## Colour

Neutrals carry only a trace of warmth (chroma near zero) so copper is the one colour on the page. No other hue, except a
toned red for a failed data check. Light and dark are each composed, not inverted.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `--shell` | #181818 | #090908 | the ink band across the top (wordmark, tabs, scan line), both colourways |
| `--shell-ink` / `-2` | #F2F0EC / #ABA69E | #EEEBE6 / #A49E96 | text on the band |
| `--shell-copper` | #D08A52 | #D08A52 | wordmark क्ष, its rule, the open tab, the switch, "Next scan in progress" |
| `--paper` | #EEECE8 | #151413 | the ground under the work |
| `--paper-2` | #F9F8F6 | #1E1D1B | sheets, cards, the case file, inputs |
| `--paper-3` | #E0DDD8 | #2A2826 | chips, selected row, empty strip days, muted discs |
| `--well` | #E6E3DF | #272624 | heat-grid cells |
| `--ink` | #181818 | #EEEBE6 | primary text (brand ink) |
| `--ink-2` | #3D3B38 | #C5C0B9 | secondary text, values |
| `--ink-3` | #5C5853 | #969089 | meta, labels (5.2:1 or more on every surface) |
| `--rule` / `--rule-2` | ink 12% / 24% | ink 10% / 20% | hairlines / control outlines |
| `--copper` = `--copper-text` | #9C5A2B | #D08A52 | figures, marks, discs, bars, squares, focus ring; as text 4.5:1 or more on paper and sheets |
| `--glow` | copper light | copper light | only as a glow around the busiest copper marks |
| `--neg` | #A3322A | #EE8573 | a failed data check, nothing else |

Copper text never sits on a heat well; the busiest cell's number is bold ink.
**Basemap.** OpenFreeMap positron (light) / dark, fully greyed by `--tile-filter` (no sepia) so only copper carries colour.

**Browser surfaces.** `color-scheme` per theme, themed scrollbars, copper caret and accent, selection in solid copper,
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
