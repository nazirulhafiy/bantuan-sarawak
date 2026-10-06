# Design

The live site is the static pages from `scripts/build.py`, styled by `site/style.css`. This note describes that system. It does not propose a redesign.

Type is Geist, then the system sans-serif stack. The page is white, ink is near-black, and the accents are Sarawak red `#d22630`, yellow `#f7c948`, and black `#111111`. The body is at most 840px wide. The brief, category list, and cards sit on a 760px rail. Dark mode uses the same hierarchy on a near-black canvas. Cards stay 8px radius or less.

## Scheme card

The card is a full-width block inside the category list: no inner page padding, a 1px border, and the corners clipped.

The title bar is black (`#111111`) and runs the full width of the card. On it, the rank and the title share one line. Both are white, 16px, weight 700. The rank is the number in that category, then a period. The title is not uppercased and has no extra letter-spacing. Ranks restart at 1 in the next category. Below 560px width, the bar has more padding (`14px 16px`), a small gap between rank and title, top-aligned flex so wrapped titles breathe, and `line-height: 1.5` on the title (and rank) for readability.

Under the bar, the body is padded 16px on the sides and 16px on top. Amounts, when shown, are 16px. A page amount is weight 750. Each amount is a bullet (`•`), not a number.

## Source

The word Source is a yellow pill: background `#f7c948`, text `#111111`, 12px, weight 900, uppercase, padding 2px 6px. The links under it are 12px in Sarawak red ink. The pill is the card’s source label, not a second heading style.

## Due date

A due date inside scheme copy is a red label with white text: `span.due-date`. Background `#d22630`, text `#fff`, inline, padding `0 5px`. It uses the same font size, line height, and weight as the surrounding scheme copy (`ol.scheme-copy` list items, 15px), not a smaller pill. One label per date. The same date is not also shown as plain text.

## Numbered copy

Cards that set `copy_ordered` render eligibility and description as `ol.scheme-copy`: 15px, muted, with 6px between items. An `amount_note` on that card is the last item in the same list.

Cards without `copy_ordered` use ordinary 15px paragraphs in `.scheme-copy`. Bantuan Am, Bantuan Belia-Beliawanis, and Sri Pertiwi are the ones that do this.

## Category icons

Each category heading has one stroke icon, 22×22, `stroke-width: 2`, `currentColor`, `aria-hidden`. The heading text is the accessible name. The icons are not repeated in the category filter.

The shapes are distinct: a house (Household), an open book (Students), a terrace of roofs (Housing), a circle and cross (Senior Citizen), a pram (New Baby), a shopfront (Small Business), and a heart (Welfare).

Category headings are 24px, weight 700. The filter buttons are separate: 9px, uppercase, with the category name and a count. They do not use the icons.

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
