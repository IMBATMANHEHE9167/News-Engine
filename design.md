# Design: VIDRAKSH News Engine

The locked system for `index.html`. Every change to the page reads this first. Change it on purpose; the file is the rule.
Method: Unslop and Hallmark (v2, the Kiln theme adapted to VIDRAKSH), then Impeccable (Operate mode, colorize, craft
floor) and Taste Skill (colour, type and contrast rules) for the colourway refinement. Brand values come from the
VIDRAKSH logo and are not negotiable.

## Direction

- **Product.** An hourly register of what Pune's press reports about crime and public order, joined into cases, set
  beside Pune's official figures, for an analyst, a commissioner or a security expert who needs to know what happened,
  where, when, and how far the record can be trusted.
- **Mode.** Operate: a working tool. Standard controls, scannable registers, colour that does jobs.
- **Character.** Exact, physical, unhurried.
- **World.** The logo's three materials: ink, paper, copper. Copper glows where more happened.
- **Moments.** The day strip on the News tab, the news file, the full-screen maps, the official record, the findings.
- **Logo.** विद्रक्ष with क्ष in copper and a thin copper rule centred under the whole wordmark, a third of its width
  (as in the original logo file `vidraksh-live/_samples/logo.png`). Never move the rule to one side.
- **Signature.** The short copper rule. Under a record's time it marks severity: a copper rule for a fatal case, a
  copper dot when someone was injured. Never decoration.

## Copper is sacred

Copper appears only as true copper, never a paler, darker, browner, greyed or see-through shade of it: no ramps, no
opacity, no gradients, no copper tints behind rows.

- One copper, #B3641D (chosen by the user 2026-11-21 over the earlier #B86A33 / #D08A52, which read as orange and close to
  Claude's coral), for every mark, bar, disc, square, large figure, the wordmark क्ष, its rule and the open tab, in both themes.
