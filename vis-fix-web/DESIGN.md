# vis-fix design system

The locked visual decisions for this frontend. **Read this before changing any
UI code.** The point of writing it down is to stop the design drifting back to
defaults one small tweak at a time.

## Direction

vis-fix is a CLI debugging tool. It should feel precise, technical and
diagnostic, like a measuring instrument rather than a SaaS product. The visual
language is borrowed from terminals, oscilloscopes and log viewers.

Reference points, and what each one contributes:

| Reference | What we take | What we skip |
|---|---|---|
| Linear | Restraint. One accent used as a functional flashlight. Hairline borders. Type hierarchy carries the page. Low weight band (400 to 510), never bold by reflex. Tight negative tracking on display type. | Its lavender accent |
| Warp | The tension this product actually has: monospace data inside a readable modern shell. Prose in the display face, output in mono. | Skeuomorphic terminal cosplay |
| Railway | Dark and technical without going cold. Warmth comes from the amber accent, not from decoration. | |
| Raycast | Motion signals precision rather than delight. Fast linear easing. Positive letter spacing on small type over dark backgrounds. | |

## Tokens

All tokens live in `src/index.css` inside `@theme`. **Raw hex appears in that
block and nowhere else.** Components use the Tailwind utilities generated from
the tokens (`bg-raised`, `text-muted`, `border-line`).

### Color, 6 core plus 2 state

```
--color-surface  #0a0c0d   substrate
--color-raised   #111416   panels
--color-line     #1e2427   hairline rules
--color-text     #e6e8e7   primary type
--color-muted    #7d8a8c   secondary type
--color-signal   #ffb454   the accent, one only
```

Plus two signal state tokens. These are a data encoding rather than brand
color, because a debugging tool that cannot render pass and fail is a worse
tool:

```
--color-ok       #6fbf8a
--color-alert    #e2685c
```

The accent works like a flashlight. It marks the active measurement, the
primary action, and code literals. It is never a background wash, never a
gradient, never a glow.

### Type, a real pairing

```
--font-display  Space Grotesk Variable   headings and prose
--font-mono     JetBrains Mono Variable  data, labels, logs, code, controls
```

Never one generic font doing both jobs. Both are self hosted through
`@fontsource-variable`, so there is no CDN dependency, it works offline, and it
survives a strict CSP.

Scale contrast is deliberate and large. The h1 is 48 to 60px with `-0.028em`
tracking. Structural labels are 10px uppercase with `+0.09em` tracking, since
small type needs positive tracking to survive a dark background. There is
nothing in the middle.

### Spacing

The default 4px scale is the only scale. Permitted steps: `1 1.5 2 2.5 3 4 6 8
12 16`. Half steps (6px, 10px) are allowed only for padding inside dense
controls, because the research on Linear and Raycast puts compact control
padding at 8 to 12px and whole steps alone are too coarse there. Everything
structural uses whole steps.

Two arbitrary values are deliberate: the waterfall grid track definition, since
a data table needs explicit column widths, and the small type sizes, which
belong to the type scale rather than the spacing scale.

## Radius

One value, `--radius-instrument: 3px`, applied with intent. Controls and input
panels only. Data marks stay sharp: the waterfall bars, the screenshot preview,
example thumbnails and output panels all have square corners. Rounding
everything by reflex is exactly what this rule exists to prevent.

## The signature: the timing waterfall

`components/Waterfall.tsx`. One memorable moment, with everything else
deliberately quiet so it reads.

The agent pipeline is drawn the way a browser network panel or a logic analyser
draws one. Every step is positioned by when it started and sized by how long it
took, from real `performance.now()` measurements. The running bar breathes at
1.1s until its duration is known. Steps arrive on a 140ms linear fade, with no
bounce, no elastic and no stagger everything.

Color in the waterfall is data, not decoration:

* normal work uses `signal` at full strength
* web search uses `signal` at 45%, so external I/O reads lighter
* failure uses `alert`

This is the only animation in the product. Do not add a second one.

## Banned

Never introduce these, even when they look fine in isolation:

* purple to blue or purple to cyan gradients, gradient text
* glassmorphism (blur plus transparency plus border) as a card style
* icon, title and blurb feature grids in threes, centered
* `01 / 02 / 03` markers unless the thing is genuinely sequential
* bounce or elastic easing, fade up on scroll on everything
* marketing voice: "seamless", "empower", "modern workflow"
* neon glow as an accent treatment
* one generic font (Inter, Roboto, system-ui) doing both headings and body

## Removed on purpose

An earlier pass had a boot sequence, a typewriter hero, blinking carets, glow
text shadows, CRT scanlines, an amber radial gradient and fake macOS traffic
lights. All cut. They were theatre, decoration imitating a terminal rather than
the product doing real work. The fake window chrome was replaced by a real
statusline (`components/StatusLine.tsx`) where every field reports actual
state: model, run phase, rate limit.

## Checklist before shipping a UI change

1. Cover the wordmark. Is it still obviously a debugging tool? The waterfall
   and the mono data grid should carry that on their own.
2. Did any banned pattern come back?
3. Is there still exactly one animated moment?
4. Any raw hex outside the `@theme` block, or any spacing value off the scale?
5. Remove one decoration that crept in.
