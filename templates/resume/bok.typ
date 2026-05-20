// bok — Korean resume template
// Requires summary_ko on all selected cards (enforced in pcli.py before Typst).
// Education section appears above experience. Korean font and section labels.

#import "_macros.typ": *

#let data-path = sys.inputs.at("data-path", default: ".build/resume-data.json")
#let data = json(data-path)
#let basics = data.basics
#let cards = data.cards
#let education = data.education
#let meta = data.meta

// Page setup
#set page(
  paper: "a4",
  margin: (x: 1.8cm, y: 1.5cm),
)
#set text(font: "New Computer Modern", size: 9.5pt, lang: "ko")
#set par(justify: true, leading: 0.65em)

// ─── Header ────────────────────────────────────────────────────────────────

#align(center)[
  #text(size: 18pt, weight: "bold")[#basics.at("name", default: "")]
  \
  #text(size: 10pt, style: "italic")[#basics.at("label", default: "")]
  \
  #text(size: 9pt, fill: gray)[#contact-row(basics)]
]

#v(6pt)

// ─── Summary ───────────────────────────────────────────────────────────────

#let profile-summary = basics.at("summary_ko", default: basics.at("summary_en", default: ""))

#if profile-summary != "" {
  section-heading("소개")
  par(profile-summary)
  v(4pt)
}

// ─── Education (placed above experience in bok) ────────────────────────────

#if education.len() > 0 {
  section-heading("학력")
  for edu in education {
    grid(
      columns: (1fr, auto),
      [
        #text(weight: "bold")[#edu.at("institution", default: "")]
        #h(4pt)
        #text(fill: gray, size: 8.5pt)[#edu.at("area", default: "") · #edu.at("studyType", default: "")]
      ],
      [#text(size: 8.5pt, fill: gray)[#edu.at("startDate", default: "") – #edu.at("endDate", default: "")]]
    )
    v(3pt)
  }
}

// ─── Experience ────────────────────────────────────────────────────────────

#let exp-types = ("role", "project", "hackathon")
#let exp-cards = cards.filter(c => exp-types.contains(c.type))

#if exp-cards.len() > 0 {
  section-heading("경력 및 프로젝트")
  for card in exp-cards {
    grid(
      columns: (1fr, auto),
      [
        #text(weight: "bold")[#card.title]
        #h(4pt)
        #text(fill: gray, size: 8.5pt)[#card.type]
      ],
      [#text(size: 8.5pt, fill: gray)[#period-str(card.period)]]
    )
    // Use Korean summary (summary_ko guaranteed by pcli.py validation)
    par(card.at("summary_ko", default: card.summary))
    if card.metrics.len() > 0 {
      bullet-list(card.metrics)
    }
    v(4pt)
  }
}

// ─── Talks & Writing ───────────────────────────────────────────────────────

#let content-types = ("talk", "writing", "paper", "award")
#let content-cards = cards.filter(c => content-types.contains(c.type))

#if content-cards.len() > 0 {
  section-heading("발표 및 저술")
  for card in content-cards {
    grid(
      columns: (1fr, auto),
      [#text(weight: "bold")[#card.title]],
      [#text(size: 8.5pt, fill: gray)[#card.period.start]]
    )
    par(card.at("summary_ko", default: card.summary))
    v(3pt)
  }
}

// ─── Footer ────────────────────────────────────────────────────────────────

#v(1fr)
#align(center)[
  #text(size: 7.5pt, fill: luma(180))[
    생성일: #meta.generated_at · #meta.card_count 개 카드 · 템플릿: #meta.template
  ]
]
