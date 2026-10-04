# Federal assistance backlog

These federal schemes were removed from the published Bantuan Sarawak directory so the site lists Sarawak state assistance only. They are not generated into the site. This file is the record for adding them back later.

The figures were taken from the directory data checked on 4 October 2026. Each scheme below is the object that was stored in `data/schemes.json`, including every field. There is no separate eligibility field: eligibility and other description are the `paragraphs` array.

To restore a scheme, copy its JSON object back into `data/schemes.json`. Keep `level` as `FEDERAL` and `group` as the category id.

10 federal schemes were removed. 22 state schemes remain in `data/schemes.json`.

## Schemes removed

- PPR (`ppr`, Housing)
- Youth Agropreneur NextGen 2026 (`nextgen`, Small business)
- BUDI Agri-Komoditi (`budi`, Small business)
- Bantuan Warga Emas (BWE) (`bwe`, JKMS welfare)
- Bantuan Kanak-Kanak (BKK) (`bkk-child`, JKMS welfare)
- Elaun Pekerja Orang Kurang Upaya (EPOKU) (`epoku`, JKMS welfare)
- Bantuan Orang Kurang Upaya Tidak Berupaya Bekerja (BTB) (`btb`, JKMS welfare)
- Bantuan Penjagaan (BPT) (`bpt`, JKMS welfare)
- Bantuan Anak Pelihara (BAP) (`bap`, JKMS welfare)
- Bencana / Tabung Bantuan Segera (`bencana`, JKMS welfare)

## PPR

- **Name:** PPR
- **Id:** `ppr`
- **Category:** Housing (`housing`)
- **Level:** FEDERAL
- **Short label:** PPR
- **Amount basis:** page
- **Amounts:**
  - Rent RM100 a month
  - Ownership price RM50,400 to RM59,220
- **Amount note:** Federal programme (JPN). HDC manages completed units in Sarawak. This is not a state HDC product.
- **Eligibility and description:**
  - The HDC page states the ownership price band and the monthly rent for completed units.
- **Official sources:**
  - HDC — PPR: https://hdc.sarawak.gov.my/web/subpage/webpage_view/63

JSON object to restore:

```json
{
  "id": "ppr",
  "group": "housing",
  "level": "FEDERAL",
  "short": "PPR",
  "title": "PPR",
  "amount_basis": "page",
  "amounts": [
    "Rent RM100 a month",
    "Ownership price RM50,400 to RM59,220"
  ],
  "amount_note": "Federal programme (JPN). HDC manages completed units in Sarawak. This is not a state HDC product.",
  "paragraphs": [
    "The HDC page states the ownership price band and the monthly rent for completed units."
  ],
  "links": [
    {
      "label": "HDC — PPR",
      "url": "https://hdc.sarawak.gov.my/web/subpage/webpage_view/63"
    }
  ]
}
```

## Youth Agropreneur NextGen 2026

- **Name:** Youth Agropreneur NextGen 2026
- **Id:** `nextgen`
- **Category:** Small business (`business`)
- **Level:** FEDERAL
- **Short label:** NextGen
- **Amount basis:** page
- **Amounts:**
  - In-kind start-up support up to RM30,000
  - In-kind scale-up support up to RM50,000
- **Amount note:** Federal KPKM programme, posted on the Sarawak M-FICORD site. Not a state grant.
- **Eligibility and description:**
  - Apply through the federal portal named on the M-FICORD notice.
- **Official sources:**
  - M-FICORD notice: https://mficord.sarawak.gov.my/web/subpage/announcement_view/127
  - eGAN application portal: https://app-egam.kpkm.gov.my

JSON object to restore:

