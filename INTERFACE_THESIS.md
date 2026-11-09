# Interface Thesis

## Visual Foundation

AIElectronicChips.com is an evidence-classified technical reference and an
industrial-intelligence asset. Its interface expresses the **Silicon Sovereignty
Stack** as a comprehensible system of engineering and industrial dependencies,
without reducing the entire subject of AI chips to sovereignty alone.

The approved visual direction is **Luminous Silicon Atlas**: a light, restrained
scientific reading environment, not a dark dashboard, promotional SaaS page,
or speculative sci-fi interface. This is a visual direction, **not** a new
brand or domain name.

The appearance must help readers understand architecture, suppliers,
constraints, uncertainty and provenance. Visual authority cannot substitute
for scientific evidence.

## Visual Language and Semantic Tokens

- **Pale silicon** `#F5F7F5` is the page substrate; **white** `#FFFFFF`
  is the primary reading surface. Secondary panels use `#EEF2EF` and
  evidence tint uses `#EAF2F2`. There is no automatic dark theme.
- **Deep slate** `#263746` carries ordinary reading text; the darker
  `#1A2935` carries headings. Secondary labels use `#4F5E6B`.
- **Technology teal** `#147881` distinguishes silicon logic, links and
  structural emphasis. Text links use the darker accessible `#0F646C`.
- **Copper** `#A56843` communicates metallization, memory and physical
  interconnects, but is **not** used for ordinary small text; accessible
  copper text uses `#8A5232`.
- The fine background die grid evokes wafer reticles. Copper routes,
  vias and eight-layer cross-sections represent actual dependency
  relationships, not invented technical measurements.
- The brand mark evokes a semiconductor die crossed by one trace.
  Source IDs use monospaced identifier chips; pending records remain
  visibly distinguishable.

Colors are explained by function and are never used alone as evidence.
Evidence classes `S` (standard announcement), `A` (attributed),
`C` (bounded analysis), and `U` (unresolved) retain their literal
labels and differentiated borders/fills, including a dashed edge for
unresolved items. The interface must not imply review completion or
verified relationships where none exist.

## Interaction Model

Eight ontology layers form the navigable reference:

1. Design
2. Fabrication
3. Packaging
4. Memory
5. Interconnect
6. Power and Thermal
7. Controls
8. Deployment

Readers should move between an overview, dependency explanation, the
exact source, confidence/limitations, and unresolved questions. A visual
diagram is an aid to comprehension, never a replacement for registered
source locators.

Source-backed reference pages, diagrams, tables, citations and the
strategic-availability form must retain their existing semantic structure,
routes, and keyboard operability. The HBM diagram and wide data tables
may scroll horizontally on mobile, but their text must not shrink until
illegible; give visible scroll cues and keyboard-focusable, labelled
scrolling regions. Navigation remains available at narrow widths.

## Typography and Reading Comfort

Use system font stacks; no remote font requirement. Headings may use
an institutional serif stack, with clear sans-serif body copy and
monospaced IDs. Long-form reading text should remain generous
(about 16–17px at ordinary browser settings), with balanced line length
and line height. Prioritize legible **mobile** labels and table headings
rather than minimizing them to fit a fixed-width panel.

Meet WCAG AA contrast for text (at least 4.5:1 for normal text), and
non-text component visibility (at least 3:1 where applicable).
Keyboard focus must remain visible. Do not suppress focus indicators
without a more visible replacement. Respect reduced-motion preferences.

## Prohibited Patterns

- decorative neon, glowing robots/brains, gaming aesthetics, or sci-fi effects;
- glassmorphism, illegible fine print, and excessive gradients or shadows;
- animated complexity without an explanatory purpose;
- arbitrary scores, synthetic indicators or maps without methodology;
- hidden source context, missing uncertainty labels, or colors that imply
  a higher evidence classification than recorded;
- dark-background defaults that compromise sustained reading;
- unverified product-qualification, supplier-substitution, or review-completion
  claims smuggled into visuals or design captions.

## Implementation and Governance

The global palette, component rules, and responsive breakpoints live in
`assets/css/main.css` and `assets/css/evidence.css`; supporting OG previews
are generated consistently with the same visual system. Retain existing
selectors and the functioning static-site architecture. No new tracking
scripts, decorative frameworks or external font dependencies are needed.

This thesis documents **presentation**. It does not approve scientific
claims, candidate Atlas relationships, trademark or acquisition strategy,
or publication of internal research files. The content/provenance gates
remain independent from visual review. Future variants should be tested
at desktop and mobile widths on all published routes before merge.
