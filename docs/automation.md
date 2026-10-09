# CI: docs check

On every pull request (open, sync, reopen, and when labels change), the **docs check** workflow compares the PR diff to a narrow watch list of design and behaviour files: `site/*.css`, `site/*.js`, and `scripts/build.py` (the builder that generates `index.html` and `about.html`). Content under `data/`, routine markdown, and generated `dist/` are not watched.

If the PR changes any watched file and changes nothing under `docs/`, the check fails. Update `docs/design.md` or another file under `docs/` in the same PR, or add the **`no-docs-needed`** label when no documentation update is required. The label is defined in the repository; agents and contributors should use it only when the visual or behavioural change truly needs no doc sync.

# Weekly pass

There is no bot and no schedule. Do not add either until Nazirul says the site is complete. A person does this pass.

Once a week, do both of these:

a) **New schemes.** Add a state scheme only when it has its own official page. The steps are under “Add a scheme”.
b) **Current schemes.** Open the official page already linked on each scheme in `data/schemes.json` and update that card so it matches the page. If the scheme is wholly past due, remove it. If an earlier phase has passed and a later phase is current, keep the card and describe the current phase. The steps are under “Change a listed scheme” and “Retire a scheme”.

If the page and the card already match, leave the card. Do not invent a figure, a date, or an eligibility line. If the page does not state it, it does not go on the card.

## Pages to re-check

Re-open the URL stored on the card. Do not replace it with a news post, an announcement index, or a different host.

### Household

- Sumbangan Keperluan Asas Sarawak (SKAS) 2026 — https://service.sarawak.gov.my/web/web/home/sla_view/0/821/
- Domestic Electricity Discount — https://www.sarawakenergy.com/media-info/announcements-publications/extension-of-electricity-discounts-for-sarawak-energy-account-holders-until-december-2026

### Students

- Bantuan Kewangan Khas (BKK) for IPT Students, Free Laptop, and Book Voucher — https://myys.yayasansarawak.org.my/
- Inisiatif Graduan Pulang Sarawak (IGPS) and Geran Kemasukan IPT — https://yayasansarawak.org.my/en/biasiswa-2/
- Selected-Course Tuition Waiver at Four Institutions — https://meitd.sarawak.gov.my/web/subpage/webpage_view/156
- School Uniform Assistance Programme and Free School Transportation Service for Students — https://yayasansarawak.org.my/en/bantuan-pelajar-ke-ipt2/

### Housing

- HDAS Deposit Assistance — https://hdc.sarawak.gov.my/web/subpage/webpage_view/163
- SRAS Rent Assistance — https://hdc.sarawak.gov.my/web/subpage/webpage_view/139
- Rumah Spektra Permata — https://hdc.sarawak.gov.my/web/subpage/webpage_view/127
- Sri Pertiwi — https://mudenr.sarawak.gov.my/web/attachment/show/?docid=U2JnN2NtQmNWZi9DWkhaYUlUMnhsdz09OjrhxKX9m6xObBhS-XQMz_Kf

### Senior Citizen

- Senior Citizen Health Benefit (SCHB) — https://service.sarawak.gov.my/web/web/home/sla_view/0/742/
- Kenyalang Gold Card (KGC) — https://service.sarawak.gov.my/web/web/home/sla_view/211/822
- Bantuan Ihsan Kematian (BIK) — https://service.sarawak.gov.my/web/web/home/sla_view/211/847/

### New Baby

- Bantuan Ibu Bersalin (BIB) — https://service.sarawak.gov.my/web/web/home/sla_view/211/383/
- Endowment Fund Sarawak (EFS) — https://kpwk.sarawak.gov.my/web/subpage/webpage_view/100

### Small Business