```json
{
  "id": "nextgen",
  "group": "business",
  "level": "FEDERAL",
  "short": "NextGen",
  "title": "Youth Agropreneur NextGen 2026",
  "amount_basis": "page",
  "amounts": [
    "In-kind start-up support up to RM30,000",
    "In-kind scale-up support up to RM50,000"
  ],
  "amount_note": "Federal KPKM programme, posted on the Sarawak M-FICORD site. Not a state grant.",
  "paragraphs": [
    "Apply through the federal portal named on the M-FICORD notice."
  ],
  "links": [
    {
      "label": "M-FICORD notice",
      "url": "https://mficord.sarawak.gov.my/web/subpage/announcement_view/127"
    },
    {
      "label": "eGAN application portal",
      "url": "https://app-egam.kpkm.gov.my"
    }
  ]
}
```

## BUDI Agri-Komoditi

- **Name:** BUDI Agri-Komoditi
- **Id:** `budi`
- **Category:** Small business (`business`)
- **Level:** FEDERAL
- **Short label:** BUDI
- **Amount basis:** none
- **Amounts:** none stored
- **Unspecified amount:** Federal diesel cash subsidy. The page checked does not state a ringgit amount, so none is shown.
- **Eligibility and description:**
  - KPKM subsidy for eligible farmers, livestock operators and aquaculture operators. It is separate from the state schemes on this page.
- **Official sources:**
  - KPKM — BUDI Agri-Komoditi: https://www.kpkm.gov.my/en/information/media-statement/year-2024/2024/2435-bantuan-tunai-subsidi-diesel-sektor-pertanian-di-bawah-inisiatif-budi-agri-komoditi

JSON object to restore:

```json
{
  "id": "budi",
  "group": "business",
  "level": "FEDERAL",
  "short": "BUDI",
  "title": "BUDI Agri-Komoditi",
  "amount_basis": "none",
  "unspecified": "Federal diesel cash subsidy. The page checked does not state a ringgit amount, so none is shown.",
  "paragraphs": [
    "KPKM subsidy for eligible farmers, livestock operators and aquaculture operators. It is separate from the state schemes on this page."
  ],
  "links": [
    {
      "label": "KPKM — BUDI Agri-Komoditi",
      "url": "https://www.kpkm.gov.my/en/information/media-statement/year-2024/2024/2435-bantuan-tunai-subsidi-diesel-sektor-pertanian-di-bawah-inisiatif-budi-agri-komoditi"
    }
  ]
}
```

## Bantuan Warga Emas (BWE)

- **Name:** Bantuan Warga Emas (BWE)
- **Id:** `bwe`
- **Category:** JKMS welfare (`welfare`)
- **Level:** FEDERAL
- **Short label:** BWE
- **Amount basis:** page
- **Amounts:**
  - RM600 a month
- **Amount note:** Federal JKM rate. A JKMS pamphlet still shows RM500. Use RM600.
- **Eligibility and description:**
  - Federal senior aid. You apply at a JKMS office. The amount on this card is the figure on jkm.gov.my, not the older pamphlet.
- **Official sources:**
  - JKM — monthly aid: https://www.jkm.gov.my/main/article/bantuan-bulanan
  - JKMS welfare schemes: https://welfare.sarawak.gov.my/web/subpage/webpage_view/117

JSON object to restore:

```json
{
  "id": "bwe",
  "group": "welfare",
  "level": "FEDERAL",
  "short": "BWE",
  "title": "Bantuan Warga Emas (BWE)",
  "amount_basis": "page",
  "amounts": [
    "RM600 a month"
  ],
  "amount_note": "Federal JKM rate. A JKMS pamphlet still shows RM500. Use RM600.",
  "paragraphs": [
    "Federal senior aid. You apply at a JKMS office. The amount on this card is the figure on jkm.gov.my, not the older pamphlet."
  ],
  "links": [
    {
      "label": "JKM — monthly aid",
      "url": "https://www.jkm.gov.my/main/article/bantuan-bulanan"
    },
    {
      "label": "JKMS welfare schemes",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/117"
    }
  ]
}
```

## Bantuan Kanak-Kanak (BKK)

