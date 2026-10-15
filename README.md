# trellis

The regulatory frame a test result is mapped onto.

A security test produces findings. A regulated organisation has obligations.
This repository is the join: a machine-readable catalogue of what EU and Norwegian law requires of an AI system, and a crosswalk from the techniques an assurance review exercises to the obligations those techniques produce evidence for.

It is maintained by [Sunflower Consulting](https://github.com/sunflower-consulting) and used by our assessment tooling. It is published because a crosswalk nobody can check is a crosswalk nobody should trust.

## This is not legal advice

Nothing here is legal advice, and we are not lawyers.
These are engineering notes about what to test and what evidence to keep, written so that a technical finding can be discussed with the people who do give legal advice.

Every record names the official text it was read from and the date it was last checked.
Check it yourself before you rely on it.
Where we could not confirm something against an official source, the record says `verification: unconfirmed` rather than quietly rounding up.

## What is in here

```
obligations/     one record per obligation, by instrument
crosswalk/       technique -> the obligations it produces evidence for
taxonomy/        the technique vocabulary
tier/            an AI system's description -> its risk class under the AI Act
calendar.yaml    the dates, each with the source it came from
dist/snapshot.yaml   the generated file consumers vendor
```

An obligation id is `instrument:citation` - `ai-act:Art.15(4)`, `dora:Art.25`, `iso-42001:A.6.2.4`.
A client reading it in a report needs no key, and a renderer can group by instrument with one string split.

## What is covered

66 obligations across five instruments, and 22 of them are
ones a test result can speak to at all.

| Instrument | Obligations |
|---|---|
| EU AI Act, Regulation (EU) 2024/1689 as amended by Regulation (EU) 2026/1744 | 30 |
| DORA, Regulation (EU) 2022/2554, and the TLPT delegated regulation | 16 |
| Cyber Resilience Act, Regulation (EU) 2024/2847 | 10 |
| Norway's digitalsikkerhetsloven and its forskrift | 9 |
| ISO/IEC 42001:2023 | 1 |

This is deliberately partial. It catalogues what an assurance review of a deployed LLM
application touches, not the whole of any instrument: the institutional machinery -
notified bodies, market surveillance, committee procedure, penalties - is out of scope
and will stay out.

One record carries `verification: unconfirmed`, and it is the ISO/IEC 42001 control:
that standard is sold rather than published, so no free official text of its Annex A
exists and the record can never honestly be marked confirmed. It carries the control
identifier and our own description of what an auditor looks for, corroborated from
independent certification bodies, and none of the standard's wording.

Everything else was read off an official text - EUR-Lex or the Commission's own AI Act
Service Desk for EU instruments, Lovdata for Norwegian ones - and names the URL it was
read from.

## The field this exists for

Every obligation carries `verifiable`, which is one of three values:

| value | meaning |
|---|---|
| `test` | an adversarial run against a deployed system can produce evidence for it |
| `review` | no probe could ever establish it; it is a document or a process |
| `hybrid` | a test can show the control failed; only a review shows it exists |

This is a claim about epistemology, not about effort.
It exists so a report can state plainly which obligations an engagement produced *test evidence* for and which are *review assertions*, and so that it cannot quietly imply the first where it only has the second.

A report built on this dataset renders a `review` obligation with the reviewer's assertion and an explicit "no test evidence", never as a pass, and never as a count of zero findings.
Zero findings and nothing tested are different claims, and conflating them is the failure the whole thing is built to avoid.

## Using it

Consumers vendor `dist/snapshot.yaml` - one file, checked in, with a digest over its content.

```bash
python3 bin/bundle.py      # regenerate dist/snapshot.yaml from the sources
python3 -m pytest          # the dataset's own guards
```

Not a package dependency and not a submodule, deliberately.
One consumer has to run offline with no network; the other has no package install at all.
And an uninitialised submodule is an empty directory rather than an error, which would render a compliance appendix with zero rows and no complaint.

The copy being a deliberate act is the point: it pins what a given report cited, and a change to the law arrives as a reviewable diff on one file rather than as a silent update underneath a published document.

## Contributing a correction

If a citation is wrong, a date has moved or a summary has drifted from what the provision says, open an issue with the official source and we will fix it.
Corrections against the text beat opinions about the text.

Obligations are amended, never deleted. A record whose provision changes is marked `superseded` and points at what replaced it, because a report citing it has to stay explainable after the law moves.

## Licence

The obligation data, crosswalk, taxonomy and calendar are [CC BY 4.0](LICENSE-DATA).
The code under `bin/` and `tests/` is [Apache-2.0](LICENSE).

Attribution for the technique vocabulary and for the framework mappings we build on is in [NOTICE](NOTICE).
