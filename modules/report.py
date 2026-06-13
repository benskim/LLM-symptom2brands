from datetime import datetime
from models import AuditReport


def generate_markdown_report(report: AuditReport) -> str:
    v = report.visibility
    c = report.citations
    g = report.grounding

    lines = []

    lines.append(f"# AI Visibility Audit: {report.brand_name}")
    lines.append(f"\n**Generated:** {report.created_at[:10]}  ")
    lines.append(f"**Website:** {report.brand_website}  ")
    lines.append(f"**Status:** Ready for human review\n")
    lines.append("---\n")

    lines.append("## Executive Summary\n")
    score = v.visibility_score if v else 0
    if score == 0:
        verdict = "❌ Not detected in AI recommendations"
    elif score < 10:
        verdict = "⚠️ Very low visibility — rarely recommended"
    elif score < 30:
        verdict = "🔶 Low visibility — occasionally recommended"
    elif score < 60:
        verdict = "🟡 Moderate visibility — sometimes recommended"
    else:
        verdict = "✅ Good visibility — frequently recommended"

    lines.append(f"**AI Visibility Verdict:** {verdict}\n")
    lines.append(
        f"{report.brand_name} appeared in **{v.mentions if v else 0}** out of "
        f"**{v.samples if v else 0}** AI responses sampled across gut health queries. "
        f"This translates to a visibility score of **{score}%**.\n"
    )
    lines.append("---\n")

    lines.append("## Section 1 — Visibility Score\n")
    if v:
        bar_filled = int(score / 5)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        lines.append(f"```\nVisibility Score: {score}%\n[{bar}]\nMentions: {v.mentions} / {v.samples} samples\n```\n")
        lines.append(f"- **Score:** {score}%")
        lines.append(f"- **Mentions:** {v.mentions}")
        lines.append(f"- **Samples taken:** {v.samples}")
        lines.append(f"- **Prompts tested:** 5 gut-health queries × 5 samples each\n")
    else:
        lines.append("_Visibility data unavailable._\n")
    lines.append("---\n")

    lines.append("## Section 2 — Competitor Capture\n")
    if report.competitors:
        lines.append("| Brand | AI Mentions |")
        lines.append("|-------|------------|")
        for brand, count in list(report.competitors.items())[:10]:
            lines.append(f"| {brand} | {count} |")
        lines.append("")
        top = list(report.competitors.keys())[0] if report.competitors else "N/A"
        lines.append(f"**Top competitor detected:** {top}\n")
    else:
        lines.append("_No competitor data extracted._\n")
    lines.append("---\n")

    lines.append("## Section 3 — Citation Surface\n")
    if c:
        lines.append(f"- **Brand domain citations:** {c.brand_domain_mentions}")
        lines.append(f"- **Total citations found:** {c.total_citation_mentions}")
        lines.append(f"- **Brand citation share:** {c.citation_share}%\n")
        if c.domain_counts:
            lines.append("**Top cited domains:**\n")
            lines.append("| Domain | Count |")
            lines.append("|--------|-------|")
            for domain, count in list(c.domain_counts.items())[:8]:
                lines.append(f"| {domain} | {count} |")
            lines.append("")
        if g:
            lines.append(f"**Grounding classification:**")
            lines.append(f"- Static knowledge signals: {g.static_mentions}")
            lines.append(f"- Web-sourced signals: {g.web_mentions}\n")
    else:
        lines.append("_Citation data unavailable._\n")
    lines.append("---\n")

    lines.append("## Section 4 — Evidence Gaps\n")
    if report.evidence_gaps:
        for gap in report.evidence_gaps:
            confidence_emoji = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(gap.confidence, "⚪")
            lines.append(f"### {confidence_emoji} {gap.gap_type.replace('_', ' ').title()}")
            lines.append(f"**Confidence:** {gap.confidence.upper()}\n")
            for e in gap.evidence:
                lines.append(f"- {e}")
            lines.append("")
    else:
        lines.append("_No evidence gaps identified._\n")
    lines.append("---\n")

    lines.append("## Section 5 — Quick Wins\n")
    lines.append("_Prioritized by estimated impact. Human review required before acting._\n")
    if report.quick_wins:
        for i, win in enumerate(report.quick_wins[:10], 1):
            lines.append(f"{i}. {win}")
        lines.append("")
    else:
        lines.append("_No recommendations generated._\n")
    lines.append("---\n")

    lines.append("## ⚠️ Human Review Checklist\n")
    lines.append("Before sending this report to a client, verify:\n")
    lines.append("- [ ] Visibility score matches expectations for the brand")
    lines.append("- [ ] Competitor names are correctly identified (not false positives)")
    lines.append("- [ ] Evidence gaps are grounded in the data, not invented")
    lines.append("- [ ] Quick wins are relevant to this specific brand")
    lines.append("- [ ] No claims made about \"root cause\" or \"guaranteed\" outcomes")
    lines.append("- [ ] Report tone is professional and founder-friendly\n")
    lines.append("---\n")
    lines.append(f"*AI Symptom Acquisition Audit™ — Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")

    return "\n".join(lines)
