# China's fiscal data provision to the IMF — line-by-line verification

*Prepared 2026-10-19. Checks China's fiscal data against the IMF's formal requirements as they stand today, using IMF primary sources plus publication lags measured from this repository's own archive.*

---

## 0. How to read this, and the one distinction that governs everything

Three different things get called "IMF data requirements." They have different legal force, different tests, and China sits in a different place on each. Conflating them is the most common error in this kind of check.

| Regime | What it is | Enforceable? | Where the test lives |
|---|---|---|---|
| **A. Provision to the Fund** | Article VIII, Section 5 + Decision 13183-(04/10) Annex A | **Yes** — censure → ineligibility → suspension of voting rights → compulsory withdrawal | Left four columns of CR 26/44 Annex VII Table 3 |
| **B. Publication via SDDS** | Voluntary subscription China joined 2015-10-07 | No — but observance is published annually | Right four columns of the same table, plus the DSBB |
| **C. Adequacy for surveillance** | Staff judgment in the Article IV report | **No** — not an obligation at all | Annex VII Table 1 Data Adequacy Assessment |

**The headline finding.** China is broadly compliant in regimes A and B. Almost every substantive criticism the Fund makes of Chinese fiscal data — the LGFV perimeter, the missing current/capital expenditure split, the legal rather than economic definition of hidden debt — lives in regime C, where **there is no requirement to breach**. A check that reports those as non-compliance is wrong. The one place the criticism is becoming an obligation is the 2024 Review's new Annex A item 13, covered in §1.2.

A second trap: SDDS flexibility options legitimately move the goalposts, and the Article IV table does **not** reflect them (CR 26/44 Annex VII Table 3, footnote 7). The general-government row shows "2Q" expected against "NLT 7M" for China. That gap is **compliant**, not a breach, because the option is declared and justified.

**Sources.** Requirements are from the IMF Articles of Agreement; Decision No. 13183-(04/10) as amended through No. 17692-(24/33); the *SDDS Guide for Subscribers and Users* (2013); the IMF Dissemination Standards Bulletin Board (`dsbb.imf.org`, including its JSON API); China's SDDS Annual Observance Report 2025; and IMF Country Report No. 26/44 (China 2025 Article IV, staff report completed 2026-01-28, Board 2026-02-13). Lag measurements are my own, computed from the release archive in this repository. Every line states which.

---

## 1. Regime A — Provision to the Fund (legally binding)

### 1.1 The treaty itself contains no fiscal item

| # | Requirement | Verified position | Verdict |
|---|---|---|---|
| A-1 | Article VIII §5(a) enumerates twelve categories a member must furnish | The list runs (i)–(xii) and contains **no government-finance item**. No revenue, no expenditure, no balance, no public debt. "National income" is item (viii). | **Not applicable** — the fiscal obligation is not in the treaty |
| A-2 | Article VIII §5(b): furnish "in as detailed and accurate a manner as is practicable and, so far as possible, to avoid mere estimates"; the Fund shall consider members' "varying ability" | Governs all provision. Decision 13183 ¶3: obligation is "to the best of its ability," and "the Fund will give the member the benefit of any doubt." | Standard of conduct, not a line item |

The IMF acknowledged the gap itself: PIN 04/10 states that the Article VIII §5 list "excluded some key categories of fiscal and monetary information." That is why the real obligation sits in the 2004 Decision.

### 1.2 Decision 13183-(04/10) Annex A — the actual fiscal obligation

**Item 4 (the long-standing one), verbatim:** *"revenue, expenditure, balance and composition of financing (i.e., foreign financing and domestic bank and nonbank financing) for the general and central governments respectively; the stocks of central government and central government-guaranteed debt, including currency and maturity composition and, if the debt data are amenable to classification on the basis of the residency or nonresidency of the holder, the extent to which the debt is held by residents or nonresidents."*

Footnote 2 defines the perimeter: *"The general government consists of the central government (budgetary funds, extrabudgetary funds, and social security funds) and state and local governments."* CR 26/44 Annex VII Table 3 footnote 4 reproduces this word for word, so the obligation and the surveillance table use an identical perimeter.