- Bantuan Ketua Isi Rumah Wanita (KIRWaS) — https://jwks.sarawak.gov.my/web/subpage/webpage_view/182
- Sarawak Micro Credit Scheme (SMCS) — https://service.sarawak.gov.my/web/web/home/sla_view/259/390
- Geran Pelancaran / Modal Mikro — https://welfare.sarawak.gov.my/web/subpage/webpage_view/159

### Welfare

- Bantuan Am (BA) and Bantuan Belia-Beliawanis (BBB) — https://welfare.sarawak.gov.my/web/subpage/webpage_view/130

Read the date lines on SKAS (the 10 November 2026 payment and the acknowledgement before mid-December 2026), the electricity discount window and the 28 February 2027 bill-correction date, and the Yayasan windows that close on 30 October 2026 for BKK, Free Laptop, and Book Voucher. Also read the relative windows on IGPS, BIK, BIB, and EFS. Those are the lines that go stale first.

## Change a listed scheme

Edit the object in `data/schemes.json`.

- **Amount.** Put only what that official page states into `amounts`. If the page no longer states a ringgit figure, do not keep the old one.
- **Eligibility.** Edit `paragraphs`. That array is the eligibility and description. There is no separate eligibility field.
- **Phase, due date, deadline.** Name the current phase in `paragraphs`. Put each calendar due date in `due` as well, using the page’s date phrase, so the build can wrap that same phrase in the red label. `due` is a string, or a list when the card has more than one date. The phrase must appear once in `paragraphs` or `amount_note`. The build does not append a second copy, and it does not accept HTML in the JSON. On a `copy_ordered` card the label sits inside the numbered item that already contains the phrase. If a phase has ended and a later phase is current, describe the current phase. If the scheme is wholly past due, retire it.
- **Check date.** Set `checked` in `data/site.json` to the day you re-read the pages (`YYYY-MM-DD`). That value is the “Last updated” line. Also update the check-date sentences in `data/site.json` (`about_description` and the figures section) and the about lede in `scripts/build.py`. `tests/test_build.py` expects the same date string, including `TUESDAY, 6 OCT 2026` while the check date is 6 October 2026, so update the test in the same change.
- **New ringgit figure.** If the built page shows a ringgit amount the tests do not already allow, add the digits without commas to `ALLOWED_RM` in `tests/test_build.py`.

## Add a scheme

Add a scheme only when all of these are true:

- It is a Sarawak state scheme. The published directory is state only. Federal schemes stay in `docs/federal-assistance-backlog.md`.
- It has its own official `https` page. A news view, an announcement index, or a page that only mentions the scheme is not enough.
- Any amount you show is on that page, or on an official attachment that page points to.

Give it a new `id`, `level` set to `STATE`, and a `group` that already exists in `data/site.json`. A new group also needs a Phosphor duotone heading icon: add the SVG under `assets/phosphor` and map the group id in `scripts/build.py`. The tests expect 24 state schemes and 24 source links, one link on each scheme. Update those counts when you add or remove a scheme or a link.

## Retire a scheme

Remove the object when the official page is gone or the scheme is closed. Do not leave its title or a stale amount in site copy. Do not put `rental`, `hdras`, or `spektra-lite` back.

## Source links

Every `links` URL must be `https`, and the host must be in `OFFICIAL_HOSTS` in `scripts/build.py`. Add a host there only when it is the agency that publishes the scheme.

Each card has exactly one `links` entry. Keep the official programme page for the agency in charge. Drop an apply portal, a duplicate “how to apply” page, or a second Yayasan page. Do not leave a card with no link.

The label is the full agency name from that page. **Exception:** a card whose only URL is on `service.sarawak.gov.my` is labelled **Service Sarawak**, not the ministry or department shown on the portal. Other hosts keep the full name: Housing Development Corporation, Jabatan Kebajikan Masyarakat Sarawak, Ministry of Education, Innovation and Talent Development, Yayasan Sarawak on my-Yayasan and programme pages, and so on. Drop suffixes such as “JKMS — Geran Pelancaran”, “JWKS — KIRWaS”, “Sri Pertiwi guidelines”, and “Yayasan IPT page”. The tuition-waiver label stays the full ministry name, not “MEITD”. Link the scheme’s own page, not the agency homepage, when the scheme has one. SRAS keeps the Housing Development Corporation page only.

