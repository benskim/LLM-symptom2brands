from datetime import datetime
from models import AuditReport


def generate_markdown(report: AuditReport) -> str:
    v = report.visibility
    c = report.citations
    g = report.grounding
    score = v.visibility_score if v else 0.0

    if score == 0:
        verdict = "❌ Not detected in AI recommendations"
    elif score < 10:
        verdict = "⚠️  Very low visibility — rarely recommended"
    elif score < 30:
        verdict = "🔶 Low visibility — occasionally recommended"
    elif score < 60:
        verdict = "🟡 Moderate visibility — sometimes recommended"
    else:
        verdict = "✅ Good visibility — frequently recommended"

    bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# AI Visibility Audit: {report.brand_name}",
        f"",
        f"**Date:** {now}  ",
        f"**Website:** {report.brand_website}  ",
        f"**Verdict:** {verdict}",
        f"",
        f"---",
        f"",
        f"## Executive Summary",
        f"",
        f"{report.brand_name} appeared in **{v.mentions if v else 0}** of **{v.samples if v else 0}** AI responses "
        f"sampled across {len(report.prompts_used)} gut health queries ({5} samples each).  ",
        f"Visibility score: **{score}%**  ",
        f"Top competitor by AI mentions: **{list(report.competitors.keys())[0] if report.competitors else 'N/A'}**",
        f"",
        f"---",
        f"",
        f"## 1. Visibility Score",
        f"",
        f"```",
        f"Score: {score}%",
        f"[{bar}]",
        f"Mentions : {v.mentions if v else 0}",
        f"Samples  : {v.samples if v else 0}",
        f"Prompts  : {len(report.prompts_used)}",
        f"```",
        f"",
        f"---",
        f"",
        f"## 2. Competitor Capture",
        f"",
    ]

    if report.competitors:
        lines += ["| Rank | Brand | AI Mentions |", "|------|-------|-------------|"]
        for i, (brand, count) in enumerate(list(report.competitors.items())[:10], 1):
            lines.append(f"| {i} | {brand} | {count} |")
    else:
        lines.append("_No competitors detected._")

    lines += [
        f"",
        f"---",
        f"",
        f"## 3. Citation Surface",
        f"",
        f"- Brand domain citations: **{c.brand_domain_mentions if c else 0}**",
        f"- Total citations in responses: **{c.total_citation_mentions if c else 0}**",
        f"- Brand citation share: **{c.citation_share if c else 0}%**",
        f"",
    ]

    if c and c.domain_counts:
        lines += ["| Domain | Count |", "|--------|-------|"]
        for domain, count in list(c.domain_counts.items())[:8]:
            lines.append(f"| {domain} | {count} |")
        lines.append("")

    if g:
        lines += [
            f"**Grounding signals:**",
            f"- Static knowledge: {g.static_mentions}",
            f"- Web-sourced: {g.web_mentions}",
            f"",
        ]

    lines += [
        f"---",
        f"",
        f"## 4. Evidence Gaps",
        f"",
    ]

    if report.evidence_gaps:
        conf_emoji = {"high": "🔴", "medium": "🟠", "low": "🟡"}
        for gap in report.evidence_gaps:
            emoji = conf_emoji.get(gap.confidence, "⚪")
            lines.append(f"### {emoji} {gap.gap_type.replace('_', ' ').title()} ({gap.confidence.upper()} confidence)")
            lines.append("")
            for e in gap.evidence:
                lines.append(f"- {e}")
            lines.append("")
    else:
        lines.append("_No evidence gaps identified._\n")

    lines += [
        f"---",
        f"",
        f"## 5. Quick Wins",
        f"",
        f"_Prioritized by estimated impact. Human review required before acting._",
        f"",
    ]

    for i, win in enumerate(report.quick_wins[:10], 1):
        lines.append(f"{i}. {win}")

    lines += [
        f"",
        f"---",
        f"",
        f"## Human Review Checklist",
        f"",
        f"- [ ] Visibility score is plausible for this brand",
        f"- [ ] Competitor names are real (no hallucinations)",
        f"- [ ] Evidence gaps are data-backed, not invented",
        f"- [ ] Quick wins apply to this specific brand",
        f"- [ ] No forbidden language: root cause / guaranteed / definitive",
        f"",
        f"---",
        f"",
        f"_AI Visibility Audit™ — {now}_",
    ]

    return "\n".join(lines)