| # | Component of item 4 | China's position, per CR 26/44 Table 3 | Verdict |
|---|---|---|---|
| A-3 | General government: revenue, expenditure, balance, composition of financing | Latest observation **2024**, received **September 2025**; frequency of data A, frequency of reporting A | **Met** — provided annually, as reported |
| A-4 | Central government: same four elements | Latest observation **November 2025**, received **December 2025**; M / M | **Met** |
| A-5 | Stocks of central government and central government-guaranteed debt, incl. currency and maturity composition | Latest observation **2025Q3**, received **December 2025**; Q / Q | **Met** as reported to the Fund |
| A-6 | Residency split of holders, where data are amenable | China declares resident/non-resident on its SDDS metadata (§2.4) | **Met** |

**Caveat on A-3 to A-6.** These verdicts rest on the Fund's own record of what it received. Provision to the Fund is not public, so there is no independent way to audit it. No breach of Article VIII §5 has been declared against China; a declaration would be public under Decision 13183 ¶17.

### 1.3 The 2024 Review added three new fiscal obligations — this is where the ground is moving

Decision No. 17692-(24/33), 1 April 2024, expanded Annex A from 12 items to 27. **Items 13, 14 and 15 are all fiscal.**

| # | New obligation | First reporting period | China's position | Verdict |
|---|---|---|---|---|
| A-7 | **Item 13** — total stock of **general government** debt | **2025** | Not addressed in CR 26/44; not covered by the DSBB, which governs publication rather than provision | **Could not verify** |
| A-8 | Item 13 decomposition by maturity, currency, residency, covering ≥80% of the general-government debt stock | 2027 | Not yet due | Not yet due |
| A-9 | **Item 14** — central and general government debt by creditor type, instrument, and individual multilateral and official bilateral creditors | 2027 | Not yet due | Not yet due |
| A-10 | **Item 15** — liquid financial assets of central and general government | 2027 | Not yet due | Not yet due |

**Item 13 is the live question.** A total general-government debt stock became a mandatory provision item with first reporting period 2025 — precisely the aggregate China does not publish (see B-10). Whether China has provided it privately to the Fund cannot be determined from public sources.

**A structural gap in the monitoring.** CR 26/44's Table 3 has 16 rows: the 12 original Annex A items (item 4 expanding to three rows) plus international investment position and exchange rates. It therefore tracks **only items 1–12**. Items 13–15 appear nowhere in it, and I found no IMF statement of how compliance with them is monitored instead. Anyone checking against the *current* obligation set cannot rely on the Article IV table alone.

**What the Board declined to require**, from the 2024 staff report footnote 25: staff proposed mandatory provision of aggregated debt and profit/loss data on **non-financial public corporations**, and proposed including **general-government-guaranteed debt** in the mandatory perimeter. Directors raised concerns on both and neither was adopted. **LGFVs therefore remain outside the mandatory perimeter**, which is why the Fund's LGFV criticism cannot be a compliance finding.

---

## 2. Regime B — SDDS publication (voluntary, observance published)

China subscribed on **2015-10-07**, confirmed three ways: Press Release 15/466, the DSBB API field `SubscriptionDate`, and China's 2025 Annual Observance Report. **China is not an SDDS Plus adherent** — the API returns 32 adherents and China is not among them.

### 2.1 The four fiscal data categories

*Prescriptions from the SDDS Guide (2013) ¶1.10 and ¶4.2. China's practice from the DSBB API and corroborated independently by CR 26/44 Table 3 — two sources, identical values.*

| # | Category | Prescribed periodicity | Prescribed timeliness | China declares | Verdict |
|---|---|---|---|---|---|
| B-1 | General government operations | Annual | **Two quarters** | A / **NLT 7 months** | **Met via declared flexibility option** |
| B-2 | Central government operations | **Monthly** | **One month** | M / **25 days** | **Met, with margin** |
| B-3 | Central government debt | **Quarterly** | **One quarter** | Q / 1Q | **Met, exactly, no margin** |
| B-4 | General government gross debt | Quarterly *(encouraged)* | 4 months *(encouraged)* | **Nothing declared** | **Not a breach** — encouraged only |

