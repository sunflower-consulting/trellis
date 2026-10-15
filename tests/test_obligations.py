"""The obligation catalogue's own guards.

These are mostly about honesty rather than correctness, because correctness against a
legal text is not something a test can assert. What a test CAN assert is that every
record says where it was read from, when, and what kind of evidence could ever satisfy
it -- so that a reader who wants to check is never stopped by us.
"""
import json
import re
from datetime import date
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schema" / "obligation.schema.json").read_text())
INSTRUMENTS = set(SCHEMA["properties"]["instrument"]["enum"])


def _records():
    out = []
    for p in sorted((ROOT / "obligations").rglob("*.yaml")):
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        if doc:
            out.append((p, doc))
    return out


def test_there_are_obligations_at_all():
    """The alarm for a loader that silently reads nothing, which every other test in
    this file would pass vacuously."""
    assert _records(), "no obligation records found"


def test_every_record_matches_the_schema():
    jsonschema = pytest.importorskip("jsonschema")
    v = jsonschema.Draft202012Validator(SCHEMA)
    bad = []
    for p, doc in _records():
        for e in v.iter_errors(doc):
            bad.append(f"{p.name}: {'/'.join(str(x) for x in e.path) or '<root>'}: {e.message}")
    assert bad == [], "\n".join(bad)


def test_every_id_parses_as_instrument_and_citation():
    """`instrument:citation`, so a report can print the id and a reader needs no key,
    and a renderer can group by instrument with one split and no join."""
    for p, d in _records():
        assert ":" in d["id"], f"{p.name}: {d['id']} has no instrument prefix"
        inst, _, cite = d["id"].partition(":")
        assert inst in INSTRUMENTS, f"{p.name}: unknown instrument {inst}"
        assert inst == d["instrument"], f"{p.name}: id prefix and instrument disagree"
        assert cite == d["citation"], f"{p.name}: id citation and citation field disagree"


def test_no_two_records_share_an_id():
    seen = {}
    for p, d in _records():
        assert d["id"] not in seen, f"{p.name} and {seen[d['id']].name} share {d['id']}"
        seen[d["id"]] = p


def test_the_file_name_is_derivable_from_the_id():
    """Ids contain characters a filename should not, so the two cannot be equal the way
    a corpus case id equals its filename. They still have to be mechanically related,
    or a record becomes findable only by reading every file."""
    for p, d in _records():
        slug = re.sub(r"[^a-z0-9]+", "-", d["citation"].lower()).strip("-")
        assert p.stem == slug, f"{p.name}: expected {slug}.yaml for {d['id']}"
        assert p.parent.name == d["instrument"], \
            f"{p.name}: filed under {p.parent.name}, instrument says {d['instrument']}"


# --- the honesty fields ----------------------------------------------------------

def test_a_review_obligation_says_what_would_satisfy_it():
    """`review` means no probe could ever establish it. Without naming what a reviewer
    must produce instead, that classification is an excuse rather than a handover."""
    thin = [d["id"] for _p, d in _records()
            if d["verifiable"] in ("review", "hybrid")
            and len(d.get("evidence_expected", "").strip()) < 40]
    assert thin == [], f"review/hybrid obligations with no usable evidence_expected: {thin}"


def test_every_record_says_where_it_was_read_and_when():
    """A claim about a moving target with no indication of when it was true is not
    checkable, and these dates have moved once already."""
    today = date.today().isoformat()
    for p, d in _records():
        assert d["source_url"].startswith("http"), f"{p.name}: no source_url"
        assert d["last_checked"] <= today, f"{p.name}: last_checked is in the future"


#: Where an official text of each instrument can be read. EUR-Lex is the obvious one
#: and is not the only one: the Commission's own AI Act Service Desk publishes the
#: consolidated text and was reachable when EUR-Lex was serving bot challenges, and
#: Lovdata is the official source for Norwegian law. ISO has no free official text at
#: all, which is why it is absent here and why its records cannot be confirmed.
OFFICIAL = {
    "ai-act": ("eur-lex.europa.eu", "ec.europa.eu", "publications.europa.eu"),
    "dora": ("eur-lex.europa.eu", "publications.europa.eu"),
    "cra": ("eur-lex.europa.eu", "publications.europa.eu"),
    "digitalsikkerhetsloven": ("lovdata.no", "regjeringen.no"),
    "iso-42001": (),
}


def test_a_record_not_read_from_an_official_source_says_so():
    """The rule the domain list was reaching for, stated directly.

    A citation a client's counsel can check without asking us is the whole point, and
    the check that matters is not WHICH official domain but whether the record claims
    to be confirmed when it was read off somebody's blog. ISO/IEC 42001 has no free
    official text, so its records can never be `source-confirmed` and the dataset
    should say that rather than quietly implying otherwise.
    """
    for p, d in _records():
        official = OFFICIAL[d["instrument"]]
        from_official = any(dom in d["source_url"] for dom in official)
        if not from_official:
            assert d.get("verification") == "unconfirmed", (
                f"{p.name}: cites {d['source_url']}, which is not an official source "
                f"for {d['instrument']}, but claims to be source-confirmed")


def test_an_unconfirmed_record_is_visible_rather_than_dropped():
    """Publishable, and never silent. A record we could not confirm is more useful than
    a gap -- but only if it says so, because the alternative is a reader assuming every
    row was checked."""
    for _p, d in _records():
        assert d.get("verification") in ("source-confirmed", "unconfirmed"), \
            f"{d['id']}: no verification state"


def test_the_review_only_share_has_not_quietly_collapsed():
    """The pressure on this dataset is commercial, and it runs one way: a page of
    "review only, not tested" rows looks thin beside a competitor's green matrix, and
    the cheapest way to improve the look is to reclassify.

    Pinned per instrument so a bulk move fails here and has to be argued for in the
    commit that changes the number. If a reclassification is right, change this count
    and say why in the message.
    """
    counts = {}
    for _p, d in _records():
        if d["verifiable"] == "review":
            counts[d["instrument"]] = counts.get(d["instrument"], 0) + 1
    recorded = yaml.safe_load((ROOT / "tests" / "review-counts.yaml").read_text())
    assert counts == recorded, (
        f"the review-only share changed.\n  now:      {counts}\n  recorded: {recorded}\n"
        "Reclassifying an obligation as testable is a claim about evidence, not a "
        "tidy-up. Update tests/review-counts.yaml in the commit that argues for it.")


# --- lifecycle --------------------------------------------------------------------

def test_an_obligation_is_superseded_never_deleted():
    """A report citing `ai-act:Art.15(4)` has to stay explainable after the provision
    changes. Same argument the corpus makes for retiring a case rather than deleting
    it: an id that vanished explains nothing."""
    ids = {d["id"] for _p, d in _records()}
    for _p, d in _records():
        if d["status"] == "superseded":
            assert d["superseded_by"] in ids, \
                f"{d['id']} is superseded by {d['superseded_by']}, which is not here"
        if d["status"] == "withdrawn":
            assert d.get("status_reason"), f"{d['id']} is withdrawn with no reason"


def test_every_system_class_is_one_the_tier_rules_can_produce():
    """`obligations/` and `tier/` join on this vocabulary. If they drift, an inventory
    gets classified into a class no obligation is keyed to, and the report renders an
    empty mapping for a system that is squarely in scope."""
    tier = yaml.safe_load((ROOT / "tier" / "ai-act.yaml").read_text())
    produced = set(tier.get("classes", {})) | {"all"}
    used = {c for _p, d in _records() for c in d["system_class"]}
    assert used <= produced, f"classes no tier rule can produce: {sorted(used - produced)}"
