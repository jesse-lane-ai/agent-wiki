#!/usr/bin/env python3
"""
Agentics Wiki v1 Compile Pipeline
==================================
Reads the vault, extracts structured data, and emits machine-facing cache artifacts.

Usage:
    python3 _system/skills/compile-wiki/scripts/compile.py [--vault-root <path>] [--verbose]

Outputs (under _system/cache/):
    pages.json            - normalized page index
    claims.jsonl          - all extracted claims
    relations.jsonl       - all extracted relations
    agent-digest.json     - high-signal agent context
    contradictions.json   - contradiction registry
    questions.json        - open question registry
    timeline-events.json  - chronological event index
    source-index.json     - source metadata registry

Outputs (under _system/indexes/):
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
import re
import subprocess
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SKIP_DIRS = {".obsidian", "_system", "_archive", "_inbox", "_attachments", "raw", "reports"}
SKIP_FILES = {"AGENTS.md", "WIKI.md", "INBOX.md", "ONBOARD.md", "AGENT-WIKI-SPEC-v1.md"}
CACHE_DIR = "_system/cache"
INDEX_DIR = "_system/indexes"
LOG_DIR = "_system/logs"
REPORTS_DIR = "reports"

STALE_DAYS = 90  # pages not updated in this many days are flagged
LOW_CONFIDENCE_THRESHOLD = 0.50
LARGE_SOURCE_TARGET_WORD_MIN = 8_000
LARGE_SOURCE_TARGET_WORD_MAX = 15_000
LARGE_SOURCE_HARD_WORD_MAX = 20_000
LARGE_SOURCE_PARTITION_WORD_THRESHOLD = 25_000

# Agent digest limits — named constants so they are easy to tune as the vault grows.
# Increase if high-value pages are being silently truncated.
MAX_DIGEST_KEY_PAGES = 50        # max entity/concept pages included in agent digest
MAX_DIGEST_CLAIMS = 30           # max top supported claims included in agent digest
MAX_DIGEST_QUESTIONS = 20        # max open question pages included in agent digest
MAX_DIGEST_CONTRADICTIONS = 10   # max open contradictions included in agent digest

VALID_PAGE_TYPES = {"source", "entity", "concept", "synthesis", "question", "report", "claim", "index", "overview"}
VALID_GENERAL_STATUSES = {"active", "draft", "archived", "deprecated"}
VALID_SOURCE_STATUSES = {"unprocessed", "partitioned", "processed", "archived"}
VALID_SOURCE_TYPES = {"webpage", "article", "document", "pdf", "transcript", "email", "meeting-notes", "dataset", "screenshot", "bridge", "import", "other"}
VALID_SOURCE_ROLES = {"whole", "parent", "part"}
VALID_ENTITY_TYPES = {"person", "organization", "project", "product", "system", "place", "event", "artifact", "document", "other"}
VALID_CONCEPT_TYPES = {
    "definition",
    "principle",
    "framework",
    "method",
    "policy",
    "standard",
    "pattern",
    "workflow",
    "runbook",
    "checklist",
    "playbook",
    "theory",
    "taxonomy",
    "other",
}
VALID_SYNTHESIS_TYPES = {"summary", "overview", "analysis", "timeline", "brief", "comparison"}
VALID_CLAIM_STATUSES = {"supported", "weakly_supported", "inferred", "unverified", "contested", "contradicted", "deprecated"}
VALID_CLAIM_TYPES = {"descriptive", "historical", "causal", "interpretive", "normative", "forecast"}
VALID_EVIDENCE_RELATIONS = {"supports", "weakens", "contradicts", "context_only"}
VALID_EVIDENCE_KINDS = {"quote", "summary", "measurement", "observation", "screenshot", "transcript", "inference"}
VALID_QUESTION_STATUSES = {"open", "researching", "blocked", "resolved", "dropped"}
VALID_QUESTION_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_RELATION_PREDICATES = {
    "is_a",
    "part_of",
    "depends_on",
    "uses",
    "produces",
    "founded_by",
    "owned_by",
    "located_in",
    "related_to",
    "supports",
    "contradicts",
    "mentions",
    "applies_to",
    "derived_from",
}
REQUIRED_UNIVERSAL_FIELDS = {"id", "pageType", "title", "status", "createdAt", "updatedAt", "aliases", "tags"}
FOLDER_PAGE_TYPES = {
    "sources": "source",
    "entities": "entity",
    "concepts": "concept",
    "claims": "claim",
    "syntheses": "synthesis",
    "questions": "question",
    "reports": "report",
}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

class FrontmatterParseError(ValueError):
    """Raised when markdown frontmatter is not valid for the supported YAML subset."""


def _line_indent(line: str) -> int:
    """Count leading spaces. Tabs are intentionally not accepted in frontmatter indentation."""
    if line.startswith("\t"):
        raise FrontmatterParseError("tabs are not supported for indentation")
    return len(line) - len(line.lstrip(" "))


def _strip_inline_comment(value: str) -> str:
    """Strip unquoted YAML comments from scalar values."""
    in_single = False
    in_double = False
    escaped = False
    for i, ch in enumerate(value):
        if ch == "\\" and in_double and not escaped:
            escaped = True
            continue
        if ch == "'" and not in_double and not escaped:
            in_single = not in_single
        elif ch == '"' and not in_single and not escaped:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if i == 0 or value[i - 1].isspace():
                return value[:i].rstrip()
        escaped = False
    return value.strip()


def _split_inline_items(value: str) -> list[str]:
    """Split a comma-separated inline YAML list while respecting simple quotes."""
    items = []
    buf = []
    in_single = False
    in_double = False
    escaped = False
    depth = 0
    for ch in value:
        if ch == "\\" and in_double and not escaped:
            escaped = True
            buf.append(ch)
            continue
        if ch == "'" and not in_double and not escaped:
            in_single = not in_single
        elif ch == '"' and not in_single and not escaped:
            in_double = not in_double
        elif not in_single and not in_double:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == "," and depth == 0:
                items.append("".join(buf).strip())
                buf = []
                escaped = False
                continue
        buf.append(ch)
        escaped = False
    final = "".join(buf).strip()
    if final:
        items.append(final)
    return items


def _parse_scalar(value: str) -> Any:
    """Parse a scalar from the supported YAML subset."""
    value = _strip_inline_comment(value)
    if value == "":
        return ""
    if value in ("[]",):
        return []
    if value in ("{}",):
        return {}
    if value[0:1] == "[" and value[-1:] == "]":
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item) for item in _split_inline_items(inner)]
    if value[0:1] == "{" and value[-1:] == "}":
        inner = value[1:-1].strip()
        result = {}
        if not inner:
            return result
        for item in _split_inline_items(inner):
            key, item_value = _split_key_value(item)
            result[key] = _parse_scalar(item_value)
        return result
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        quoted = value[1:-1]
        if value.startswith('"'):
            return bytes(quoted, "utf-8").decode("unicode_escape")
        return quoted.replace("''", "'")

    lower = value.lower()
    if lower in ("true", "false"):
        return lower == "true"
    if lower in ("null", "none", "~"):
        return None
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+)([eE][-+]?\d+)?", value) or re.fullmatch(r"[-+]?\d+[eE][-+]?\d+", value):
        try:
            return float(value)
        except ValueError:
            pass
    return value


def _split_key_value(text: str) -> tuple[str, str]:
    """Split `key: value` text on the first colon."""
    if ":" not in text:
        raise FrontmatterParseError(f"expected key/value pair, got {text!r}")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise FrontmatterParseError("empty mapping key")
    return key, value.strip()


def _looks_like_key_value(text: str) -> bool:
    """Return True when text has YAML's `key:` or `key: value` shape."""
    colon = text.find(":")
    return colon > 0 and (colon == len(text) - 1 or text[colon + 1].isspace())


