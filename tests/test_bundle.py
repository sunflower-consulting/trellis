"""The generated bundle, against the sources it was generated from.

Consumers vendor `dist/snapshot.yaml` and never read this repository's tree, so the
bundle IS the dataset as far as they are concerned. Two ways that goes wrong: the
bundle is stale, or somebody edits it directly because the sources were inconvenient.
Both show up here.
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

import bundle  # noqa: E402


def _dist():
    return yaml.safe_load((ROOT / "dist" / "snapshot.yaml").read_text(encoding="utf-8"))


def test_the_bundle_is_the_sources():
    """Both directions. A stale bundle ships last week's law; a hand-edited one ships
    something that is in no source file and cannot be reviewed as a diff of one."""
    built, shipped = bundle.build(), _dist()
    for section in ("obligations", "crosswalk", "taxonomy", "tier", "calendar", "unmapped"):
        assert built[section] == shipped.get(section), \
            f"dist/snapshot.yaml is out of date in '{section}': run bin/bundle.py"


def test_the_digest_covers_the_content():
    """A consumer pins this to assert it holds the bytes it thinks it holds. If the
    digest did not move with the content, the two vendored copies could drift while
    both claimed the same version."""
    shipped = _dist()
    rebuilt = bundle.build()
    assert shipped["body_sha256"] == rebuilt["body_sha256"]
    assert len(shipped["body_sha256"]) == 64


def test_the_digest_moves_when_the_content_does():
    """The mutation this file exists for: a digest that never changes is worse than
    none, because consumers trust it."""
    before = bundle.build()["body_sha256"]
    real = bundle._load_dir
    try:
        bundle._load_dir = lambda p: {**real(p), "ai-act:Art.99": {"id": "ai-act:Art.99"}}
        assert bundle.build()["body_sha256"] != before
    finally:
        bundle._load_dir = real
    assert bundle.build()["body_sha256"] == before


def test_the_bundle_records_the_revision_it_came_from():
    """And says so when the tree was dirty. A report whose provenance claims a clean
    revision when the files differed is worse than one that admits a working tree."""
    assert _dist()["generated_from"]


def test_the_schema_version_is_declared():
    """A consumer pinned to 1 should refuse a 2 rather than read half of it."""
    assert _dist()["schema_version"] == bundle.SCHEMA_VERSION
