# Consultant Workflow Model For Career Studio

Date: 2026-05-25  
Method: synthesis of public resume and portfolio guidance; no consultant interviews conducted.

## Why This Model Exists

Career Studio should not behave like a form that asks the user to pre-normalize their own
history. It should behave like a careful career editor: accept rough evidence, ask what is
missing, produce target-specific material, and leave factual approval with the user.

Supporting sources:

- [UC Davis accomplishment statements](https://careercenter.ucdavis.edu/resumes-and-materials/resumes/accomplishment-statements)
- [MIT CAPD resume guidance](https://capd.mit.edu/channels/resumes/)
- [NACE Job Outlook 2025](https://www.naceweb.org/docs/default-source/default-document-library/2025/publication/research-report/2025-nace-job-outlook-jan-2025.pdf)
- [Santa Monica College portfolio guidance](https://www.smc.edu/student-support/career-services/student-resources/documents/portfolios.pdf)
- [Nielsen Norman Group UX Careers report](https://media.nngroup.com/media/reports/free/UserExperienceCareers_2nd_Edition.pdf)
- [UC Davis cover letters](https://careercenter.ucdavis.edu/resumes-and-materials/cover-letters)
- [Tufts cover letters](https://careers.tufts.edu/channels/cover-letters/)
- [NCS fair recruitment guidance](https://www.ncs.go.kr/company/ch03/CH-104-001-01.scdo)

## Workflow

| Stage | Consultant question | AI may do | Human must decide | Current Studio status |
|---|---|---|---|---|
| 1. Intake | What happened, in the user's own words? | accept free text and links | what may be shared | Implemented |
| 2. Target | Which reader and artifact is this for? | apply Resume/Portfolio/Both intent | role/application target | Partial: intent exists, audience/preset absent |
| 3. Evidence extraction | Which facts, dates, metrics, tools, artifacts, and roles are supported? | extract candidates with provenance | confirm accuracy and confidentiality | Gap: prompt generates draft directly |
| 4. Gap interview | Which missing details change credibility? | ask for period, metric, evidence, role, visibility | answer or knowingly leave unknown | Partial: basic missing prompts exist |
| 5. Positioning | What capability does this evidence demonstrate? | propose target-relevant emphasis | approve truthful emphasis | Gap |
| 6. Drafting | How does the same evidence read as resume versus portfolio? | produce separate draft surfaces | edit and select version | Implemented, quality unverified |
| 7. Proof and QA | Is every claim supportable and usable? | flag unsupported/contradictory claims | final factual sign-off | Gap |
| 8. Commit/output | Should this enter canonical memory and artifacts? | save only after explicit action; build outputs | approve card and output selection | Implemented |

## Recommended AI Contract

Before a persuasive draft is shown, an AI response should make the evidentiary boundary
reviewable.

| Output group | Purpose | Persist by default? |
|---|---|---:|
| `source_facts` | only facts directly supported by raw input | No, preview metadata |
| `assumptions` | useful but unconfirmed interpretations | No |
| `missing_info` | questions required for stronger or safer claims | No |
| `positioning` | suggested competency or narrative emphasis | No |
| `resume_bullet` | concise output-specific draft | Only when user saves approved draft |
| `portfolio_body` | problem/approach/outcome/insight draft | Only when user saves approved draft |

## Human Approval Gates

The user must explicitly approve or edit:

- dates and chronology;
- numerical outcomes and metric definitions;
- personal contribution within team work;
- employer/client/confidential information;
- public evidence URLs or visuals;
- final text saved into `cards/*.mdx`.

## Guardrails

| Risky pattern | Required handling |
|---|---|
| No metric in source | Ask for metric or describe a deliverable without a numeric claim. |
| Team project with unclear ownership | Ask for personal role; do not imply sole ownership. |
| Mention of confidential/client work | Ask about disclosure before producing public-ready evidence. |
| Link or visual missing | Invite supporting material; portfolio can remain a draft. |
| Compelling but unsupported inference | Put it in `assumptions`, never in the saved claim by default. |

## Cycle 20 Recommendation

Implement a grounded one-shot preview contract first: extract facts, assumptions, follow-up
questions, and target-specific draft surfaces in one structured response. A two-stage
extraction/composition workflow should be introduced only if measured quality improvement
outweighs its added token, latency, and failure cost.

## Following Cycle Recommendation: Application Writing Harness

Once grounded preview is verified, expand the workflow to `cover_letter` / 자기소개서 and
`application_answer` outputs. These are not extended resumes:

| Output | Selection and drafting method |
|---|---|
| Resume | compress several verified experiences into scan-ready evidence |
| Portfolio | make a selected project's reasoning and outcome inspectable |
| Cover letter / 자기소개서 | select experience that explains fit, contribution, and grounded motivation for a supplied target |
| Application answer | interpret one question/competency, select the strongest episode, and answer under its character limit |

The application-writing harness should receive:

- one or more approved card IDs, or allow retrieval from approved cards;
- target organization and role context supplied by the user;
- job description or evaluation competency where available;
- the exact question and character limit for question-answer mode.

It should preview:

- `question_intent` or `competency_target`;
- `selected_cards` and `selection_reason`;
- `personal_facts` from cards only;
- `target_context_used` from supplied application context only;
- `assumptions`, `missing_info`, and `answer_draft`;
- character count and over-limit status.

This preserves one source of truth for the user's history while recognizing that a submitted
answer also needs external target context.

Public guidance basis:

- Cover-letter guidance consistently treats the letter as tailored connection between selected
  experiences and one employer/role, rather than a repetition of the resume.
- NCS fair-recruitment guidance centers job-relevant competency evidence and excludes
  bias-inducing personal background fields, so formal Korean application-answer generation
  needs explicit restriction handling.