def _prepare_yaml_lines(text: str) -> list[tuple[int, str]]:
    """Return non-empty, non-comment YAML lines as (indent, stripped_text)."""
    prepared = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = _line_indent(raw)
        prepared.append((indent, raw.strip()))
    return prepared


def _parse_block_scalar(lines: list[tuple[int, str]], index: int, parent_indent: int, folded: bool) -> tuple[str, int]:
    """Parse a literal (`|`) or folded (`>`) block scalar."""
    parts = []
    while index < len(lines):
        indent, text = lines[index]
        if indent <= parent_indent:
            break
        parts.append(" " * max(0, indent - parent_indent - 2) + text)
        index += 1
    if folded:
        return " ".join(part.strip() for part in parts).strip(), index
    return "\n".join(parts), index


def _parse_node(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    current_indent, text = lines[index]
    if current_indent < indent:
        return {}, index
    if current_indent != indent:
        raise FrontmatterParseError(f"unexpected indentation before {text!r}")
    if text.startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_map(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict, int]:
    result = {}
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise FrontmatterParseError(f"unexpected indentation before {text!r}")
        if text.startswith("- "):
            break

        key, value = _split_key_value(text)
        index += 1
        if value in ("|", ">"):
            result[key], index = _parse_block_scalar(lines, index, current_indent, folded=(value == ">"))
        elif value == "":
            if index < len(lines) and lines[index][0] > current_indent:
                result[key], index = _parse_node(lines, index, lines[index][0])
            else:
                result[key] = None
        else:
            result[key] = _parse_scalar(value)
    return result, index


def _parse_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list, int]:
    result = []
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent or not text.startswith("- "):
            break

        item_text = text[2:].strip()
        index += 1
        if item_text == "":
            if index < len(lines) and lines[index][0] > current_indent:
                item, index = _parse_node(lines, index, lines[index][0])
            else:
                item = None
        elif _looks_like_key_value(item_text) and not item_text.startswith(("'", '"')):
            key, value = _split_key_value(item_text)
            item = {}
            if value in ("|", ">"):
                item[key], index = _parse_block_scalar(lines, index, current_indent, folded=(value == ">"))
            elif value == "":
                if index < len(lines) and lines[index][0] > current_indent:
                    item[key], index = _parse_node(lines, index, lines[index][0])
                else:
                    item[key] = None
            else:
                item[key] = _parse_scalar(value)

            if index < len(lines) and lines[index][0] > current_indent:
                extra, index = _parse_map(lines, index, lines[index][0])
                item.update(extra)
        else:
            item = _parse_scalar(item_text)
        result.append(item)
    return result, index


def parse_frontmatter_yaml(fm_text: str) -> dict:
    """Parse the frontmatter subset used by the Agentics vault schema.

    This intentionally avoids external dependencies. It supports mappings,
    nested block lists, lists of mappings, inline lists/dicts, quoted strings,
    numbers, booleans, nulls, and literal/folded block scalars.
    """
    lines = _prepare_yaml_lines(fm_text)
    if not lines:
        return {}
    parsed, index = _parse_node(lines, 0, lines[0][0])
    if index != len(lines):
        raise FrontmatterParseError(f"could not parse line {index + 1}: {lines[index][1]!r}")
    if not isinstance(parsed, dict):
        raise FrontmatterParseError(f"frontmatter must be a mapping, got {type(parsed).__name__}")
    return parsed


def parse_frontmatter(text: str) -> tuple[dict, str, str | None]:
    """Extract YAML frontmatter from a markdown file. Returns (meta, body, error)."""
    if not text.startswith("---"):
        return {}, text, None
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text, "unterminated_frontmatter"
    fm_text = text[3:end].strip()
    body = text[end + 4:].strip()
    try:
        meta = parse_frontmatter_yaml(fm_text) or {}
    except FrontmatterParseError as exc:
        return {}, body, f"invalid_frontmatter: {exc}"
    if not isinstance(meta, dict):
        return {}, body, f"invalid_frontmatter: frontmatter must be a mapping, got {type(meta).__name__}"
    return meta, body, None


