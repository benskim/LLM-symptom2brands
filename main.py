#!/usr/bin/env python3
"""
AI Symptom Acquisition Audit™
Usage:
    python main.py --brand "Begin Health" --url "https://beginhealth.com"
    python main.py --brand "Seed" --url "seed.com" --prompts prompts.json
    python main.py config.json
"""

import argparse
import json
import os
import sys
import re
import time
from datetime import datetime
from pathlib import Path

from models import AuditReport
from modules.visibility import run_visibility_sampling
from modules.competitors import aggregate_competitors
from modules.citations import extract_citations
from modules.grounding import classify_grounding
from modules.evidence_gap import analyze_evidence_gaps
from modules.report import generate_markdown
from database import init_db, save_audit


def load_prompts(path: str) -> list[str]:
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("prompts file must be a JSON array of strings")
    return [str(p).strip() for p in data if str(p).strip()]


def slug(brand_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", brand_name.lower()).strip("_")


def parse_args():
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json") and not sys.argv[1].startswith("-"):
        with open(sys.argv[1]) as f:
            cfg = json.load(f)
        return cfg.get("brand"), cfg.get("url") or cfg.get("website"), cfg.get("prompts", "prompts.json")

    parser = argparse.ArgumentParser(
        description="AI Symptom Acquisition Audit™ — generate an AI visibility report for a gut health brand"
    )
    parser.add_argument("--brand", required=True, help='Brand name, e.g. "Begin Health"')
    parser.add_argument("--url",   required=True, help="Brand website, e.g. https://beginhealth.com")
    parser.add_argument("--prompts", default="prompts.json", help="Path to prompts JSON file (default: prompts.json)")
    args = parser.parse_args()
    return args.brand, args.url, args.prompts


def check_api_key():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        print("\n[ERROR] GEMINI_API_KEY is not set.")
        print("  Set it with:  export GEMINI_API_KEY='your-key-here'")
        print("  Or add it to a .env file and source it before running.\n")
        sys.exit(1)


def print_step(n: int, total: int, label: str):
    print(f"\n[{n}/{total}] {label}")


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

    total_steps = 6
    started = time.time()

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

    # ── Module A: Visibility Sampling ────────────────────────────
    print_step(1, total_steps, "Module A — Visibility Sampling")
    try:
        report.visibility = run_visibility_sampling(brand_name, prompts)
        v = report.visibility
        print(f"  ✓ Score: {v.visibility_score}%  ({v.mentions} mentions / {v.samples} samples)")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        report.status = "FAILED"
        _save_failed(brand_name, brand_url, report)
        sys.exit(1)

    # ── Module B: Competitor Aggregation ─────────────────────────
    print_step(2, total_steps, "Module B — Competitor Aggregation")
    try:
        report.competitors = aggregate_competitors(report.visibility, brand_name)
        top = list(report.competitors.items())[:3]
        top_str = ", ".join(f"{b}({n})" for b, n in top)
        print(f"  ✓ Top competitors: {top_str or 'none detected'}")
    except Exception as e:
        print(f"  ✗ FAILED: {e} — continuing")

    # ── Module C: Citation Surface ───────────────────────────────
    print_step(3, total_steps, "Module C — Citation Surface")
    try:
        report.citations = extract_citations(report.visibility, brand_url)
        c = report.citations
        print(f"  ✓ Brand citations: {c.brand_domain_mentions} / {c.total_citation_mentions} total "
              f"({c.citation_share}%)")
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
    print_step(5, total_steps, "Module E — Evidence Gap Analysis (Gemini, temperature=0)")
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
    base = slug(brand_name)
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


def _save_failed(brand_name, brand_url, report):
    os.makedirs("reports", exist_ok=True)
    base = slug(brand_name)
    path = f"reports/{base}_audit_FAILED.json"
    with open(path, "w") as f:
        json.dump({"status": "FAILED", "brand": brand_name, "url": brand_url}, f, indent=2)
    print(f"  Saved failure record: {path}")


if __name__ == "__main__":
    brand, url, prompts_path = parse_args()
    run_audit(brand, url, prompts_path)
