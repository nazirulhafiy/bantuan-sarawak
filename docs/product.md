# Product

## What this site is

Bantuan Sarawak is an independent directory of Sarawak state government assistance, at [bantuan.sarawak.news](https://bantuan.sarawak.news/).

It is a list of schemes. It is not a news feed, not a government website, and not an application form. The Sarawak government does not run it. Each card links to the official page that was checked. Applications are made on that page.

The published directory lists state schemes only. Federal schemes that were removed are recorded in `docs/federal-assistance-backlog.md`. A scheme with no direct official page is left out. So is a ringgit amount that was not on the page checked.

The site is a static build. `data/schemes.json` and `data/site.json` go through `scripts/build.py` into `dist/`. GitHub Pages publishes `dist/` when changes merge to `main`.

## Who it is for

People in Sarawak who need a scheme’s amount, who it is for, the current phase or deadline, and the official page. Household, student, housing, senior, new-baby, small-business, and welfare schemes are grouped that way on the page.

No account is required. This site does not answer applications. Questions go to the office named on the official page. Talikhidmat and JKMS are listed on the About page as desks, not as a contact form for this website.

## What a scheme card must contain

Each object in `data/schemes.json` needs:

- `id` — stable slug, unique in the file.
- `group` — a category id from `data/site.json`.
- `level` — `STATE` for anything on the published directory.
- `title` — the scheme name shown on the card.
- `amount_basis` — `page`, `attachment`, or `none`. See `docs/automation.md`.
- `paragraphs` — eligibility and description. There is no separate eligibility field.
- `links` — exactly one official `https` source. The label is the full name of the agency in charge, as printed on that page. It is not the scheme name, and it is not a portal brand when the agency is known.
- `due` — optional. A date phrase from that page, or a list of them when the card has more than one. The build wraps each phrase in the red due-date label. The phrase must already appear once in `paragraphs` or `amount_note`. Do not put HTML in the JSON.

When `amount_basis` is `page` or `attachment`, `amounts` is required. When it is `none`, do not set `amounts`. A `none` card needs `copy_ordered` or `unspecified`.

`short` may be stored. The public card does not show it, and it does not show a State or Federal badge.

On the page, a card shows, in order:

1. A rank that restarts at 1 in each category, then the title, on one black bar.
2. The amount list, or the note that no ringgit figure is shown.
3. The eligibility and description. Cards with `copy_ordered` use a numbered list (`ol.scheme-copy`). An `amount_note` on those cards is the last numbered item. A due date in that copy is a red label with white text, inside the sentence or list item.
4. A Source line and the one official link.

## Freshness

Phases end, due dates move, and amounts go stale. The operating rule is a weekly re-check of the official page already linked on each listed scheme, then an update to that card. Do not invent a figure, a date, or an eligibility line.

A time-sensitive card states the current phase in the copy and puts each due date in `due`. The date has to be on that one official page. If the scheme is wholly past due, remove it. If an earlier phase has passed and a later phase is current, keep the card and describe the current phase.

The public “Last updated” line is `checked` in `data/site.json`. The figures now on the site were checked on 6 October 2026. Date-sensitive lines include the SKAS payment on 10 November 2026 and the acknowledgement before mid-December 2026, the electricity discount through December 2026 and bill corrections by 28 February 2027, and the Yayasan application windows that close on 30 October 2026 for BKK, Free Laptop, and Book Voucher. IGPS, BIK, BIB, and EFS state a relative window, not a calendar due date.

How to do the pass, including which pages to open, is `docs/automation.md`.

## Still in development

The site is not finished. Do not hand it to a maintainer bot until Nazirul says it is complete. There is no bot and no schedule. Publishing still means a reviewed change merged to `main`.
