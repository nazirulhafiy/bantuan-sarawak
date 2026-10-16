# Design

The live site is the static pages from `scripts/build.py`, styled by `site/style.css`. This note describes that system. It does not propose a redesign.

Type is Geist, then ui-sans-serif, system-ui, and the system sans-serif stack. Geist is the official variable font (weights 100–900), self-hosted under the SIL Open Font License from the vercel/geist-font v1.7.2 release, with `font-display: swap`. The page is white, ink is near-black, and the accents are Sarawak red `#d22630`, yellow `#f7c948`, and black `#111111`. The body is at most 840px wide. The brief, category list, and cards sit on a 760px rail. Dark mode uses the same hierarchy on a near-black canvas. Cards stay 8px radius or less.

## Masthead

The top bar (`.bar`) sticks to the viewport. Its background is the page colour and runs edge to edge, so the list scrolls underneath it. The wordmark, Home and About, the theme control, and the menu sit in an inner rail (`.bar-inner`, at most 760px) lined up with the brief and the cards.

On viewports wider than 560px the Sarawak rule stays on that rail. Red sits under the wordmark. Yellow and black split the rest of the rail equally. From 560px down the rule runs from the left edge of the screen to the right, including behind the theme control and the menu. The red segment shifts left by the bar’s side padding (`--page-gutter`: 20px, or 15px from 560px down). The yellow and black segment runs past those controls to the right edge. The bar background and the scrolled shadow stay full-bleed at every width.

After any scroll, `site/app.js` adds `.is-scrolled` on the bar. That draws a thin bottom edge and a soft shadow. `html` uses `overflow-x: clip` so the full-bleed bar does not add a horizontal scrollbar, and `scroll-padding-top` (72px, 76px from 560px down) so in-page links clear the bar.

## Home brief

The home hero is the centred `.brief` block. The visible subtitle is `p.brief-deck`, built from `introduction` in `data/site.json`:

- Sarawak aid and schemes, in one place.

The headline above it is the `title` field in the same file (`h1` in the brief). The “Last updated” line follows the deck.

## Motion