def coerce_float(value: Any) -> float | None:
    """Convert a value to float when possible, otherwise return None."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def add_validation_issue(issues: list[dict], issue_type: str, path: str, message: str, **details) -> None:
    """Record a validation problem and surface it during compile."""
    issue = {
        "type": issue_type,
        "path": path,
        "message": message,
        "details": details or {},
    }
    issues.append(issue)
    print(f"  WARNING: [{issue_type}] {path}: {message}")


def is_blank(value: Any) -> bool:
    """Return True when a required value is absent."""
    return value is None or value == ""


def is_yyyy_mm_dd(value: Any) -> bool:
    """Return True for YYYY-MM-DD strings that are real calendar dates."""
    text = str(value)
    if not DATE_PATTERN.fullmatch(text):
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def validate_required_fields(record: dict, fields: set[str], owner_path: str, issues: list[dict],
                             object_type: str, object_id: str = "") -> None:
    """Warn when required fields are missing or blank."""
    missing = [field for field in sorted(fields) if field not in record or is_blank(record.get(field))]
    if missing:
        add_validation_issue(
            issues,
            f"missing_{object_type}_fields",
            owner_path,
            f"{object_type.replace('_', ' ').title()} is missing required field(s): {', '.join(missing)}.",
            objectId=object_id,
            fields=missing,
        )


def validate_enum(value: Any, allowed: set[str], issue_type: str, owner_path: str, issues: list[dict],
                  field: str, object_id: str = "") -> None:
    """Warn when a non-empty enum value is outside its allowed set."""
    if is_blank(value):
        return
    if str(value) not in allowed:
        add_validation_issue(
            issues,
            issue_type,
            owner_path,
            f"Field `{field}` has unsupported value {value!r}.",
            objectId=object_id,
            field=field,
            value=value,
            allowed=sorted(allowed),
        )


def validate_number_range(value: Any, low: float, high: float, issue_type: str, owner_path: str,
                          issues: list[dict], field: str, object_id: str = "") -> float | None:
    """Warn when a numeric value is missing, non-numeric, or outside range."""
    numeric = coerce_float(value)
    if numeric is None:
        add_validation_issue(
            issues,
            issue_type,
            owner_path,
            f"Field `{field}` must be numeric.",
            objectId=object_id,
            field=field,
            value=value,
        )
        return None
    if numeric < low or numeric > high:
        add_validation_issue(
            issues,
            issue_type,
            owner_path,
            f"Field `{field}` must be between {low} and {high}.",
            objectId=object_id,
            field=field,
            value=value,
        )
    return numeric


def validate_date_field(value: Any, issue_type: str, owner_path: str, issues: list[dict],
                        field: str, object_id: str = "") -> None:
    """Warn when a non-empty date does not use YYYY-MM-DD."""
    if is_blank(value):
        return
    if not is_yyyy_mm_dd(value):
        add_validation_issue(
            issues,
            issue_type,
            owner_path,
            f"Field `{field}` must use YYYY-MM-DD.",
            objectId=object_id,
            field=field,
            value=value,
        )


def validate_array_field(value: Any, issue_type: str, owner_path: str, issues: list[dict],
                         field: str, object_id: str = "") -> None:
    """Warn when a field expected to be an array is not a list."""
    if not isinstance(value, list):
        add_validation_issue(
            issues,
            issue_type,
            owner_path,
            f"Field `{field}` must be an array.",
            objectId=object_id,
            field=field,
            valueType=type(value).__name__,
        )


def coerce_int(value: Any) -> int | None:
    """Convert a value to int when possible, otherwise return None."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def word_count(text: str) -> int:
    """Return a simple deterministic word count for source-size checks."""
    return len(re.findall(r"\b\w+\b", text))


def summarize_validation_issues(issues: list[dict]) -> dict[str, int]:
    """Return a simple count by validation issue type."""
    summary = {}
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        summary[issue_type] = summary.get(issue_type, 0) + 1
    return summary


def validate_evidence_record(evidence: Any, claim_id: str, owner_path: str, issues: list[dict], index: int) -> None:
    """Validate one evidence entry against required v1 fields."""
    if not isinstance(evidence, dict):
        add_validation_issue(
            issues,
            "invalid_evidence_record",
            owner_path,
            f"Evidence entry {index} on claim {claim_id or '(missing id)'} must be a mapping.",
            claimId=claim_id,
            index=index,
        )
        return

    evidence_id = str(evidence.get("id", "")).strip()
    validate_required_fields(
        evidence,
        {"id", "sourceId", "path", "kind", "relation", "weight", "updatedAt"},
        owner_path,
        issues,
        "evidence",
        evidence_id,
    )
    validate_enum(evidence.get("kind"), VALID_EVIDENCE_KINDS, "invalid_evidence_kind", owner_path, issues, "kind", evidence_id)
    validate_enum(evidence.get("relation"), VALID_EVIDENCE_RELATIONS, "invalid_evidence_relation", owner_path, issues, "relation", evidence_id)
    if "weight" in evidence and not is_blank(evidence.get("weight")):
        validate_number_range(evidence.get("weight"), 0.0, 1.0, "invalid_evidence_weight", owner_path, issues, "weight", evidence_id)
    validate_date_field(evidence.get("updatedAt"), "invalid_evidence_date", owner_path, issues, "updatedAt", evidence_id)
    validate_date_field(evidence.get("retrievedAt"), "invalid_evidence_date", owner_path, issues, "retrievedAt", evidence_id)


def validate_claim_record(record: dict, owner_id: str, owner_path: str, issues: list[dict]) -> None:
    """Validate a standalone or embedded claim record against v1 fields."""
    claim_id = str(record.get("id", "")).strip()
    validate_required_fields(
        record,
        {"id", "text", "status", "confidence", "claimType", "evidence", "createdAt", "updatedAt"},
        owner_path,
        issues,
        "claim",
        claim_id,
    )
    validate_enum(record.get("status"), VALID_CLAIM_STATUSES, "invalid_claim_status", owner_path, issues, "status", claim_id)
    validate_enum(record.get("claimType"), VALID_CLAIM_TYPES, "invalid_claim_type", owner_path, issues, "claimType", claim_id)
    if "confidence" in record and not is_blank(record.get("confidence")):
        validate_number_range(record.get("confidence"), 0.0, 1.0, "invalid_claim_confidence", owner_path, issues, "confidence", claim_id)
    validate_date_field(record.get("createdAt"), "invalid_claim_date", owner_path, issues, "createdAt", claim_id)
    validate_date_field(record.get("updatedAt"), "invalid_claim_date", owner_path, issues, "updatedAt", claim_id)

    evidence = record.get("evidence")
    if isinstance(evidence, list):
        for index, evidence_record in enumerate(evidence, start=1):
            validate_evidence_record(evidence_record, claim_id, owner_path, issues, index)
    elif "evidence" in record and not is_blank(evidence):
        validate_array_field(evidence, "invalid_claim_evidence", owner_path, issues, "evidence", claim_id)

    if "claimStatus" in record:
        add_validation_issue(
            issues,
            "deprecated_claim_status_field",
            owner_path,
            "Use `status` for claims; `claimStatus` is no longer part of the v1 schema.",
            ownerId=owner_id,
            claimId=claim_id,
        )