- Small copper text is the same hue made readable (4.6:1): `--copper-text` #9F550E on paper, #C1732B on the dark ground
  (and `--shell-copper-text` #C1732B for small text on the band). Labels on copper are white, semibold.
- Glow: the copper itself as light (`--glow`), around the busiest marks only.

How much happened is shown by:

- **Size** on the maps (a solid copper disc whose radius grows with the count) and in heat grids (a copper square in a
  neutral well whose area is the count).
- **Height** in bar charts (the day strip, types over time, weapons and action, official years), every bar the same copper.
- **Light** for the busiest: a copper glow (`--glow`, used only as emitted light) around the top discs, bars and cells.
- **Shape** for a second category: solid copper vs an open ring (active/quiet groups, fatal/injured, last 30 days vs the
  30 before).
- **Copper vs neutral** for scope: on the day strip, copper days are the days the time choice covers, the rest are
  neutral; in official charts the latest year is copper, earlier years neutral.
- Everything else is neutral: empty cells, muted discs, other bars, shares solved, ranks.

A browser scan (every element on every tab, chart and theme, at 1440, 1280, 768 and 390) finds no copper-family
colour except these values. The failed-data-check red (`--neg`) is the only other hue.

## Colour

Neutrals carry only a trace of warmth (chroma near zero) so copper is the one colour on the page. Light and dark are
each composed, not inverted.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `--shell` | #181818 | #090908 | the ink band across the top (wordmark, tabs, scan line), both colourways |
| `--shell-ink` / `-2` | #F2F0EC / #ABA69E | #EEEBE6 / #A49E96 | text on the band |
| `--shell-copper` | #B3641D | #B3641D | wordmark क्ष, its rule, the open tab, the switch; `--shell-copper-text` #C1732B for "Next scan in progress" |
| `--paper` | #ECEAE6 | #151413 | the ground under the work |
| `--paper-2` | #FAF9F7 | #1E1D1B | sheets, panels, the news file, inputs |
| `--paper-3` | #DDD9D3 | #2A2826 | chips, selected row, empty strip days, muted discs |
| `--well` | #E3DFD9 | #272624 | heat-grid cells |
| `--ink` | #121212 | #EEEBE6 | primary text; the hovered day on the strip |
| `--ink-2` | #221F1C | #C5C0B9 | secondary text, values, English under Marathi |
| `--ink-3` | #47433E | #969089 | meta, labels (5.4:1 or more on every surface) |
| `--rule` / `--rule-2` | ink 14% / 30% | ink 10% / 20% | hairlines / control outlines |
| `--copper` | #B3641D | #B3641D | marks, discs, bars, squares, large figures, focus ring |
| `--copper-text` | #9F550E | #C1732B | small copper text |
| `--on-copper` | #FFFFFF | #FFFFFF | text on copper (the open tab, tags, disc counts), semibold |
| `--glow` | copper light | copper light | only as a glow around the busiest copper marks, and live marks |
| `--neg` | #A3322A | #EE8573 | a failed data check, nothing else |

Copper text never sits on a heat well; the busiest cell's number is bold ink.
**Basemap (founder's choice 2026-11-25, map-lab option C).** Our own vector style made in code from OpenFreeMap Positron
(`baseStyle()` in index.html): every colour set in the brand greys per theme (`BASE_PAL`), water a cool grey, parks and woods a
hair greener, road-number badges hidden, English labels; hill shading from Mapzen terrarium elevation tiles (AWS Open Data). No
filter on the vector map (it stays sharp); `--tile-filter` greys only the raster OpenStreetMap fallback.

**Browser surfaces.** `color-scheme` per theme, themed scrollbars, copper caret and accent, selection in solid copper,
`theme-color` = `--shell`.

## Type

- Display figures and statement headings: **Boska**. Every headline and all interface text: **Mukta** (carries
  Devanagari). Times and counts in registers: **JetBrains Mono** (data only). Marathi display: Tiro Devanagari Marathi.
- Sentence case everywhere; no tracked capitals. Nothing under 12px except numbers inside heat cells (11px).
- **English under Marathi.** Every Marathi headline on any tab carries the machine's English summary of that report
  beneath it (`--ink-2`), found by the report's link. Reports the engine has not read (some situations, older gang
  reports) have none yet.

## Space, shape, depth

- 4px grid. Radius: pills for controls (`--r-ctl`), 14px wells, 22px sheets, cards and panels.
- Depth from surface steps (paper, paper-2, paper-3) and hairlines; one soft shadow for floating things (news file,
  panels over a map, popups). In dark the shadow adds a faint 1px ring so edges hold.

## Shell and layout

- Ink band (64px, sticky): wordmark, the five tabs in their fixed order (News, Map & patterns, Live situations,
  Organised crime, Analytics), scan line, theme switch.
- Scope band (60px, sticky) on paper under it: two dropdowns at its centre, **Area** (a map pin) and **Time** (a clock),
  which decide every tab; the stamp at the right. Time is Today, Last 7 days, Last 30 days, Last 3 months, All time, or
  one day picked on the News strip.
- **News** scrolls as a page: statement and day strip, the type filter with the sources under it, the register, the
  news file.
- **Map & patterns, Live situations, Organised crime** fill the screen under the band; the page does not scroll and the
  wheel (or a pinch) zooms the map; there are no plus and minus buttons, only "Fit to area". Panels float over the map
  and scroll on their own: Map (left: where, way of mapping, filters, key, area; right: patterns, then the official
  record), Live situations (right: the list), Organised crime (left: gang links; top centre: search; right: groups).
- **Map & patterns** (from the Map 2 experiment, 2026-11-21): its panels are glass (`--glass`, `backdrop-filter`) so the
  map shows through. Counted incidents are drawn on a canvas as Points (one dot per incident, a fixed size on screen,
  coloured by six kinds of crime, `--f-*`), Hotspots (a 700 m smoothing on the `--h1`..`--h5` ramp, coloured against
  the busiest place in the whole area chosen, not just the screen) or Both. Area-only incidents sit in a small spiral at
  the area centre. Areas are not drawn: pointing shows a faint outline, name and count; selecting a point or an area
  opens it in the left panel. This is the one deliberate exception to "copper is the one colour": the kinds and the
  ramp are the map's data colours and appear nowhere else. Type is the page's own (Mukta, Boska), sentence case.
  Phones: holding a finger still on the map (230 ms, one tick) starts a scrub: running it across ticks once per incident
  passed (so a busy place buzzes), harder on entering an area (whose faint outline shows), with a tip above the finger;
  lifting opens what is under it. A quick swipe still pans; a pinch ticks every half zoom step; every control ticks.
- **One map for the three map tabs** (2026-11-21). Map & patterns, Live situations and Organised crime share one map
  (`#gmap` on `#stage`), which keeps its view as the tabs change (fitted to the area view only the first time and when the
  area changes). Each tab is a layer of glass panels over it and draws into panes of its own (`t<id>Heat`, `t<id>`,
  `t<id>Top`). Moving between them, the panels push out the way of travel and the new tab's push in (460 ms, transform
  only so the glass stays sharp; going right along the tabs, right to left), while the old tab's marks fade out and the
  new tab's fade in. Reduced motion swaps them at once.