Motion follows [ai.sarawak.news](https://ai.sarawak.news).

The home brief and the About hero use `hero-reveal`: a rise of 18px over 0.85s, easing `cubic-bezier(.22, 1, .36, 1)`. The About hero is the title and lede only; there is no eyebrow line above the heading. The lines inside the brief, and each About section, use `hero-content-reveal`: a rise of 10px over 0.7s with the same easing. The brief network is not part of that content reveal.

Each scheme card uses `story-reveal` once: a rise of 12px over 0.7s with the same easing. `site/app.js` adds `is-revealed` when an IntersectionObserver sees the card enter the viewport, then unobserves that card. The reveal runs once. It does not use CSS `animation-timeline: view()`.

On pointer devices (`@media (hover: hover)`), hovering a scheme card (`.scheme`) adds a subtle lift and shadow from `site/style.css`. The border lightens (`#cbd1da` in light mode, `#4b5663` in dark). A soft shadow appears (`0 8px 20px rgb(17 24 39 / 8%)` light, `0 8px 20px rgb(0 0 0 / 28%)` dark). The card moves up 3px with a slight rotation (`translateY(-3px) rotate(-.25deg)`, or `rotate(.25deg)` on an even sibling). Transitions run on transform, box-shadow, border-color, and background-color (about 0.18–0.22s ease). Touch-only viewports skip this hover block.

`prefers-reduced-motion: reduce` removes transform motion and keeps the cards visible. The back-to-top control appears and hides with no fade, and its scroll to the top is instant.

## Hero network

The home brief has one still drawing, `svg.brief-net`, in the top-right. It follows the hero network on [ai.sarawak.news](https://ai.sarawak.news): an inlined SVG, absolutely placed, faded with a left-to-right mask, and clipped by the brief. It is decorative. It is `aria-hidden`, it does not take clicks, and it has no animation of its own. It adds no words.

The nodes are the seven category tiles: the same Phosphor duotone marks as the section headings, on a pale-yellow tile with an 8px radius. Thin lines join them. The drawing fades out before the headline and runs off the right edge. On a phone the same drawing is smaller and stays in the upper right.

In light mode the lines use `#4b5563` at `opacity: 0.3`, with a left-to-right mask so the drawing fades before the headline.

In dark mode the whole graphic is quieter so the headline stays the focus. The lines use `color: rgba(247, 201, 72, 0.2)` at `opacity: 0.62`. Network tiles use `fill: rgba(247, 201, 72, 0.08)` and `stroke: rgba(247, 201, 72, 0.26)`. Icon strokes use `rgba(247, 201, 72, 0.3)`. The duotone fill inside each node uses `opacity: 0.26` on `.brief-net-fill`.

## Scheme card

The card is a full-width block inside the category list: no inner page padding, a 1px border, and the corners clipped.

The title bar runs the full width of the card. In light mode it stays black (`#111111`) via `background: var(--sarawak-black)` on `.scheme-head`. In dark mode only, the theme token `--card-head` (`#222833` on `html[data-theme="dark"]`) sets the bar fill through `html[data-theme="dark"] .scheme-head { background: var(--card-head); border-bottom: 1px solid var(--line); }`. Light mode does not define `--card-head` and keeps no bottom border on the bar. On the bar, the rank and the title share one line. Both are white, 16px, weight 700. The rank is the number in that category, then a period. The title is not uppercased and has no extra letter-spacing. Ranks restart at 1 in the next category. Below 560px, `.scheme-head` is a two-column grid (`auto 1fr`) so the rank stays on the first line with the title start, wrapped title lines hang under the title text (not the number), and rank/title use `line-height: 1.5`.

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

In dark mode the tile and border come from the theme tokens on `html[data-theme="dark"]`: `--group-icon-tile` is `rgba(247, 201, 72, 0.12)` and `--group-icon-border` is `rgba(247, 201, 72, 0.55)`. The tile text colour is Sarawak yellow. The duotone fill (`.group-icon-fill`) uses `opacity: 0.28`.

Category headings are 24px, weight 700. The filter buttons are separate: 9px, uppercase, with the category name and a count. They do not use the icons. The active chip is black fill with white text; the count on an active chip is Sarawak yellow. In dark mode, `html[data-theme="dark"] .category-filter-button.is-active` keeps the black fill but uses `border-color: var(--sarawak-yellow)` so the selected chip (for example All) shows a Sarawak-yellow outline.

When the buttons overflow, the row scrolls sideways with a 48px fade (`--category-fade`) on the edge that still has hidden chips. `site/app.js` toggles `can-scroll-start` and `can-scroll-end` on the scroll wrapper so a chevron and page-coloured gradient appear on the start edge, the end edge, or both. The hints are `pointer-events: none`. They hide on an edge once the row is scrolled flush there. Trailing inline padding matches the fade width so the last label can scroll clear of the end hint. If every button fits, neither hint appears.

## Type scale

- Page title: `clamp(36px, 6vw, 48px)`, weight 700.
- Home subtitle (`p.brief-deck`): 18px (17px below 560px). Live copy: “Sarawak aid and schemes, in one place.”
- Body: 16px.
- Category heading: 24px (20px below 560px).
- Scheme rank and title: 16px.
- Amounts: 16px.
- Scheme copy, including `ol.scheme-copy`: 15px.
- Due-date label: same size and weight as scheme copy (15px), white on `#d22630`.
- Source pill and source links: 12px.
- “Last updated”: 10px, uppercase.
- Category filter buttons: 9px, uppercase.

## Analytics

[Bantuan Sarawak](https://bantuan.sarawak.news) uses two build-time tags. Neither changes what visitors see on the page.

**Google Analytics 4.** Measurement ID `G-7R9G7T5N9P`. `render_ga_script()` in `scripts/build.py` emits the async `gtag.js` loader and config in `<head>` on every built page.

**Cloudflare Web Analytics.** Privacy-friendly, cookie-less traffic measurement. When a site token is configured, `render_analytics_script()` adds a deferred `beacon.min.js` script before `</body>` on the home and About pages.

The Cloudflare token lives in `CLOUDFLARE_WEB_ANALYTICS_TOKEN` in `scripts/build.py` (set for `bantuan.sarawak.news`), or in the `CLOUDFLARE_WEB_ANALYTICS_TOKEN` environment variable at build time (env overrides the constant). An empty token omits the beacon entirely. Do not reuse tokens from ai.sarawak.news or other sites.

The beacon matches the sister site pattern: `https://static.cloudflareinsights.com/beacon.min.js` with `defer` and `data-cf-beacon` JSON `{"token":"…","spa":true}`. This repository does not ship a Content-Security-Policy meta tag; if one is added later, allow `www.googletagmanager.com` and `*.google-analytics.com` for GA4, and `static.cloudflareinsights.com` (script) and `cloudflareinsights.com` (connect) for Cloudflare when analytics is enabled.

## Back to top

The home page has one control, `<button type="button" class="back-to-top" aria-label="Back to top">`. The visible words are “Back to top” plus an up arrow (`↑`, `aria-hidden`). It is fixed to the bottom-right corner of the screen, under the sticky masthead (`z-index: 5` against the bar’s `40`), so it does not cover the bar or the theme control. The paint is hardcoded on the control. It does not use the page colour tokens.

Above 560px it is a pill: padding 8px 12px, gap 3.08px, 11px Geist, weight 850, line-height 1.3, letter-spacing normal, radius 999px. It sits 24px from the right edge and 24px from the bottom edge. On a wide viewport that inset lands in the margin beside the centred column, clear of the cards. From 560px down the label is hidden and the control is a 44×44px circle (`border-radius: 50%`), 18px arrow, gap 5.04px, padding 0. The phone inset is `max(14px, env(safe-area-inset-right, 0px) + 14px)` on the right and the same with `safe-area-inset-bottom` on the bottom.

The fill is `#111` in both themes. The label and the arrow are `#f7c948` in both themes. Light mode uses a 1px `#111` border. Dark mode (`html[data-theme="dark"]`) uses a 1px `#f7c948` border. Hover keeps those colours. The type is the Geist already on the page (variable, weights 100–900, so 850 is included), named again on the button so the pill does not inherit another family.

`site/app.js` shows it when `scrollY` is at least 600 and hides it when `scrollY` is under 600. The shown state is `.back-to-top:not([hidden])`: opacity 1, visible, and no translate. Hidden, it sits at opacity 0, `visibility: hidden`, and `translateY(6px)`. The change is a 0.18s ease on opacity, transform, and visibility. `prefers-reduced-motion: reduce` drops that fade, and the scroll to the top is instant. The markup starts with the `hidden` attribute. Until the fade-in finishes, and again from the start of the fade-out, it is `inert` with `tabindex="-1"`. The `hidden` attribute returns once the fade-out ends. `visibility: hidden` and `hidden` keep it out of the tab order. Focus, when it is shown, is a 3px `#f7c948` ring with a 2px offset. Activating it scrolls to the top (`smooth`, or `auto` when reduced motion is on).

## Footer

The explore column lists Home and About, then a heading that reads Categories. The Categories divider runs the full width of the footer nav panel: a `::before` on `.site-footer-categories-title` extends past the nav padding (`left`/`right: -28px` on desktop, `-18px` at max-width 560px) so the line meets the box edges. Space between About and that divider comes from `margin-bottom: 14px` on the first link list and `margin-top: 34px` on the heading.
