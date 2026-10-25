# Design

The live site is the static pages from `scripts/build.py`, styled by `site/style.css`. This note describes that system. It does not propose a redesign.

Type is Geist, then ui-sans-serif, system-ui, and the system sans-serif stack. Geist is the official variable font (weights 100–900), self-hosted under the SIL Open Font License from the vercel/geist-font v1.7.2 release, with `font-display: swap`. The page is white, ink is near-black, and the accents are Sarawak red `#d22630`, yellow `#f7c948`, and black `#111111`. The body is at most 840px wide. The brief, category list, and cards sit on a 760px rail. Dark mode uses the same hierarchy on a near-black canvas. Cards stay 8px radius or less.

Custom properties come from `site/style.css`. `python3 kit/generate_docs.py` writes the table from the first `:root` and `html[data-theme="dark"]` rules.

<!-- BEGIN GENERATED: design-tokens -->
| Token | `:root` | `html[data-theme="dark"]` |
| --- | --- | --- |
| `--canvas` | #ffffff | #0f1115 |
| `--page` | #ffffff | #0f1115 |
| `--card` | #ffffff | #171b22 |
| `--ink` | #111827 | #f3f5f7 |
| `--muted` | #6b7280 | #aeb6c2 |
| `--line` | #e2e4e9 | #2c333d |
| `--sarawak-red` | #d22630 | #f15b61 |
| `--sarawak-red-ink` | #9f1d26 | #ff8d92 |
| `--sarawak-yellow` | #f7c948 | #f7c948 |
| `--sarawak-yellow-soft` | #fffbea | #3a3110 |
| `--sarawak-black` | #111111 | #111111 |
| `--group-icon-tile` | #fff6d2 | rgba(247, 201, 72, 0.12) |
| `--group-icon-border` | #f7c948 | rgba(247, 201, 72, 0.55) |
| `--page-gutter` | 20px |  |
| `--card-head` |  | #222833 |
<!-- END GENERATED: design-tokens -->

## Masthead

The top bar (`.bar`) scrolls with the page (`position: relative`). Its background is the page colour and runs edge to edge. At rest there is no full-bleed gray hairline under the bar; only the Sarawak tri-colour segments mark the bottom edge. The wordmark, Home and About, the theme control, and the menu sit in an inner rail (`.bar-inner`, at most 760px) lined up with the brief and the cards.

The home link (`.brand`) starts with Design Bot’s origami line hornbill (hub `#snnav` / `#snnav2`), then the site `title` from `data/site.json`, with a small gap. Markup comes from `kit.python.shell.render_header`. Sources are `kit/assets/icons/nav-mark-transparent.svg` (light) and `kit/assets/icons/nav-mark-transparent-dark.svg` (dark; transparent, no `#111` square), mirrored under `site/icons/` and published to `dist/icons/`. Images use `alt=""` and `aria-hidden`; the text labels the link. Mark height matches the wordmark line (`1.15em`). The brand stays on one line (`white-space: nowrap`) down to 375px. SVGs are used as supplied — no recolouring.

On viewports wider than 560px the Sarawak rule stays on that rail. Red sits under the wordmark. Yellow and black split the rest of the rail equally. From 560px down the rule runs from the left edge of the screen to the right, including behind the theme control and the menu. The red segment shifts left by the bar’s side padding (`--page-gutter`: 20px, or 15px from 560px down). The yellow and black segment runs past those controls to the right edge. The bar background stays full-bleed at every width. `html` uses `overflow-x: clip` so the full-bleed bar does not add a horizontal scrollbar.

## Home brief

Site wording is owned by `data/site.json` (`title`, `tagline`, `description`, `about_lead`). The build fills every surface from that file; do not hand-type those strings in `scripts/`, `tests/`, `docs/`, or `README.md`, except inside a generated block. `tests/test_site_copy.py` fails if they appear elsewhere. `python3 kit/generate_docs.py` writes the table from `data/site.json`.

<!-- BEGIN GENERATED: site-copy -->
| Field | Value |
| --- | --- |
| `title` | Bantuan.Sarawak.News |
| `tagline` | Sarawak government assistance, in one directory. |
| `description` | Each scheme links to its source. |
<!-- END GENERATED: site-copy -->

- `title` → header and footer brand, `og:site_name`
- `tagline` → home `<h1>`
- `description` → `p.brief-deck` and home meta / og / twitter descriptions
- `about_lead` → About lede (`.about-lede`)
- Home `<title>` / `og:title` / `twitter:title` use `og_title`; About page titles use `about_seo_title` and `about_description`