**On B-1.** The flexibility option is properly taken and justified. China's declared reason, verbatim from its DSBB metadata: *"According to the Budget Law, the Ministry of Finance is allowed to publish central government and national final revenue and expenditure data for the previous year after approval by the NPC, which generally occurs in the middle of July."* The SDDS Guide ¶2.26 requires a justification; one is on file. **Do not score the 2Q-versus-7M gap as non-compliance.**

**On the flexibility budget.** The SDDS permits **two** regular flexibility options across all sectors combined, not two per sector. China has taken three option-slots across two categories: labour market employment (periodicity), labour market wages (periodicity and timeliness), and GGO (timeliness). Whether labour market counts as one category or two is genuinely ambiguous in the Guide; the 2025 Observance Report raises no concern, implying the one-category reading. Either way **China has no headroom to relax CGO or CGD.**

### 2.2 Prescribed components

| # | Requirement | China's position | Verdict |
|---|---|---|---|
| B-5 | GGO/CGO financing disaggregated into domestic (bank, nonbank) and foreign; the maturity-plus-instrument-or-currency fallback applies only **if that split is "not feasible"** | The NSDP general-government row shows **no bank/nonbank split**; China uses the fallback but declares **no infeasibility justification** | **Technically unsatisfied condition.** The 2025 Observance Report ¶9 records China as meeting coverage for all categories, so the Fund accepts it. Flagged, not scored as breach |
| B-6 | Central government debt disaggregated by maturity **and** at least one of residency, instrument, or currency | China declares **all four**: maturity, residency, instrument, currency | **Exceeds requirement** |
| B-7 | Guide ¶4.32 — state whether maturity is **residual or original** | Metadata silent | **Not met** (disclosure requirement) |
| B-8 | Guide ¶4.31 — state whether CGD coverage is identical to CGO coverage | Metadata silent | **Not met** (disclosure requirement) |
| B-9 | Guide ¶4.19 — describe which central government units CGO covers and excludes | Metadata says only "the monthly accounting statement of the central government" | **Not met** (disclosure requirement) |
| B-10 | Non-central-government debt guaranteed by central government, "as relevant" | No guaranteed-debt line anywhere; the 2025 Observance Report ¶8 states China took **no "as relevant" coverage flexibility options**, so the omission is undeclared | **Undeclared omission** |

B-7 through B-9 are small but real: each is an explicit metadata obligation in the Guide that China's filing does not satisfy.

### 2.3 Advance release calendars

Guide ¶8.6: ARCs are **required for all prescribed categories**, which includes all three prescribed fiscal ones. The ARC flexibility option **was phased out at end-2017**, so since January 2018 the "Friday rule" applies with no escape.

| # | Requirement | China's position | Verdict |
|---|---|---|---|
| B-11 | ARC for general government operations | **None provided.** All 13 ARC month slots null. The 2025 Annual Observance Report ¶7 names GGO explicitly among categories where China did not meet the ARC requirement | **NOT MET — a current, Fund-flagged non-observance on a fiscal category** |
| B-12 | ARC for central government operations | Provided (26 Sep 2026, 25 Oct 2026, 25 Nov 2026) | **Met** |
| B-13 | ARC for central government debt | Provided | **Met** |

**B-11 is the clearest single failure in this entire check.** It is a prescribed requirement, on a fiscal category, with no flexibility option available, currently flagged by the Fund in a published report.

### 2.4 Observance during 2025

| # | Test | Result | Verdict |
|---|---|---|---|
| B-14 | CGO timeliness met every month | **No** — missed for the September reference month by 3 days | **Not met in 2025** |
| B-15 | CGO punctual against its own ARC | **No** — 3 days and 7 days late on two occasions | **Not met in 2025** |
| B-16 | GGO punctual against ARC | Listed among non-punctual categories | **Not met in 2025** |
| B-17 | GGO timeliness met | Yes, judged against the NLT 7M flexibility | **Met** |
| B-18 | CGD timeliness and punctuality | Met all four quarters | **Met** |

