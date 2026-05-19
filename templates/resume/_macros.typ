// Shared macros for resume templates

#let period-str(p) = {
  let s = p.start
  let e = if p.end != none { p.end } else { "present" }
  s + " – " + e
}

#let section-heading(title) = {
  set text(weight: "bold", size: 10pt)
  upper(title)
  line(length: 100%, stroke: 0.5pt + gray)
  v(2pt)
}

#let bullet-list(items) = {
  if items.len() == 0 { return }
  for item in items {
    [• #item \ ]
  }
}

#let contact-row(basics) = {
  let parts = ()
  if "email" in basics { parts.push(basics.email) }
  if "phone" in basics { parts.push(basics.phone) }
  if "location" in basics { parts.push(basics.location) }
  if "url" in basics { parts.push(basics.url) }
  parts.join(" · ")
}