The home hero is the centred `.brief` block. The “Last updated” line follows the deck.

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
- Home subtitle (`p.brief-deck`): 18px (17px below 560px). Live copy comes from `description` in `data/site.json`.
- Body: 16px.
- Category heading: 24px (20px below 560px).
- Scheme rank and title: 16px.
- Amounts: 16px.
- Scheme copy, including `ol.scheme-copy`: 15px.
- Due-date label: same size and weight as scheme copy (15px), white on `#d22630`.
- Source pill and source links: 12px.
- “Last updated”: 10px, uppercase.
- Category filter buttons: 9px, uppercase.

## Shared kit

Fleet chrome (header, Contact footer link, back-to-top, analytics loader, nav marks) is vendored from [sarawak-news-hub](https://github.com/nazirulhafiy/sarawak-news-hub) `kit/` at the commit in `kit/PIN`. Do not hand-edit files under `kit/`; bump the PIN and re-sync. Local / CI: `python3 kit/sync.py --check --hub-path "$SN_HUB_PATH"`. After sync, `python3 kit/generate_docs.py --check` fails when a generated block drifts from sources. Layout and commands: `kit/README.md`.

## Hosting

<!-- BEGIN GENERATED: hosting -->
| Field | Value |
| --- | --- |
| `hostname` | `bantuan.sarawak.news` |
| `target` | GitHub Pages |
<!-- END GENERATED: hosting -->

`.github/workflows/build.yml` runs the tests, builds `dist/`, checks generated docs, and deploys that folder with GitHub Pages on push to `main`. `dist/CNAME` matches the hostname above.

## Analytics

[Bantuan Sarawak](https://bantuan.sarawak.news) uses one build-time analytics loader. It does not change what visitors see on the page.

**Registry.** `data/analytics.json` is the typed fleet registry. Validation lives in `kit/python/analytics_registry.py` (re-exported from `scripts/analytics_registry.py`). The build reads it; do not hard-code a second copy of IDs or cookie names in templates. `python3 kit/generate_docs.py` writes the table from the registry.

<!-- BEGIN GENERATED: analytics -->
| Field | Value |
| --- | --- |
| `ga4_measurement_id` | `G-PYSEQGMJLC` |
| `cf_beacon_token` | `bfba3801f65a489185b168a7446c7a62` |
| `internal_cookie` | `sn_internal` |
| `hosts` | `bantuan.sarawak.news`, `www.bantuan.sarawak.news` |
<!-- END GENERATED: analytics -->

**Single loader.** `kit.python.analytics_loader.render_analytics_loader()` (called from `scripts/build.py`) emits one inline `<script data-sn-analytics-loader>` in `<head>` on every built page. That script loads GA4 `gtag.js` and injects the Cloudflare beacon — **only** when `location.hostname` is `bantuan.sarawak.news` or `www.bantuan.sarawak.news`. It does not load on `*.pages.dev`, `*.github.io`, `*.vercel.app`, `localhost`, or any other host.

**Internal traffic.** `?internal=1` sets a first-party cookie `sn_internal=1` (~1 year, `Path=/`, `SameSite=Lax`; `Secure` on https). `?internal=0` clears the primary cookie and every listed legacy name. While `sn_internal` **or** the legacy cookie `ga_internal` is set (devices already marked before the rename), GA4 config includes `traffic_type: 'internal'`, and the Cloudflare Web Analytics beacon is **not** loaded. Agents and automation that open the live site must use `?internal=1` (see `AGENTS.md`, `tools/shots.config.json`).

**Cloudflare Web Analytics.** Privacy-friendly, cookie-less traffic measurement. Do not reuse tokens from ai.sarawak.news or other sites. Fleet `spa` is `false` (static pages).

The beacon URL is `https://static.cloudflareinsights.com/beacon.min.js` with `data-cf-beacon` JSON `{"token":"…","spa":false}`. CI runs `scripts/check_analytics_dist.py` so each built HTML page has exactly one loader, IDs/tokens match the registry, and cookie/`spa` values cannot drift. This repository does not ship a Content-Security-Policy meta tag; if one is added later, allow `www.googletagmanager.com` and `*.google-analytics.com` for GA4, and `static.cloudflareinsights.com` (script) and `cloudflareinsights.com` (connect) for Cloudflare when analytics is enabled.

## Social image

`site/social-card.png` is a 1200×630 PNG. The build copies it to `dist/social-card.png`. Home and About point `og:image` and `twitter:image` at `https://bantuan.sarawak.news/social-card.png` plus a content hash query string from `versioned_href` in `kit/python/asset_urls.py` (first 12 hex characters of the SHA-256 of that file). Replacing the file changes the query string. `tests/test_asset_urls.py` fails if `scripts/`, `kit/`, `docs/`, `README.md`, `AGENTS.md`, or site HTML, JS, CSS, or SVG contain a hand-typed asset query stamp outside a generated block. The provisional favicon remains the inline emoji data URI in `scripts/build.py`.

## Back to top

Markup comes from `kit.python.shell.render_back_to_top`. CSS and JS are owned by `kit/css/back-to-top.css` and `kit/js/back-to-top.js`, mirrored into `site/style.css` / `site/app.js` between `/* sn-kit:back-to-top:begin|end */` markers. The control is a `<button type="button" class="back-to-top" aria-label="Back to top">` with a “Back to top” label and an `↑` arrow (`aria-hidden`). It is fixed to the bottom-right corner of the screen (`z-index: 5`) so it does not cover the theme control when visible. The paint is hardcoded on the control. It does not use the page colour tokens.

Above 560px it is a pill: padding 8px 12px, gap 3.08px, 11px Geist, weight 850, line-height 1.3, letter-spacing normal, radius 999px. It sits 24px from the right edge and 24px from the bottom edge. On a wide viewport that inset lands in the margin beside the centred column, clear of the cards. From 560px down the label is hidden and the control is a 44×44px circle (`border-radius: 50%`), 18px arrow, gap 5.04px, padding 0. The phone inset is `max(14px, env(safe-area-inset-right, 0px) + 14px)` on the right and the same with `safe-area-inset-bottom` on the bottom.

The fill is `#111` in both themes. The label and the arrow are `#f7c948` in both themes. Light mode uses a 1px `#111` border. Dark mode (`html[data-theme="dark"]`) uses a 1px `#f7c948` border. Hover keeps those colours. The type is the Geist already on the page (variable, weights 100–900, so 850 is included), named again on the button so the pill does not inherit another family.

Kit JS shows it when `scrollY` is at least 600 and hides it when `scrollY` is under 600. The shown state is `.back-to-top:not([hidden])`: opacity 1, visible, and no translate. Hidden, it sits at opacity 0, `visibility: hidden`, and `translateY(6px)`. The change is a 0.18s ease on opacity, transform, and visibility. `prefers-reduced-motion: reduce` drops that fade, and the scroll to the top is instant. The markup starts with the `hidden` attribute. `visibility: hidden` and `hidden` keep it out of the tab order. Focus, when it is shown, is a 3px `#f7c948` ring with a 2px offset. Activating it scrolls to the top (`smooth`, or `auto` when reduced motion is on). Home and About both include the control; short pages never scroll far enough to reveal it.

## Footer

Footer markup comes from kit `render_footer(..., layout="column_stacks", fleet_site="bantuan", fleet_section_label="Hub")` with scheme-group **Categories** passed as `extra_nav_right` inner HTML from `scripts/build.py` (same pattern as Events). Layout uses independent column stacks: left stack is brand note plus **Hub** fleet nav (`site-footer-grid-fleet` with a column-local top rule); right stack is **Explore** (Home, About, Contact `mailto:contact@sarawak.news`), a full-width `<hr class="site-footer-grid-explore-divider">`, then Categories (`.site-footer-categories.site-footer-grid-categories`). Cross-links are plain `https://` anchors with no `rel="nofollow"`; fleet labels come from `kit/fleet-cross-links.json` and omit self, so Bantuan shows short **Sarawak** / **AI** / **Events**. Stack geometry and dividers are owned by the mirrored kit region `/* sn-kit:footer-column-stacks:begin|end */` in `site/style.css` (spacing tokens `--sn-footer-*`); Bantuan keeps shared typography, link hover, and credit styles outside that region. On desktop, the vertical rule between stacks is a full-height 1px grid track painted by `.site-footer-main--column-stacks::before` (not a `border-left` on the right stack), with both stacks stretched to the taller column; the Hub fleet block uses kit bottom inset padding on its top-bordered section. Mobile order: brand → Hub → Explore → Categories (kit rules); the desktop `<hr>` is hidden on small screens and Categories get a top border instead.
