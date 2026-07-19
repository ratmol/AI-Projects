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

A few arbitrary values are deliberate: the reserved scroll height on the
results section (`calc(100vh-5rem)`, explained under the signature), the
screenshot preview caps, and the small type sizes, which belong to the type
scale rather than the spacing scale.

## Radius

One value, `--radius-instrument: 3px`, applied with intent. Controls and input
panels only. Data marks stay sharp: the screenshot preview, the trace rail and
its dots, and the panels inside the result card all have square corners.
Rounding everything by reflex is exactly what this rule exists to prevent.

## The signature: the reveal

One orchestrated sequence, everything else deliberately still. The moment this
product is remembered for is what happens after you press analyze.

The page starts as input only. There is no empty results panel and no
placeholder, because an empty box promising future content is dead weight. When
a run starts, the results panel mounts and rises in over 260ms, the page scrolls
to bring it to the top, an indeterminate bar carries the wait while the model is
still thinking, and steps appear as they actually happen. The bar stops the
instant the first token lands, and from there the answer streams in.

Four parts, one sequence, defined together in `index.css` under THE SIGNATURE:

1. `.reveal`, the results panel arriving
2. `.bar-indeterminate`, carrying the wait
3. `.step-in`, each step as it happens
4. `.pulse`, the marker on the step currently running

Two implementation notes that are easy to lose:

* The results section reserves `min-h-[calc(100vh-5rem)]`. Without it the
  browser clamps the scroll, because at the moment the run starts the page is
  not yet tall enough to bring the panel to the top.
* The scroll uses `behavior: "smooth"` only when the user has not asked for
  reduced motion, and all four animations are disabled under
  `prefers-reduced-motion`.

Do not add a second animated moment somewhere else in the UI. Extending this
sequence is fine. Competing with it is not.

## Trace, deliberately quiet

`components/Trace.tsx` reports what the agent did as a plain list on a vertical
rail, the way a CI job reports itself: a state dot, the label, the duration. It
sits below the diagnosis and is secondary on purpose. It answers "what did it
do" without competing with the answer for attention.

An earlier version drew this as a timing waterfall, positioned and sized like a
browser network panel. It was accurate and it looked impressive, but reading a
chart is work, and the answer is what people came for. Measured durations are
still shown, just as numbers rather than geometry.

## Banned

Never introduce these, even when they look fine in isolation:

* purple to blue or purple to cyan gradients, gradient text
* glassmorphism (blur plus transparency plus border) as a card style
* icon, title and blurb feature grids in threes, centered
* `01 / 02 / 03` markers unless the thing is genuinely sequential. This
  exception is currently exercised once, in `components/HowItWorks.tsx`: the
  pipeline really does run compress, read, search, fix in that order, and the
  numbers are what make the ordering readable. It is not a licence to number
  anything else.
* bounce or elastic easing, fade up on scroll on everything
* marketing voice: "seamless", "empower", "modern workflow"
* neon glow as an accent treatment
* one generic font (Inter, Roboto, system-ui) doing both headings and body

## Removed on purpose

An early pass had a boot sequence, a typewriter hero, blinking carets, glow
text shadows, CRT scanlines, an amber radial gradient and fake macOS traffic
lights. All cut. They were theatre, decoration imitating a terminal rather than
the product doing real work. The fake window chrome was replaced by a real
statusline (`components/StatusLine.tsx`) where every field reports actual
state: model, run phase, rate limit.

A later pass also removed:

* **The timing waterfall.** See the trace section above. Charts make the reader
  work, and the diagnosis should be the thing that arrives.
* **The "no run yet" placeholder.** A large empty panel sitting there before
  anything has happened is a promise the page has not earned. Results now
  simply appear.
* **The two column layout.** With no placeholder to fill, the right column was
  empty half the time. One column at `max-w-3xl` reads better for prose and
  lets the screenshot area be genuinely large.

## Checklist before shipping a UI change

1. Cover the wordmark. Is it still obviously a debugging tool? The mono type,
   the statusline and the trace should carry that on their own.
2. Did any banned pattern come back?
3. Is there still exactly one animated moment?
4. Any raw hex outside the `@theme` block, or any spacing value off the scale?
5. Remove one decoration that crept in.