def normalize_claim_record(record: dict, owner_id: str, owner_path: str, issues: list[dict]) -> dict:
    """Normalize a claim record and emit validation warnings for bad fields."""
    normalized = dict(record)

    validate_claim_record(normalized, owner_id, owner_path, issues)

    confidence_raw = normalized.get("confidence")
    confidence = coerce_float(confidence_raw)
    if confidence_raw not in (None, ""):
        if confidence is None:
            normalized["confidenceRaw"] = confidence_raw
            normalized["confidence"] = None
        else:
            normalized["confidence"] = confidence

    return normalized


def normalize_page_record(record: dict, issues: list[dict]) -> dict:
    """Normalize page-level fields that the compiler depends on."""
    normalized = dict(record)
    return normalized


def validate_page_record(record: dict, issues: list[dict]) -> None:
    """Validate page metadata and folder ownership against the v1 spec."""
    page_id = record.get("id", "")
    path = record.get("path", "")
    meta = record.get("meta", {})
    page_type = record.get("pageType", "")

    validate_required_fields(meta, REQUIRED_UNIVERSAL_FIELDS, path, issues, "page", page_id)
    validate_date_field(meta.get("createdAt"), "invalid_page_date", path, issues, "createdAt", page_id)
    validate_date_field(meta.get("updatedAt"), "invalid_page_date", path, issues, "updatedAt", page_id)
    if "aliases" in meta:
        validate_array_field(meta.get("aliases"), "invalid_page_array", path, issues, "aliases", page_id)
    if "tags" in meta:
        validate_array_field(meta.get("tags"), "invalid_page_array", path, issues, "tags", page_id)

    parts = Path(path).parts
    if page_type == "index":
        validate_enum(meta.get("status"), VALID_GENERAL_STATUSES, "invalid_page_status", path, issues, "status", page_id)
        if path != "index.md":
            add_validation_issue(
                issues,
                "invalid_page_location",
                path,
                "`pageType: index` is reserved for index.md.",
                pageId=page_id,
                pageType=page_type,
            )
    elif page_type == "overview":
        validate_enum(meta.get("status"), VALID_GENERAL_STATUSES, "invalid_page_status", path, issues, "status", page_id)
        if path != "overview.md":
            add_validation_issue(
                issues,
                "invalid_page_location",
                path,
                "`pageType: overview` is reserved for overview.md.",
                pageId=page_id,
                pageType=page_type,
            )
    elif parts:
        expected = FOLDER_PAGE_TYPES.get(parts[0])
        if expected and expected != page_type:
            add_validation_issue(
                issues,
                "invalid_page_location",
                path,
                f"Page in `{parts[0]}/` must use pageType `{expected}`.",
                pageId=page_id,
                pageType=page_type,
                expectedPageType=expected,
            )

    if page_type == "source":
        validate_enum(meta.get("status"), VALID_SOURCE_STATUSES, "invalid_source_status", path, issues, "status", page_id)
        validate_enum(meta.get("sourceType"), VALID_SOURCE_TYPES, "invalid_source_type", path, issues, "sourceType", page_id)
        validate_enum(meta.get("sourceRole"), VALID_SOURCE_ROLES, "invalid_source_role", path, issues, "sourceRole", page_id)
        validate_required_fields(meta, {"sourceType", "retrievedAt", "attachments"}, path, issues, "source", page_id)
        if is_blank(meta.get("originUrl")) and is_blank(meta.get("originPath")):
            add_validation_issue(
                issues,
                "missing_source_origin",
                path,
                "Source is missing origin metadata; include `originUrl` or `originPath`.",
                pageId=page_id,
            )
        validate_date_field(meta.get("publishedAt"), "invalid_source_date", path, issues, "publishedAt", page_id)
        validate_date_field(meta.get("retrievedAt"), "invalid_source_date", path, issues, "retrievedAt", page_id)
        if "attachments" in meta:
            validate_array_field(meta.get("attachments"), "invalid_source_array", path, issues, "attachments", page_id)
        if "sourceParts" in meta:
            validate_array_field(meta.get("sourceParts"), "invalid_source_array", path, issues, "sourceParts", page_id)
    elif page_type == "entity":
        validate_enum(meta.get("status"), VALID_GENERAL_STATUSES, "invalid_page_status", path, issues, "status", page_id)
        validate_required_fields(meta, {"entityType"}, path, issues, "entity", page_id)
        validate_enum(meta.get("entityType"), VALID_ENTITY_TYPES, "invalid_entity_type", path, issues, "entityType", page_id)
    elif page_type == "concept":
        validate_enum(meta.get("status"), VALID_GENERAL_STATUSES, "invalid_page_status", path, issues, "status", page_id)
        validate_required_fields(meta, {"conceptType"}, path, issues, "concept", page_id)
        validate_enum(meta.get("conceptType"), VALID_CONCEPT_TYPES, "invalid_concept_type", path, issues, "conceptType", page_id)
    elif page_type == "synthesis":
        validate_enum(meta.get("status"), VALID_GENERAL_STATUSES, "invalid_page_status", path, issues, "status", page_id)
        validate_required_fields(meta, {"synthesisType", "sourcePages", "derivedClaims"}, path, issues, "synthesis", page_id)
        validate_enum(meta.get("synthesisType"), VALID_SYNTHESIS_TYPES, "invalid_synthesis_type", path, issues, "synthesisType", page_id)
        if "sourcePages" in meta:
            validate_array_field(meta.get("sourcePages"), "invalid_synthesis_array", path, issues, "sourcePages", page_id)
        if "derivedClaims" in meta:
            validate_array_field(meta.get("derivedClaims"), "invalid_synthesis_array", path, issues, "derivedClaims", page_id)
    elif page_type == "question":
        validate_required_fields(meta, {"priority", "relatedClaims", "relatedPages", "openedAt"}, path, issues, "question", page_id)
        validate_enum(meta.get("status"), VALID_QUESTION_STATUSES, "invalid_question_status", path, issues, "status", page_id)
        validate_enum(meta.get("priority"), VALID_QUESTION_PRIORITIES, "invalid_question_priority", path, issues, "priority", page_id)
        validate_date_field(meta.get("openedAt"), "invalid_question_date", path, issues, "openedAt", page_id)
        if "relatedClaims" in meta:
            validate_array_field(meta.get("relatedClaims"), "invalid_question_array", path, issues, "relatedClaims", page_id)
        if "relatedPages" in meta:
            validate_array_field(meta.get("relatedPages"), "invalid_question_array", path, issues, "relatedPages", page_id)

