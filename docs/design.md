# Design

The live site is the static pages from `scripts/build.py`, styled by `site/style.css`. This note describes that system. It does not propose a redesign.

Type is Geist, then ui-sans-serif, system-ui, and the system sans-serif stack. Geist is the official variable font (weights 100–900), self-hosted under the SIL Open Font License from the vercel/geist-font v1.7.2 release, with `font-display: swap`. The page is white, ink is near-black, and the accents are Sarawak red `#d22630`, yellow `#f7c948`, and black `#111111`. The body is at most 840px wide. The brief, category list, and cards sit on a 760px rail. Dark mode uses the same hierarchy on a near-black canvas. Cards stay 8px radius or less.

## Motion

Motion follows [ai.sarawak.news](https://ai.sarawak.news).

The home brief and the About hero use `hero-reveal`: a rise of 18px over 0.85s, easing `cubic-bezier(.22, 1, .36, 1)`. The lines inside the brief, and each About section, use `hero-content-reveal`: a rise of 10px over 0.7s with the same easing.

Each scheme card uses `story-reveal` once: a rise of 12px over 0.7s with the same easing. `site/app.js` adds `is-revealed` when an IntersectionObserver sees the card enter the viewport, then unobserves that card. The reveal runs once. It does not use CSS `animation-timeline: view()`.

Hover lifts a card with `translateY(-3px)` and a slight rotation (`-.25deg`, or `.25deg` on an even card).

`prefers-reduced-motion: reduce` removes transform motion and keeps the cards visible.

## Scheme card

The card is a full-width block inside the category list: no inner page padding, a 1px border, and the corners clipped.

The title bar is black (`#111111`) and runs the full width of the card. On it, the rank and the title share one line. Both are white, 16px, weight 700. The rank is the number in that category, then a period. The title is not uppercased and has no extra letter-spacing. Ranks restart at 1 in the next category. Below 560px, `.scheme-head` is a two-column grid (`auto 1fr`) so the rank stays on the first line with the title start, wrapped title lines hang under the title text (not the number), and rank/title use `line-height: 1.5`.

Under the bar, the body is padded 16px on the sides and 16px on top. Amounts, when shown, are 16px. A page amount is weight 750. Each amount is a bullet (`•`), not a number.

## Source

The word Source is a yellow pill: background `#f7c948`, text `#111111`, 12px, weight 900, uppercase, padding 2px 6px. The links under it are 12px in Sarawak red ink. The pill is the card’s source label, not a second heading style.

## Due date

A due date inside scheme copy is a red label with white text: `span.due-date`. Background `#d22630`, text `#fff`, inline, padding `0 5px`. It uses the same font size, line height, and weight as the surrounding scheme copy (`ol.scheme-copy` list items, 15px), not a smaller pill. One label per date. The same date is not also shown as plain text.

## Numbered copy

Cards that set `copy_ordered` render eligibility and description as `ol.scheme-copy`: 15px, muted, with 6px between items. An `amount_note` on that card is the last item in the same list. Below 560px, list markers sit outside the text block so wrapped lines align with the first line of copy, not under the number.

Cards without `copy_ordered` use ordinary 15px paragraphs in `.scheme-copy`. Bantuan Am, Bantuan Belia-Beliawanis, and Sri Pertiwi are the ones that do this.

## Category icons

Each category heading has one Phosphor duotone icon (MIT), inlined at build time from `assets/phosphor`. It sits on a 36px pale-yellow tile with an 8px radius and a 1px yellow border. In light mode the outline is the heading ink (`--ink`) and the duotone fill is Sarawak yellow (`#f7c948`). The icon is `aria-hidden`. The heading text is the accessible name. The icons are not repeated in the category filter.

The marks are Basket (Household), GraduationCap (Students), House (Housing), Heartbeat (Senior Citizen), Baby (New Baby), Storefront (Small Business), and HandHeart (Welfare).

In dark mode the tile is a translucent yellow (`rgba(247, 201, 72, 0.28)`) with a near-solid yellow border (`rgba(247, 201, 72, 0.95)`). The glyph stays `#f7c948`.

Category headings are 24px, weight 700. The filter buttons are separate: 9px, uppercase, with the category name and a count. They do not use the icons. When the buttons overflow, the row scrolls sideways. A fade and chevron sit in the empty gutter beside that edge, not over a label, and they hide once the row is scrolled to the edge. Trailing padding lets the last label clear the gutter. If every button fits, there is no hint.

## Type scale

- Page title: `clamp(36px, 6vw, 48px)`, weight 700.
- Deck under the title: 18px (17px below 560px).
- Body: 16px.
- Category heading: 24px (20px below 560px).
- Scheme rank and title: 16px.
- Amounts: 16px.
- Scheme copy, including `ol.scheme-copy`: 15px.
- Due-date label: same size and weight as scheme copy (15px), white on `#d22630`.
- Source pill and source links: 12px.
- “Last updated”: 10px, uppercase.
- Category filter buttons: 9px, uppercase.

## Footer

The explore column lists Home and About, then a heading that reads Categories. The Categories divider runs the full width of the footer nav panel: a `::before` on `.site-footer-categories-title` extends past the nav padding (`left`/`right: -28px` on desktop, `-18px` at max-width 560px) so the line meets the box edges. Space between About and that divider comes from `margin-bottom: 14px` on the first link list and `margin-top: 34px` on the heading.
