#!/usr/bin/env python3
"""
AI Symptom Acquisition Audit™

Usage:
  python main.py --brand "Begin Health" --url "https://beginhealth.com"
  python main.py --brand "Seed" --url "seed.com" --prompts prompts.json
  python main.py config.json
  python main.py --list
"""

import argparse
import json
import os
import sys
import re
import time

from models import AuditReport
from modules.visibility import run_visibility_sampling
from modules.competitors import aggregate_competitors
from modules.citations import extract_citations
from modules.grounding import classify_grounding
from modules.evidence_gap import analyze_evidence_gaps
from modules.report import generate_markdown
from database import init_db, save_audit, list_audits


def load_prompts(path: str) -> list[str]:
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("prompts file must be a JSON array of strings")
    return [str(p).strip() for p in data if str(p).strip()]


def slug(brand_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", brand_name.lower()).strip("_")


def check_api_key():
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        print("\n[ERROR] GEMINI_API_KEY is not set.")
        print("  Set it with:  export GEMINI_API_KEY='your-key-here'\n")
        sys.exit(1)


def print_step(n: int, total: int, label: str):
    print(f"\n[{n}/{total}] {label}")


# ── --list command ────────────────────────────────────────────────────────────

def cmd_list():
    init_db()
    rows = list_audits()
    if not rows:
        print("\n  No audits found. Run your first one with:\n")
        print('  python main.py --brand "Begin Health" --url "https://beginhealth.com"\n')
        return

    # column widths
    W_ID   = 4
    W_NAME = 24
    W_URL  = 30
    W_ST   = 8
    W_DATE = 19

    header = (
        f"{'ID':<{W_ID}}  {'Brand':<{W_NAME}}  {'Website':<{W_URL}}"
        f"  {'Status':<{W_ST}}  {'Created (UTC)':<{W_DATE}}  Report file"
    )
    sep = "-" * len(header)

    print(f"\n  Audit history  ({len(rows)} total)\n")
    print(f"  {header}")
    print(f"  {sep}")

    for r in rows:
        brand  = r["brand_name"][:W_NAME]
        url    = r["brand_website"][:W_URL]
        status = r["status"][:W_ST]
        date   = (r["created_at"] or "")[:W_DATE]
        report = f"reports/{slug(r['brand_name'])}_audit.md"
        exists = "✓" if os.path.exists(report) else "✗"
        print(
            f"  {r['id']:<{W_ID}}  {brand:<{W_NAME}}  {url:<{W_URL}}"
            f"  {status:<{W_ST}}  {date:<{W_DATE}}  {exists} {report}"
        )

    print()


# ── run audit ────────────────────────────────────────────────────────────────

def run_audit(brand_name: str, brand_url: str, prompts_path: str):
    check_api_key()
    init_db()

    if not os.path.exists(prompts_path):
        print(f"[ERROR] Prompts file not found: {prompts_path}")
        sys.exit(1)

    prompts = load_prompts(prompts_path)
    if not prompts:
        print("[ERROR] Prompts file is empty.")
        sys.exit(1)

    started = time.time()
    total_steps = 6

    print(f"\n{'='*60}")
    print(f"  AI Symptom Acquisition Audit™")
    print(f"  Brand   : {brand_name}")
    print(f"  Website : {brand_url}")
    print(f"  Prompts : {len(prompts)} queries × 5 samples = {len(prompts) * 5} total")
    print(f"{'='*60}")

    report = AuditReport(
        brand_name=brand_name,
        brand_website=brand_url,
        prompts_used=prompts,
    )

    # ── Module A: Visibility Sampling ─────────────────────────────
    print_step(1, total_steps, "Module A — Visibility Sampling")
    try:
        report.visibility = run_visibility_sampling(brand_name, prompts)
        v = report.visibility
        print(f"  ✓ Score: {v.visibility_score}%  ({v.mentions} mentions / {v.samples} samples)")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        _save_failed(brand_name, brand_url)
        sys.exit(1)

    # ── Module B: Competitor Aggregation ──────────────────────────
    print_step(2, total_steps, "Module B — Competitor Aggregation")
    try:
        report.competitors = aggregate_competitors(report.visibility, brand_name)
        top = list(report.competitors.items())[:3]
        top_str = ", ".join(f"{b}({n})" for b, n in top)
        print(f"  ✓ Top competitors: {top_str or 'none detected'}")
    except Exception as e:
        print(f"  ✗ FAILED: {e} — continuing")

    # ── Module C: Citation Surface ────────────────────────────────
    print_step(3, total_steps, "Module C — Citation Surface")
    try:
        report.citations = extract_citations(report.visibility, brand_url)
        c = report.citations
        print(f"  ✓ Brand citations: {c.brand_domain_mentions} / {c.total_citation_mentions} total ({c.citation_share}%)")
    except Exception as e:
        print(f"  ✗ FAILED: {e} — continuing")

    # ── Module D: Grounding Classification ───────────────────────
    print_step(4, total_steps, "Module D — Grounding Classification")
    try:
        report.grounding = classify_grounding(report.visibility)
        g = report.grounding
        print(f"  ✓ Static: {g.static_mentions}  Web: {g.web_mentions}")
    except Exception as e:
        print(f"  ✗ FAILED: {e} — continuing")

    # ── Module E: Evidence Gap Analysis ──────────────────────────
    print_step(5, total_steps, "Module E — Evidence Gap Analysis (temperature=0)")
    try:
        gaps, wins = analyze_evidence_gaps(
            brand_name, brand_url,
            report.visibility, report.citations,
            report.competitors, report.grounding,
        )
        report.evidence_gaps = gaps
        report.quick_wins = wins
        print(f"  ✓ Gaps: {len(gaps)}   Quick wins: {len(wins)}")
    except Exception as e:
        print(f"  ✗ FAILED: {e} — continuing")

    # ── Report Generation ─────────────────────────────────────────
    print_step(6, total_steps, "Generating Reports")
    markdown = generate_markdown(report)

    os.makedirs("reports", exist_ok=True)
    base      = slug(brand_name)
    md_path   = f"reports/{base}_audit.md"
    json_path = f"reports/{base}_audit.json"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    report_dict = report.model_dump(exclude={"visibility": {"raw_responses"}})
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, default=str)

    save_audit(brand_name, brand_url, report_dict, markdown)

    elapsed = round(time.time() - started, 1)

    print(f"\n{'='*60}")
    print(f"  ✅ AUDIT COMPLETE  ({elapsed}s)")
    print(f"  Markdown : {md_path}")
    print(f"  JSON     : {json_path}")
    print(f"{'='*60}")
    print(f"\n⚠  Human review required before sending to a client.\n")