def validate_relation_record(record: Any, owner_id: str, owner_path: str, issues: list[dict], index: int) -> None:
    """Validate one relation entry against v1 fields."""
    if not isinstance(record, dict):
        add_validation_issue(
            issues,
            "invalid_relation_record",
            owner_path,
            f"Relation entry {index} on page {owner_id} must be a mapping.",
            ownerId=owner_id,
            index=index,
        )
        return

    relation_id = f"{owner_id}:relation:{index}"
    validate_required_fields(record, {"subject", "predicate", "object", "confidence"}, owner_path, issues, "relation", relation_id)
    validate_enum(record.get("predicate"), VALID_RELATION_PREDICATES, "non_controlled_relation_predicate", owner_path, issues, "predicate", relation_id)
    if "confidence" in record and not is_blank(record.get("confidence")):
        validate_number_range(record.get("confidence"), 0.0, 1.0, "invalid_relation_confidence", owner_path, issues, "confidence", relation_id)
    if "sourceClaimIds" in record:
        validate_array_field(record.get("sourceClaimIds"), "invalid_relation_array", owner_path, issues, "sourceClaimIds", relation_id)


def validate_timeline_record(record: Any, owner_id: str, owner_path: str, issues: list[dict], index: int) -> None:
    """Validate one timeline entry against v1 fields."""
    if not isinstance(record, dict):
        add_validation_issue(
            issues,
            "invalid_timeline_record",
            owner_path,
            f"Timeline entry {index} on page {owner_id} must be a mapping.",
            ownerId=owner_id,
            index=index,
        )
        return

    timeline_id = str(record.get("id", "")).strip() or f"{owner_id}:timeline:{index}"
    validate_required_fields(record, {"id", "date", "text"}, owner_path, issues, "timeline", timeline_id)
    validate_date_field(record.get("date"), "invalid_timeline_date", owner_path, issues, "date", timeline_id)
    validate_date_field(record.get("endDate"), "invalid_timeline_date", owner_path, issues, "endDate", timeline_id)
    if "confidence" in record and not is_blank(record.get("confidence")):
        validate_number_range(record.get("confidence"), 0.0, 1.0, "invalid_timeline_confidence", owner_path, issues, "confidence", timeline_id)
    if "relatedClaims" in record:
        validate_array_field(record.get("relatedClaims"), "invalid_timeline_array", owner_path, issues, "relatedClaims", timeline_id)
    if "sourceIds" in record:
        validate_array_field(record.get("sourceIds"), "invalid_timeline_array", owner_path, issues, "sourceIds", timeline_id)
    if "relatedPages" in record:
        validate_array_field(record.get("relatedPages"), "invalid_timeline_array", owner_path, issues, "relatedPages", timeline_id)

    start = record.get("date")
    end = record.get("endDate")
    if is_yyyy_mm_dd(start) and is_yyyy_mm_dd(end):
        if date.fromisoformat(str(end)) < date.fromisoformat(str(start)):
            add_validation_issue(
                issues,
                "invalid_timeline_date_range",
                owner_path,
                "Field `endDate` must not be earlier than `date`.",
                objectId=timeline_id,
                date=start,
                endDate=end,
            )


# ---------------------------------------------------------------------------
# Vault walker
# ---------------------------------------------------------------------------

def walk_vault(vault_root: Path, verbose: bool = False) -> tuple[list[dict], list[dict]]:
    """Walk vault, parse all markdown pages, return list of page records."""
    pages = []
    validation_issues = []
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
        meta, body, parse_error = parse_frontmatter(text)

        if parse_error:
            add_validation_issue(
                validation_issues,
                "invalid_frontmatter",
                str(rel).replace("\\", "/"),
                "Frontmatter could not be parsed.",
                error=parse_error,
            )
            continue

        if not meta:
            if verbose:
                print(f"  [SKIP] No frontmatter: {rel}")
            continue

        page_id = str(meta.get("id", "")).strip()
        page_type = str(meta.get("pageType", "")).strip()

        if not page_id or not page_type:
            add_validation_issue(
                validation_issues,
                "missing_required_metadata",
                str(rel).replace("\\", "/"),
                "Frontmatter is missing required `id` or `pageType`.",
            )
            continue

        if page_type not in VALID_PAGE_TYPES:
            add_validation_issue(
                validation_issues,
                "invalid_page_type",
                str(rel).replace("\\", "/"),
                f"Unsupported pageType {page_type!r}.",
                pageId=page_id,
                pageType=page_type,
            )
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
            record["sourceRole"] = meta.get("sourceRole") or "whole"
            record["parentSourceId"] = meta.get("parentSourceId", "")
            record["partIndex"] = meta.get("partIndex", "")
            record["partCount"] = meta.get("partCount", "")
            record["locator"] = meta.get("locator", "")
            record["sourceParts"] = meta.get("sourceParts") or []
            record["originUrl"] = meta.get("originUrl", "")
            record["originPath"] = meta.get("originPath", "")
            record["publishedAt"] = str(meta.get("publishedAt", ""))
            record["retrievedAt"] = str(meta.get("retrievedAt", ""))
        elif page_type == "synthesis":
            record["synthesisType"] = meta.get("synthesisType", "")
            record["scope"] = meta.get("scope", "")
        elif page_type == "question":
            record["priority"] = meta.get("priority", "")
            record["openedAt"] = str(meta.get("openedAt", ""))
        elif page_type == "claim":
            record["claimType"] = meta.get("claimType", "")
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

        normalized_record = normalize_page_record(record, validation_issues)
        validate_page_record(normalized_record, validation_issues)
        pages.append(normalized_record)

        if verbose:
            print(f"  [PAGE] {page_id} ({page_type}) - {rel}")

    return pages, validation_issues


