# Career Output Methodology Research

Date: 2026-05-25  
Purpose: evidence basis for post-Cycle 19 Studio requirements and the next prompt-harness cycle.

## Research Question

How should one canonical career memory be transformed for two materially different output tracks?

| Track | Primary reader | Output job |
|---|---|---|
| K - Korean formal application | recruiter or structured screening process | compact, verifiable career/resume material suited to a formal application |
| G - Global tech/Web3 builder | recruiter followed by technical reviewer or collaborator | resume evidence plus a project portfolio that makes technical reasoning inspectable |

This is desk research, not user-interview evidence. Product and university pages are used as
method signals; only official or research sources are treated as stronger evidence.

## Evidence Grades

| Grade | Meaning | Use in product requirements |
|---|---|---|
| A | official employer, public authority, professional association, or research report | may support a normative requirement |
| B | university career service or established professional research organization | may support a rubric criterion |
| C | career platform or specialist editorial guidance | informs hypotheses and UI language only |

## Evidence Matrix

| ID | Track | Grade | Source | Extracted signal | Product implication |
|---|---|---:|---|---|---|
| E-01 | Shared/G | A | [NACE Job Outlook 2025](https://www.naceweb.org/docs/default-source/default-document-library/2025/publication/research-report/2025-nace-job-outlook-jan-2025.pdf) | Employers report seeking evidence of problem solving (88.3%), teamwork (81.0%), written communication (77.1%), initiative (73.7%), and technical skills (73.2%) on resumes. | A card/output rubric should score evidence of problem, contribution, communication, and technical relevance rather than keyword count alone. |
| E-02 | Shared | B | [MIT CAPD - Resumes](https://capd.mit.edu/channels/resumes/) | A resume is characterized as dense and fact-based, presenting skills, experience, and achievements for a job/team. | Resume generation must favor verified concise claims and target relevance over narrative flourish. |
| E-03 | Shared | B | [UC Davis - Accomplishment Statements](https://careercenter.ucdavis.edu/resumes-and-materials/resumes/accomplishment-statements) | Resume bullets follow action, context, and results; results should be quantified when available. | Resume intent needs action/context/result fields, but missing metrics must become follow-up questions, not invented values. |
| E-04 | Shared | A | [U.S. DOL VETS Resume Essentials, 2026](https://www.dol.gov/sites/dolgov/files/VETS/files/ResumeEssentials_PG_Interactive_Feb2026.pdf) | Targeted accomplishment statements connect results to a job posting. | A later job-targeted mode should preserve provenance between source fact, JD relevance, and rewritten bullet. |
| E-05 | K | A | [Bank of Korea recruitment notice](https://www.bok.or.kr/portal/bbs/P0000561/view.do?menuNo=200037&nttId=10084421) | Formal application instructions constrain documents and state that false application facts may cancel hiring. | Formal Korean output must prioritize truthful, compact material and explicit uncertainty handling. |
| E-06 | K | A | [MOEL job-competency resume standard form copy](https://mirae.yonsei.ac.kr/bbs/sc/68/1008736/download.do) | Structured application form is oriented around job-related qualification and experience entries. | Track K needs predictable field-ready statements rather than a visually expansive case study. |
| E-07 | K | C | [Linkareer developer resume guide](https://community.linkareer.com/employment_data/5131846) | Korean developer guidance emphasizes project contribution, results, technology, and linked evidence. | Treat project/role/metric/link prominence as a hypothesis to validate, not an official constraint. |
| E-08 | K | C | [Wanted career kickoff announcement](https://blog.wantedlab.com/news/230614) | Resume and portfolio preparation is reported as a prominent job-search pain point for junior respondents. | The Studio value proposition of one input feeding multiple outputs is plausible, but not a quality rubric by itself. |
| E-09 | G | B | [Santa Monica College - Portfolios](https://www.smc.edu/student-support/career-services/student-resources/documents/portfolios.pdf) | Early-career employers want to understand thought process; project entries should show problem, process, solution/final work, and separate individual from team roles. | Portfolio intent must surface problem, approach, outcome/evidence, and contribution boundary. |
| E-10 | G | B | [Carnegie Mellon - Portfolio Quick Tips](https://www.cmu.edu/career/documents/quick-tips/quick_tips_portfolio_2018_final.pdf) | Portfolio selection and organization should showcase abilities and key development stages. | Portfolio should select fewer stronger cards and allow artifacts/visual references. |
| E-11 | G | B | [Nielsen Norman Group - UX Careers](https://media.nngroup.com/media/reports/free/UserExperienceCareers_2nd_Edition.pdf) | Hiring-manager expectations vary by role; process artifacts and final outcomes have differing value, and writing quality itself is a signal. | A single rigid portfolio template is inappropriate; intent/preset variants should determine which evidence is highlighted. |
| E-12 | G | B | [Northeastern Experiential Network project portfolio](https://experientialnetwork.northeastern.edu/projects-portfolio/) | Published project stories connect real challenges, applied method, and practical results. | A project card can feed a concise case-study slide when its factual evidence is present. |
| E-13 | Shared | C | [Teal resume builder](https://www.tealhq.com/tools/resume-builder) | Product pattern: target-specific resume assistance and iterative feedback. | UX inspiration only; do not adopt ATS scoring as a truth oracle. |
| E-14 | Shared | C | [Gamma](https://gamma.app/) | Product pattern: generation-first authoring with visual output preview. | Supports Studio's light creation flow, not resume quality decisions. |
| E-15 | Shared | C | [LinkedIn profile guidance](https://www.linkedin.com/help/linkedin/answer/a507663) | Product pattern: durable professional identity with roles and achievements. | Supports canonical career memory framing, not generated claim quality. |
| E-16 | Shared | B | [ISTQB CTFL v4.0.1](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf) | Equivalence partitioning, boundary value analysis, decision tables, and state transitions are standard black-box techniques. | Apply these techniques to provider state, intent, card state, limits, and Studio lifecycle in the test specification. |

## Shared Invariants

The two tracks should share these non-negotiable behaviors.

| Criterion | Requirement for generated material |
|---|---|
| Factual grounding | A claimed date, number, technology, link, role, or result must come from source material or be explicitly marked as unknown. |
| Contribution clarity | Team outcomes cannot be expressed as the user's sole achievement unless the input supports it. |
| Target relevance | Drafting emphasizes evidence appropriate to the requested output and target context. |
| Evidence invitation | Missing period, metric, contribution, evidence URL, and confidentiality status become questions. |
| Human gate | AI output remains preview material until the user approves a saved card or build. |

## Track K Rubric: Formal Application Resume

Use this rubric for Korean formal or structured application presets. Score each item 1-5
only after factual-grounding checks pass.

| Dimension | Strong output behavior | Weight |
|---|---|---:|
| Truthfulness and form fit | Contains only verifiable facts and can be placed into structured application fields without rewriting. | Gate |
| Role relevance | States activity, responsibility, and job-relevant competency compactly. | 25% |
| Accomplishment evidence | Uses result or observable deliverable; requests a metric when none is supplied. | 25% |
| Readability | Korean statement is concise, formal, and scan-friendly. | 20% |
| Competency signal | Makes problem solving, collaboration, communication, or technical capability visible where supported. | 20% |
| Supporting evidence | Includes applicable link/certificate/artifact reference or flags its absence. | 10% |

Preferred shape:

```text
activity/role + relevant action + verified result or deliverable + optional metric
```

The audit does not establish a universal page limit for every Korean employer. Length and
section restrictions must remain preset- or application-specific.

## Track G Rubric: Tech/Web3 Resume And Portfolio

| Dimension | Strong resume behavior | Strong portfolio behavior | Weight |
|---|---|---|---:|
| Factual grounding | concise verified claim | evidence-backed narrative | Gate |
| Problem/need | implied only if space requires | explicitly establishes the need or constraint | 15% |
| Individual contribution | action verb and ownership boundary | role versus team work is clear | 20% |
| Technical reasoning | relevant technology only | approach plus meaningful choice/tradeoff | 20% |
| Outcome/evidence | result, link, or missing-info flag | result, artifact/link/visual, or honest pending state | 25% |
| Insight/readability | sharp bullet | readable case-story suitable for slide review | 20% |

Preferred portfolio block shape:

```text
Problem -> Framing -> Approach / Decisions -> Outcome / Evidence -> Insight
```

For engineering work this shape is an inference from career-service portfolio guidance and
the product's intended deck format; it should be validated with real target applications later.

## Product Decisions From Research

| Decision | Evidence basis | Requirement consequence |
|---|---|---|
| Do not force one output style across both tracks. | E-05, E-06, E-09, E-11 | Preserve output intent and add audience/preset-specific rubric. |
| Grounding is higher priority than eloquence. | E-02, E-03, E-05 | Next harness must expose facts/uncertainty and prohibit unsupported claims. |
| Portfolio content must show reasoning and ownership, not just screenshots. | E-09, E-10, E-11 | Keep narrative blocks and add role/evidence prompts. |
| Metrics are valuable only when supported. | E-03, E-05 | Missing metric is a question; never an invented achievement. |
| Korean-track conclusions require later local validation. | Limited Grade A/B Korean developer-portfolio material | Keep confidence noted and plan optional recruiter/mentor review later. |

## Research Limitations

- NACE is an employer survey focused on new college graduates in the United States; it
  supports shared evidence criteria but does not directly describe Korean hiring.
- Portfolio evidence is strongest for early-career and design-adjacent presentation; its
  transfer to Web3 engineering is a reasoned product hypothesis, not a measured hiring rule.
- Korean developer-specific public guidance found in this pass is largely platform/editorial
  material. Formal employer truthfulness and structure are supported, while preferred
  developer portfolio narrative still needs later human validation.