The build allowlist is not the whole rule. The tests also reject these fragments on the public pages, even when the host is listed: `news_view`, `announcement_view`, `faq_view`, `isarawakcare.sarawak.gov.my`, `Bantuan-IPT-ENG.pdf`, `article_view/0/380`, `webpage_view/117`, `sla_view/319/757`, `meitd.sarawak.gov.my/web/subpage/news_view`, `sarawakenergy.com/media-info/media-releases`, and a bare `https://hdc.sarawak.gov.my/` link. SKAS stays on `sla_view/0/821/`. BKK, Free Laptop, and Book Voucher stay on my-Yayasan, not the Yayasan IPT page.

Hosts the build already accepts:

- `ukas.sarawak.gov.my`
- `www.sarawak.gov.my`
- `service.sarawak.gov.my`
- `welfare.sarawak.gov.my`
- `www.jkm.gov.my`
- `myys.yayasansarawak.org.my`
- `yayasansarawak.org.my`
- `meitd.sarawak.gov.my`
- `hdc.sarawak.gov.my`
- `mudenr.sarawak.gov.my`
- `www.sarawakenergy.com`
- `apply-sras.ireka.my`
- `kpwk.sarawak.gov.my`
- `isarawakcare.sarawak.gov.my`
- `jwks.sarawak.gov.my`
- `mficord.sarawak.gov.my`
- `www.kpkm.gov.my`
- `app-egam.kpkm.gov.my`
- `talikhidmat.sarawak.gov.my`

## Amount basis

`amount_basis` is `page`, `attachment`, or `none`.

- `page` — the amount is on the official HTML page. `amounts` is required, and the card shows that list. Bantuan Am and Bantuan Belia-Beliawanis use `page`.
- `attachment` — the amount is only on a rate-sheet attachment, not the main HTML page. The card says “On an attachment” and still requires `amounts`. Do not use this when the figure is already on the page.
- `none` — there is no ringgit payment to show. Do not set `amounts`. Free Laptop, the school bus, and Kenyalang Gold Card use `none` with `copy_ordered`, and the numbered lines say what the person receives. Sri Pertiwi uses `none` without `copy_ordered`, so it needs `unspecified`. The build rejects `none` with amounts, and it rejects `none` when both `copy_ordered` and `unspecified` are missing.

## Numbered card bodies

A card with `"copy_ordered": true` renders `paragraphs` as a numbered list. If that card also has `amount_note`, the note is the last numbered item, not a separate paragraph. Keep `copy_ordered` on every card that already has it. Bantuan Am, Bantuan Belia-Beliawanis, and Sri Pertiwi use ordinary paragraphs.

## Do not publish rejected claims

`scripts/build.py` stops if the built pages contain any of these phrases: `wellbest`, `spta`, `siba`, `gptp`, `15 may`, `48 months`, `rm200 x` (and the × variants), `i-gps`. The tests refuse the same set.

Also leave out:

- Scheme ids `rental`, `hdras`, and `spektra-lite`.
- A SKAS amount list other than the three figures on the current card. That includes RM800. Also leave out “10 March”, “25 May”, “dedicated live page”, and “PWD”.
- “1 January 2026” and “JPN” on EFS. The application window on that card is within 1 year.
- “Use RM600”, “not the SKAS payment”, “state and federal”, “marked State”, “older rates”, and HDRAS in the about copy.

## Check the change

```bash
python3 scripts/build.py
python3 -m http.server 43123 --directory dist
python3 -m unittest discover -s tests -v
```

Open `http://127.0.0.1:43123/`. GitHub Pages publishes only after the change merges to `main`.