def validate_source_structure(pages: list[dict], validation_issues: list[dict]) -> None:
    """Validate parent/part source relationships introduced for large sources."""
    sources = [page for page in pages if page.get("pageType") == "source"]
    by_id = {str(page.get("id", "")): page for page in sources}
    by_path = {str(page.get("path", "")): page for page in sources}

    for source in sources:
        page_id = str(source.get("id", ""))
        path = str(source.get("path", ""))
        role = str(source.get("sourceRole") or "whole")
        status = str(source.get("status") or "")
        body_words = word_count(str(source.get("body") or ""))

        if role == "whole" and body_words > LARGE_SOURCE_PARTITION_WORD_THRESHOLD:
            add_validation_issue(
                validation_issues,
                "large_source_not_partitioned",
                path,
                (
                    "Source body exceeds the large-source partition threshold; "
                    "create a parent source page and child source parts."
                ),
                pageId=page_id,
                wordCount=body_words,
                threshold=LARGE_SOURCE_PARTITION_WORD_THRESHOLD,
            )

        if role == "parent":
            source_parts = source.get("sourceParts") or []
            if not isinstance(source_parts, list) or not source_parts:
                add_validation_issue(
                    validation_issues,
                    "missing_source_parts",
                    path,
                    "`sourceRole: parent` requires ordered `sourceParts` paths.",
                    pageId=page_id,
                )
                continue

            part_records = []
            for part_path in source_parts:
                part_path_text = str(part_path)
                part = by_path.get(part_path_text)
                if part is None:
                    add_validation_issue(
                        validation_issues,
                        "missing_source_part_path",
                        path,
                        f"`sourceParts` references missing source part path {part_path_text!r}.",
                        pageId=page_id,
                        partPath=part_path_text,
                    )
                    continue
                if part.get("sourceRole") != "part":
                    add_validation_issue(
                        validation_issues,
                        "invalid_source_part_role",
                        part.get("path", part_path_text),
                        "Source listed in `sourceParts` should use `sourceRole: part`.",
                        pageId=part.get("id", ""),
                        parentSourceId=page_id,
                    )
                if part.get("parentSourceId") != page_id:
                    add_validation_issue(
                        validation_issues,
                        "invalid_source_parent_reference",
                        part.get("path", part_path_text),
                        "Source part `parentSourceId` does not match the parent source.",
                        pageId=part.get("id", ""),
                        expectedParentSourceId=page_id,
                        actualParentSourceId=part.get("parentSourceId", ""),
                    )
                part_records.append(part)

            if status != "partitioned":
                unprocessed_parts = [part for part in part_records if part.get("status") == "unprocessed"]
                if unprocessed_parts:
                    add_validation_issue(
                        validation_issues,
                        "invalid_partitioned_source_status",
                        path,
                        "Parent source should use `status: partitioned` while child source parts remain unprocessed.",
                        pageId=page_id,
                        unprocessedPartCount=len(unprocessed_parts),
                    )

            if body_words > LARGE_SOURCE_TARGET_WORD_MIN:
                add_validation_issue(
                    validation_issues,
                    "large_parent_source_body",
                    path,
                    "Parent source pages should stay short and should not contain the full source body.",
                    pageId=page_id,
                    wordCount=body_words,
                    targetMax=LARGE_SOURCE_TARGET_WORD_MIN,
                )

        if role == "part":
            parent_source_id = str(source.get("parentSourceId") or "")
            parent = by_id.get(parent_source_id)
            if not parent_source_id or parent is None:
                add_validation_issue(
                    validation_issues,
                    "missing_parent_source",
                    path,
                    "`sourceRole: part` requires a valid `parentSourceId`.",
                    pageId=page_id,
                    parentSourceId=parent_source_id,
                )
            elif parent.get("sourceRole") != "parent":
                add_validation_issue(
                    validation_issues,
                    "invalid_parent_source_role",
                    path,
                    "A source part's parent should use `sourceRole: parent`.",
                    pageId=page_id,
                    parentSourceId=parent_source_id,
                    parentSourceRole=parent.get("sourceRole", ""),
                )

            part_index = coerce_int(source.get("partIndex"))
            part_count = coerce_int(source.get("partCount"))
            if part_index is None or part_index < 1:
                add_validation_issue(
                    validation_issues,
                    "invalid_source_part_index",
                    path,
                    "`sourceRole: part` requires a positive one-based `partIndex`.",
                    pageId=page_id,
                    partIndex=source.get("partIndex"),
                )
            if part_count is None or part_count < 1:
                add_validation_issue(
                    validation_issues,
                    "invalid_source_part_count",
                    path,
                    "`sourceRole: part` requires a positive `partCount`.",
                    pageId=page_id,
                    partCount=source.get("partCount"),
                )
            if part_index is not None and part_count is not None and part_index > part_count:
                add_validation_issue(
                    validation_issues,
                    "invalid_source_part_range",
                    path,
                    "`partIndex` must not exceed `partCount`.",
                    pageId=page_id,
                    partIndex=part_index,
                    partCount=part_count,
                )
            if is_blank(source.get("locator")):
                add_validation_issue(
                    validation_issues,
                    "missing_source_part_locator",
                    path,
                    "`sourceRole: part` requires a stable `locator`.",
                    pageId=page_id,
                )
            if body_words > LARGE_SOURCE_HARD_WORD_MAX:
                add_validation_issue(
                    validation_issues,
                    "large_source_part_body",
                    path,
                    "Source part body exceeds the hard large-source part size.",
                    pageId=page_id,
                    wordCount=body_words,
                    hardMax=LARGE_SOURCE_HARD_WORD_MAX,
                )