### 2.5 Methodological basis

| # | Requirement | China's position | Verdict |
|---|---|---|---|
| B-19 | SDDS **encourages** GFSM 2001 classification; GFSM 1986 presentation remains compliant | China uses **GFSM 1986** | **Compliant** — the newer framework is encouraged, not prescribed |
| B-20 | Guide ¶4.20 — budget projections "do not conform to the Standard"; data must be actual or preliminary actual | No indication China disseminates projections as actuals | **Met** |

The SDDS fiscal prescription has **never been updated to GFSM 2014** — neither the 2013 nor the 2007 edition of the Guide mentions it. So China's use of a 1986-vintage framework, while a genuine analytical limitation, is not an SDDS breach.

---

## 3. Regime C — Adequacy for surveillance (staff judgment, not an obligation)

From CR 26/44 Annex VII Table 1. Scale: A adequate; B some shortcomings but broadly adequate; C shortcomings that somewhat hamper surveillance; D serious shortcomings that significantly hamper surveillance.

| Dimension | Rating |
|---|---|
| **Overall data adequacy** | **B** |
| National accounts | C |
| Prices | B |
| **Government finance statistics** | **C** |
| External sector | B |
| Monetary and financial | B |
| Inter-sectoral consistency | B |

**Government finance statistics, by sub-dimension:**

| Sub-dimension | Rating |
|---|---|
| Coverage | **C** |
| Granularity — government operations | **C** |
| Granularity — public debt statistics | **A** |
| Consistency | **C** |
| Frequency and timeliness | **C** |

Government finance statistics is the joint-worst sector in the assessment, tied with national accounts. Four of its five sub-dimensions are C. The single A, on public-debt granularity, is a recent upgrade that the report attributes to "the availability of the breakdown of official government debt figures, covering both local and central governments."

**Note the tension between regimes.** Frequency and timeliness is rated **C** here, while regime B shows China meeting or beating every prescribed fiscal periodicity and timeliness test except the September CGO miss. These are not contradictory: regime B tests against the SDDS prescription, regime C asks whether the data are good enough for the Fund's analytical purpose. A country can satisfy the standard and still leave the Fund short.

### 3.1 What the Fund actually objects to

Verbatim from the staff assessment: *"The main areas of concern relate to national accounts data and government finance statistics. … For fiscal data, long-standing data gaps include general government data with a breakdown of expenditure by economic type (current and capital expenditure) as well as the data on off-budget entities (including LGFVs) that meet the statistical criteria for inclusion within the perimeter of the general government. The authorities have made progress and published estimates of hidden debt as of end-2023, but they are based on a legal definition not aligned with GFS."*

From Appendix VIII ¶4: China's official general government is the four accounts — general public budget, government-managed fund, state capital operations, social insurance fund. *"These accounts exclude off-budget entities such as local government financial vehicles (LGFVs), government-guided funds (GGFs), and special construction funds. Furthermore, even the official accounts data does not provide a breakdown of expenditure by economic type."*

From Appendix VIII ¶5: *"the MoF definition of hidden debt is based on legal criteria rather than an economic one, and the authorities have not published a full time series for hidden debt, nor have they provided above-the-line estimates of fiscal stance that is consistent with the debt data. Furthermore, staff estimates of off-budget LGFV debt … are more than three times the official figures for hidden debt."*

**A discrepancy inside the report.** Appendix VIII ¶5 says staff LGFV estimates are "more than three times" the official hidden-debt figure; main-text ¶67 says "about four times." Both are in CR 26/44. Quote with care.

### 3.2 How large the perimeter gap is, in the Fund's own numbers

From CR 26/44 Table 2, as reconciled on this repository's `imf-augmented.html`, for 2025, percent of GDP:

