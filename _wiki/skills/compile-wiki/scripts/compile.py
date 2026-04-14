#!/usr/bin/env python3
"""
Agentics Wiki v1 Compile Pipeline
==================================
Reads the vault, extracts structured data, and emits machine-facing cache artifacts.

Usage:
    python _wiki/compile.py [--vault-root <path>] [--verbose]

Outputs (under _wiki/cache/):
    pages.json            - normalized page index
    claims.jsonl          - all extracted claims
    relations.jsonl       - all extracted relations
    agent-digest.json     - high-signal agent context
    contradictions.json   - contradiction registry
    questions.json        - open question registry
    decisions.json        - decision registry
    timeline-events.json  - chronological event index
    source-index.json     - source metadata registry

Outputs (under _wiki/indexes/):
    alias-index.json      - alias -> page id map
    tag-index.json        - tag -> page ids map
    id-to-path.json       - page id -> path map
    path-to-id.json       - path -> page id map
    pagetype-index.json   - pageType -> page ids map

Reports (under reports/):
    open-questions.md
    contradictions.md
    low-confidence.md
    claim-health.md
    stale-pages.md
    orphaned-claims.md
    evidence-gaps.md
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml --break-system-packages")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SKIP_DIRS = {".obsidian", "_wiki", "_archive", "_inbox", "_attachments", "_views"}
SKIP_FILES = {"AGENTS.md", "WIKI.md", "INBOX.md", "INITIALIZE.md", "AGENT-WIKI-SPEC-v1.md"}
CACHE_DIR = "_wiki/cache"
INDEX_DIR = "_wiki/indexes"
LOG_DIR = "_wiki/logs"
REPORTS_DIR = "reports"

STALE_DAYS = 90  # pages not updated in this many days are flagged
LOW_CONFIDENCE_THRESHOLD = 0.50

# Agent digest limits — named constants so they are easy to tune as the vault grows.
# Increase if high-value pages are being silently truncated.
MAX_DIGEST_KEY_PAGES = 50        # max entity/concept pages included in agent digest
MAX_DIGEST_CLAIMS = 30           # max top supported claims included in agent digest
MAX_DIGEST_DECISIONS = 20        # max recent decision pages included in agent digest
MAX_DIGEST_QUESTIONS = 20        # max open question pages included in agent digest
MAX_DIGEST_CONTRADICTIONS = 10   # max open contradictions included in agent digest

VALID_PAGE_TYPES = {"source", "entity", "concept", "synthesis", "procedure", "question", "decision", "report", "claim"}
VALID_CLAIM_STATUSES = {"supported", "weakly_supported", "inferred", "unverified", "contested", "contradicted", "deprecated"}
VALID_CLAIM_TYPES = {"descriptive", "historical", "causal", "interpretive", "normative", "forecast"}
VALID_EVIDENCE_RELATIONS = {"supports", "weakens", "contradicts", "context_only"}
VALID_EVIDENCE_KINDS = {"quote", "summary", "measurement", "observation", "screenshot", "transcript", "inference"}
VALID_QUESTION_STATUSES = {"open", "researching", "blocked", "resolved", "dropped"}
VALID_DECISION_STATUSES = {"proposed", "accepted", "superseded", "rejected"}


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from a markdown file. Returns (meta, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].strip()
    try:
        meta = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, body


# ---------------------------------------------------------------------------
# Vault walker
# ---------------------------------------------------------------------------

def walk_vault(vault_root: Path, verbose: bool = False) -> list[dict]:
    """Walk vault, parse all markdown pages, return list of page records."""
    pages = []
    for md_file in sorted(vault_root.rglob("*.md")):
        rel = md_file.relative_to(vault_root)
        parts = rel.parts

        # Skip files in excluded dirs
        if any(p in SKIP_DIRS for p in parts):
            continue
        # Skip root-level excluded files
        if len(parts) == 1 and parts[0] in SKIP_FILES:
            continue

        text = md_file.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(text)

        if not meta:
            if verbose:
                print(f"  [SKIP] No frontmatter: {rel}")
            continue

        page_id = meta.get("id", "")
        page_type = meta.get("pageType", "")

        if not page_id or not page_type:
            if verbose:
                print(f"  [SKIP] Missing id or pageType: {rel}")
            continue

        record = {
            "id": page_id,
            "pageType": page_type,
            "title": meta.get("title", str(rel.stem)),
            "path": str(rel).replace("\\", "/"),
            "status": meta.get("status", ""),
            "createdAt": str(meta.get("createdAt", "")),
            "updatedAt": str(meta.get("updatedAt", "")),
            "aliases": meta.get("aliases") or [],
            "tags": meta.get("tags") or [],
            "meta": meta,
            "body": body,
        }

        # Type-specific enrichment
        if page_type == "entity":
            record["entityType"] = meta.get("entityType", "")
            record["canonicalName"] = meta.get("canonicalName", "")
        elif page_type == "concept":
            record["conceptType"] = meta.get("conceptType", "")
        elif page_type == "source":
            record["sourceType"] = meta.get("sourceType", "")
            record["originUrl"] = meta.get("originUrl", "")
            record["publishedAt"] = str(meta.get("publishedAt", ""))
            record["retrievedAt"] = str(meta.get("retrievedAt", ""))
        elif page_type == "synthesis":
            record["synthesisType"] = meta.get("synthesisType", "")
            record["scope"] = meta.get("scope", "")
        elif page_type == "question":
            record["priority"] = meta.get("priority", "")
            record["openedAt"] = str(meta.get("openedAt", ""))
        elif page_type == "decision":
            record["decisionType"] = meta.get("decisionType", "")
            record["decidedAt"] = str(meta.get("decidedAt", ""))
            record["summary"] = meta.get("summary", "")
        elif page_type == "claim":
            record["claimType"] = meta.get("claimType", "")
            record["claimStatus"] = meta.get("claimStatus", meta.get("status", ""))
            record["confidence"] = meta.get("confidence", None)
            record["text"] = meta.get("text", "")
            record["subjectPageId"] = meta.get("subjectPageId", "")
            record["sourceIds"] = meta.get("sourceIds") or []

        # Counts
        claims = meta.get("claims") or []
        relations = meta.get("relations") or []
        timeline = meta.get("timeline") or []
        record["claimCount"] = len(claims)
        record["relationCount"] = len(relations)
        record["timelineCount"] = len(timeline)

        pages.append(record)

        if verbose:
            print(f"  [PAGE] {page_id} ({page_type}) — {rel}")

    return pages


# ---------------------------------------------------------------------------
# Claim extraction
# ---------------------------------------------------------------------------

def extract_claims(pages: list[dict]) -> list[dict]:
    """Extract all claims from page metadata (embedded and standalone)."""
    all_claims = []
    for page in pages:
        # Standalone claim pages
        if page["pageType"] == "claim":
            record = {
                "id": page["id"],
                "text": page["meta"].get("text", page["title"]),
                "status": page["meta"].get("claimStatus", page["meta"].get("status", "")),
                "confidence": page["meta"].get("confidence"),
                "claimType": page["meta"].get("claimType", ""),
                "evidence": page["meta"].get("evidence") or [],
                "_owningPageId": page["meta"].get("subjectPageId", ""),
                "_owningPagePath": page["path"],
                "_owningPageType": "claim",
                "_standaloneClaimPage": True,
            }
            all_claims.append(record)
            continue
        # Embedded claims in frontmatter
        raw_claims = page["meta"].get("claims") or []
        for claim in raw_claims:
            if not isinstance(claim, dict):
                continue
            record = dict(claim)
            record["_owningPageId"] = page["id"]
            record["_owningPagePath"] = page["path"]
            record["_owningPageType"] = page["pageType"]
            record["_standaloneClaimPage"] = False
            all_claims.append(record)
    return all_claims


# ---------------------------------------------------------------------------
# Relation extraction
# ---------------------------------------------------------------------------

def extract_relations(pages: list[dict]) -> list[dict]:
    """Extract all relations from page metadata."""
    all_relations = []
    for page in pages:
        raw_relations = page["meta"].get("relations") or []
        for rel in raw_relations:
            if not isinstance(rel, dict):
                continue
            record = dict(rel)
            record["_owningPageId"] = page["id"]
            record["_owningPagePath"] = page["path"]
            all_relations.append(record)
    return all_relations


# ---------------------------------------------------------------------------
# Timeline extraction
# ---------------------------------------------------------------------------

def extract_timeline_events(pages: list[dict]) -> list[dict]:
    """Extract all timeline entries from page metadata."""
    all_events = []
    for page in pages:
        raw_events = page["meta"].get("timeline") or []
        for ev in raw_events:
            if not isinstance(ev, dict):
                continue
            record = dict(ev)
            record["_owningPageId"] = page["id"]
            record["_owningPagePath"] = page["path"]
            all_events.append(record)
    # Sort by date
    def sort_key(e):
        d = str(e.get("date", ""))
        return d
    all_events.sort(key=sort_key)
    return all_events


# ---------------------------------------------------------------------------
# Contradiction detection
# ---------------------------------------------------------------------------

def detect_contradictions(claims: list[dict]) -> list[dict]:
    """Surface contradictions from evidence relations and claim status."""
    contradictions = []
    seen_ids = set()
    ctr = 1

    # Claims with status=contradicted
    for claim in claims:
        if claim.get("status") == "contradicted":
            cid = f"contradiction.auto.claim-status.{ctr:03d}"
            ctr += 1
            contradictions.append({
                "id": cid,
                "type": "direct_conflict",
                "status": "open",
                "summary": f"Claim '{claim.get('id', '')}' has status 'contradicted'.",
                "claimIds": [claim.get("id", "")],
                "sourceIds": [],
                "resolution": None,
                "updatedAt": datetime.now().strftime("%Y-%m-%d"),
            })

    # Claims with contradicting evidence
    for claim in claims:
        evidence_list = claim.get("evidence") or []
        for ev in evidence_list:
            if not isinstance(ev, dict):
                continue
            if ev.get("relation") == "contradicts":
                key = (claim.get("id", ""), ev.get("sourceId", ""))
                if key in seen_ids:
                    continue
                seen_ids.add(key)
                cid = f"contradiction.auto.evidence.{ctr:03d}"
                ctr += 1
                contradictions.append({
                    "id": cid,
                    "type": "direct_conflict",
                    "status": "open",
                    "summary": f"Evidence '{ev.get('id', '')}' contradicts claim '{claim.get('id', '')}'.",
                    "claimIds": [claim.get("id", "")],
                    "sourceIds": [ev.get("sourceId", "")],
                    "resolution": None,
                    "updatedAt": datetime.now().strftime("%Y-%m-%d"),
                })

    return contradictions


# ---------------------------------------------------------------------------
# Semantic contradiction detection
# ---------------------------------------------------------------------------

def detect_semantic_contradictions(claims: list[dict]) -> list[dict]:
    """Detect cross-claim semantic conflicts between claims sharing a subject.

    Operates on structured fields only — no natural-language text comparison.

    Detects:
    - date_conflict: two+ historical claims on the same subject with different
      'date' values, both in an active (non-deprecated) status.
    - scope_conflict: contested claims coexisting with supported claims on the
      same subject, indicating active disagreement.
    """
    contradictions = []
    ctr = 1

    # Group claims by subjectPageId, falling back to owning page id
    by_subject: dict[str, list[dict]] = {}
    for claim in claims:
        subject = claim.get("subjectPageId") or claim.get("_owningPageId", "")
        if not subject:
            continue
        by_subject.setdefault(subject, []).append(claim)

    for subject_id, group in by_subject.items():
        # Exclude already-flagged or inactive claims from semantic analysis
        active = [
            c for c in group
            if c.get("status") not in ("deprecated", "contradicted")
        ]
        if len(active) < 2:
            continue

        # --- Date conflict ---
        # Historical claims on the same subject that have a 'date' field and
        # whose dates differ.
        dated_historical = [
            c for c in active
            if c.get("claimType") == "historical" and c.get("date")
        ]
        if len(dated_historical) >= 2:
            dates_seen: dict[str, list[dict]] = {}
            for c in dated_historical:
                d = str(c["date"])
                dates_seen.setdefault(d, []).append(c)
            if len(dates_seen) > 1:
                all_ids = [c.get("id", "") for c in dated_historical]
                cid = f"contradiction.semantic.date.{ctr:03d}"
                ctr += 1
                contradictions.append({
                    "id": cid,
                    "type": "date_conflict",
                    "status": "open",
                    "summary": (
                        f"Subject '{subject_id}' has {len(dates_seen)} conflicting historical "
                        f"dates: {sorted(dates_seen.keys())}."
                    ),
                    "claimIds": all_ids,
                    "sourceIds": [],
                    "resolution": None,
                    "updatedAt": datetime.now().strftime("%Y-%m-%d"),
                })

        # --- Scope conflict ---
        # Contested claims coexisting with supported claims on the same subject.
        contested = [c for c in active if c.get("status") == "contested"]
        supported = [
            c for c in active
            if c.get("status") in ("supported", "weakly_supported")
        ]
        if contested and supported:
            conflict_ids = [c.get("id", "") for c in contested + supported]
            cid = f"contradiction.semantic.scope.{ctr:03d}"
            ctr += 1
            contradictions.append({
                "id": cid,
                "type": "scope_conflict",
                "status": "open",
                "summary": (
                    f"Subject '{subject_id}' has {len(contested)} contested and "
                    f"{len(supported)} supported claim(s) in potential conflict."
                ),
                "claimIds": conflict_ids,
                "sourceIds": [],
                "resolution": None,
                "updatedAt": datetime.now().strftime("%Y-%m-%d"),
            })

    return contradictions


# ---------------------------------------------------------------------------
# Health analysis
# ---------------------------------------------------------------------------

def analyze_health(pages: list[dict], claims: list[dict]) -> dict:
    """Compute health signals across the vault."""
    today = date.today()

    low_confidence_claims = []
    evidence_gap_claims = []
    stale_pages = []
    orphaned_claims = []  # claims whose owning page is missing (edge case)

    page_ids = {p["id"] for p in pages}

    for claim in claims:
        conf = claim.get("confidence")
        status = claim.get("status", "")
        evidence = claim.get("evidence") or []

        # Low confidence
        if conf is not None:
            try:
                if float(conf) < LOW_CONFIDENCE_THRESHOLD:
                    low_confidence_claims.append(claim)
            except (ValueError, TypeError):
                pass
        if status in ("weakly_supported", "unverified", "contested"):
            if claim not in low_confidence_claims:
                low_confidence_claims.append(claim)

        # Evidence gaps
        real_evidence = [e for e in evidence if isinstance(e, dict) and e.get("relation") != "context_only"]
        if not real_evidence:
            evidence_gap_claims.append(claim)

        # Orphaned claims (owning page missing)
        if claim.get("_owningPageId") and claim["_owningPageId"] not in page_ids:
            orphaned_claims.append(claim)

    for page in pages:
        updated = page.get("updatedAt", "")
        if updated:
            try:
                updated_date = date.fromisoformat(str(updated))
                if (today - updated_date).days > STALE_DAYS:
                    stale_pages.append(page)
            except ValueError:
                pass

    return {
        "low_confidence_claims": low_confidence_claims,
        "evidence_gap_claims": evidence_gap_claims,
        "stale_pages": stale_pages,
        "orphaned_claims": orphaned_claims,
    }


# ---------------------------------------------------------------------------
# Agent digest
# ---------------------------------------------------------------------------

def build_agent_digest(pages: list[dict], claims: list[dict], relations: list[dict],
                       contradictions: list[dict], health: dict, compiled_at: str) -> dict:
    """Build the high-signal agent context digest."""

    def summarize_page(p: dict) -> dict:
        return {
            "id": p["id"],
            "pageType": p["pageType"],
            "title": p["title"],
            "path": p["path"],
            "status": p["status"],
            "updatedAt": p["updatedAt"],
            "summary": p["meta"].get("summary", ""),
            "claimCount": p["claimCount"],
            "relationCount": p["relationCount"],
        }

    # Entities and concepts — high-value pages for grounding
    key_pages = [p for p in pages if p["pageType"] in ("entity", "concept")]
    key_pages_summary = [summarize_page(p) for p in key_pages[:MAX_DIGEST_KEY_PAGES]]

    # Recent decisions
    decisions = [p for p in pages if p["pageType"] == "decision"]
    decisions_summary = [summarize_page(p) for p in decisions[:MAX_DIGEST_DECISIONS]]

    # Open questions
    open_questions = [p for p in pages if p["pageType"] == "question" and p["status"] in ("open", "researching", "blocked")]
    questions_summary = [summarize_page(p) for p in open_questions[:MAX_DIGEST_QUESTIONS]]

    # Top supported claims
    top_claims = sorted(
        [c for c in claims if c.get("status") == "supported" and c.get("confidence") is not None],
        key=lambda c: float(c.get("confidence", 0)),
        reverse=True,
    )[:MAX_DIGEST_CLAIMS]
    top_claims_summary = [
        {"id": c.get("id"), "text": c.get("text"), "confidence": c.get("confidence"),
         "owningPage": c.get("_owningPageId")}
        for c in top_claims
    ]

    # Notable contradictions
    open_contradictions = [c for c in contradictions if c.get("status") == "open"][:MAX_DIGEST_CONTRADICTIONS]

    return {
        "compiledAt": compiled_at,
        "specVersion": "v1",
        "vaultStats": {
            "totalPages": len(pages),
            "totalClaims": len(claims),
            "totalRelations": len(relations),
            "totalContradictions": len(contradictions),
            "openQuestions": len(open_questions),
            "lowConfidenceClaims": len(health["low_confidence_claims"]),
            "evidenceGapClaims": len(health["evidence_gap_claims"]),
            "stalePages": len(health["stale_pages"]),
        },
        "keyPages": key_pages_summary,
        "recentDecisions": decisions_summary,
        "openQuestions": questions_summary,
        "topClaims": top_claims_summary,
        "openContradictions": open_contradictions,
    }


# ---------------------------------------------------------------------------
# Index builders
# ---------------------------------------------------------------------------

def build_indexes(pages: list[dict]) -> dict:
    alias_index = {}
    tag_index = {}
    id_to_path = {}
    path_to_id = {}
    pagetype_index = {}

    for p in pages:
        pid = p["id"]
        path = p["path"]

        id_to_path[pid] = path
        path_to_id[path] = pid

        pt = p["pageType"]
        pagetype_index.setdefault(pt, []).append(pid)

        for alias in (p["aliases"] or []):
            alias_index[str(alias)] = pid

        for tag in (p["tags"] or []):
            tag_index.setdefault(str(tag), []).append(pid)

    return {
        "alias-index": alias_index,
        "tag-index": tag_index,
        "id-to-path": id_to_path,
        "path-to-id": path_to_id,
        "pagetype-index": pagetype_index,
    }


# ---------------------------------------------------------------------------
# Report generators
# ---------------------------------------------------------------------------

def make_report_header(title: str, compiled_at: str) -> str:
    return f"""---
