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
- `links` — at least one official `https` source. The label is a short agency name, with no scheme suffix.

When `amount_basis` is `page` or `attachment`, `amounts` is required. When it is `none`, do not set `amounts`. A `none` card needs `copy_ordered` or `unspecified`.

`short` may be stored. The public card does not show it, and it does not show a State or Federal badge.

On the page, a card shows, in order:

1. A rank that restarts at 1 in each category, then the title, on one black bar.
2. The amount list, or the note that no ringgit figure is shown.
3. The eligibility and description. Cards with `copy_ordered` use a numbered list (`ol.scheme-copy`). An `amount_note` on those cards is the last numbered item.
4. A Source line and the official links.

## Freshness

Phases end, due dates move, and amounts go stale. The operating rule is a weekly re-check of the official page already linked on each listed scheme, then an update to that card. Do not invent a figure, a date, or an eligibility line.

The public “Last updated” line is `checked` in `data/site.json`. The figures now on the site were checked on 4 October 2026. Date-sensitive lines include the SKAS payment and acknowledgement dates, the electricity discount window, and the application windows on IGPS, BIK, BIB, and EFS.

How to do the pass, including which pages to open, is `docs/automation.md`.

## Still in development

The site is not finished. Do not hand it to a maintainer bot until Nazirul says it is complete. There is no bot and no schedule. Publishing still means a reviewed change merged to `main`.