# ---------------------------------------------------------------------------
# Claim extraction
# ---------------------------------------------------------------------------

def extract_claims(pages: list[dict], validation_issues: list[dict]) -> list[dict]:
    """Extract all claims from page metadata (embedded and standalone)."""
    all_claims = []
    for page in pages:
        # Standalone claim pages
        if page["pageType"] == "claim":
            record = normalize_claim_record(
                {
                    "id": page["id"],
                    "text": page["meta"].get("text", page["title"]),
                    "status": page["meta"].get("status", ""),
                    "confidence": page.get("confidence"),
                    "claimType": page["meta"].get("claimType", ""),
                    "evidence": page["meta"].get("evidence") or [],
                    "createdAt": page["meta"].get("createdAt", ""),
                    "updatedAt": page["meta"].get("updatedAt", ""),
                    "subjectPageId": page["meta"].get("subjectPageId", ""),
                    "_owningPageId": page["id"],
                    "_owningPagePath": page["path"],
                    "_owningPageType": "claim",
                    "_standaloneClaimPage": True,
                },
                owner_id=page["id"],
                owner_path=page["path"],
                issues=validation_issues,
            )
            all_claims.append(record)
            continue
        # Embedded claims in frontmatter
        raw_claims = page["meta"].get("claims") or []
        for claim in raw_claims:
            if not isinstance(claim, dict):
                continue
            record = normalize_claim_record(
                {
                    **claim,
                    "_owningPageId": page["id"],
                    "_owningPagePath": page["path"],
                    "_owningPageType": page["pageType"],
                    "_standaloneClaimPage": False,
                },
                owner_id=page["id"],
                owner_path=page["path"],
                issues=validation_issues,
            )
            all_claims.append(record)
    return all_claims


# ---------------------------------------------------------------------------
# Relation extraction
# ---------------------------------------------------------------------------

def extract_relations(pages: list[dict], validation_issues: list[dict]) -> list[dict]:
    """Extract all relations from page metadata."""
    all_relations = []
    for page in pages:
        raw_relations = page["meta"].get("relations") or []
        for index, rel in enumerate(raw_relations, start=1):
            validate_relation_record(rel, page["id"], page["path"], validation_issues, index)
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

def extract_timeline_events(pages: list[dict], validation_issues: list[dict]) -> list[dict]:
    """Extract all timeline entries from page metadata."""
    all_events = []
    for page in pages:
        raw_events = page["meta"].get("timeline") or []
        for index, ev in enumerate(raw_events, start=1):
            validate_timeline_record(ev, page["id"], page["path"], validation_issues, index)
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
            numeric_conf = coerce_float(conf)
            if numeric_conf is not None and numeric_conf < LOW_CONFIDENCE_THRESHOLD:
                low_confidence_claims.append(claim)
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
                       contradictions: list[dict], health: dict, validation_issues: list[dict],
                       compiled_at: str) -> dict:
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

    # Open questions
    open_questions = [p for p in pages if p["pageType"] == "question" and p["status"] in ("open", "researching", "blocked")]
    questions_summary = [summarize_page(p) for p in open_questions[:MAX_DIGEST_QUESTIONS]]

    # Top supported claims
    top_claims = sorted(
        [c for c in claims if c.get("status") == "supported" and c.get("confidence") is not None],
        key=lambda c: coerce_float(c.get("confidence")) or 0,
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
            "validationIssues": len(validation_issues),
        },
        "keyPages": key_pages_summary,
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


def finalize_report_body(body: str) -> str:
    """Normalize report body ending."""
    return f"{body.rstrip()}\n"


def format_wikilink(path: str, title: str | None = None) -> str:
    """Convert a vault-relative markdown path into an Obsidian wikilink."""
    target = path.replace("\\", "/")
    if target.endswith(".md"):
        target = target[:-3]
    if title:
        return f"[[{target}|{title}]]"
    return f"[[{target}]]"


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
            out += f"- **[{q['status'].upper()}]** {format_wikilink(q['path'], q['title'])} — priority: `{priority}`\n"
        out += "\n"

    if resolved:
        out += "## Resolved\n\n"
        for q in resolved:
            out += f"- {format_wikilink(q['path'], q['title'])}\n"
        out += "\n"

    if not active and not resolved:
        out += "_No questions recorded yet._\n"

    return finalize_report_body(out)


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

    return finalize_report_body(out)


def generate_low_confidence_report(health: dict, compiled_at: str) -> str:
    out = make_report_header("Low Confidence Claims", compiled_at)
    low = health["low_confidence_claims"]
    out += f"**{len(low)}** low-confidence claims (confidence < {LOW_CONFIDENCE_THRESHOLD} or status unverified/weakly_supported/contested)\n\n"

    if low:
        out += "## Claims\n\n"
        sorted_low = sorted(low, key=lambda c: coerce_float(c.get("confidence")) or 0)
        for c in sorted_low:
            conf = c.get("confidence", "—")
            status = c.get("status", "—")
            page = c.get("_owningPageId", "—")
            out += f"- `{c.get('id', '?')}` — conf: `{conf}`, status: `{status}`, page: `{page}`\n"
            out += f"  - {c.get('text', '')}\n"
        out += "\n"
    else:
        out += "_No low-confidence claims detected._\n"

    return finalize_report_body(out)


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

    return finalize_report_body(out)