pageType: report
title: {title}
compiledAt: {compiled_at}
---

# {title}

> Generated by compile pipeline on {compiled_at}. Do not edit manually.

"""


def generate_open_questions_report(pages: list[dict], compiled_at: str) -> str:
    questions = [p for p in pages if p["pageType"] == "question"]
    active = [q for q in questions if q["status"] in ("open", "researching", "blocked")]
    resolved = [q for q in questions if q["status"] == "resolved"]
    dropped = [q for q in questions if q["status"] == "dropped"]

    out = make_report_header("Open Questions", compiled_at)
    out += f"**{len(active)}** open / **{len(resolved)}** resolved / **{len(dropped)}** dropped\n\n"

    if active:
        out += "## Active\n\n"
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "": 4}
        active_sorted = sorted(active, key=lambda q: priority_order.get(q.get("meta", {}).get("priority", ""), 4))
        for q in active_sorted:
            priority = q.get("meta", {}).get("priority", "—")
            out += f"- **[{q['status'].upper()}]** [{q['title']}]({q['path']}) — priority: `{priority}`\n"
        out += "\n"

    if resolved:
        out += "## Resolved\n\n"
        for q in resolved:
            out += f"- [{q['title']}]({q['path']})\n"
        out += "\n"

    if not active and not resolved:
        out += "_No questions recorded yet._\n"

    return out


def generate_contradictions_report(contradictions: list[dict], compiled_at: str) -> str:
    out = make_report_header("Contradictions", compiled_at)
    open_c = [c for c in contradictions if c.get("status") == "open"]
    resolved_c = [c for c in contradictions if c.get("status") == "resolved"]

    out += f"**{len(open_c)}** open / **{len(resolved_c)}** resolved\n\n"

    if open_c:
        out += "## Open Contradictions\n\n"
        for c in open_c:
            out += f"- `{c['id']}` — {c.get('summary', '')}\n"
            claim_ids = c.get("claimIds", [])
            if claim_ids:
                out += f"  - Claims: {', '.join(f'`{cid}`' for cid in claim_ids)}\n"
        out += "\n"

    if not open_c:
        out += "_No open contradictions detected._\n"

    return out


def generate_low_confidence_report(health: dict, compiled_at: str) -> str:
    out = make_report_header("Low Confidence Claims", compiled_at)
    low = health["low_confidence_claims"]
    out += f"**{len(low)}** low-confidence claims (confidence < {LOW_CONFIDENCE_THRESHOLD} or status unverified/weakly_supported/contested)\n\n"

    if low:
        out += "## Claims\n\n"
        sorted_low = sorted(low, key=lambda c: float(c.get("confidence", 0) or 0))
        for c in sorted_low:
            conf = c.get("confidence", "—")
            status = c.get("status", "—")
            page = c.get("_owningPageId", "—")
            out += f"- `{c.get('id', '?')}` — conf: `{conf}`, status: `{status}`, page: `{page}`\n"
            out += f"  - {c.get('text', '')}\n"
        out += "\n"
    else:
        out += "_No low-confidence claims detected._\n"

    return out


def generate_claim_health_report(health: dict, compiled_at: str, total_claims: int) -> str:
    out = make_report_header("Claim Health", compiled_at)
    gaps = health["evidence_gap_claims"]
    low = health["low_confidence_claims"]

    out += f"**{total_claims}** total claims | **{len(gaps)}** evidence gaps | **{len(low)}** low-confidence\n\n"

    if gaps:
        out += "## Evidence Gaps\n\n"
        out += "_Claims with no direct supporting evidence:_\n\n"
        for c in gaps:
            page = c.get("_owningPageId", "—")
            out += f"- `{c.get('id', '?')}` (page: `{page}`) — {c.get('text', '')}\n"
        out += "\n"
    else:
        out += "## Evidence Gaps\n\n_No evidence gaps detected._\n\n"

    return out


def generate_stale_pages_report(health: dict, compiled_at: str) -> str:
    out = make_report_header("Stale Pages", compiled_at)
    stale = health["stale_pages"]
    out += f"**{len(stale)}** pages not updated in more than {STALE_DAYS} days\n\n"

    if stale:
        out += "## Stale Pages\n\n"
        sorted_stale = sorted(stale, key=lambda p: p.get("updatedAt", ""))
        for p in sorted_stale:
            out += f"- [{p['title']}]({p['path']}) — last updated: `{p['updatedAt']}`\n"
        out += "\n"
    else:
        out += "_No stale pages detected._\n"

    return out


def generate_orphaned_claims_report(health: dict, compiled_at: str) -> str:
    out = make_report_header("Orphaned Claims", compiled_at)
    orphaned = health["orphaned_claims"]
    out += f"**{len(orphaned)}** claims whose owning page ID was not found in the vault\n\n"

    if orphaned:
        out += "## Orphaned Claims\n\n"
        for c in orphaned:
            out += f"- `{c.get('id', '?')}` — owning page: `{c.get('_owningPageId', '?')}`\n"
        out += "\n"
    else:
        out += "_No orphaned claims detected._\n"

    return out


def generate_evidence_gaps_report(health: dict, compiled_at: str) -> str:
    out = make_report_header("Evidence Gaps", compiled_at)
    gaps = health["evidence_gap_claims"]
    out += f"**{len(gaps)}** claims with no direct evidence\n\n"

    if gaps:
        out += "## Claims Without Direct Evidence\n\n"
        for c in gaps:
            page = c.get("_owningPageId", "—")
            out += f"- `{c.get('id', '?')}` (page: `{page}`)\n"
            out += f"  - {c.get('text', '')}\n"
        out += "\n"
    else:
        out += "_All claims have at least one direct evidence entry._\n"

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Agentics Wiki v1 Compile Pipeline")
    parser.add_argument("--vault-root", default=".", help="Path to vault root (default: current directory)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    compiled_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    compiled_date = datetime.now().strftime("%Y-%m-%d")

    print(f"Agentics Wiki v1 Compile Pipeline")
    print(f"Vault root: {vault_root}")
    print(f"Compiled at: {compiled_at}")
    print()

    # Ensure output dirs exist
    cache_dir = vault_root / CACHE_DIR
    index_dir = vault_root / INDEX_DIR
    log_dir = vault_root / LOG_DIR
    reports_dir = vault_root / REPORTS_DIR

    for d in [cache_dir, index_dir, log_dir, reports_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # --- Walk vault ---
    print("Reading vault pages...")
    pages = walk_vault(vault_root, verbose=args.verbose)
    print(f"  Found {len(pages)} pages with frontmatter")

    # Validate unique IDs
    id_counts = {}
    for p in pages:
        id_counts[p["id"]] = id_counts.get(p["id"], 0) + 1
    duplicate_ids = {k: v for k, v in id_counts.items() if v > 1}
    if duplicate_ids:
        print(f"  WARNING: Duplicate page IDs found: {list(duplicate_ids.keys())}")

    # --- Extract structured data ---
    print("Extracting claims...")
    claims = extract_claims(pages)
    print(f"  Found {len(claims)} claims")

    print("Extracting relations...")
    relations = extract_relations(pages)
    print(f"  Found {len(relations)} relations")

    print("Extracting timeline events...")
    timeline_events = extract_timeline_events(pages)
    print(f"  Found {len(timeline_events)} timeline events")

    print("Detecting contradictions...")
    contradictions = detect_contradictions(claims)
    semantic_contradictions = detect_semantic_contradictions(claims)
    contradictions.extend(semantic_contradictions)
    print(f"  Found {len(contradictions)} contradictions ({len(semantic_contradictions)} semantic)")

    print("Analyzing health...")
    health = analyze_health(pages, claims)
    print(f"  Low-confidence claims: {len(health['low_confidence_claims'])}")
    print(f"  Evidence gap claims: {len(health['evidence_gap_claims'])}")
    print(f"  Stale pages: {len(health['stale_pages'])}")

    # --- Build registries ---
    questions_registry = [
        {
            "id": p["id"],
            "title": p["title"],
            "path": p["path"],
            "status": p["status"],
            "priority": p["meta"].get("priority", ""),
            "openedAt": p["meta"].get("openedAt", ""),
            "updatedAt": p["updatedAt"],
            "relatedClaims": p["meta"].get("relatedClaims", []),
            "relatedPages": p["meta"].get("relatedPages", []),
        }
        for p in pages if p["pageType"] == "question"
    ]

    decisions_registry = [
        {
            "id": p["id"],
            "title": p["title"],
            "path": p["path"],
            "status": p["status"],
            "decisionType": p.get("decisionType", ""),
            "summary": p.get("summary", "") or p["meta"].get("summary", ""),
            "decidedAt": p.get("decidedAt", ""),
            "updatedAt": p["updatedAt"],
            "relatedPages": p["meta"].get("relatedPages", []),
        }
        for p in pages if p["pageType"] == "decision"
    ]

    source_index = [
        {
            "id": p["id"],
            "title": p["title"],
            "path": p["path"],
            "status": p["status"],
            "sourceType": p.get("sourceType", ""),
            "originUrl": p.get("originUrl", ""),
            "publishedAt": p.get("publishedAt", ""),
            "retrievedAt": p.get("retrievedAt", ""),
            "updatedAt": p["updatedAt"],
            "attachments": p["meta"].get("attachments", []),
        }
        for p in pages if p["pageType"] == "source"
    ]

    # --- Build agent digest ---
    print("Building agent digest...")
    agent_digest = build_agent_digest(pages, claims, relations, contradictions, health, compiled_at)

    # --- Build indexes ---
    print("Building indexes...")
    indexes = build_indexes(pages)

    # --- Write cache files ---
    print("\nWriting cache files...")

    # pages.json — strip raw meta/body to keep file clean
    pages_output = []
    for p in pages:
        po = {k: v for k, v in p.items() if k not in ("meta", "body")}
        pages_output.append(po)
    (cache_dir / "pages.json").write_text(
        json.dumps({"compiledAt": compiled_at, "pages": pages_output}, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"  Wrote pages.json ({len(pages_output)} pages)")

    # claims.jsonl
    with open(cache_dir / "claims.jsonl", "w", encoding="utf-8") as f:
        for c in claims:
            f.write(json.dumps(c, default=str) + "\n")
    print(f"  Wrote claims.jsonl ({len(claims)} claims)")

    # relations.jsonl
    with open(cache_dir / "relations.jsonl", "w", encoding="utf-8") as f:
        for r in relations:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"  Wrote relations.jsonl ({len(relations)} relations)")

    # agent-digest.json
    (cache_dir / "agent-digest.json").write_text(
        json.dumps(agent_digest, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"  Wrote agent-digest.json")

    # contradictions.json
    (cache_dir / "contradictions.json").write_text(
        json.dumps({"compiledAt": compiled_at, "contradictions": contradictions}, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"  Wrote contradictions.json ({len(contradictions)} entries)")

    # questions.json
    (cache_dir / "questions.json").write_text(
        json.dumps({"compiledAt": compiled_at, "questions": questions_registry}, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"  Wrote questions.json ({len(questions_registry)} entries)")

    # decisions.json
    (cache_dir / "decisions.json").write_text(
        json.dumps({"compiledAt": compiled_at, "decisions": decisions_registry}, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"  Wrote decisions.json ({len(decisions_registry)} entries)")

    # timeline-events.json
    (cache_dir / "timeline-events.json").write_text(
        json.dumps({"compiledAt": compiled_at, "events": timeline_events}, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"  Wrote timeline-events.json ({len(timeline_events)} events)")

    # source-index.json
    (cache_dir / "source-index.json").write_text(
        json.dumps({"compiledAt": compiled_at, "sources": source_index}, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"  Wrote source-index.json ({len(source_index)} sources)")

    # claims-index.json — standalone claim pages only
    claims_index = [
        {
            "id": p["id"],
            "title": p["title"],
            "path": p["path"],
            "claimStatus": p.get("claimStatus", p["status"]),
            "claimType": p.get("claimType", ""),
            "confidence": p.get("confidence"),
            "text": p.get("text", ""),
            "subjectPageId": p.get("subjectPageId", ""),
            "sourceIds": p.get("sourceIds") or [],
            "updatedAt": p["updatedAt"],
        }
        for p in pages if p["pageType"] == "claim"
    ]
    (cache_dir / "claims-index.json").write_text(
        json.dumps({"compiledAt": compiled_at, "claims": claims_index}, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"  Wrote claims-index.json ({len(claims_index)} standalone claims)")

    # --- Write indexes ---
    print("\nWriting indexes...")
    for name, data in indexes.items():
        path = index_dir / f"{name}.json"
        path.write_text(json.dumps({"compiledAt": compiled_at, "data": data}, indent=2, default=str), encoding="utf-8")
        print(f"  Wrote {name}.json")

    # --- Write reports ---
    print("\nWriting reports...")

    (reports_dir / "open-questions.md").write_text(
        generate_open_questions_report(pages, compiled_date), encoding="utf-8"
    )
    print(f"  Wrote reports/open-questions.md")

    (reports_dir / "contradictions.md").write_text(
        generate_contradictions_report(contradictions, compiled_date), encoding="utf-8"
    )
    print(f"  Wrote reports/contradictions.md")

    (reports_dir / "low-confidence.md").write_text(
        generate_low_confidence_report(health, compiled_date), encoding="utf-8"
    )
    print(f"  Wrote reports/low-confidence.md")

    (reports_dir / "claim-health.md").write_text(
        generate_claim_health_report(health, compiled_date, len(claims)), encoding="utf-8"
    )
    print(f"  Wrote reports/claim-health.md")

    (reports_dir / "stale-pages.md").write_text(
        generate_stale_pages_report(health, compiled_date), encoding="utf-8"
    )
    print(f"  Wrote reports/stale-pages.md")

    (reports_dir / "orphaned-claims.md").write_text(
        generate_orphaned_claims_report(health, compiled_date), encoding="utf-8"
    )
    print(f"  Wrote reports/orphaned-claims.md")

    (reports_dir / "evidence-gaps.md").write_text(
        generate_evidence_gaps_report(health, compiled_date), encoding="utf-8"
    )
    print(f"  Wrote reports/evidence-gaps.md")

    # --- Write compile log ---
    log_entry = {
        "compiledAt": compiled_at,
        "vaultRoot": str(vault_root),
        "stats": agent_digest["vaultStats"],
        "duplicateIds": duplicate_ids,
    }
    log_path = log_dir / f"compile-{compiled_date}.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, default=str) + "\n")
    print(f"\nWrote compile log: {log_path.name}")

    print(f"\n✓ Compile complete.")
    print(f"  Pages: {len(pages)} | Claims: {len(claims)} | Relations: {len(relations)} | Contradictions: {len(contradictions)}")
    print(f"  Open questions: {len([p for p in pages if p['pageType']=='question' and p['status'] in ('open','researching','blocked')])}")
    print(f"  Evidence gaps: {len(health['evidence_gap_claims'])} | Low confidence: {len(health['low_confidence_claims'])}")


if __name__ == "__main__":
    main()
