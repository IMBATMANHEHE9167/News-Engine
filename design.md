# Design: VIDRAKSH News Engine

The locked system for `index.html`. Every change to the page reads this first. Change it on purpose; the file is the rule.
Method: Unslop (audit, direction, nine passes) and Hallmark (app-screen redesign, Floor, gates), adapted to an
information-dense intelligence workspace. Brand values come from the VIDRAKSH logo and are not negotiable.

## Direction

- **Product.** An hourly register of what Pune's press reports about crime and public order, joined into cases, for an
  analyst who needs to know what happened, where, when, and how far the record can be trusted.
- **Character.** Exact, unhurried, accountable.
- **World.** The duty officer's station diary and case register: ruled paper, black ink, a copper seal. Read for hours,
  at a desk, often at night.
- **Moments.** (1) The case record: one case's reports laid out in time, with incident day, publication times, sources
  and status kept apart. (2) The map, where precision is drawn honestly (dot, ring, disc), and the Rhythm chart.
- **Signature.** The short copper rule from under the wordmark. It marks the one thing that is current: the open tab
  and the selected record. It is never used as decoration and appears nowhere else.

## Colour

Neutrals are the logo's pure greys; copper is the logo's copper. No other hue, except a toned red for a failed check.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `--paper` | #E6E6E6 | #131313 | the desk: shell, rails, background (brand paper) |
| `--sheet` | #F2F2F2 | #191919 | the working sheet: registers, panels |
| `--raised` | #FAFAFA | #232323 | inputs, active segment, tooltip, popups |
| `--ink` | #181818 | #ECECEC | primary text (brand ink) |
| `--ink-2` | #454545 | #B8B8B8 | secondary text, values |
| `--ink-3` | #666666 | #8C8C8C | meta, labels, captions (AA on paper and sheet) |
| `--rule` | ink at 12% | ink at 11% | hairlines |
| `--copper` | #9C5A2B | #C98652 | the signature rule, focus ring, data marks |
| `--copper-text` | #8A4D22 | #D2925F | copper used as text (AA) |
| `--neg` | #A3322A | #E0786A | a failed data check, nothing else |

Copper appears on: the active tab rule, the selected record rule, the focus ring, map marks, the leading series of a
chart, one key figure, a "Rising" finding and the "Next scan in progress" state. Category names, labels, buttons and
borders are neutral.

## Type

- Interface: **Mukta** (brand face, carries Devanagari), tabular figures on every number. Headlines and findings:
  **Newsreader**, with **Tiro Devanagari Marathi** for Marathi. No third family.
- Scale (ratio ~1.15): 12/16 meta · 13/20 secondary · 14/20 body UI · 16/24 prose · 18/24 record headline (serif) ·
  22/28 section or profile title (serif) · 28/32 key figure.
- Weights 400 and 500; 600 only for the wordmark. Sentence case everywhere: no uppercase, no letter-spaced labels, no
  italic for emphasis.

## Space, shape, depth

- 4px grid: 4 8 12 16 20 24 32 40 48. Inside a group smaller than between groups.
- Radius: 4px controls, segments, tooltip; 8px panels and the map. Nothing is a pill.
- Depth from surface steps (paper → sheet → raised) and hairlines. One soft shadow, for floating things only
  (tooltip, popup, suggestions).

## Shell and layout

- Top bar (56px, sticky): wordmark, the five tabs in their fixed order (Reports, Map & patterns, Situations,
  Organised crime, Analytics), last/next scan, theme switch. Scope bar (sticky under it): Area and Period, the stamp.
- Content is capped at 1600px. Each tab uses rail + sheet: a 240px rail for that tab's own controls, the sheet for
  records. Reports adds a 400px case panel from 1200px.
- Under 1024px the bar stacks (brand row, sticky tab row, scope rows); under 760px rails become horizontal rows above
  the sheet and the case panel opens inline under its record.

## Components

- **Record row** (reports, situations, groups): a time column (publication time, tabular), then type line, serif
  headline (the publisher's link), meta fields separated by space, never by dots. Status words "Being checked" and
  "Later development" are quiet text, never colour.
- **Segmented control** (area, period, findings/graphs): text buttons; the active one is a raised surface with a
  hairline.
- **Ranked list**: label, tabular count, a 2px neutral bar.
- **Charts**: inline SVG, hairline grid, 12px labels, one copper series, the rest neutral; legends are real swatches.
- **Map**: copper marks; the legend states the three precisions with their counts.

## States and motion

- Every control has hover, `:focus-visible` (2px copper outline, instant), active/selected and disabled.
- Loading text, empty states that say what belongs there, and the existing honest notes stay.
- Motion: colour and opacity only, 140ms, `cubic-bezier(.22,1,.36,1)`. Nothing loops. Reduced motion removes
  transitions and smooth scrolling.

## Contracts the design never touches

`INCIDENTS = EVENTS.filter(e => !e.orphan && !e.uv)` is what is counted, mapped and graphed. Data field names are the
collector's contract. Element ids read by the script stay.

## Exports

The tokens live in `:root` of `index.html` (single-file page). Credits: Unslop by Damir Sokolovsky (CC BY 4.0);
Hallmark by Together AI.
