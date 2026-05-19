// Default one-page resume template
// Data injected via: typst compile --input data-path=<json> --input lang=<lang>

#import "_macros.typ": *

#let data-path = sys.inputs.at("data-path", default: ".build/resume-data.json")
#let lang = sys.inputs.at("lang", default: "en")
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
#set text(font: "New Computer Modern", size: 9.5pt, lang: "en")
#set par(justify: true, leading: 0.6em)

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

#let summary-key = if lang == "ko" { "summary_ko" } else { "summary_en" }
#let profile-summary = basics.at(summary-key, default: basics.at("summary_en", default: ""))

#if profile-summary != "" {
  section-heading("Summary")
  par(profile-summary)
  v(4pt)
}

// ─── Experience ────────────────────────────────────────────────────────────

#let exp-types = ("role", "project", "hackathon")
#let exp-cards = cards.filter(c => exp-types.contains(c.type))

#if exp-cards.len() > 0 {
  section-heading("Experience")
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
    par(card.summary)
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
  section-heading("Talks & Writing")
  for card in content-cards {
    grid(
      columns: (1fr, auto),
      [#text(weight: "bold")[#card.title]],
      [#text(size: 8.5pt, fill: gray)[#card.period.start]]
    )
    par(card.summary)
    v(3pt)
  }
}

// ─── Education ─────────────────────────────────────────────────────────────

#if education.len() > 0 {
  section-heading("Education")
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

// ─── Footer ────────────────────────────────────────────────────────────────

#v(1fr)
#align(center)[
  #text(size: 7.5pt, fill: luma(180))[
    Generated #meta.generated_at · #meta.card_count cards · template: #meta.template
  ]
]