def generate_stale_pages_report(health: dict, compiled_at: str) -> str:
    out = make_report_header("Stale Pages", compiled_at)
    stale = health["stale_pages"]
    out += f"**{len(stale)}** pages not updated in more than {STALE_DAYS} days\n\n"

    if stale:
        out += "## Stale Pages\n\n"
        sorted_stale = sorted(stale, key=lambda p: p.get("updatedAt", ""))
        for p in sorted_stale:
            out += f"- {format_wikilink(p['path'], p['title'])} — last updated: `{p['updatedAt']}`\n"
        out += "\n"
    else:
        out += "_No stale pages detected._\n"

    return finalize_report_body(out)


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

    return finalize_report_body(out)


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

    return finalize_report_body(out)


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
    pages, validation_issues = walk_vault(vault_root, verbose=args.verbose)
    print(f"  Found {len(pages)} pages with frontmatter")
    if validation_issues:
        print(f"  Validation issues detected: {len(validation_issues)}")

    # Validate unique IDs
    id_paths = {}
    for p in pages:
        id_paths.setdefault(p["id"], []).append(p["path"])
    duplicate_ids = {k: v for k, v in id_paths.items() if len(v) > 1}
    if duplicate_ids:
        print(f"  WARNING: Duplicate page IDs found:")
        for dup_id, paths in duplicate_ids.items():
            print(f"    - {dup_id} in files: {', '.join(paths)}")
            add_validation_issue(
                validation_issues,
                "duplicate_page_id",
                paths[0],
                f"Page id {dup_id!r} appears in multiple files.",
                pageId=dup_id,
                paths=paths,
            )

    validate_source_structure(pages, validation_issues)

    # --- Extract structured data ---
    print("Extracting claims...")
    claims = extract_claims(pages, validation_issues)
    print(f"  Found {len(claims)} claims")
    claim_id_paths = {}
    for claim in claims:
        claim_id = str(claim.get("id", "")).strip()
        if claim_id:
            claim_id_paths.setdefault(claim_id, []).append(claim.get("_owningPagePath", ""))
    duplicate_claim_ids = {k: v for k, v in claim_id_paths.items() if len(v) > 1}
    for claim_id, paths in duplicate_claim_ids.items():
        add_validation_issue(
            validation_issues,
            "duplicate_claim_id",
            paths[0],
            f"Claim id {claim_id!r} appears in multiple claim records.",
            claimId=claim_id,
            paths=paths,
        )

    print("Extracting relations...")
    relations = extract_relations(pages, validation_issues)
    print(f"  Found {len(relations)} relations")

    print("Extracting timeline events...")
    timeline_events = extract_timeline_events(pages, validation_issues)
    print(f"  Found {len(timeline_events)} timeline events")
    timeline_id_paths = {}
    for event in timeline_events:
        timeline_id = str(event.get("id", "")).strip()
        if timeline_id:
            timeline_id_paths.setdefault(timeline_id, []).append(event.get("_owningPagePath", ""))
    duplicate_timeline_ids = {k: v for k, v in timeline_id_paths.items() if len(v) > 1}
    for timeline_id, paths in duplicate_timeline_ids.items():
        add_validation_issue(
            validation_issues,
            "duplicate_timeline_id",
            paths[0],
            f"Timeline id {timeline_id!r} appears in multiple timeline records.",
            timelineId=timeline_id,
            paths=paths,
        )

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
    if validation_issues:
        validation_summary = summarize_validation_issues(validation_issues)
        summary_text = ", ".join(f"{k}={v}" for k, v in sorted(validation_summary.items()))
        print(f"  Validation issues: {summary_text}")
    else:
        validation_summary = {}

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

    source_index = [
        {
            "id": p["id"],
            "title": p["title"],
            "path": p["path"],
            "status": p["status"],
            "sourceType": p.get("sourceType", ""),
            "sourceRole": p.get("sourceRole", "whole"),
            "parentSourceId": p.get("parentSourceId", ""),
            "partIndex": p.get("partIndex", ""),
            "partCount": p.get("partCount", ""),
            "locator": p.get("locator", ""),
            "sourceParts": p.get("sourceParts", []),
            "originUrl": p.get("originUrl", ""),
            "originPath": p.get("originPath", ""),
            "publishedAt": p.get("publishedAt", ""),
            "retrievedAt": p.get("retrievedAt", ""),
            "updatedAt": p["updatedAt"],
            "attachments": p["meta"].get("attachments", []),
        }
        for p in pages if p["pageType"] == "source"
    ]

    # --- Build agent digest ---
    print("Building agent digest...")
    agent_digest = build_agent_digest(pages, claims, relations, contradictions, health, validation_issues, compiled_at)

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

    print("\nWriting root page catalog...")
    index_result = subprocess.run(
        [
            sys.executable,
            str(vault_root / "_system/scripts/index.py"),
            "--vault-root",
            str(vault_root),
            "--write",
            "--no-log",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if index_result.stdout.strip():
        print(f"  {index_result.stdout.strip()}")

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

    # validation-issues.json
    (cache_dir / "validation-issues.json").write_text(
        json.dumps(
            {
                "compiledAt": compiled_at,
                "issues": validation_issues,
                "summary": validation_summary,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8"
    )
    print(f"  Wrote validation-issues.json ({len(validation_issues)} issues)")

    # claims-index.json — standalone claim pages only
    claims_index = [
        {
            "id": p["id"],
            "title": p["title"],
            "path": p["path"],
            "status": p["status"],
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
    open_questions_count = len([
        p for p in pages
        if p["pageType"] == "question" and p["status"] in ("open", "researching", "blocked")
    ])
    log_message = (
        "compile-wiki: regenerated index, cache, indexes, and reports; "
        f"pages={len(pages)} claims={len(claims)} relations={len(relations)} "
        f"contradictions={len(contradictions)} openQuestions={open_questions_count} "
        f"evidenceGaps={len(health['evidence_gap_claims'])} "
        f"lowConfidence={len(health['low_confidence_claims'])} "
        f"validationIssues={len(validation_issues)} duplicatePageIds={len(duplicate_ids)}"
    )
    subprocess.run(
        [
            sys.executable,
            str(vault_root / "_system/scripts/log.py"),
            "--vault-root",
            str(vault_root),
            "--message",
            log_message,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    print(f"\nWrote operational log: {LOG_DIR}/log.md")

    print(f"\nCompile complete.")
    print(f"  Pages: {len(pages)} | Claims: {len(claims)} | Relations: {len(relations)} | Contradictions: {len(contradictions)}")
    print(f"  Open questions: {open_questions_count}")
    print(f"  Evidence gaps: {len(health['evidence_gap_claims'])} | Low confidence: {len(health['low_confidence_claims'])}")
    print(f"  Validation issues: {len(validation_issues)}")


if __name__ == "__main__":
    main()