| Measure | 2025 | Gap to official |
|---|---|---|
| Official (central + local government debt) | 68.4 | — |
| IMF / WEO general government (adds ≈⅔ of LGFV debt) | 98.9 | +30.5 |
| IMF augmented (adds remaining LGFV, guided and special-construction funds) | 126.6 | +58.2 |

The Fund's own general-government measure is **30.5 percentage points of GDP above** what China reports as government debt. Officially recognised hidden debt was RMB 14.3tn at end-2023, falling to RMB 10.5tn at end-2024 largely through debt swaps.

**Why this is not a compliance finding.** The Board declined in April 2024 to bring non-financial public corporations or government-guaranteed debt into the mandatory perimeter (§1.3). The Fund therefore builds its augmented aggregates from commercial sources — WIND for LGFV liabilities, Zero2IPO for guided funds — rather than from data China is obliged to supply. The report says so: *"The fiscal data used in the Article IV consultation supplements the official GFS statistics with Staff estimates … from WIND and Zero2IPO."*

### 3.3 Corrective actions

The report's entire "Corrective actions and capacity development priorities" entry, verbatim: *"The authorities reiterated their commitment to improve data quality, including through collaboration with the Fund."*

No remedial action is required or scheduled. Two IMF–MOF technical cooperation engagements on government finance statistics took place in April and July 2024, which is relevant to the Article VIII §5 standard that members are "obliged to improve their statistical reporting capacity over time."

**There is no data ROSC for China.** The 2025 Observance Report ¶17 states China has never received a Data module Report on Observance of Standards and Codes mission.

---

## 4. Independent check — publication lags measured from this archive

The sections above rest on what the IMF and China declare. This section tests the declarations against the actual release record held in this repository. Lags are days from the end of the reference period to publication, for releases since January 2024.

| Release | Periodicity | n | Median lag | Range | Bears on |
|---|---|---|---|---|---|
| MOF 全国财政收支情况 (national fiscal revenue and expenditure) | Monthly | 13 | **19 d** | 14–24 | B-2 |
| MOF 地方政府债券发行和债务余额情况 (local government debt) | Monthly | 32 | **31 d** | 24–45 | Beyond SDDS |
| Debt Center 地方政府债券市场报告, Chinese | Monthly | 31 | **39 d** | 30–112 | Beyond SDDS |
| Same report, English translation | Monthly | 25 | **48 d** | 37–75 | Beyond SDDS |
| MOHRSS social insurance bulletin | Monthly | 30 | **29 d** | 22–39 | Beyond SDDS |

**Finding 1 — China publishes faster than it declares.** Its SDDS commitment for central government operations is 25 days; the measured median is **19 days**, with the slowest of 13 releases at 24 days. Every observed release since January 2024 fell within the declared 25-day commitment. This is consistent with CR 26/44's "25D" entry and does not contradict the one 2025 timeliness miss, which the Fund records for the September reference month.

**Finding 2 — the monthly release does not cover general government.** The monthly report carries two of China's four budget accounts. Measured against 2025 expenditure:

| Component | Share of general government | Monthly release? |
|---|---|---|
| General public budget | 55.9% | Yes — MOF |
| Government-managed fund | 22.0% | Yes — MOF |
| Four social insurance schemes | 15.7% | Yes — MOHRSS, separate publisher |
| Medical insurance | 5.9% | **No** |
| State capital operations | 0.5% | **No** — annual only |

So **93.6%** of general-government expenditure has some monthly release and **6.4%** has none. The medical-insurance gap dates from the scheme moving to the National Healthcare Security Administration in 2018, after which it left the MOHRSS table. This is not an SDDS breach — SDDS prescribes monthly data for *central* government operations only, and general government annually — but it quantifies why the Fund rates coverage and frequency C.

*Precision note: the ~11.14tn full social-insurance account used as the denominator is an approximate figure carried in this repository, not a precisely sourced one, so these shares are good to about one percentage point.*

**Finding 3 — much of what China publishes is beyond anything the IMF requires.** Monthly local-government debt stock by province, monthly bond issuance by issuer and instrument, and per-province statutory debt-limit filings all exceed SDDS prescriptions, which ask only for quarterly *central* government debt. The 2026 provincial issuance series in this repository, covering all 37 issuers, has no counterpart in any IMF requirement.

