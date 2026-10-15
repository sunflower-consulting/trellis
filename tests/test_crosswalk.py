"""The crosswalk's guards, including the one that keeps the dataset honest.

A crosswalk rots in one direction: the corpus grows, nobody maps the new techniques,
and the appendix simply has fewer rows. Missing, not wrong, and so nothing fails. The
denominator test below is the whole defence against that, and it is why
`_unmapped.yaml` exists with a required reason rather than letting silence do the job.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _yaml(p):
    """Missing file -> empty, so the assertion that notices says what is wrong. A
    traceback from `read_text` names the path and not the problem."""
    f = ROOT / p
    if not f.is_file():
        return {}
    return yaml.safe_load(f.read_text(encoding="utf-8")) or {}


def _crosswalk():
    return _yaml("crosswalk/llm-techniques.yaml").get("techniques", {})


def _unmapped():
    return _yaml("crosswalk/_unmapped.yaml").get("techniques", {})


def _vocabulary():
    return _yaml("taxonomy/llm-techniques.yaml").get("techniques", {})


def _obligation_ids():
    return {yaml.safe_load(p.read_text(encoding="utf-8"))["id"]
            for p in (ROOT / "obligations").rglob("*.yaml")}


def _obligations():
    return {(d := yaml.safe_load(p.read_text(encoding="utf-8")))["id"]: d
            for p in (ROOT / "obligations").rglob("*.yaml")}


def test_there_is_a_crosswalk_at_all():
    assert _crosswalk(), "no crosswalk entries found"


def test_no_dangling_taxa():
    """Every technique the crosswalk names exists in the vocabulary.

    A dangling name costs a reader a lookup and teaches them to distrust the table,
    which is a worse outcome than the row being absent.
    """
    vocab = set(_vocabulary())
    named = set(_crosswalk()) | set(_unmapped())
    assert named <= vocab, f"techniques not in the vocabulary: {sorted(named - vocab)}"


def test_no_dangling_obligation_ids():
    known = _obligation_ids()
    bad = {t: [o for o in entry.get("obligations", []) if o not in known]
           for t, entry in _crosswalk().items()}
    bad = {t: v for t, v in bad.items() if v}
    assert bad == {}, f"mappings pointing at obligations that do not exist: {bad}"


def test_no_crosswalk_maps_a_review_only_obligation_to_a_technique():
    """The honesty keystone.

    `review` means no probe could ever establish it. Crosswalking a technique to one
    lets a TEST RESULT claim a document-review obligation -- the appendix shows a
    finding under a row that no finding could ever speak to. If a mapping here looks
    right, the obligation is `hybrid` and the record is what should change, not this.
    """
    obs = _obligations()
    offenders = {}
    for t, entry in _crosswalk().items():
        for oid in entry.get("obligations", []):
            if obs.get(oid, {}).get("verifiable") == "review":
                offenders.setdefault(t, []).append(oid)
    assert offenders == {}, (
        f"techniques mapped to review-only obligations: {offenders}. A test result "
        f"cannot speak to these; reclassify the obligation as hybrid, with a reason, "
        f"or drop the mapping.")


def test_every_technique_is_crosswalked_or_excused():
    """The denominator, and the thing that stops this rotting quietly.

    `_unmapped.yaml` is the only escape, and it demands a reason, so that "no
    obligation in this catalogue is about that" and "nobody has looked yet" are
    different states a count can tell apart.
    """
    vocab, mapped, excused = set(_vocabulary()), set(_crosswalk()), set(_unmapped())
    missing = vocab - mapped - excused
    assert missing == set(), (
        f"{len(missing)} techniques are neither crosswalked nor excused: "
        f"{sorted(missing)[:12]}{' ...' if len(missing) > 12 else ''}")


def test_every_excused_technique_says_why():
    thin = [t for t, e in _unmapped().items()
            if len((e or {}).get("reason", "")) < 20]
    assert thin == [], f"excused with no usable reason: {thin}"


def test_every_mapping_gives_a_rationale():
    """"Why does a path traversal in generated output bear on Art. 15(4)" is what a
    client's counsel asks, and an unexplained mapping is what makes a compliance
    appendix read as marketing."""
    thin = [t for t, e in _crosswalk().items() if len(e.get("rationale", "")) < 20]
    assert thin == [], f"mappings with no usable rationale: {thin}"


def test_a_technique_may_map_to_several_obligations():
    """The inverse guard. One finding can bear on a testing duty and a logging duty at
    once, and a crosswalk that quietly became one-to-one would drop the second every
    time without anything failing."""
    widths = [len(e.get("obligations", [])) for e in _crosswalk().values()]
    assert widths and max(widths) > 1, \
        "every technique maps to at most one obligation, which means somebody made " \
        "this a lookup rather than a crosswalk"