- **Name:** Bantuan Kanak-Kanak (BKK)
- **Id:** `bkk-child`
- **Category:** JKMS welfare (`welfare`)
- **Level:** FEDERAL
- **Short label:** BKK
- **Amount basis:** page
- **Amounts:**
  - RM250 a month at age 6 and under
  - RM200 a month from age 7 to under 18
  - Maximum RM1,000 a family
- **Amount note:** Stated on the JKMS Bantuan Kanak-Kanak page. This is federal child aid, not the state IPT special assistance that also uses the initials BKK.
- **Eligibility and description:**
  - Federal aid, handled at a JKMS office.
- **Official sources:**
  - JKMS — Bantuan Kanak-Kanak: https://welfare.sarawak.gov.my/web/subpage/webpage_view/187
  - How to apply: https://welfare.sarawak.gov.my/web/subpage/webpage_view/130

JSON object to restore:

```json
{
  "id": "bkk-child",
  "group": "welfare",
  "level": "FEDERAL",
  "short": "BKK",
  "title": "Bantuan Kanak-Kanak (BKK)",
  "amount_basis": "page",
  "amounts": [
    "RM250 a month at age 6 and under",
    "RM200 a month from age 7 to under 18",
    "Maximum RM1,000 a family"
  ],
  "amount_note": "Stated on the JKMS Bantuan Kanak-Kanak page. This is federal child aid, not the state IPT special assistance that also uses the initials BKK.",
  "paragraphs": [
    "Federal aid, handled at a JKMS office."
  ],
  "links": [
    {
      "label": "JKMS — Bantuan Kanak-Kanak",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/187"
    },
    {
      "label": "How to apply",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/130"
    }
  ]
}
```

## Elaun Pekerja Orang Kurang Upaya (EPOKU)

- **Name:** Elaun Pekerja Orang Kurang Upaya (EPOKU)
- **Id:** `epoku`
- **Category:** JKMS welfare (`welfare`)
- **Level:** FEDERAL
- **Short label:** EPOKU
- **Amount basis:** page
- **Amounts:**
  - RM450 a month
- **Amount note:** The JKMS attachment and federal JKM both state RM450 a month.
- **Eligibility and description:**
  - Federal aid, handled at a JKMS office.
- **Official sources:**
  - JKM — monthly aid: https://www.jkm.gov.my/main/article/bantuan-bulanan
  - JKMS welfare schemes: https://welfare.sarawak.gov.my/web/subpage/webpage_view/117

JSON object to restore:

```json
{
  "id": "epoku",
  "group": "welfare",
  "level": "FEDERAL",
  "short": "EPOKU",
  "title": "Elaun Pekerja Orang Kurang Upaya (EPOKU)",
  "amount_basis": "page",
  "amounts": [
    "RM450 a month"
  ],
  "amount_note": "The JKMS attachment and federal JKM both state RM450 a month.",
  "paragraphs": [
    "Federal aid, handled at a JKMS office."
  ],
  "links": [
    {
      "label": "JKM — monthly aid",
      "url": "https://www.jkm.gov.my/main/article/bantuan-bulanan"
    },
    {
      "label": "JKMS welfare schemes",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/117"
    }
  ]
}
```

## Bantuan Orang Kurang Upaya Tidak Berupaya Bekerja (BTB)

- **Name:** Bantuan Orang Kurang Upaya Tidak Berupaya Bekerja (BTB)
- **Id:** `btb`
- **Category:** JKMS welfare (`welfare`)
- **Level:** FEDERAL
- **Short label:** BTB
- **Amount basis:** attachment
- **Amounts:**
  - RM300 a month
- **Amount note:** This figure is on a JKMS rate-sheet attachment.
- **Eligibility and description:**
  - Federal aid for an OKU who is unable to work. Apply at a JKMS office.
- **Official sources:**
  - JKMS welfare schemes: https://welfare.sarawak.gov.my/web/subpage/webpage_view/117
  - How to apply: https://welfare.sarawak.gov.my/web/subpage/webpage_view/130

JSON object to restore:

