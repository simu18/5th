// Shared layout for the EXP-0 report (no external packages, works offline).

#let report(lang: "en", body) = {
  set document(author: "Rahaman Md Afifur")
  set page(paper: "a4", margin: (left: 30mm, right: 15mm, top: 20mm, bottom: 20mm))
  set text(font: ("Times New Roman", "Liberation Serif", "DejaVu Serif"), size: 12pt, lang: lang)
  set par(justify: true, leading: 0.62em, first-line-indent: 1.25cm)
  set heading(numbering: "1.1")
  show heading: set block(above: 1.2em, below: 0.7em)
  show heading.where(level: 1): set text(size: 14pt)
  show heading.where(level: 2): set text(size: 12.5pt)
  set table(stroke: 0.5pt + luma(120), inset: (x: 4pt, y: 3pt), align: left + horizon)
  show table: set text(size: 9.5pt)
  show table: set par(justify: false, first-line-indent: 0pt)
  show figure: set block(breakable: false)
  show figure.where(kind: table): set block(breakable: true)
  show figure.caption: set text(size: 10pt)
  set figure(gap: 0.6em)
  show raw: set text(font: ("DejaVu Sans Mono", "Liberation Mono"), size: 8pt)
  show raw.where(block: true): block.with(fill: luma(245), inset: 6pt, width: 100%)
  show raw.where(block: true): set par(justify: false)
  show link: it => text(fill: rgb("#1c5cab"), it)
  set list(indent: 0.6cm)
  set enum(indent: 0.6cm)
  body
}

// Title page: all strings are passed in, so the same layout serves both languages.
#let title-page(org: "", faculty: "", work: "", topic: "", course: "", variant: "",
                done-label: "", student: "", group: "", teacher-label: "", teacher: "",
                city-year: "") = {
  set page(numbering: none)
  set par(first-line-indent: 0pt, justify: false)
  align(center)[
    #text(size: 13pt, weight: "bold", org) \
    #v(0.3em)
    #text(size: 12pt, faculty)
  ]
  v(1fr)
  align(center)[
    #text(size: 16pt, weight: "bold", work) \
    #v(0.5em)
    #text(size: 15pt, topic) \
    #v(0.5em)
    #text(size: 12pt, course) \
    #v(0.8em)
    #text(size: 12pt, variant)
  ]
  v(1fr)
  align(right)[
    #block(width: 9.5cm)[
      #set align(left)
      #done-label \
      #student \
      #group
      #v(0.8em)
      #teacher-label \
      #teacher
    ]
  ]
  v(1.5fr)
  align(center, city-year)
  pagebreak()
}