def _save_failed(brand_name: str, brand_url: str):
    os.makedirs("reports", exist_ok=True)
    path = f"reports/{slug(brand_name)}_audit_FAILED.json"
    with open(path, "w") as f:
        json.dump({"status": "FAILED", "brand": brand_name, "url": brand_url}, f, indent=2)
    print(f"  Saved failure record: {path}")


# ── entry point ───────────────────────────────────────────────────────────────

def parse_args():
    # shortcut: python main.py config.json
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json") and not sys.argv[1].startswith("-"):
        with open(sys.argv[1]) as f:
            cfg = json.load(f)
        return "run", cfg.get("brand"), cfg.get("url") or cfg.get("website"), cfg.get("prompts", "prompts.json")

    parser = argparse.ArgumentParser(
        description="AI Symptom Acquisition Audit™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            '  python main.py --brand "Begin Health" --url "https://beginhealth.com"\n'
            '  python main.py --brand "Seed" --url "seed.com" --prompts prompts.json\n'
            "  python main.py --list\n"
            "  python main.py config.json"
        ),
    )
    parser.add_argument("--brand",   help='Brand name, e.g. "Begin Health"')
    parser.add_argument("--url",     help="Brand website, e.g. https://beginhealth.com")
    parser.add_argument("--prompts", default="prompts.json", help="Prompts JSON file (default: prompts.json)")
    parser.add_argument("--list",    action="store_true",   help="List all past audits")

    args = parser.parse_args()

    if args.list:
        return "list", None, None, None

    if not args.brand or not args.url:
        parser.error("--brand and --url are required (or use --list to view past audits)")

    return "run", args.brand, args.url, args.prompts


if __name__ == "__main__":
    cmd, brand, url, prompts_path = parse_args()
    if cmd == "list":
        cmd_list()
    else:
        run_audit(brand, url, prompts_path)