```json
{
  "id": "btb",
  "group": "welfare",
  "level": "FEDERAL",
  "short": "BTB",
  "title": "Bantuan Orang Kurang Upaya Tidak Berupaya Bekerja (BTB)",
  "amount_basis": "attachment",
  "amounts": [
    "RM300 a month"
  ],
  "amount_note": "This figure is on a JKMS rate-sheet attachment.",
  "paragraphs": [
    "Federal aid for an OKU who is unable to work. Apply at a JKMS office."
  ],
  "links": [
    {
      "label": "JKMS welfare schemes",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/117"
    },
    {
      "label": "How to apply",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/130"
    }
  ]
}
```

## Bantuan Penjagaan (BPT)

- **Name:** Bantuan Penjagaan (BPT)
- **Id:** `bpt`
- **Category:** JKMS welfare (`welfare`)
- **Level:** FEDERAL
- **Short label:** BPT
- **Amount basis:** attachment
- **Amounts:**
  - RM500 a month
- **Amount note:** This figure is on a JKMS rate-sheet attachment.
- **Eligibility and description:**
  - The JKMS scheme list names this in full: Bantuan Penjagaan Orang Kurang Upaya Terlantar, Pesakit Kronik Terlantar dan Pesakit Kronik Tidak Terlantar. It is federal aid, handled at a JKMS office.
- **Official sources:**
  - JKMS welfare schemes: https://welfare.sarawak.gov.my/web/subpage/webpage_view/117
  - How to apply: https://welfare.sarawak.gov.my/web/subpage/webpage_view/130

JSON object to restore:

```json
{
  "id": "bpt",
  "group": "welfare",
  "level": "FEDERAL",
  "short": "BPT",
  "title": "Bantuan Penjagaan (BPT)",
  "amount_basis": "attachment",
  "amounts": [
    "RM500 a month"
  ],
  "amount_note": "This figure is on a JKMS rate-sheet attachment.",
  "paragraphs": [
    "The JKMS scheme list names this in full: Bantuan Penjagaan Orang Kurang Upaya Terlantar, Pesakit Kronik Terlantar dan Pesakit Kronik Tidak Terlantar. It is federal aid, handled at a JKMS office."
  ],
  "links": [
    {
      "label": "JKMS welfare schemes",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/117"
    },
    {
      "label": "How to apply",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/130"
    }
  ]
}
```

## Bantuan Anak Pelihara (BAP)

- **Name:** Bantuan Anak Pelihara (BAP)
- **Id:** `bap`
- **Category:** JKMS welfare (`welfare`)
- **Level:** FEDERAL
- **Short label:** BAP
- **Amount basis:** attachment
- **Amounts:**
  - RM250 to RM500
- **Amount note:** This range is on a JKMS rate-sheet attachment.
- **Eligibility and description:**
  - Federal aid, handled at a JKMS office.
- **Official sources:**
  - JKMS welfare schemes: https://welfare.sarawak.gov.my/web/subpage/webpage_view/117
  - How to apply: https://welfare.sarawak.gov.my/web/subpage/webpage_view/130

JSON object to restore:

```json
{
  "id": "bap",
  "group": "welfare",
  "level": "FEDERAL",
  "short": "BAP",
  "title": "Bantuan Anak Pelihara (BAP)",
  "amount_basis": "attachment",
  "amounts": [
    "RM250 to RM500"
  ],
  "amount_note": "This range is on a JKMS rate-sheet attachment.",
  "paragraphs": [
    "Federal aid, handled at a JKMS office."
  ],
  "links": [
    {
      "label": "JKMS welfare schemes",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/117"
    },
    {
      "label": "How to apply",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/130"
    }
  ]
}
```

## Bencana / Tabung Bantuan Segera

- **Name:** Bencana / Tabung Bantuan Segera
- **Id:** `bencana`
- **Category:** JKMS welfare (`welfare`)
- **Level:** FEDERAL
- **Short label:** Bencana
- **Amount basis:** none
- **Amounts:** none stored
- **Unspecified amount:** A monthly amount is not stated on the official page, so none is shown.
- **Eligibility and description:**
  - Bencana is a service area, not a named monthly scheme. Tabung Bantuan Segera is a federal lump-sum channel. Apply through JKMS.