- **Every tab on the map** (2026-11-21, after the three map tabs). News and Analytics are each one glass sheet over the same map
  (`--glass-page`, 93% solid on light and 92% on dark, about 90% less see-through than the map panels, so reading stays clear and the map is only just there),
  scrolling inside themselves, with their day headings pinned solid. All five tabs slide in tab order (News, Map & Patterns,
  Live Situations, Organised Crime, Analytics). The map runs on under the Area/Time bar, which is glass too but almost solid
  (`--scope-bg`, about 13% see-through); its height is measured (`--scope-real`) so the sheets sit just under it at every
  width. The reading note moved to the foot of the News sheet.
- **Live situations in red** (`--live`): a live situation (today or ongoing) is a small red dot that blinks on and off
  and keeps its size; a planned one is an open red ring with its date; recent ones stay small ash dots. "Live" and its
  blinking dot in the list are red too. Red here means "happening now or coming", nowhere else.
- **Gang links** is an arc diagram: the groups in a column, busiest first, with their reports; hairline arcs to the left
  join groups named together, thicker for more reports; a solid copper dot is active, an open ring quiet. Pointing at a
  group lights its arcs in copper and shows beside each partner how many reports name them together.
- Under 1024px the band stacks (brand row, tab row, scan line, scope), and a map tab's panels become one bottom sheet
  with a switch between them and Expand / Collapse.
- **Analytics** opens with a big Findings / Graphs slider at the top centre. Findings: the official record first, then
  what the news shows. Graphs: Official record, Rhythm, Trend, Change by area, Types over time, Where × what, Calendar,
  Harm, Weapons & police action. Both end with every source and its date.

## States and motion

- Every control has hover, `:focus-visible` (2px copper outline; shell copper on the band), active and disabled.
- **Day strip.** A pointer over a bar turns it ink and a flag reads the day; a click shows that day across the page;
  the arrow keys move between days. On phones a finger run across the bars ticks once per bar (Android vibrates;
  Safari 18 and later give a light tap) and lifting it shows that day. A slider under the strip moves it back to the
  first day with news.
- **News file count** runs up from zero in one second whenever the News tab is opened.
- **Live** situations blink: a copper ring and dot switch on and off (never fade), 1.1s.
- Motion otherwise: colour and opacity, 160ms, `cubic-bezier(.22,1,.36,1)`; the Analytics slider thumb slides 340ms.
  Reduced motion removes transitions, blinking and the count-up.

## Contracts the design never touches

`INCIDENTS = EVENTS.filter(e => !e.orphan && !e.uv)` is what is counted, mapped and graphed. Data field names are the
collector's contract (report `u` is the article link). Element ids read by the script, the scan line, Analytics > Data
checks and the refresh/self-reload logic stay.

**Official figures.** `data/official.json` is kept by hand: registered cases as the police and the NCRB published them,
each release with its date, what it covers and where it was read. A figure two reports disagree on is left out and the
disagreement noted. Nothing is computed from it beyond a change between two published years.
`data/officialwatch.json` is written daily by `collector/official.py` (`official.yml`): new releases spotted in the news
and the NCRB's newest Crime in India year. It never changes a figure.

## Exports

The tokens live in `:root` of `index.html` (single-file page). Credits: Unslop by Damir Sokolovsky (CC BY 4.0);
Hallmark by Together AI; Impeccable by Paul Bakaus (Apache 2.0); Taste Skill by Leonxlnx (MIT).
