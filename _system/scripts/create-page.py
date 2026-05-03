#!/usr/bin/env python3
"""
Deterministic page scaffolder for the Agentics vault.

Usage:
    python3 _system/scripts/create-page.py --type concept --subtype method --slug adaptive-reuse --title "Adaptive Reuse" --body-file /tmp/body.md
    python3 _system/scripts/create-page.py --type synthesis --subtype brief --slug coastal-resilience-options --title "Coastal Resilience Options" --scope "coastal flood mitigation options" --source-page source.2026-04-28.article.coastal-flooding --derived-claim claim.descriptive.high-tide-risk --body-file /tmp/body.md
    python3 _system/scripts/create-page.py --type source --subtype webpage --slug urban-tree-canopy --title "Urban Tree Canopy" --source-url https://example.test --body-file /tmp/source.md
    python3 _system/scripts/create-page.py --type claim --subtype descriptive --slug canopy-benefit --title "Canopy Benefit" --body-file /tmp/body.md --evidence 'id=evidence.quote.supports.canopy-benefit;sourceId=source.2026-04-28.article.urban-tree-canopy;path=sources/2026-04-28-article-urban-tree-canopy.md;kind=quote;relation=supports;weight=0.60;updatedAt=2026-04-28'
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


LOG_SCRIPT = Path("_system/scripts/log.py")

PAGE_FOLDERS = {
    "source": "sources",
    "entity": "entities",
    "concept": "concepts",
    "claim": "claims",
    "question": "questions",
    "synthesis": "syntheses",
}
VALID_PAGE_TYPES = set(PAGE_FOLDERS)
VALID_SOURCE_ROLES = {"whole", "parent", "part"}
VALID_SOURCE_STATUSES = {"unprocessed", "partitioned", "processed", "archived"}
VALID_GENERAL_STATUSES = {"active", "draft", "archived", "deprecated"}
VALID_CLAIM_STATUSES = {"supported", "weakly_supported", "inferred", "unverified", "contested", "contradicted", "deprecated"}
VALID_QUESTION_STATUSES = {"open", "researching", "blocked", "resolved", "dropped"}
VALID_QUESTION_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_SOURCE_TYPES = {"webpage", "article", "document", "pdf", "transcript", "email", "meeting-notes", "dataset", "screenshot", "bridge", "import", "other"}
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
VALID_CLAIM_TYPES = {"descriptive", "historical", "causal", "interpretive", "normative", "forecast"}
VALID_EVIDENCE_RELATIONS = {"supports", "weakens", "contradicts", "context_only"}
VALID_EVIDENCE_KINDS = {"quote", "summary", "measurement", "observation", "screenshot", "transcript", "inference"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ScaffoldingError(ValueError):
    """Raised when requested page scaffolding is invalid."""


def is_date(value: str) -> bool:
    if not DATE_PATTERN.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def require_date(value: str, field: str) -> None:
    if value and not is_date(value):
        raise ScaffoldingError(f"{field} must use YYYY-MM-DD")


def require_slug(value: str) -> None:
    if not SLUG_PATTERN.fullmatch(value):
        raise ScaffoldingError("--slug must use kebab-case lowercase letters, numbers, and hyphens")


def yaml_quote_string(value: str) -> str:
    if value == "":
        return ""
    if ": " in value or " #" in value or value.startswith(("#", "-", "?", "@", "`", "!", "&", "*")):
        return json.dumps(value, ensure_ascii=False)
    if re.fullmatch(r"[A-Za-z0-9_./:@#|?&=%+,\- ]+", value) and value.strip() == value:
        lowered = value.lower()
        if lowered not in {"true", "false", "null", "none", "~"} and not re.fullmatch(r"[-+]?\d+(\.\d+)?", value):
            return value
    return json.dumps(value, ensure_ascii=False)


def yaml_lines(key: str, value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, list):
        if not value:
            return [f"{prefix}{key}: []"]
        lines = [f"{prefix}{key}:"]
        for item in value:
            if isinstance(item, dict):
                item_fields = list(item.items())
                first_key, first_value = item_fields[0]
                if isinstance(first_value, (list, dict)):
                    lines.append(f"{prefix}  - {first_key}:")
                    if first_value:
                        if isinstance(first_value, list):
                            for nested_item in first_value:
                                lines.append(f"{prefix}      - {yaml_scalar(nested_item)}")
                        else:
                            for nested_key, nested_value in first_value.items():
                                lines.extend(yaml_lines(nested_key, nested_value, indent + 6))
                else:
                    lines.append(f"{prefix}  - {first_key}: {yaml_scalar(first_value)}")
                for sub_key, sub_value in item_fields[1:]:
                    lines.extend(yaml_lines(sub_key, sub_value, indent + 4))
            else:
                lines.append(f"{prefix}  - {yaml_scalar(item)}")
        return lines
    if isinstance(value, dict):
        if not value:
            return [f"{prefix}{key}: {{}}"]
        lines = [f"{prefix}{key}:"]
        for sub_key, sub_value in value.items():
            lines.extend(yaml_lines(sub_key, sub_value, indent + 2))
        return lines
    return [f"{prefix}{key}: {yaml_scalar(value)}"]


def yaml_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return yaml_quote_string(str(value))


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.extend(yaml_lines(key, value))
    lines.extend(["---", "", body.strip(), ""])
    return "\n".join(lines)


def read_body(args: argparse.Namespace, wiki_root: Path) -> str:
    if args.body_file:
        body_path = Path(args.body_file)
        if not body_path.is_absolute():
            body_path = wiki_root / body_path
        try:
            body = body_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ScaffoldingError(f"cannot read --body-file: {exc}") from exc
    else:
        body = args.body or ""
    if not body.strip():
        raise ScaffoldingError("body prose/content is required")
    return body.strip()


def parse_evidence_value(value: str) -> dict[str, Any]:
    """Parse one evidence record from JSON or semicolon-separated key=value pairs."""
    value = value.strip()
    if not value:
        raise ScaffoldingError("--evidence values must not be empty")
    if value.startswith("{"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ScaffoldingError(f"--evidence JSON is invalid: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ScaffoldingError("--evidence JSON must be an object")
        return parsed

    record: dict[str, Any] = {}
    for part in value.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ScaffoldingError("--evidence entries must use JSON objects or semicolon-separated key=value pairs")
        key, raw = part.split("=", 1)
        key = key.strip()
        if not key:
            raise ScaffoldingError("--evidence contains an empty key")
        record[key] = raw.strip()
    if not record:
        raise ScaffoldingError("--evidence did not contain any fields")
    return record


def normalize_evidence_record(record: dict[str, Any], index: int) -> dict[str, Any]:
    """Validate and order one evidence record for stable frontmatter output."""
    allowed_fields = {
        "id",
        "sourceId",
        "path",
        "lines",
        "kind",
        "relation",
        "weight",
        "note",
        "excerpt",
        "retrievedAt",
        "updatedAt",
        "locatorText",
    }
    unknown = sorted(set(record) - allowed_fields)
    if unknown:
        raise ScaffoldingError(f"--evidence entry {index} has unsupported field(s): {', '.join(unknown)}")

    required = {"id", "sourceId", "path", "kind", "relation", "weight", "updatedAt"}
    missing = sorted(field for field in required if record.get(field) in (None, ""))
    if missing:
        raise ScaffoldingError(f"--evidence entry {index} is missing required field(s): {', '.join(missing)}")

    kind = str(record["kind"])
    relation = str(record["relation"])
    if kind not in VALID_EVIDENCE_KINDS:
        raise ScaffoldingError(f"--evidence entry {index} has invalid kind {kind!r}")
    if relation not in VALID_EVIDENCE_RELATIONS:
        raise ScaffoldingError(f"--evidence entry {index} has invalid relation {relation!r}")

    try:
        weight = float(record["weight"])
    except (TypeError, ValueError) as exc:
        raise ScaffoldingError(f"--evidence entry {index} weight must be numeric") from exc
    if weight < 0.0 or weight > 1.0:
        raise ScaffoldingError(f"--evidence entry {index} weight must be between 0.0 and 1.0")

    require_date(str(record["updatedAt"]), f"--evidence entry {index} updatedAt")
    if record.get("retrievedAt"):
        require_date(str(record["retrievedAt"]), f"--evidence entry {index} retrievedAt")

    ordered: dict[str, Any] = {
        "id": str(record["id"]),
        "sourceId": str(record["sourceId"]),
        "path": str(record["path"]),
    }
    for field in ("lines", "kind", "relation"):
        if record.get(field) not in (None, ""):
            ordered[field] = str(record[field])
    ordered["weight"] = weight
    for field in ("note", "excerpt", "retrievedAt", "updatedAt", "locatorText"):
        if record.get(field) not in (None, ""):
            ordered[field] = str(record[field])
    return ordered


def parse_evidence_records(args: argparse.Namespace) -> list[dict[str, Any]]:
    return [
        normalize_evidence_record(parse_evidence_value(value), index)
        for index, value in enumerate(args.evidence, start=1)
    ]


def extract_frontmatter_id(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        if line.startswith("id:"):
            raw = line.split(":", 1)[1].strip().strip("\"'")
            return raw or None
    return None


def find_duplicate_id(wiki_root: Path, page_id: str) -> str | None:
    for path in sorted(wiki_root.rglob("*.md")):
        rel = path.relative_to(wiki_root)
        if any(part in {".git", ".obsidian", "_system", "_archive", "_inbox", "_attachments", "raw", "reports"} for part in rel.parts):
            continue
        try:
            existing_id = extract_frontmatter_id(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if existing_id == page_id:
            return str(rel).replace("\\", "/")
    return None


def id_to_filename(page_id: str) -> str:
    if page_id.startswith("source."):
        return page_id[len("source."):].replace(".", "-") + ".md"
    return page_id.replace(".", "-") + ".md"


def page_path(args: argparse.Namespace, page_id: str) -> Path:
    folder = PAGE_FOLDERS[args.page_type]
    if args.page_type == "source" and args.source_role == "part":
        folder = "sources/parts"
    return Path(folder) / id_to_filename(page_id)


def subtype_field(page_type: str) -> str | None:
    return {
        "source": "sourceType",
        "entity": "entityType",
        "concept": "conceptType",
        "claim": "claimType",
        "synthesis": "synthesisType",
    }.get(page_type)


def validate_subtype(page_type: str, subtype: str) -> None:
    allowed = {
        "source": VALID_SOURCE_TYPES,
        "entity": VALID_ENTITY_TYPES,
        "concept": VALID_CONCEPT_TYPES,
        "claim": VALID_CLAIM_TYPES,
        "synthesis": VALID_SYNTHESIS_TYPES,
    }.get(page_type)
    if allowed is not None and subtype not in allowed:
        raise ScaffoldingError(f"--subtype {subtype!r} is not valid for page type {page_type!r}")


def default_status(args: argparse.Namespace) -> str:
    if args.status:
        return args.status
    if args.page_type == "source":
        return "partitioned" if args.source_role == "parent" else "unprocessed"
    if args.page_type == "claim":
        return "unverified"
    if args.page_type == "question":
        return "open"
    return "active"


def validate_status(page_type: str, status: str) -> None:
    allowed = VALID_GENERAL_STATUSES
    if page_type == "source":
        allowed = VALID_SOURCE_STATUSES
    elif page_type == "claim":
        allowed = VALID_CLAIM_STATUSES
    elif page_type == "question":
        allowed = VALID_QUESTION_STATUSES
    if status not in allowed:
        raise ScaffoldingError(f"--status {status!r} is not valid for page type {page_type!r}")


def validate_claim_args(args: argparse.Namespace) -> None:
    if args.confidence < 0.0 or args.confidence > 1.0:
        raise ScaffoldingError("--confidence must be between 0.0 and 1.0")
    parse_evidence_records(args)


def validate_synthesis_args(args: argparse.Namespace) -> None:
    if not args.scope:
        raise ScaffoldingError("synthesis pages require --scope")


def build_page_id(args: argparse.Namespace, created_at: str) -> str:
    if args.page_type == "source":
        source_date = args.source_date or args.retrieved_at or created_at
        require_date(source_date, "--source-date")
        suffix = f".part{args.part_index:03d}" if args.source_role == "part" else ""
        return f"source.{source_date}.{args.subtype}.{args.slug}{suffix}"
    if args.page_type == "question":
        return f"question.{args.subtype}.{args.slug}"
    return f"{args.page_type}.{args.subtype}.{args.slug}"


def validate_body(page_type: str, body: str) -> None:
    words = re.findall(r"\b\w+\b", body)
    if page_type != "source" and len(words) < 5:
        raise ScaffoldingError("authored knowledge pages require substantive body prose")


def append_optional(frontmatter: dict[str, Any], key: str, value: Any) -> None:
    if value not in (None, ""):
        frontmatter[key] = value


def build_frontmatter(args: argparse.Namespace, page_id: str, created_at: str) -> dict[str, Any]:
    status = default_status(args)
    validate_status(args.page_type, status)
    frontmatter: dict[str, Any] = {
        "id": page_id,
        "pageType": args.page_type,
        "title": args.title,
        "status": status,
    }

    field = subtype_field(args.page_type)
    if field:
        frontmatter[field] = args.subtype

    if args.page_type == "source":
        frontmatter["sourceRole"] = args.source_role
        if args.source_role == "parent":
            frontmatter["sourceParts"] = args.source_part
            if args.part_count is not None:
                frontmatter["partCount"] = args.part_count
        elif args.source_role == "part":
            frontmatter["parentSourceId"] = args.parent_source_id
            frontmatter["partIndex"] = args.part_index
            frontmatter["partCount"] = args.part_count
            frontmatter["locator"] = args.locator
            frontmatter["sourceParts"] = []
        else:
            frontmatter["sourceParts"] = []
        append_optional(frontmatter, "originUrl", args.source_url)
        append_optional(frontmatter, "originPath", args.origin_path)
        append_optional(frontmatter, "publishedAt", args.published_at)
        frontmatter["retrievedAt"] = args.retrieved_at or created_at
        append_optional(frontmatter, "convertedAt", args.converted_at)
        append_optional(frontmatter, "conversionTool", args.conversion_tool)
        append_optional(frontmatter, "conversionToolVersion", args.conversion_tool_version)
        append_optional(frontmatter, "conversionBackend", args.conversion_backend)
        if args.conversion_warning:
            frontmatter["conversionWarnings"] = args.conversion_warning
    elif args.page_type == "entity":
        frontmatter["canonicalName"] = args.canonical_name or args.title
    elif args.page_type == "claim":
        frontmatter["confidence"] = args.confidence
        frontmatter["text"] = args.claim_text or args.title
        frontmatter["subjectPageId"] = args.subject_page_id or ""
        frontmatter["sourceIds"] = args.source_id
        frontmatter["evidence"] = parse_evidence_records(args)
    elif args.page_type == "question":
        frontmatter["priority"] = args.priority
        frontmatter["relatedClaims"] = args.related_claim
        frontmatter["relatedPages"] = args.related_page
        frontmatter["openedAt"] = args.opened_at or created_at
    elif args.page_type == "synthesis":
        frontmatter["scope"] = args.scope or ""
        frontmatter["sourcePages"] = args.source_page
        frontmatter["derivedClaims"] = args.derived_claim

    if args.page_type not in {"claim", "question", "synthesis"} and args.source_page:
        frontmatter["sourcePages"] = args.source_page
    if args.page_type not in {"question"} and args.related_page:
        frontmatter["relatedPages"] = args.related_page

    frontmatter["createdAt"] = created_at
    frontmatter["updatedAt"] = args.updated_at or created_at
    frontmatter["aliases"] = args.alias
    frontmatter["tags"] = args.tag
    if args.page_type == "source":
        frontmatter["attachments"] = args.attachment
    return frontmatter


def validate_source_args(args: argparse.Namespace) -> None:
    if args.source_role not in VALID_SOURCE_ROLES:
        raise ScaffoldingError("--source-role must be whole, parent, or part")
    if args.source_role == "whole":
        if args.parent_source_id or args.part_index is not None or args.part_count is not None or args.locator:
            raise ScaffoldingError("whole source pages must not include part fields")
    elif args.source_role == "parent":
        if not args.source_part:
            raise ScaffoldingError("parent source pages require at least one --source-part path")
        if args.parent_source_id or args.part_index is not None or args.locator:
            raise ScaffoldingError("parent source pages must not include child-only part fields")
    elif args.source_role == "part":
        if not args.parent_source_id:
            raise ScaffoldingError("part source pages require --parent-source-id")
        if args.part_index is None or args.part_count is None:
            raise ScaffoldingError("part source pages require --part-index and --part-count")
        if args.part_index < 1 or args.part_count < 1 or args.part_index > args.part_count:
            raise ScaffoldingError("--part-index must be between 1 and --part-count")
        if not args.locator:
            raise ScaffoldingError("part source pages require --locator")
    if not args.source_url and not args.origin_path:
        raise ScaffoldingError("source pages require --source-url or --origin-path")


def validate_dates(args: argparse.Namespace, created_at: str) -> None:
    for field_name in ("updated_at", "source_date", "retrieved_at", "published_at", "converted_at", "opened_at"):
        value = getattr(args, field_name, None)
        if value:
            require_date(value, f"--{field_name.replace('_', '-')}")
    require_date(created_at, "--date")


def write_operational_log(wiki_root: Path, message: str) -> None:
    subprocess.run(
        [sys.executable, str(wiki_root / LOG_SCRIPT), "--message", message],
        check=True,
        capture_output=True,
        text=True,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a canonical page from supplied metadata and body content.")
    parser.add_argument("--type", dest="page_type", required=True, choices=sorted(VALID_PAGE_TYPES), help="Page type to create")
    parser.add_argument("--subtype", required=True, help="Page-type-specific subtype or question domain")
    parser.add_argument("--slug", required=True, help="Stable kebab-case slug")
    parser.add_argument("--title", required=True, help="Page title")
    body = parser.add_mutually_exclusive_group(required=True)
    body.add_argument("--body-file", help="Path to Markdown body content")
    body.add_argument("--body", help="Markdown body content")
    parser.add_argument("--date", dest="created_at", default=date.today().isoformat(), help="createdAt date; defaults to today")
    parser.add_argument("--updated-at", help="updatedAt date; defaults to createdAt")
    parser.add_argument("--status", help="Page status; defaults by page type")
    parser.add_argument("--alias", action="append", default=[], help="Alias value; repeatable")
    parser.add_argument("--tag", action="append", default=[], help="Tag value; repeatable")
    parser.add_argument("--source-page", action="append", default=[], help="Related source page ID; repeatable")
    parser.add_argument("--related-page", action="append", default=[], help="Related page ID; repeatable")
    parser.add_argument("--related-claim", action="append", default=[], help="Related claim ID; repeatable")

    parser.add_argument("--source-date", help="Date component for source IDs; defaults to retrievedAt or createdAt")
    parser.add_argument("--source-url", help="Origin URL for source pages")
    parser.add_argument("--origin-path", help="Origin path for source pages")
    parser.add_argument("--retrieved-at", help="Source retrieval date")
    parser.add_argument("--published-at", help="Source publication date")
    parser.add_argument("--converted-at", help="Source conversion date")
    parser.add_argument("--conversion-tool", help="Conversion tool name")
    parser.add_argument("--conversion-tool-version", help="Conversion tool version")
    parser.add_argument("--conversion-backend", help="Conversion backend")
    parser.add_argument("--conversion-warning", action="append", default=[], help="Conversion warning; repeatable")
    parser.add_argument("--source-role", choices=sorted(VALID_SOURCE_ROLES), default="whole", help="Source role")
    parser.add_argument("--source-part", action="append", default=[], help="Parent source part path; repeatable")
    parser.add_argument("--parent-source-id", help="Parent source ID for source parts")
    parser.add_argument("--part-index", type=int, help="One-based source part index")
    parser.add_argument("--part-count", type=int, help="Total source part count")
    parser.add_argument("--locator", help="Stable source part locator")
    parser.add_argument("--attachment", action="append", default=[], help="Attachment ID/path; repeatable")

    parser.add_argument("--canonical-name", help="Entity canonical name")
    parser.add_argument("--claim-text", help="Atomic claim text")
    parser.add_argument("--confidence", type=float, default=0.60, help="Claim confidence")
    parser.add_argument("--subject-page-id", help="Claim subject page ID")
    parser.add_argument("--source-id", action="append", default=[], help="Claim source ID; repeatable")
    parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        help=(
            "Claim evidence record; repeatable. Use a JSON object or semicolon-separated key=value pairs. "
            "Required fields: id, sourceId, path, kind, relation, weight, updatedAt."
        ),
    )
    parser.add_argument("--priority", default="medium", choices=sorted(VALID_QUESTION_PRIORITIES), help="Question priority")
    parser.add_argument("--opened-at", help="Question openedAt date")
    parser.add_argument("--scope", help="Synthesis scope")
    parser.add_argument("--derived-claim", action="append", default=[], help="Synthesis derived claim ID; repeatable")

    parser.add_argument("--dry-run", action="store_true", help="Print resolved page data without writing")
    parser.add_argument("--no-log", action="store_true", help="Do not write an operational log entry")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    wiki_root = Path.cwd().resolve()

    try:
        require_slug(args.slug)
        validate_subtype(args.page_type, args.subtype)
        validate_dates(args, args.created_at)
        if args.page_type == "source":
            validate_source_args(args)
        elif args.page_type == "claim":
            validate_claim_args(args)
        elif args.page_type == "synthesis":
            validate_synthesis_args(args)
        elif args.evidence:
            raise ScaffoldingError("--evidence only applies to claim pages")
        elif args.source_role != "whole":
            raise ScaffoldingError("source role flags only apply to source pages")

        body = read_body(args, wiki_root)
        validate_body(args.page_type, body)
        page_id = build_page_id(args, args.created_at)
        rel_path = page_path(args, page_id)
        abs_path = wiki_root / rel_path
        duplicate_path = find_duplicate_id(wiki_root, page_id)
        if duplicate_path:
            raise ScaffoldingError(f"page ID already exists in {duplicate_path}")
        if abs_path.exists():
            raise ScaffoldingError(f"target file already exists: {rel_path}")

        frontmatter = build_frontmatter(args, page_id, args.created_at)
        markdown = render_markdown(frontmatter, body)
        result = {
            "schemaVersion": 1,
            "mode": "dry-run" if args.dry_run else "write",
            "mutating": not args.dry_run,
            "id": page_id,
            "path": str(rel_path).replace("\\", "/"),
            "pageType": args.page_type,
            "status": frontmatter["status"],
            "written": False,
        }

        if args.dry_run:
            result["frontmatter"] = frontmatter
        else:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(markdown, encoding="utf-8")
            result["written"] = True
            if not args.no_log:
                write_operational_log(wiki_root, f"create-page: created {args.page_type} page {page_id} at {result['path']}")

        json.dump(result, sys.stdout, indent=None if args.compact else 2, sort_keys=True)
        sys.stdout.write("\n")
    except ScaffoldingError as exc:
        json.dump(
            {
                "schemaVersion": 1,
                "mode": "dry-run" if getattr(args, "dry_run", False) else "write",
                "mutating": False,
                "written": False,
                "error": str(exc),
            },
            sys.stdout,
            indent=None if getattr(args, "compact", False) else 2,
            sort_keys=True,
        )
        sys.stdout.write("\n")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