- **Official sources:**
  - JKMS welfare schemes: https://welfare.sarawak.gov.my/web/subpage/webpage_view/117
  - How to apply: https://welfare.sarawak.gov.my/web/subpage/webpage_view/130

JSON object to restore:

```json
{
  "id": "bencana",
  "group": "welfare",
  "level": "FEDERAL",
  "short": "Bencana",
  "title": "Bencana / Tabung Bantuan Segera",
  "amount_basis": "none",
  "unspecified": "A monthly amount is not stated on the official page, so none is shown.",
  "paragraphs": [
    "Bencana is a service area, not a named monthly scheme. Tabung Bantuan Segera is a federal lump-sum channel. Apply through JKMS."
  ],
  "links": [
    {
      "label": "JKMS welfare schemes",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/117"
    },
    {
      "label": "How to apply",
      "url": "https://welfare.sarawak.gov.my/web/subpage/webpage_view/130"
    }
  ]
}
```

## Directory copy that named these schemes

This copy was on the site because the schemes above were published. It was removed or rewritten with the schemes. The wording below is the text that was stored.

### Site description

> An independent directory of Sarawak state and federal assistance. Amounts come from official pages checked on 4 October 2026, and each scheme links to its source.

### Home introduction

> A directory of state and federal help for people in Sarawak. Amounts on this page were on an official page when the list was checked on 4 October 2026. This site does not take applications.

### About lede

> An independent list of state and federal assistance, with official links only. Amounts were checked on 4 October 2026.

### Housing group introduction

The PPR sentences were removed. The HDRAS sentence stayed.

> State schemes are published by the Housing Development Corporation and UKAS. PPR is federal. HDC manages completed PPR units. The HDRAS monthly repayment is not stated on the official HDC page, so no repayment figure is shown.

### Small business group introduction

> State enterprise schemes are listed first. Youth Agropreneur NextGen and BUDI Agri-Komoditi are federal programmes posted for Sarawak applicants. They are marked Federal.

### JKMS welfare group introduction

> Jabatan Kebajikan Masyarakat Sarawak handles state aid and federal aid at district offices. Bantuan Am and Bantuan Belia-Beliawanis are state. Bantuan Warga Emas, Bantuan Kanak-Kanak, EPOKU, BTB, BPT and Bantuan Anak Pelihara are federal. The JKMS page, updated 9 September 2026, lists a state-aid poverty line (PGK) of RM1,198 a month and a federal-aid PGK of RM1,236 a month. Apply at the nearest Pejabat Kebajikan Masyarakat with form JKMS/1/2010 (Pindaan 1/2024). The stated process time is 30 days. Phone 082-374888. Email welfare@sarawak.gov.my.

### JKMS welfare group links removed

These links were on the welfare group, not on a single scheme card. The same URLs are also stored on the scheme records above.

- Bantuan Kanak-Kanak: https://welfare.sarawak.gov.my/web/subpage/webpage_view/187
- Federal JKM monthly aid: https://www.jkm.gov.my/main/article/bantuan-bulanan

### About, where the figures come from

> The Bantuan Warga Emas figure used here is the federal JKM rate of RM600 a month. An older JKMS pamphlet still shows RM500.

### About, State and federal

Section id: `labels`. Title: State and federal.

> Every scheme is marked State or Federal. State schemes are Sarawak government programmes. Federal schemes are national programmes, including some that you apply for at a Sarawak JKMS office.
>
> PPR, Youth Agropreneur NextGen and BUDI Agri-Komoditi are federal. So are Bantuan Warga Emas, Bantuan Kanak-Kanak, EPOKU, BTB, BPT, Bantuan Anak Pelihara, and Tabung Bantuan Segera. Bantuan Am and Bantuan Belia-Beliawanis are state.