---

## 5. Open items I could not verify

Listed so they are not mistaken for findings.

1. **Item 13 provision (A-7).** Whether China has furnished a total general-government debt stock to the Fund, mandatory from reporting year 2025. Provision is not public; CR 26/44 is silent; the DSBB governs a different obligation.
2. **How items 13–15 are monitored.** The Article IV table covers only Annex A items 1–12. No IMF statement found explaining the alternative mechanism.
3. **The stale general-government entry on the NSDP.** China's National Summary Data Page carries a last-update date of 2026-10-19 while its newest general-government observation is **2024**. Under China's own NLT 7M flexibility, 2025 data were due by end-July 2026 — an apparent slip of about two and a half months. The *fact* is verified; the *cause* is not. It could be an NSDP posting lag rather than non-publication by MOF. I could not resolve it from this archive: the repository scrapes only MOF's monthly topic page, which does not carry the annual final accounts (决算), and I could not locate the final-accounts column on the MOF site in the time available. **Resolving this is the single highest-value follow-up**, because if MOF did not publish by end-July 2026 it is a genuine breach of China's own declared flexibility terms.
4. **Whether China's central-government-debt maturity split is residual or original** (B-7), **whether CGD coverage matches CGO** (B-8), and **which central government units CGO covers** (B-9). All three are metadata silences, which is itself the finding.
5. **The flexibility-option count** (§2.1). Whether labour market is one category or two determines whether China is at two of two or three of two. The Guide does not resolve it.
6. **The periodicity and timeliness understanding attached to Annex A item 4 itself**, as distinct from the SDDS prescription. CR 26/44 shows 2024 general-government data received September 2025 — three quarters — but I could not confirm whether a three-quarter understanding formally governs item 4.
7. **Whether the social-insurance series gap is China's or ours.** This repository's series stops at 2026-06, but the ministry's site does not answer automated requests and this project deliberately ships no bypass, so I could not establish what has been published since. **Do not read our gap as a Chinese publication failure.**

---

## 6. Bottom line

**On the binding obligation (regime A): compliant so far as can be established.** All three fiscal rows of the Article IV surveillance table show China providing data at the expected frequency. No breach has been declared, and a declaration would be public. The one genuine unknown is the new item 13, mandatory from 2025, which asks for exactly the general-government debt aggregate China does not publish.

**On SDDS publication (regime B): substantially compliant, with one real failure and several disclosure gaps.** China meets or beats every prescribed fiscal periodicity and timeliness, over-delivers on central-government debt disaggregation, and has one properly declared and justified flexibility option. Against that: **no advance release calendar for general government operations**, which is prescribed, has no available flexibility option, and is currently flagged by the Fund (B-11); a central-government-operations timeliness miss and two punctuality misses in 2025; an undeclared omission of guaranteed debt; and three metadata disclosures the Guide requires that China's filing does not make.

**On adequacy for surveillance (regime C): this is where the real problem is, and it is not a compliance problem.** Government finance statistics is rated C, the joint-worst sector, with four of five sub-dimensions at C. The Fund's own general-government debt measure sits 30.5 percentage points of GDP above China's official figure, and it builds that measure from commercial data vendors because the Board declined in 2024 to make the off-budget perimeter a mandatory reporting obligation.

**The sharpest way to put it:** China meets the letter of what the IMF requires on fiscal data while leaving the Fund unable to see roughly a third of GDP in government debt. That is a deficiency in the requirements, not in the compliance — and the 2024 Review's item 13 is the first move to close it.

---

*Verification basis: IMF Articles of Agreement; Decision No. 13183-(04/10) as amended through No. 17692-(24/33); SDDS Guide for Subscribers and Users (2013); IMF Dissemination Standards Bulletin Board and its JSON API; China SDDS Annual Observance Report 2025; IMF Country Report No. 26/44. Lag and coverage measurements computed from the release archive in this repository on 2026-10-19 and reproducible from it.*
