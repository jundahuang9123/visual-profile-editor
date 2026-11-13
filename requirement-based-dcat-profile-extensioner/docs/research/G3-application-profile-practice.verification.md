# Verification report: G3-application-profile-practice

Role: sceptic. Date: 2026-11-13. Every verdict below rests on a source I opened myself in this task.

## Limits of this verification

- Web search was not available: the shared search budget of the run was already used up (three queries refused, none executed). Nothing that the researcher took from search summaries could be checked independently. This affects scrocca2025mobilitydcat, scrocca2022napdcat, bures2022napcore, the derycke2025healthdcat paper text, dragan2019maintenance, the perego2016jrc paper text, coyle2009dcap, healthdataeu2024d62 and the four context works.
- Checked from primary sources (local clones under /home/user/refs, plus two raw.githubusercontent.com fetches):
  - SEMICeu/DCAT-AP-reuse-guidelines index.html (commit e958ded), full text read.
  - SEMICeu/DCAT-AP releases 3.0.0, 3.0.0-hvd, 3.0.1 (index.html, CHANGELOG.md, shacl), 2.0.1 PDF, issue submission guidelines PDF (commit 4470b8e).
  - mobilityDCAT-AP: gh-pages f035bf9 releases/1.1.0 and 3.0.0 index.html, releases/1.1.0/mobilitydcat-ap.ttl; main 3f228c7 src/shacl/README.md, src/shacl/shapes.ttl, migration guide xlsx; wiki chapters 1 and 6; validation repository.
  - healthdcat-ap.github.io OldContent/index.html (a155911).
  - GeoDCAT-AP 1.0 PDF and 3.0.0 index.html; StatDCAT-AP 1.0.0 PDF (raw fetch, pinned commit 12a2424); DCAT-AP-JRC docs/1.0/index.html.
  - dcmi/repository at 268219f (raw fetch; the local clone has an empty working tree): Singapore Framework and DescriptionSetProfile wiki copies.
  - w3c/dxwg: ucr/static/index.html (Editor's Draft 10 January 2019) and rec-snapshot-2024 dcat REC Overview.html (W3C Recommendation 22 August 2024).
  - UKGovLD/publishing-statistical-data d382ad5: integrity-*.sparql and TestWF.java.

## Verdicts per step

| Step | Verdict | What I checked and found |
|---|---|---|
| G3-S01 | partially_confirmed | Four standard situations are in Step 2 exactly as described. Not supported as stated: (a) "fixed order" is not said; the text lists the situations and once says "skip to the next situations". (b) Step 2 has five worked examples, not six, and the field labels vary (Existing DCAT-AP solution / DCAT-AP solution / DCAT solution / Approach / Resolution); a sixth example (spatial resolution) is in the range section with fields Use case / DCAT-AP situation / Problem / Solution. (c) "The published extensions follow the same order" is the researcher's inference; none of mobilityDCAT-AP 1.1.0, StatDCAT-AP, GeoDCAT-AP 1.0 or DCAT-AP-JRC states this ladder. |
| G3-S02 | confirmed | Reuse guidelines, cardinality situation: mandatory stays mandatory, at most one stays at most one, "raise an issue", GeoDCAT-AP rights example; "It is not possible to loosen them under any conditions". mobilityDCAT-AP src/shacl/shapes.ttl header: CatalogueRecord dct:conformsTo, "to be reported to the DCAT-AP maintainers". HealthDCAT-AP: "Mandatory properties retain their required status." |
| G3-S03 | confirmed | All five cases with the cited examples (contact point as text, release date xsd:date vs xsd:gDay, eli:LegalResource vs skos:Concept with double typing) are in the range situation; quote verbatim. |
| G3-S04 | confirmed | Four strength levels and their handling are in the controlled-vocabulary situation; "it must be used with a different property" verbatim. DCAT-AP 3.0.1: "All profiles in the ecosystem MUST avoid conflicts by creating subproperties." DCAT-AP 3.0.0 lists seven SHOULD criteria. mobilitydcat-ap.ttl line 603: mobilityTheme rdfs:subPropertyOf dcat:theme. |
| G3-S05 | confirmed | Three outcomes and the applicable-legislation example are in the semantic-fit situation. |
| G3-S06 | confirmed | "If you want to add a new property" situation: supporting vocabulary in a managed namespace, open domain/range, generic definition, two specifications with own lifecycle. mobilitydcat-ap.ttl uses rdfs:subPropertyOf (4 times), dcam:domainIncludes (78), dcam:rangeIncludes, skos:scopeNote. StatDCAT-AP Annex II confirmed (one row, numSeries, has no cardinality). |
| G3-S07 | partially_confirmed | A/E/P confirmed in DCAT-AP 3.0.0, HVD 3.0.0, GeoDCAT-AP 3.0.0 and HealthDCAT-AP; 3.0.1 CHANGELOG issue 370 confirms the tag changing "from extended to as-is". Corrections: DCAT-AP 3.0.0's own tags are relative to DCAT, not DCAT-AP; mobilityDCAT-AP 3.0.0 does not use plain A/E/P but a longer scheme with GeoDCAT-AP variants (I saw "GE" and "P: proprietary definition"). |
| G3-S08 | confirmed | mobilityDCAT-AP 1.1.0: plus/minus marking (section 2.2 and intro), A.2 table, "raised to "mandatory", compared to [DCAT-AP-v2.0.1]". HVD: usage notes cite "Article 3.3", "Article 3.4". |
| G3-S09 | confirmed | src/shacl/README.md and Annex G.1 of 3.0.0: owl:imports plus deltas, file split, severity levels (shapes.ttl: 24 Violation, 8 Warning, 34 Info), named property shapes with sh:name, sh:description, sh:message. DCAT-AP 3.0.0 dcat-ap-SHACL.ttl: one IRI per constraint, 300 rdfs:seeAlso statements (string literals pointing at specification anchors). |
| G3-S10 | confirmed | DCAT 3 section 4 definition of profile; HVD "it MUST conform to DCAT-AP"; HealthDCAT-AP "MUST first conform to DCAT-AP"; mobilityDCAT-AP 3.0.0 G.1 "the inherited rule prevails ... raised with the DCAT-AP maintainers rather than worked around". |
| G3-S11 | partially_confirmed | mobilityDCAT-AP validation: categories, positives/negatives, ids in file names, validator.py lines 24-37 all confirmed (there is also an upstream-examples folder). Data Cube: only some tests pair a base graph with a delta (integrity-1, integrity-2); others use a single stand-alone failing graph (missing-measure.ttl, missing-range.ttl). "Each check ... base plus delta" is too strong. |
| G3-S12 | confirmed | UCR draft section 3 (template fields, vote options, deduplication, maintained links) and section 4 (four tag facets, "Requirements first") confirmed; 51 use-case ids found. The link from each requirement to a GitHub issue was not rechecked. |
| G3-S13 | unverified | No source available to me states "forty requirements" or the counts 8/5/22/5; the mobilityDCAT-AP specification and wiki do not contain them, and web search was unavailable. |
| G3-S14 | confirmed | Wiki chapter 1 lines 47 and 65 ("technology-independent data structure"; "first step was to check ... DCAT-AP"); GeoDCAT-AP 1.0 Table 2 preamble (obligation of either specification per row); Singapore Framework "Domain model (mandatory)". The attribution to scrocca2025mobilitydcat was not checked. |
| G3-S15 | partially_confirmed | Confirmed: reuse guidelines Step 3 (webinar votes are the fallback when no consensus is reached), UCR vote options, StatDCAT-AP Annex III columns. Not checked by me: "SEMIC labels track issue states" and "maintenance reports group issues by change class" (dragan2019maintenance not opened). |
| G3-S16 | confirmed | DCAT-AP submission guidelines: "classify the issue as a bug fix, minor semantic issue or major semantic issue"; wiki chapter 6 definitions and X.Y.Z scheme verbatim; migration guide xlsx has a Category column with values such as "MUST change - breaking, action required before go-live". dragan2019maintenance itself not opened. |
| G3-S17 | confirmed | DCAT-AP 2.0.1 Annex II columns URI, Type, Action, Description, Issue, Release; StatDCAT-AP Annex II; mobilityDCAT-AP 1.1.0 change-log line on "schema" verbatim. |
| G3-S18 | confirmed | Singapore Framework components and the internal-consistency sentence verbatim; reuse guidelines Step 4. coyle2009dcap not checked. |
| G3-S19 | confirmed | GeoDCAT-AP 1.0 section 4.3 (partial and provisional mappings, "unstable") and sections 5.2/5.3 (Core, Extended). |
| G3-S20 | confirmed | Usage-scope situation of the guidelines; HealthDCAT-AP opendata/protected/sensitive shape files; both HVD and HealthDCAT-AP say "The SHACL templates assume that all resources are subject to ...". |
| G3-S21 | confirmed | HVD passage verbatim, including the added check with severity Violation; DCAT-AP 3.0.1: "SHOULD only be used for requirements that can be verified by a machine". |
| G3-S22 | partially_confirmed | Numbered checks with one-line statement and ASK query "true if there is a problem" confirmed (22 files for numbers 1 to 21, 19 split into a and b). The test pattern is mixed, see G3-S11. |
| G3-S23 | partially_confirmed | DCAT 3 section 7 (eleven pairs, MAY/MUST NOT) and DCAT-AP 3.0.0 ("have no conformance expectation") confirmed; mobilityDCAT-AP 3.0.0 has "A.3 Classes and properties not used from DCAT-AP" where 1.1.0 said "removed". That a reason is documented for each unused element was not checked. |
| G3-S24 | confirmed | Each quoted criterion is in its source (HealthDCAT-AP best practices, StatDCAT-AP 6.2, DCAT-AP-JRC criteria, GeoDCAT-AP 4.1). The ordering is a synthesis, as the step itself says; scrocca2025mobilitydcat not checked. |
| G3-S25 | confirmed | GeoDCAT-AP 1.0 "no new terms have been defined"; DCAT-AP-JRC "does not define classes or properties of its own"; StatDCAT-AP six rows, four stat: properties; mobilityDCAT-AP 1.1.0 A.2 "2 additional classes and 48 additional properties"; my own count of the ttl also gives 2 classes and 12 properties in the mobilitydcatap namespace. |

## Corrected texts

- G3-S01: SEMIC resolves each use case by one of four standard situations, listed in this sequence: covered by DCAT-AP (reuse as-is); covered with adjustments (tighten only); covered by W3C DCAT, another vocabulary or another DCAT-AP profile (reuse that); not covered (new term in the profile's own namespace). Step 2 gives five worked examples whose field labels vary (Use case, Existing DCAT-AP solution or DCAT-AP solution or DCAT solution, Resolution or Approach). That older extensions follow the same sequence is our reading, not stated by them.
- G3-S07: Property rows are tagged A, E or P in DCAT-AP 3 (relative to DCAT), and in the HVD annex, GeoDCAT-AP 3 and HealthDCAT-AP (relative to DCAT-AP). mobilityDCAT-AP 3.0.0 uses an extended scheme that also qualifies reuse from GeoDCAT-AP. The tag depends on the base version: DCAT-AP 3.0.1 changed one from extended to as-is after relaxing a cardinality.
- G3-S11 / G3-S22: The Data Cube development repository tests the integrity checks with a valid graph for the positive case and, for the negative case, either that graph plus a small delta graph or a separate failing graph named after the fault.
- G3-S15: drop, or mark "verify:", the two clauses on SEMIC labels and on maintenance reports.
- G3-S23: mobilityDCAT-AP 3.0.0 lists elements "not used from DCAT-AP" (Annex A.3) where version 1.1.0 spoke of removed properties. verify: whether a reason is given per element.

## Overreach flags (how_we_reuse goes beyond the source; label as our adaptation)

- G3-S01: the mandatory sentence per skipped rung, the few-shot use of the examples and the Verify rejection rule are ours; the guideline neither states a strict order nor a justification duty.
- G3-S07: A/E/P are editorial tags assigned by specification editors; deriving them mechanically from a delta status is ours.
- G3-S13: routing by requirement category is ours, and the underlying counts are unverified.
- G3-S14: two LLM passes with IRI-free first pass is ours; the sources describe a human modelling sequence.
- G3-S16: the rule table (raised minimum, narrowed range, closed value list imply major) is ours; the sources only give examples (optional additions minor; mandatory properties or mandatory vocabulary major).
- G3-S20: "never encoded only in usage notes" is stricter than the guideline, which accepts a conditional note for a single property.
- G3-S21: downgrading an untestable "must" atom is ours; the DCAT-AP sentence concerns controlled-vocabulary levels only.
- G3-S24: the six-tier ranking is ours (the step says so; keep that label wherever it is reused).

## Paper-level corrections

- semicreuse2026: five worked examples in Step 2 (plus one in the range section), not six in one layout; webinar votes are the fallback when discussion yields no consensus. Repository HEAD is dated 10 June 2026 while the configured publishDate is 2026-06-17; README copyright line says 2025.
- semicdcatap: the A/E/P qualification in DCAT-AP 3.0.0 is against DCAT. The 300 figure is the number of rdfs:seeAlso statements in dcat-ap-SHACL.ttl; the shapes there are not typed as property shapes. The count of 13 MUST bindings was not recounted.
- mobilitydcatspec: the "2 weeks" in wiki chapter 6 is a no-opposition window for minor resolutions, not an editor response time; the two-week editor response is in the DCAT-AP submission guidelines only.
- nilsson2008singapore: the mandatory/optional components, the internal-consistency sentence and the DSP exclusions are confirmed; I did not find the wording "basis for reviewing profiles for documentary completeness" in the part I searched, treat it as unverified wording.
- w3cdcatucr: 51 use cases confirmed; the figure of 68 requirements in 14 groups was not recounted.
- w3cdatacube: 22 query files for checks 1 to 21; test pattern mixed (see G3-S11).
- Not checkable in this task (no search, hosts blocked): scrocca2025mobilitydcat, scrocca2022napdcat, bures2022napcore, derycke2025healthdcat paper text, healthdataeu2024d62, coyle2009dcap, perego2016jrc paper text, dragan2019maintenance, wilkinson2016fair, gregory2020search, koesten2020reuse, chapman2020search. Their summaries stay at the researcher's stated confidence and should be read as unverified by the sceptic.
